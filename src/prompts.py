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


PROMPT_GENERAR_APUNTES_TEMPLATE = """Eres un asistente experto en redacción académica y creación de material de estudio. Tu tarea es generar apuntes de clase detallados y bien estructurados en formato Markdown.
Utilizarás dos fuentes principales:
1.  La TRANSCRIPCIÓN COMPLETA de la clase.
2.  Un ESQUEMA JERÁRQUICO detallado de los temas tratados en esa clase (que fue generado previamente a partir de la transcripción).

--- OBJETIVO ---
Redactar apuntes completos y claros, como si fueran para un estudiante que necesita entender a fondo la materia de la clase. Los apuntes deben seguir la estructura del ESQUEMA proporcionado y extraer la información detallada de la TRANSCRIPCIÓN.

--- INSTRUCCIONES DETALLADAS ---
1.  **Sigue el Esquema:** Utiliza el ESQUEMA como la estructura principal de tus apuntes. Cada punto y subpunto del esquema debe convertirse en una sección o subsección en tus apuntes (usando encabezados Markdown apropiados: #, ##, ###, etc., correspondientes a la jerarquía del esquema).
2.  **Extrae de la Transcripción:** Para CADA PUNTO del esquema, localiza la información relevante en la TRANSCRIPCIÓN COMPLETA y utilízala para redactar una explicación clara y detallada. No te limites a copiar fragmentos; reelabora y sintetiza la información.
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
6.  **Omite Contenido Irrelevante:** Aunque la transcripción completa se proporciona como referencia, céntrate en desarrollar los puntos del ESQUEMA. Evita incluir información de la transcripción que no esté directamente relacionada con los temas del esquema.
7.  **Extensión:** Sé lo suficientemente detallado para que los apuntes sean útiles, pero evita la palabrería innecesaria. La longitud de cada sección dependerá de la cantidad de información relevante en la transcripción para ese punto del esquema.

--- ESQUEMA DETALLADO DE LA CLASE (Guía para la estructura) ---
{esquema_clase}
--- FIN ESQUEMA DETALLADO ---

--- TRANSCRIPCIÓN COMPLETA DE LA CLASE (Fuente principal para el contenido) ---
{texto_completo}
--- FIN TRANSCRIPCIÓN COMPLETA ---

Apuntes de Clase Detallados en Markdown (comienza con el primer encabezado basado en el esquema):
"""

PROMPT_GENERAR_APUNTES_DESDE_ESQUEMA_CONOCIMIENTO_LLM_TEMPLATE = """Eres un asistente experto en redacción académica y creación de material de estudio sobre Optimización. Tu tarea es generar apuntes de clase detallados y bien estructurados en formato Markdown, basándote ÚNICAMENTE en el ESQUEMA JERÁRQUICO proporcionado y tu conocimiento general sobre los temas listados.

--- OBJETIVO ---
Redactar apuntes completos y claros que expliquen los temas y conceptos del ESQUEMA. Imagina que estás creando material de estudio general sobre estos tópicos.

--- INSTRUCCIONES DETALLADAS ---
1.  **Sigue el Esquema:** Utiliza el ESQUEMA como la estructura principal de tus apuntes. Cada punto y subpunto del esquema debe convertirse en una sección o subsección en tus apuntes (usando encabezados Markdown apropiados: #, ##, ###, etc., correspondientes a la jerarquía del esquema).
2.  **Elabora con tu Conocimiento:** Para CADA PUNTO del esquema, redacta una explicación clara y detallada utilizando tu conocimiento general sobre Optimización y temas relacionados.
3.  **Profundidad y Claridad:**
    *   Define los conceptos clave mencionados en el esquema.
    *   Explica los procesos o métodos descritos.
    *   Si es apropiado, puedes inventar ejemplos simples para ilustrar los puntos del esquema.
    *   Asegúrate de que las explicaciones sean comprensibles, pedagógicas y académicamente correctas.
4.  **Formato Markdown:**
    *   Usa encabezados para los títulos de temas y subtemas según el esquema.
    *   Utiliza listas con viñetas (`-` o `*`) para enumeraciones o puntos clave dentro de una explicación.
    *   Usa **negrita** para resaltar términos importantes.
    *   Si mencionas fórmulas generales o pseudocódigo, intenta representarlo de la mejor manera posible en Markdown.
5.  **Fluidez y Coherencia:** Asegúrate de que los apuntes fluyan bien de una sección a otra y que el lenguaje sea académico y preciso.
6.  **Extensión:** Sé lo suficientemente detallado para que los apuntes sean útiles, pero evita la palabrería innecesaria. La longitud de cada sección dependerá de la complejidad del punto del esquema.
7.  **NO te refieras a una "clase" o "profesor" específico, ya que no tienes la transcripción.** Habla en términos generales sobre los temas.

--- ESQUEMA DETALLADO DE TEMAS (Guía para la estructura y contenido a desarrollar) ---
{esquema_clase}
--- FIN ESQUEMA DETALLADO ---

Apuntes Detallados en Markdown (basados en tu conocimiento y el esquema, comienza con el primer encabezado):
"""

