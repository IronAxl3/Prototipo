import os  
import re  
import markdown  
import warnings  
warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")
import logging
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google.genai").propagate = False
from datetime import datetime  
import io  
import time  
import zipfile  
import pymupdf  
from fpdf import FPDF  
from google import genai  
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception  

MODELO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")  
LIMITE_CARACTERES_DOC = 20000  


def extraer_texto_pdf(archivo_pdf):
    """Extrae texto plano de un PDF."""
    try:
        if isinstance(archivo_pdf, (bytes, bytearray)):
            data = bytes(archivo_pdf)
        elif hasattr(archivo_pdf, "read"):
            try:
                archivo_pdf.seek(0)
            except Exception:
                pass
            data = archivo_pdf.read()
            if not data:
                return "[ERROR] Archivo PDF vacío."
        else:
            return "[ERROR] Formato de archivo no soportado."

        documento = pymupdf.open(stream=data, filetype="pdf")
        texto_completo = ""
        for pagina in documento:
            texto_completo += pagina.get_text()
        documento.close()

        if not texto_completo.strip():
            return "[AVISO] El PDF no contiene texto extraíble (posible escaneo sin OCR)."
        return texto_completo
    except Exception as e:
        return f"[ERROR] No se pudo extraer el texto del PDF: {e}"


def procesar_zip_proyectos(archivo_zip):
    """Agrupa PDFs por carpeta (proyecto) y extrae texto. Retorna (proyectos, advertencias)."""
    proyectos = []
    advertencias = []
    try:
        if hasattr(archivo_zip, "getvalue"):
            try:
                zip_bytes = archivo_zip.getvalue()
            except Exception:
                try:
                    archivo_zip.seek(0)
                except Exception:
                    pass
                zip_bytes = archivo_zip.read()
        elif hasattr(archivo_zip, "read"):
            try:
                archivo_zip.seek(0)
            except Exception:
                pass
            zip_bytes = archivo_zip.read()
        else:
            zip_bytes = bytes(archivo_zip)

        if not zip_bytes:
            return [], ["El archivo ZIP está vacío."]

        agrupados = {}
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                ruta = info.filename
                if ruta.startswith("__MACOSX") or "/__MACOSX/" in ruta:
                    continue
                if not ruta.lower().endswith(".pdf"):
                    continue
                ruta_norm = ruta.replace("\\", "/")
                partes = [p for p in ruta_norm.split("/") if p]
                if len(partes) == 1:
                    carpeta = "Proyecto_sin_carpeta"
                    nombre_arch = partes[0]
                else:
                    carpeta = partes[0].strip()
                    nombre_arch = partes[-1]
                if not carpeta:
                    continue
                if carpeta not in agrupados:
                    agrupados[carpeta] = []
                with z.open(info) as f:
                    pdf_bytes = f.read()
                agrupados[carpeta].append((nombre_arch, pdf_bytes))

            if not agrupados:
                return [], ["El ZIP no contiene archivos PDF con estructura de carpetas válida."]

            for nombre_proyecto, archivos in agrupados.items():
                try:
                    texto_proyecto = texto_informe = texto_anexos = None
                    # Patrones de palabra entera para evitar falsos positivos en nombres de archivo
                    _pat_proyecto = re.compile(r"\b(proyecto|aprobado)\b", re.IGNORECASE)
                    _pat_informe = re.compile(r"\b(informe|t[eé]cnico)\b", re.IGNORECASE)
                    _pat_anexo = re.compile(r"\banexo\b", re.IGNORECASE)

                    for nombre_arch, data in archivos:
                        if _pat_proyecto.search(nombre_arch) and texto_proyecto is None:
                            texto_proyecto = extraer_texto_pdf(io.BytesIO(data))
                        elif _pat_informe.search(nombre_arch) and texto_informe is None:
                            texto_informe = extraer_texto_pdf(io.BytesIO(data))
                        elif _pat_anexo.search(nombre_arch) and texto_anexos is None:
                            texto_anexos = extraer_texto_pdf(io.BytesIO(data))

                    faltantes = []
                    if texto_proyecto is None:
                        faltantes.append("Proyecto Aprobado")
                    if texto_informe is None:
                        faltantes.append("Informe Técnico")
                    if texto_anexos is None:
                        faltantes.append("Anexos")
                    if faltantes:
                        advertencias.append(f"Proyecto '{nombre_proyecto}' omitido: faltan {', '.join(faltantes)} ({len(archivos)} PDF(s) encontrados).")
                        continue

                    tiene_error = False
                    for txt, etiqueta in [(texto_proyecto, "Proyecto Aprobado"), (texto_informe, "Informe Técnico"), (texto_anexos, "Anexos")]:
                        if txt.startswith("[ERROR]"):
                            advertencias.append(f"Proyecto '{nombre_proyecto}' omitido: error en {etiqueta} - {txt}")
                            tiene_error = True
                            break
                        if txt.startswith("[AVISO]"):
                            advertencias.append(f"Proyecto '{nombre_proyecto}': {etiqueta} sin texto extraíble (posible escaneo).")
                    if tiene_error:
                        continue

                    proyectos.append({"nombre": nombre_proyecto, "texto_proyecto": texto_proyecto, "texto_informe": texto_informe, "texto_anexos": texto_anexos})
                except Exception as e:
                    advertencias.append(f"Proyecto '{nombre_proyecto}' error inesperado: {e}")
                    continue
        return proyectos, advertencias
    except zipfile.BadZipFile:
        return [], ["El archivo no es un ZIP válido."]
    except Exception as e:
        return [], [f"Error al procesar ZIP: {e}"]


