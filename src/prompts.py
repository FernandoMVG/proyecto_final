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
# Este prompt es para generar apuntes de clase detallados en Markdown
PROMPT_GENERAR_APUNTES_TEMPLATE = """Eres un asistente experto en redacción académica y creación de material de estudio. Tu tarea es generar apuntes de clase detallados y bien estructurados en formato Markdown.
Utilizarás dos fuentes principales:
1.  Los FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN de la clase.
2.  Una SECCIÓN ESPECÍFICA DEL ESQUEMA JERÁRQUICO de la clase. (que fue generado previamente a partir de la transcripción).

--- OBJETIVO ---
Redactar apuntes completos y claros, como si fueran para un estudiante que necesita entender a fondo la materia de la clase. Los apuntes deben seguir la estructura del ESQUEMA proporcionado utilizando como fuente principal los FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN.

--- INSTRUCCIONES DETALLADAS ---
1.  **Sigue el Esquema:** Utiliza el SECCIÓN DEL ESQUEMA como la estructura principal de tus apuntes. Cada punto y subpunto del esquema debe convertirse en una sección o subsección en tus apuntes (usando encabezados Markdown apropiados: #, ##, ###, etc., correspondientes a la jerarquía del esquema).
2.  **Extrae de los Fragmentos de Transcripción:** Para CADA PUNTO de la SECCIÓN DEL ESQUEMA, localiza la información relevante en los FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN y utilízala para redactar una explicación clara y detallada. No te limites a copiar fragmentos; reelabora y sintetiza la información.
3.  **Profundidad y Claridad:**
    *   Define los conceptos clave mencionados en el esquema.
    *   Explica los procesos o métodos descritos.
    *   Si el esquema menciona ejemplos, incorpóralos en tu redacción.
    *   Asegúrate de que las explicaciones sean comprensibles y pedagógicas.
4.  **Formato Markdown:**
    *   Usa encabezados para los títulos de temas y subtemas según el esquema.
    *   Utiliza listas con viñetas (`-` o `*`) para enumeraciones o puntos clave dentro de una explicación.
    *   Usa **negrita** para resaltar términos importantes.
    *   Si hay fórmulas o código simple mencionado, intenta representarlo de la mejor manera posible en Markdown (ej. usando bloques de código ` ``` ` o comillas invertidas para `código inline`).
5.  **Fluidez y Coherencia:** Asegúrate de que los apuntes fluyan bien de una sección a otra y que el lenguaje sea académico y preciso.
6.  **Omite Contenido Irrelevante:** Aunque los FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN se proporcionan como referencia, céntrate en desarrollar los puntos del ESQUEMA. Evita incluir información de la transcripción que no esté directamente relacionada con los temas del esquema.
7.  **Extensión:** Sé lo suficientemente detallado para que los apuntes sean útiles, pero evita la palabrería innecesaria. La longitud de cada sección dependerá de la cantidad de información relevante en la transcripción para ese punto del esquema.

--- ESQUEMA DETALLADO DE LA CLASE (Guía para la estructura) ---
{seccion_del_esquema_actual} 
--- FIN ESQUEMA DETALLADO ---

--- FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN (Contexto para esta sección) ---
{contexto_relevante_de_transcripcion}
--- FIN FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN ---

Apuntes de Clase Detallados en Markdown (comienza con el primer encabezado basado en el esquema):
"""