PROMPT_DESARROLLAR_SECCION_ESQUEMA_CONOCIMIENTO_LLM_TEMPLATE = """Eres un asistente experto en redacción académica y creación de material de estudio sobre Optimización. Tu tarea es desarrollar DETALLADAMENTE UNA SECCIÓN específica de un esquema de clase, utilizando tu conocimiento general sobre los temas listados en esa sección. El objetivo es producir apuntes que se lean como explicaciones narrativas y bien desarrolladas.

--- OBJETIVO ---
Redactar apuntes completos y claros que expliquen los temas y conceptos de la SECCIÓN DEL ESQUEMA proporcionada, utilizando principalmente párrafos explicativos.

--- INSTRUCCIONES DETALLADAS PARA ESTA SECCIÓN ---
1.  **Enfócate en la Sección Dada:** Utiliza la "SECCIÓN DEL ESQUEMA A DESARROLLAR" como la estructura principal para tus apuntes de esta sección. Cada punto y subpunto de esta sección del esquema debe convertirse en un encabezado o sub-encabezado Markdown si es apropiado, seguido de una explicación desarrollada.
2.  **Elabora con tu Conocimiento en Párrafos:** Para CADA PUNTO de la sección del esquema proporcionada, redacta una explicación clara y detallada utilizando tu conocimiento general sobre Optimización y temas relacionados. **Prioriza el uso de párrafos bien construidos para explicar los conceptos, procesos y métodos.**
3.  **Profundidad y Claridad:**
    *   Define los conceptos clave mencionados.
    *   Explica los procesos o métodos descritos en detalle.
    *   Si es apropiado, incluye ejemplos simples para ilustrar los puntos, integrándolos en la narrativa.
    *   Asegúrate de que las explicaciones sean comprensibles, pedagógicas y académicamente correctas.
4.  **Uso Moderado de Listas:** Puedes usar listas con viñetas (`-` o `*`) de forma **moderada y solo cuando sea estrictamente necesario** para enumerar elementos discretos (ej. pasos de un algoritmo, tipos de variables, etc.). **Evita abusar de los bullet points; prefiere la prosa explicativa.**
5.  **Formato Markdown:** Usa encabezados para la estructura. Usa **negrita** para resaltar términos importantes dentro de los párrafos.
6.  **Salida:** Genera ÚNICAMENTE el contenido Markdown para ESTA SECCIÓN. Comienza directamente con el primer encabezado o texto de la sección. NO incluyas la frase "Continúa el proceso..." ni frases similares.

--- SECCIÓN DEL ESQUEMA A DESARROLLAR ---
{sub_esquema}
--- FIN SECCIÓN DEL ESQUEMA ---

Apuntes Detallados para ESTA SECCIÓN (en Markdown, usando principalmente párrafos):
"""