def _es_error_rate_limit(exc):
    """Detecta errores 429/quota para reintento."""
    # Si la excepción expone código de estado HTTP, verificarlo directamente
    status = getattr(exc, "code", None) or getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if status is not None:
        try:
            return int(status) == 429
        except (ValueError, TypeError):
            pass
    msg = str(exc).lower()
    palabras_clave = ["429", "resourceexhausted", "quota exceeded", "too many requests", "rate limit"]
    return any(p in msg for p in palabras_clave)


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60), retry=retry_if_exception(_es_error_rate_limit), reraise=True)
def _llamar_gemini_con_retry(cliente, prompt):
    """Llama a Gemini con backoff exponencial ante 429."""
    return cliente.models.generate_content(model=MODELO_GEMINI, contents=prompt)


def _truncar_con_aviso(texto, limite, nombre_documento):
    """Trunca un texto al límite indicado y agrega aviso si se cortó contenido."""
    if len(texto) > limite:
        return texto[:limite] + f"\n\n[AVISO: El texto de '{nombre_documento}' fue truncado a {limite} caracteres por límite de contexto del modelo.]"
    return texto


def auditar_proyecto_ia(texto_proyecto, texto_informe, texto_anexos, api_key):
    """Audita congruencia documental con IA (4 secciones)."""
    texto_proyecto = _truncar_con_aviso(texto_proyecto, LIMITE_CARACTERES_DOC, "Proyecto Aprobado")
    texto_informe = _truncar_con_aviso(texto_informe, LIMITE_CARACTERES_DOC, "Informe Técnico")
    texto_anexos = _truncar_con_aviso(texto_anexos, LIMITE_CARACTERES_DOC, "Anexos")

    prompt = f"""
    Eres un auditor corporativo senior, independiente y riguroso, con redacción impecable, formal y ejecutiva en español neutro.
    Tu misión es contrastar con máximo rigor tres documentos de un mismo proyecto y producir un informe claro, trazable y visualmente estructurado.

    ============================================================
    DOCUMENTO 1 - PROYECTO APROBADO (fuente contractual y vinculante)
    ============================================================
    {texto_proyecto}

    ============================================================
    DOCUMENTO 2 - INFORME TÉCNICO (resultados reportados por el ejecutor)
    ============================================================
    {texto_informe}

    ============================================================
    DOCUMENTO 3 - ANEXOS (evidencias que respaldan el Informe)
    ============================================================
    {texto_anexos}

    ============================================================
    INSTRUCCIÓN DE REDACCIÓN Y FORMATO - CUMPLE ESTRICTAMENTE
    ============================================================
    Redacta en español formal, preciso y corporativo. Usa frases cortas, voz activa y terminología técnica consistente.
    Evita coloquialismos y repeticiones. Prioriza la evidencia sobre la opinión.

    Entrega el reporte en Markdown impecable usando EXACTAMENTE esta estructura con encabezados visibles:

    Enumera de forma literal y numerada cada objetivo y entregable explícitamente declarado en el Proyecto Aprobado.
    Cita textualmente entre comillas cuando sea relevante. No infieras compromisos no escritos.

    Para cada objetivo del punto 1, indica en una tabla Markdown el estado: **SÍ** | **NO** | **PARCIAL**.
    Columnas sugeridas: | Entregable | Estado | Evidencia en Informe (sección/página/dato) | Observación técnica |
    Justifica cada estado citando literalmente la sección o dato del Informe Técnico.

    Evalúa si los Anexos respaldan de forma CUANTITATIVA y CUALITATIVA los resultados del Informe.
    Señala con viñetas: discrepancias numéricas, fechas inconsistentes, soportes ausentes o no trazables, y calidad de la evidencia.

    Emite un veredicto único en negrita: **CUMPLE** | **CUMPLE PARCIALMENTE** | **NO CUMPLE**.
    Añade un párrafo de síntesis ejecutiva (4-6 líneas) y una lista de riesgos de incumplimiento priorizados con impacto.

    REGLAS DE RIGOR Y ESTILO:
    - No inventes información no presente en los documentos.
    - Si un dato no es verificable, escribe **"NO VERIFICABLE"** y explica por qué.
    - Mantén tono formal, objetivo y trazable. Usa negritas para estados y veredicto.
    - Todo el reporte debe ser Markdown limpio con tablas con bordes, listas y encabezados 
    """

    try:
        cliente = genai.Client(api_key=api_key)
        respuesta = _llamar_gemini_con_retry(cliente, prompt)
        return respuesta.text
    except Exception as e:
        return f"ERROR: No se pudo auditar con el modelo '{MODELO_GEMINI}': {e}\n\nVerifica tu API Key en https://aistudio.google.com y reintenta. Si es error 429, el sistema ya reintentó con backoff exponencial."


