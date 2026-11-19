import time                          
import streamlit as st               
from backend import (
    extraer_texto_pdf,          
    generar_pdf,                
    procesar_zip_proyectos,     
    auditar_proyecto_ia,        
    generar_reporte_maestro,    
)

st.set_page_config(
    page_title="DGITT // Auditoría Documental",
    page_icon=":material/school:",
    layout="wide",
)

with st.sidebar:
    st.markdown("<div style='font-family:JetBrains Mono,monospace; font-size:0.72rem; letter-spacing:0.10em; color:#9CA3AF; margin-bottom:4px;'> ÁREA DE INFORMÁTICA // DGITT</div>", unsafe_allow_html=True)
    st.header("Configuración")
    api_key = st.text_input(
        "API Key de Google AI Studio",
        type="password",
        help="Obtén tu clave gratuita en https://aistudio.google.com",
        key="api_key_sidebar",
        placeholder="AQ.Ab8…",
    )
    st.markdown("---")
    modo_oscuro = st.toggle("🌙 Modo noche", value=True, key="modo_oscuro", help="Fondo oscuro reduce fatiga visual")
    st.caption("Modo noche - para un descanso visual" if modo_oscuro else "Laboratorio claro — ideal para revisión diurna.")

if modo_oscuro:
    _bg, _card, _card2, _border, _border2, _text, _muted, _muted2, _accent, _accent2, _sidebar_bg = "#0F1115", "#16181E", "#1A1D24", "#23262E", "#2A2D36", "#CBD5E1", "#94A3B8", "#64748B", "#60A5FA", "#22D3EE", "#0B0D11"
else:
    _bg, _card, _card2, _border, _border2, _text, _muted, _muted2, _accent, _accent2, _sidebar_bg = "#F8FAFC", "#FFFFFF", "#F1F5F9", "#E2E8F0", "#CBD5E1", "#1E293B", "#64748B", "#94A3B8", "#3B82F6", "#06B6D4", "#F1F5F9"

