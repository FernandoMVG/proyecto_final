# src/prompts.py

PROMPT_MAP_REFINADO_TEMPLATE = """Contexto: Eres un asistente IA altamente estructurado y preciso. Tu tarea es analizar un fragmento de una transcripción de clase de Optimización y extraer los conceptos clave y un resumen.

--- INSTRUCCIONES ---
Analiza el siguiente FRAGMENTO A PROCESAR.
Genera tu respuesta exactamente en el FORMATO DE EJEMPLO proporcionado.
NO añadas texto introductorio, explicaciones ni texto fuera de las etiquetas "Conceptos Clave:" y "Resumen Breve:".

--- FORMATO DE EJEMPLO (SIGUE ESTA ESTRUCTURA AL PIE DE LA LETRA) ---
Conceptos Clave:
- [Primer Concepto Importante del Fragmento]
- [Segundo Concepto Importante del Fragmento]
- [Tercer Concepto Importante del Fragmento]
Resumen Breve:
[Resumen conciso de 2 a 3 frases sobre la idea principal del fragmento.]
--- FIN FORMATO DE EJEMPLO ---

--- EJEMPLO REAL DE TRANSCRIPCIÓN Y SALIDA DESEADA ---
Fragmento de Transcripción:
"Okay, entonces si tenemos una función objetivo que queremos maximizar, digamos F(x, y), y tenemos un conjunto de restricciones, como x + y <= 10 y x >= 0, y >= 0. Esto define nuestra región factible, que es un polígono. Los puntos óptimos, si existen, siempre estarán en uno de los vértices de este polígono."
Salida Deseada para ese Fragmento:
Conceptos Clave:
- Función Objetivo
- Restricciones
- Región Factible
- Vértices
Resumen Breve:
Este fragmento introduce la formulación básica de un problema de optimización lineal, definiendo la función objetivo y las restricciones. Explica cómo las restricciones delimitan una región factible poligonal y menciona que los puntos óptimos se encuentran en los vértices de esta región.
--- FIN EJEMPLO REAL ---

--- FRAGMENTO A PROCESAR ---
{chunk_texto}
--- FIN FRAGMENTO A PROCESAR ---

Tu Respuesta (siguiendo estrictamente el FORMATO DE EJEMPLO, incluyendo AMBAS etiquetas "Conceptos Clave:" y "Resumen Breve:"):
"""


PROMPT_REDUCE_TEMPLATE = """Contexto: Eres un asistente experto creando una guía de estudio concisa y bien estructurada en formato Markdown para una clase de Optimización.
Has analizado la transcripción de la clase por partes. Aquí tienes un resumen de los puntos clave y conceptos identificados en cada parte:

--- RESUMEN POR PARTES ---
{texto_consolidado}
--- FIN RESUMEN POR PARTES ---

Tarea Principal: Sintetiza la información anterior en una guía de estudio completa y coherente en Markdown.

Instrucciones de Formato y Contenido:
1.  **Título Principal:** Comienza con un título principal adecuado para la guía (ej. `# Guía de Estudio: Optimización - Clase [Fecha/Tema]`).
2.  **Estructura Lógica:** Organiza el contenido por temas principales. Usa encabezados Markdown (`##` para temas principales, `###` para subtemas). Agrupa la información relacionada de diferentes partes de la transcripción bajo el encabezado temático correspondiente.
3.  **Contenido Claro:** Explica los conceptos de forma clara y concisa, basándote en los resúmenes proporcionados. No te limites a listar los resúmenes, intégralos en una narrativa fluida.
4.  **Conceptos Clave:** Opcionalmente, puedes incluir una sección `## Conceptos Clave Principales` al final, listando los conceptos más importantes de forma única (extraídos de los resúmenes).
5.  **Extensión:** Sé completo pero evita redundancias innecesarias.
6.  **Salida:** Genera ÚNICAMENTE el contenido Markdown de la guía, empezando por el título principal. No incluyas explicaciones previas ni posteriores a la guía.

Guía de Estudio en Markdown:
# Guía de Estudio: Optimización
"""