def generar_reporte_maestro(resultados, advertencias=None):
    """Concatena auditorías en un Reporte Maestro."""
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = []
    lineas.append("# Reporte Maestro — Auditoría Documental Masiva\n")
    lineas.append(f"**Fecha:** {fecha}\n")
    lineas.append(f"**Proyectos auditados:** {len(resultados)}\n")
    lineas.append(f"**Proyectos omitidos/advertencias:** {len(advertencias) if advertencias else 0}\n")
    lineas.append("\n---\n")
    if advertencias:
        lineas.append("## Advertencias y proyectos omitidos\n")
        for adv in advertencias:
            lineas.append(f"- {adv}")
        lineas.append("\n---\n")
    if resultados:
        lineas.append("## Índice de proyectos\n")
        for nombre in resultados.keys():
            lineas.append(f"- {nombre}")
        lineas.append("\n---\n")
    for nombre, contenido in resultados.items():
        lineas.append(f"\n## Proyecto: {nombre}\n\n")
        lineas.append(contenido)
        lineas.append("\n\n---\n")
    if not resultados:
        lineas.append("\n*No se generó contenido auditable. Verifica que cada carpeta contenga los 3 PDFs requeridos.*\n")
    return "\n".join(lineas)


def _sanitizar_latin1(texto):
    """Reemplaza caracteres no compatibles con latin-1 y devuelve texto seguro para FPDF."""
    _map = {
        "—": "--", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "…": "...", "•": "-", "·": "-", "®": "(R)", "©": "(C)", "™": "(TM)",
        "€": "EUR", "£": "GBP", "¥": "JPY",
    }
    for k, v in _map.items():
        texto = texto.replace(k, v)
    return texto.encode("latin-1", "replace").decode("latin-1")


class ReporteFormal(FPDF):
    """PDF formal con header/footer corporativos."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.rect(10, 8, 190, 12)
        self.set_xy(10, 8)
        self.cell(190, 12, _sanitizar_latin1("REPORTE DE AUDITORIA DOCUMENTAL"), align="C")
        self.line(10, 22, 200, 22)
        self.ln(16)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, _sanitizar_latin1(f"Pagina {self.page_no()} de {{nb}}"), align="R")


def generar_pdf(texto, titulo="Reporte"):
    """Genera PDF formal desde Markdown (HTML con tablas, fallback a texto plano)."""
    try:
        texto = _sanitizar_latin1(texto)
        titulo = _sanitizar_latin1(titulo)

        html_crudo = markdown.markdown(texto, extensions=["tables"])
        html_final = re.sub(r"<table[^>]*>", '<table border="1" width="100%" cellpadding="4">', html_crudo)
        html_final = re.sub(r"<td\b[^>]*>(.*?)</td>", lambda m: f"<td>{re.sub(r'<[^>]+>', '', m.group(1))}</td>", html_final, flags=re.DOTALL)
        html_final = re.sub(r"<th\b[^>]*>(.*?)</th>", lambda m: f"<th>{re.sub(r'<[^>]+>', '', m.group(1))}</th>", html_final, flags=re.DOTALL)

        pdf = ReporteFormal()
        pdf.alias_nb_pages()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, _sanitizar_latin1(titulo), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, _sanitizar_latin1(f"Fecha de generación: {fecha}"), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 8, _sanitizar_latin1("Evaluacion de Congruencia"), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)
        pdf.set_font("Helvetica", size=10)
        pdf.write_html(html_final)
        return bytes(pdf.output())

    except Exception as e_html:
        print(f"[WARN] write_html falló (tablas complejas), reintentando en modo texto plano: {e_html}")
        try:
            pdf = ReporteFormal()
            pdf.alias_nb_pages()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, _sanitizar_latin1(titulo), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, _sanitizar_latin1(f"Fecha de generación: {fecha}"), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 11)
            pdf.cell(0, 8, _sanitizar_latin1("Evaluacion de Congruencia"), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)
            pdf.set_font("Helvetica", size=10)
            texto_plano = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
            texto_plano = re.sub(r"\*(.*?)\*", r"\1", texto_plano)
            texto_plano = re.sub(r"^#{1,6}\s*", "", texto_plano, flags=re.MULTILINE)
            for linea in texto_plano.split("\n"):
                safe = _sanitizar_latin1(linea)
                if safe.strip() == "":
                    pdf.ln(4)
                else:
                    pdf.multi_cell(0, 6, safe, new_x="LMARGIN", new_y="NEXT")
            return bytes(pdf.output())
        except Exception as e2:
            print(f"[ERROR] No se pudo generar el PDF ni siquiera en fallback: {e2}")
            return None