st.html(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: {_bg} !important; }}
section[data-testid="stSidebar"] {{ background: {_sidebar_bg} !important; border-right: 1px solid {_border} !important; }}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {{ font-family: 'JetBrains Mono', monospace !important; letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.80rem !important; color: {_text} !important; border-bottom: 1px solid {_border} !important; padding-bottom: 10px; }}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {{ color: {_muted} !important; }}
div[data-testid="stTextInput"] input {{ background: {_card2} !important; border: 1px solid {_border2} !important; color: {_text} !important; border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important; }}
div[data-testid="stTextInput"] input::placeholder {{ color: {_muted} !important; }}
div[data-testid="stTextInput"] input:focus {{ border-color: {_accent} !important; box-shadow: 0 0 0 2px {_accent}20 !important; }}
button[data-baseweb="tab"] {{ font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important; letter-spacing: 0.06em !important; text-transform: uppercase !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ border-bottom: 2px solid {_accent} !important; color: {_text} !important; background: {_card} !important; }}
div[data-testid="stButton"] > button {{ border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; border: 1px solid {_border2} !important; background: {_card} !important; color: {_text} !important; box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important; }}
div[data-testid="stButton"] > button[kind="primary"] {{ background: {_accent} !important; color: 
div[data-testid="stButton"] > button[kind="primary"]:hover {{ background: 
section[data-testid="stFileUploader"] {{ background: {_card} !important; border: 1px solid {_border} !important; border-radius: 8px !important; padding: 2px !important; }}
section[data-testid="stFileUploaderDropzone"] {{ background: {_card2} !important; border: 1px dashed {_border2} !important; border-radius: 6px !important; }}
section[data-testid="stFileUploaderDropzone"] * {{ color: {_muted} !important; }}
section[data-testid="stFileUploader"] button {{ background: {_border2} !important; color: {_text} !important; border: 1px solid {_border2} !important; border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important; }}
section[data-testid="stFileUploader"] button:hover {{ background: {_border} !important; border-color: {_accent} !important; }}
div[data-testid="stCaptionContainer"] p {{ color: {_muted} !important; font-size: 0.82rem !important; line-height: 1.6 !important; }}
div[data-testid="stCaptionContainer"] code {{ background: {_card2} !important; border: 1px solid {_border} !important; color: {_muted} !important; padding: 2px 6px !important; border-radius: 4px !important; }}
div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li, div[data-testid="stMarkdownContainer"] ul, div[data-testid="stMarkdownContainer"] ol {{ color: {_text} !important; line-height: 1.65 !important; }}
div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2, div[data-testid="stMarkdownContainer"] h3, div[data-testid="stMarkdownContainer"] h4, div[data-testid="stMarkdownContainer"] h5, div[data-testid="stMarkdownContainer"] h6 {{ color: {_text} !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.02em !important; border-bottom: 1px solid {_border} !important; padding-bottom: 6px !important; margin-top: 18px !important; }}
div[data-testid="stMarkdownContainer"] strong, div[data-testid="stMarkdownContainer"] b {{ color: {_text} !important; font-weight: 700 !important; }}
div[data-testid="stMarkdownContainer"] em, div[data-testid="stMarkdownContainer"] i {{ color: {_muted} !important; }}
div[data-testid="stMarkdownContainer"] hr {{ border-color: {_border} !important; }}
div[data-testid="stMarkdownContainer"] blockquote {{ border-left: 3px solid {_accent} !important; background: {_card2} !important; color: {_muted} !important; padding: 10px 14px !important; border-radius: 4px !important; }}
div[data-testid="stMarkdownContainer"] th {{ background: 
div[data-testid="stMarkdownContainer"] table {{ border: 1px solid {_border} !important; border-collapse: collapse !important; background: {_card} !important; border-radius: 6px !important; overflow: hidden !important; }}
div[data-testid="stMarkdownContainer"] td {{ border: 1px solid {_border} !important; color: {_text} !important; background: {_card} !important; }}
div[data-testid="stMarkdownContainer"] tr:nth-child(even) td {{ background: {_card2} !important; }}
div[data-testid="stAlert"] {{ background: {_card} !important; border: 1px solid {_border} !important; border-radius: 6px !important; }}
/* Descargas - azul casual visible en noche, sin blanco quemado */
div[data-testid="stDownloadButton"] > button {{ background: {_accent}14 !important; border: 1px solid {_accent}33 !important; color: {_accent2 if modo_oscuro else _accent} !important; border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; letter-spacing: 0.04em !important; font-weight: 600 !important; }}
div[data-testid="stDownloadButton"] > button:hover {{ background: {_accent}22 !important; border-color: {_accent}55 !important; color: {_accent} !important; transform: translateY(-1px); }}
header[data-testid="stHeader"] {{ background: {_bg} !important; border-bottom: 1px solid {_border} !important; }}
header[data-testid="stHeader"] * {{ color: {_muted} !important; }}
div[data-testid="stToolbar"] {{ background: transparent !important; }}
div[data-testid="stDecoration"] {{ background: {_accent} !important; height: 2px !important; }}
div[data-testid="stAlert"] {{ animation: slideUp 0.3s ease-out; }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes slideUp {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes pulseDot {{ 0%,100% {{ box-shadow: 0 0 0 0 {_accent}55; }} 50% {{ box-shadow: 0 0 0 6px transparent; }} }}
@keyframes shimmer {{ 0% {{ transform: translateX(-100%); }} 100% {{ transform: translateX(100%); }} }}
@keyframes typingDot {{ 0%, 60%, 100% {{ opacity: 0.3; transform: translateY(0); }} 30% {{ opacity: 1; transform: translateY(-2px); }} }}
.tech-dot {{ animation: pulseDot 2s infinite; }}
div[data-testid="stProgress"] > div > div {{ position: relative; overflow: hidden; }}
div[data-testid="stProgress"] > div > div::after {{ content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent); animation: shimmer 1.6s infinite; }}
div[data-testid="stStatusWidget"] {{ animation: slideUp 0.25s ease-out; }}
.typing-dots span {{ display: inline-block; width: 5px; height: 5px; border-radius: 50%; background: {_accent}; margin: 0 2px; animation: typingDot 1.2s infinite; }}
.typing-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
.typing-dots span:nth-child(3) {{ animation-delay: 0.4s; }}

</style>""")


st.html(f"""<div class="tech-header-anim" style="display:flex; align-items:center; gap:12px; padding:11px 14px; background:{_card2}; border:1px solid {_border}; border-left:3px solid {_accent}; margin-bottom:20px; font-family:'JetBrains Mono',monospace; font-size:0.72rem; letter-spacing:0.06em; border-radius:6px; animation: slideUp 0.4s ease-out;">
<span style="font-weight:700; color:{_text}; letter-spacing:0.08em;">DGITT // DGITT</span>
<span class="tech-dot" style="width:6px; height:6px; background:{_accent2}; border-radius:50%; display:inline-block;"></span>
<span style="color:{_muted};">ÁREA DE INFORMÁTICA // GEMINI-3.6-FLASH</span>
<span style="margin-left:auto; color:{_muted}; font-size:0.70rem;">{'NOCHE' if modo_oscuro else 'DÍA'} // DGITT</span>
</div>""")

st.markdown(f"<div style='font-family:JetBrains Mono,monospace; font-size:0.72rem; letter-spacing:0.12em; color:{_accent}; font-weight:700; margin-bottom:6px;'>DIRECCIÓN GENERAL DE INVESTIGACIÓN Y TRANSFERENCIA TECNOLÓGICA</div><h1 style='font-family:Inter,sans-serif; font-weight:800; font-size:1.95rem; letter-spacing:-0.04em; color:{_text}; margin:0; line-height:1.1;'>Área de Informática — Motor de Auditoría Documental</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-family:Inter,sans-serif; font-size:0.88rem; color:{_muted}; margin-top:8px;'>Plataforma <span style='color:{_accent}; font-weight:700;'> </span> para validación masiva. Cada carpeta es un proyecto · 3 PDFs por proyecto · Hasta <code style='font-family:JetBrains Mono,monospace; background:{_card2}; border:1px solid {_border}; padding:1px 6px; border-radius:4px; color:{_muted};'>100</code> proyectos por lote.</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Auditoría Masiva (ZIP)", "Auditoría Individual (PDFs)"])

with tab1:
    st.caption(
        "Sube un ZIP con hasta 100 carpetas (cada carpeta = un proyecto). "
        "Cada carpeta debe contener 3 PDFs: **Proyecto Aprobado**, **Informe Técnico** y **Anexos**."
    )
    st.caption(
        "Estructura esperada: `Proyecto_001/Proyecto Aprobado.pdf` · "
        "`Proyecto_001/Informe Técnico.pdf` · `Proyecto_001/Anexos.pdf`"
    )

    archivo_zip = st.file_uploader(
        "Archivo ZIP con proyectos (máx. 100 carpetas)",
        type=["zip"],
        help="Selecciona el ZIP que contiene todas las carpetas de proyectos.",
        key="zip_uploader_masivo",
    )

    boton_auditar = st.button("Iniciar Auditoría Masiva", type="primary", use_container_width=True, key="btn_masivo")

    if boton_auditar:
        if not archivo_zip:
            st.warning("Debes subir un archivo ZIP primero.")
        elif not api_key:
            st.warning("Ingresa tu API Key de Google AI Studio en el sidebar.")
        else:
            with st.spinner("Descomprimiendo ZIP y extrayendo texto de PDFs..."):
                proyectos, advertencias = procesar_zip_proyectos(archivo_zip)

            if advertencias:
                with st.expander(f"Advertencias ({len(advertencias)} proyecto(s) con incidencias)", expanded=True):
                    for adv in advertencias:
                        st.warning(adv)

            if not proyectos:
                st.error(
                    "No se encontraron proyectos válidos para auditar. "
                    "Verifica que cada carpeta contenga los 3 PDFs requeridos."
                )
            else:
                st.info(f"Se detectaron **{len(proyectos)}** proyecto(s) válidos. Iniciando auditoría con `{len(proyectos)}` llamadas a Gemini...")

                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                barra = progress_placeholder.progress(0, text="Iniciando auditoría...")

                resultados = {}
                errores_no_bloqueantes = []
                advertencias_loop = []

                with status_placeholder.status("Auditando proyectos...", expanded=True) as estado:
                    for idx, proyecto in enumerate(proyectos):
                        nombre = proyecto["nombre"]
                        estado.write(f"**[{idx+1}/{len(proyectos)}] Auditando:** {nombre} ...")
                        barra.progress((idx) / len(proyectos), text=f"Auditoría {idx+1}/{len(proyectos)}: {nombre}")

                        try:
                            reporte = auditar_proyecto_ia(
                                proyecto["texto_proyecto"],
                                proyecto["texto_informe"],
                                proyecto["texto_anexos"],
                                api_key,
                            )
                            resultados[nombre] = reporte
                            if reporte.startswith("ERROR:"):
                                errores_no_bloqueantes.append(nombre)
                                estado.write(f"  → {nombre}: **error controlado** (ver reporte)")
                            else:
                                estado.write(f"  → {nombre}: **completado**")

                        except Exception as e:
                            msg = f"ERROR: No se pudo auditar '{nombre}': {e}"
                            resultados[nombre] = msg
                            errores_no_bloqueantes.append(nombre)
                            estado.write(f"  → {nombre}: **error inesperado** - {e}")
                            advertencias_loop.append(f"Proyecto '{nombre}' falló pero se continúa: {e}")

                        if idx < len(proyectos) - 1:
                            time.sleep(2)

                    barra.progress(1.0, text=f"Auditoría completada: {len(resultados)}/{len(proyectos)}")
                    estado.update(label=f"Auditoría completada: {len(resultados)} proyectos procesados", state="complete", expanded=False)

                for w in advertencias_loop:
                    st.warning(w)

                if errores_no_bloqueantes:
                    st.warning(f"{len(errores_no_bloqueantes)} proyecto(s) con error controlado: {', '.join(errores_no_bloqueantes)}")

                with st.spinner("Generando Reporte Maestro..."):
                    reporte_maestro = generar_reporte_maestro(resultados, advertencias)

                st.session_state.reporte_maestro = reporte_maestro
                st.session_state.resultados_individuales = resultados
                st.rerun()

    if "reporte_maestro" in st.session_state:
        st.divider()
        st.markdown("<div style=\"animation: fadeIn 0.5s ease-out\">", unsafe_allow_html=True)
        st.subheader("Reporte Maestro")
        st.markdown(st.session_state.reporte_maestro)
        st.markdown("</div>", unsafe_allow_html=True)

        col_txt, col_pdf = st.columns(2)
        with col_txt:
            st.download_button(
                label="Descargar Reporte Maestro (.txt)",
                data=st.session_state.reporte_maestro,
                file_name="reporte_maestro.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_maestro_txt",
            )
        with col_pdf:
            reporte_hash = hash(st.session_state.reporte_maestro)
            if "reporte_maestro_pdf" not in st.session_state or st.session_state.get("reporte_maestro_hash") != reporte_hash:
                with st.spinner("Generando PDF con tablas..."):
                    pdf_bytes = generar_pdf(st.session_state.reporte_maestro, titulo="Reporte Maestro - Auditoría Masiva")
                    st.session_state.reporte_maestro_pdf = pdf_bytes
                    st.session_state.reporte_maestro_hash = reporte_hash
            else:
                pdf_bytes = st.session_state.reporte_maestro_pdf

            if pdf_bytes:
                st.download_button(
                    label="Descargar Reporte Maestro (.pdf)",
                    data=pdf_bytes,
                    file_name="reporte_maestro.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_maestro_pdf",
                )
            else:
                st.error("No se pudo generar el PDF. Descarga el TXT como respaldo. Si el reporte tiene tablas muy anchas, se usará el fallback de texto plano.")
    elif not boton_auditar and "reporte_maestro" not in st.session_state:
        st.info(
            "Sube un ZIP y presiona **Iniciar Auditoría Masiva** para comenzar. "
            "Cada carpeta será auditada de forma secuencial con pausas y reintentos automáticos ante límites de tasa."
        )

with tab2:
    st.caption(
        "Sube los 3 PDFs de un único proyecto para generar su reporte de auditoría individual. "
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        archivo_aprobado = st.file_uploader(
            "1. Proyecto Aprobado",
            type=["pdf"],
            help="PDF del Proyecto Aprobado (fuente contractual).",
            key="aprobado_individual",
        )
    with col2:
        archivo_informe = st.file_uploader(
            "2. Informe Técnico",
            type=["pdf"],
            help="PDF del Informe Técnico (resultados reportados).",
            key="informe_individual",
        )
    with col3:
        archivo_anexos = st.file_uploader(
            "3. Anexos",
            type=["pdf"],
            help="PDF de los Anexos (evidencias).",
            key="anexos_individual",
        )

    boton_individual = st.button("Generar Reporte Individual", type="primary", use_container_width=True, key="btn_individual")

    if boton_individual:
        if not api_key:
            st.warning("Ingresa tu API Key de Google AI Studio en el sidebar.")
        elif not (archivo_aprobado and archivo_informe and archivo_anexos):
            st.warning("Debes cargar los tres archivos PDF: Proyecto Aprobado, Informe Técnico y Anexos.")
        else:
            with st.spinner("Extrayendo texto..."):
                texto_aprobado = extraer_texto_pdf(archivo_aprobado.read())
                texto_informe = extraer_texto_pdf(archivo_informe.read())
                texto_anexos = extraer_texto_pdf(archivo_anexos.read())

            if texto_aprobado.startswith("[ERROR]") or texto_informe.startswith("[ERROR]") or texto_anexos.startswith("[ERROR]"):
                st.error(f"Falló la extracción de texto: {texto_aprobado} | {texto_informe} | {texto_anexos}")
            elif texto_aprobado.startswith("[AVISO]") or texto_informe.startswith("[AVISO]") or texto_anexos.startswith("[AVISO]"):
                st.warning("Uno o más PDFs no contienen texto extraíble (posible escaneo sin OCR). Igualmente se intentará auditar.")
                with st.spinner("Analizando con IA..."):
                    try:
                        reporte_individual = auditar_proyecto_ia(texto_aprobado, texto_informe, texto_anexos, api_key)
                        st.session_state.reporte_individual = reporte_individual
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error durante la auditoría: {e}")
            else:
                with st.spinner("Analizando con IA..."):
                    try:
                        reporte_individual = auditar_proyecto_ia(texto_aprobado, texto_informe, texto_anexos, api_key)
                        st.session_state.reporte_individual = reporte_individual
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error durante la auditoría: {e}")

    if "reporte_individual" in st.session_state:
        st.divider()
        st.markdown("<div style=\"animation: fadeIn 0.5s ease-out\">", unsafe_allow_html=True)
        st.subheader("Reporte Individual")
        st.markdown(st.session_state.reporte_individual)
        st.markdown("</div>", unsafe_allow_html=True)
        col_txt2, col_pdf2 = st.columns(2)
        with col_txt2:
            st.download_button(
                label="Descargar reporte (.txt)",
                data=st.session_state.reporte_individual,
                file_name="reporte_individual.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_individual_txt",
            )
        with col_pdf2:
            ind_hash = hash(st.session_state.reporte_individual)
            if "reporte_individual_pdf" not in st.session_state or st.session_state.get("reporte_individual_hash") != ind_hash:
                with st.spinner("Generando PDF con tablas..."):
                    pdf_bytes_ind = generar_pdf(st.session_state.reporte_individual, titulo="Reporte de Auditoría")
                    st.session_state.reporte_individual_pdf = pdf_bytes_ind
                    st.session_state.reporte_individual_hash = ind_hash
            else:
                pdf_bytes_ind = st.session_state.reporte_individual_pdf

            if pdf_bytes_ind:
                st.download_button(
                    label="Descargar reporte (.pdf)",
                    data=pdf_bytes_ind,
                    file_name="reporte_individual.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_individual_pdf",
                )
            else:
                st.error("No se pudo generar el PDF. Si el reporte tiene tablas muy complejas, se usará el fallback de texto plano.")
