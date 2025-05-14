# src/prompts.py

PROMPT_GENERAR_ESQUEMA_TEMPLATE = """Eres un asistente experto en análisis académico y estructuración de contenido. Tienes como entrada una transcripción completa de una clase universitaria.

--- OBJETIVO ---
Tu tarea es analizar la transcripción completa y generar un ESQUEMA JERÁRQUICO detallado (usando numeración como 1., 1.1., 1.1.1., 2., etc.) de los temas, subtemas, conceptos clave, definiciones y ejemplos explicados durante la clase. El esquema debe reflejar la organización y el flujo lógico del contenido presentado por el profesor.

--- INSTRUCCIONES DETALLADAS ---
1.  **Identifica Temas Principales:** Detecta los grandes bloques temáticos que el profesor introduce y desarrolla. Estos serán tus puntos de nivel 1 (ej. 1. Introducción a la Programación Lineal, 2. Método Simplex, etc.).
2.  **Desglosa en Subtemas:** Dentro de cada tema principal, identifica los subtemas o componentes específicos que se explican. Estos serán puntos de nivel 2 (ej. 1.1. Definición de Función Objetivo, 1.2. Tipos de Restricciones).
3.  **Incluye Detalles Relevantes:** Para cada subtema, si es aplicable, incluye:
    *   Conceptos clave específicos introducidos.
    *   Definiciones importantes proporcionadas.
    *   Ejemplos ilustrativos mencionados.
    *   Preguntas relevantes de estudiantes y las respuestas del profesor si aportan al contenido académico.
    Estos pueden ser puntos de nivel 3 o superior (ej. 1.2.1. Restricciones de no negatividad, 1.2.2. Ejemplo de problema de producción).
4.  **Filtra Contenido No Académico:** OMITE deliberadamente partes de la transcripción que no sean contenido académico relevante. Esto incluye:
    *   Tangentes o divagaciones del profesor sobre temas no relacionados (ej. el clima, anécdotas personales no ilustrativas).
    *   Interrupciones logísticas (ej. "Voy a borrar la pizarra", "¿Se escucha bien al fondo?").
    *   Conversaciones administrativas o sociales que no aporten al entendimiento de la materia.
5.  **Refleja la Progresión:** El esquema debe seguir el orden en que los temas fueron presentados en la clase.
6.  **Claridad y Concisión:** Usa frases concisas para describir cada punto del esquema. No escribas párrafos largos dentro del esquema.
7.  **Formato Estricto:** Utiliza únicamente numeración jerárquica (1., 1.1., 1.1.1., 2., etc.). No uses viñetas (-, *).

--- TRANSCRIPCIÓN COMPLETA ---
{texto_completo}
--- FIN TRANSCRIPCIÓN COMPLETA ---

Esquema estructurado y jerárquico de la clase (comienza con 1.):
"""


PROMPT_FUSIONAR_ESQUEMAS_TEMPLATE = """Eres un editor experto y organizador de contenido académico. Has recibido varios esquemas parciales que cubren diferentes secciones consecutivas de una misma clase universitaria. Tu tarea es fusionar estos esquemas parciales en un ÚNICO ESQUEMA MAESTRO coherente, completo y bien estructurado.

--- INSTRUCCIONES PARA LA FUSIÓN ---
1.  **Consistencia Jerárquica:** Asegura que la numeración (1., 1.1., 1.1.1., 2., etc.) sea continua y lógica a lo largo de todo el esquema maestro.
2.  **Eliminar Redundancias:** Si temas o subtemas idénticos o muy similares aparecen al final de un esquema parcial y al inicio del siguiente (debido al solapamiento de los fragmentos originales), combínalos de forma inteligente para evitar repeticiones.
3.  **Mantener el Detalle:** Preserva todos los detalles únicos y relevantes de cada esquema parcial. No omitas subpuntos importantes.
4.  **Flujo Lógico:** El esquema maestro debe reflejar una progresión natural de los temas como si la clase se hubiera analizado de una sola vez.
5.  **Formato:** El resultado final debe ser un único bloque de texto que represente el esquema maestro completo, siguiendo el formato de numeración jerárquica. Comienza directamente con el primer punto del esquema (ej. "1. ...").

--- ESQUEMAS PARCIALES A FUSIONAR (Presentados en orden) ---
{texto_esquemas_parciales}
--- FIN ESQUEMAS PARCIALES ---

ESQUEMA MAESTRO FUSIONADO Y COMPLETO (comienza con 1.):
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