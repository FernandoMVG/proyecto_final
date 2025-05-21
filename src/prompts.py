# src/prompts.py

PROMPT_GENERAR_ESQUEMA_PARCIAL_TEMPLATE = """Eres un asistente experto en análisis académico y estructuración de contenido. Tienes como entrada un FRAGMENTO de una transcripción de una clase universitaria. Este fragmento es parte de una clase más larga.

--- OBJETIVO DEL FRAGMENTO ---
Tu tarea es analizar ESTE FRAGMENTO de la transcripción y generar un ESQUEMA JERÁRQUICO detallado (usando numeración como X.Y.Z, donde X es un número que indica un tema principal DENTRO DE ESTE FRAGMENTO) de los temas, subtemas, conceptos clave, definiciones y ejemplos explicados EN ESTE FRAGMENTO.
El esquema debe reflejar la organización y el flujo lógico del contenido presentado por el profesor DENTRO DE ESTE FRAGMENTO.
NO intentes adivinar la numeración global de la clase completa. Comienza la numeración de los temas principales identificados en ESTE FRAGMENTO con "1.".

--- INSTRUCCIONES DETALLADAS PARA ESTE FRAGMENTO ---
1.  **Identifica Temas Principales del Fragmento:** Detecta los bloques temáticos que el profesor introduce y desarrolla DENTRO DE ESTE FRAGMENTO. Estos serán tus puntos de nivel 1 (ej. 1. Discusión sobre el Método Simplex, 2. Ejemplos de Variables de Holgura).
2.  **Desglosa en Subtemas del Fragmento:** Dentro de cada tema principal del fragmento, identifica los subtemas o componentes específicos que se explican. Estos serán puntos de nivel 2 (ej. 1.1. Pasos del Algoritmo Simplex, 1.2. Interpretación de la Tabla Simplex).
3.  **Incluye Detalles Relevantes del Fragmento:** Para cada subtema, si es aplicable, incluye:
    *   Conceptos clave específicos introducidos EN ESTE FRAGMENTO.
    *   Definiciones importantes proporcionadas EN ESTE FRAGMENTO.
    *   Ejemplos ilustrativos mencionados EN ESTE FRAGMENTO.
    *   Preguntas relevantes de estudiantes y las respuestas del profesor si aportan al contenido académico DENTRO DE ESTE FRAGMENTO.
    Estos pueden ser puntos de nivel 3 o superior (ej. 1.1.1. Selección de la variable de entrada).
4.  **Filtra Contenido No Académico del Fragmento:** OMITE deliberadamente partes del fragmento que no sean contenido académico relevante.
5.  **Refleja la Progresión del Fragmento:** El esquema debe seguir el orden en que los temas fueron presentados EN ESTE FRAGMENTO.
6.  **Claridad y Concisión:** Usa frases concisas.
7.  **Formato Estricto:** Utiliza únicamente numeración jerárquica (1., 1.1., 1.1.1., 2., etc.) relativa a ESTE FRAGMENTO.

--- FRAGMENTO DE TRANSCRIPCIÓN (Parte {chunk_numero} de {total_chunks}) ---
{texto_fragmento}
--- FIN FRAGMENTO DE TRANSCRIPCIÓN ---

Esquema estructurado y jerárquico de ESTE FRAGMENTO de la clase (comienza con 1.):
"""

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
