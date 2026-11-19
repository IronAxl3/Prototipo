# DGITT // Auditoría Documental

Plataforma de auditoría documental masiva para la **Dirección General de Investigación y Transferencia Tecnológica**. Permite contrastar de forma automática tres PDFs por proyecto (*Proyecto Aprobado*, *Informe Técnico* y *Anexos*) utilizando IA de Google Gemini, generando reportes de congruencia en Markdown y PDF.

## ¿Qué hace?

- Sube un archivo **ZIP** con hasta 100 carpetas (una carpeta por proyecto).
- Cada carpeta debe contener los 3 PDFs requeridos.
- Extrae el texto de los PDFs y lo envía a Gemini para auditar:
  1. Objetivos y entregables prometidos.
  2. Resultados reportados vs. promesas.
  3. Validación de evidencias (anexos).
  4. Veredicto final y riesgos.
- Genera un **Reporte Maestro** con todos los proyectos auditados.
- También permite auditoría individual subiendo los 3 PDFs de un solo proyecto.
- Descarga reportes en formato `.txt` y `.pdf`.

## Estructura esperada del ZIP

```
Proyecto_001/
  Proyecto Aprobado.pdf
  Informe Técnico.pdf
  Anexos.pdf
Proyecto_002/
  ...
```

## Requisitos

- Python 3.10+
- Una **API Key de Google AI Studio** (gratuita): https://aistudio.google.com

## Instalación

1. Clona o descarga este repositorio.
2. Crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Ejecuta la aplicación:

```bash
streamlit run app.py
```

4. Abre el navegador en la URL que indique Streamlit (por defecto: http://localhost:8501).

## Cómo usar

1. En la barra lateral, pega tu **API Key de Google AI Studio**.
2. Elige el modo de auditoría:
   - **Auditoría Masiva (ZIP):** sube un ZIP con varias carpetas de proyectos.
   - **Auditoría Individual (PDFs):** sube los 3 PDFs de un solo proyecto.
3. Pulsa el botón para iniciar la auditoría.
4. Descarga el reporte generado en `.txt` o `.pdf`.

## Estructura del proyecto

```
app.py              # Interfaz de usuario (Streamlit)
backend.py          # Lógica de extracción, auditoría IA y generación de reportes
requirements.txt    # Dependencias de Python
README.md           # Este archivo
venv/               # Entorno virtual (se crea al instalar)
```

## Notas

- La app no almacena claves de API; se solicitan por sesión en la barra lateral.
- Los PDFs escaneados sin texto extraíble generarán un aviso, pero se intentará auditar igualmente.
- En caso de límites de tasa (429) de Gemini, el sistema reintentará automáticamente con backoff exponencial.