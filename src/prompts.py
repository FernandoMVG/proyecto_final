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
PROMPT_GENERAR_APUNTES_TEMPLATE = """Eres un asistente experto en redacción académica y creación de material de estudio. Tu tarea es generar apuntes de clase DETALLADOS y BIEN ESTRUCTURADOS en formato Markdown para UNA SECCIÓN ESPECÍFICA del esquema de una clase.
Utilizarás dos fuentes principales de información:
1.  La SECCIÓN DEL ESQUEMA proporcionada, que indica los temas y subtemas a cubrir.
2.  Los FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN, que contienen el contenido de la clase relacionado con esta sección del esquema.

--- OBJETIVO PRINCIPAL ---
Redactar apuntes COMPLETOS, CLAROS y PEDAGÓGICOS para la SECCIÓN DEL ESQUEMA dada, basándote FIRMEMENTE en la información contenida en los FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN. El objetivo es que un estudiante pueda entender a fondo los puntos de esta sección del esquema.

--- INSTRUCCIONES DETALLADAS ---
1.  **ESTRUCTURA BASADA EN EL ESQUEMA:**
    *   Toma la "SECCIÓN DEL ESQUEMA A DESARROLLAR" como la guía absoluta para la estructura de tus apuntes.
    *   El primer punto/título de la "SECCIÓN DEL ESQUEMA" debe ser el encabezado Markdown principal para esta sección de apuntes (ej., si el esquema dice "2. Preparación de Datos", tu apunte comenzará con `## 2. Preparación de Datos`).
    *   Los subpuntos dentro de la "SECCIÓN DEL ESQUEMA" deben desarrollarse como sub-encabezados Markdown (`###`, `####`) o, si son detalles más pequeños, como parte de la explicación o en listas con viñetas. Mantén la jerarquía del esquema.

2.  **ELABORACIÓN PROFUNDA DESDE LOS FRAGMENTOS DE TRANSCRIPCIÓN:**
    *   Para CADA PUNTO Y SUBPUNTO de la "SECCIÓN DEL ESQUEMA", busca la información correspondiente DENTRO de los "FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN".
    *   SINTETIZA y REELABORA esta información para construir una explicación detallada. NO te limites a copiar o parafrasear superficialmente. DEFINE conceptos, EXPLICA procesos, DESARROLLA ejemplos mencionados.
    *   Tu objetivo es transformar la información de los fragmentos en apuntes comprensibles y bien redactados.

3.  **MANEJO DE INFORMACIÓN ESCASA:**
    *   Si para un punto específico del esquema, los "FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN" NO contienen información suficiente, clara o directa para desarrollar una explicación detallada, DEBES indicarlo explícitamente. Escribe una frase concisa como: "(No se encontró información detallada en el contexto proporcionado para este punto específico del esquema)".
    *   NO INVENTES información que no esté respaldada por los fragmentos. NO uses placeholders genéricos como "(Aquí va la explicación...)". Es preferible indicar la falta de información a generar contenido incorrecto o de relleno.

4.  **FORMATO MARKDOWN CUIDADOSO:**
    *   Utiliza encabezados (`##`, `###`, `####`) consistentemente según la jerarquía del esquema.
    *   Usa listas con viñetas (`-` o `*`) para enumeraciones o puntos clave.
    *   Usa **negrita** para resaltar términos importantes o títulos de conceptos dentro de un párrafo.
    *   Representa fórmulas o código simple de la mejor manera posible (bloques ` ``` ` o `código inline`).

5.  **CALIDAD DE LA REDACCIÓN:**
    *   Asegura la fluidez y coherencia entre las explicaciones de los diferentes puntos.
    *   Utiliza un lenguaje académico, claro y preciso.

6.  **ENFOQUE Y RELEVANCIA:**
    *   Céntrate EXCLUSIVAMENTE en desarrollar los puntos de la "SECCIÓN DEL ESQUEMA A DESARROLLAR" utilizando los "FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN".
    *   Evita incluir información de los fragmentos que no esté directamente relacionada con la sección actual del esquema.

7.  **EXTENSIÓN ADECUADA:**
    *   Sé lo suficientemente detallado para que los apuntes sean útiles. La longitud de la explicación para cada punto dependerá de la riqueza de la información en los "FRAGMENTOS RELEVANTES".

--- SECCIÓN DEL ESQUEMA A DESARROLLAR ---
{seccion_del_esquema_actual}
--- FIN SECCIÓN DEL ESQUEMA ---

--- FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN (Contexto para esta sección) ---
{contexto_relevante_de_transcripcion}
--- FIN FRAGMENTOS RELEVANTES DE LA TRANSCRIPCIÓN ---

Apuntes Detallados en Markdown para la SECCIÓN DEL ESQUEMA (comienza directamente con el primer encabezado basado en la "SECCIÓN DEL ESQUEMA A DESARROLLAR"):
"""