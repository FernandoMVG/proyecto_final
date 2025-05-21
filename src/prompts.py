# src/prompts.py

PROMPT_GENERAR_ESQUEMA_PARCIAL_TEMPLATE = """Eres un asistente experto en análisis académico y estructuración de contenido.
Tu entrada es un FRAGMENTO de una transcripción de una clase universitaria (Parte {chunk_numero} de {total_chunks}).

--- OBJETIVO DEL FRAGMENTO ---
Analiza ESTE FRAGMENTO y genera un ESQUEMA JERÁRQUICO detallado de su contenido.
El esquema debe usar numeración (1., 1.1., 1.1.1., 2., etc.) relativa a ESTE FRAGMENTO, reflejando los temas, subtemas, conceptos clave, definiciones y ejemplos explicados EN ESTE FRAGMENTO.
Comienza la numeración de los temas principales identificados en ESTE FRAGMENTO con "1.". NO intentes adivinar la numeración global de la clase completa.

--- INSTRUCCIONES DETALLADAS PARA ESTE FRAGMENTO ---
1.  **Identifica Temas Principales del Fragmento:** Estos serán tus puntos de nivel 1 (ej. 1. Tema A del Fragmento).
2.  **Desglosa en Subtemas del Fragmento:** Dentro de cada tema principal del fragmento, identifica componentes específicos (nivel 2, ej. 1.1. Subcomponente X del Fragmento).
3.  **Incluye Detalles Relevantes del Fragmento:** Para cada subtema, si aplica, añade conceptos, definiciones, ejemplos o preguntas/respuestas relevantes de ESTE FRAGMENTO (nivel 3+, ej. 1.1.1. Detalle Y del Fragmento).
4.  **Filtra Contenido No Académico del Fragmento:** OMITE partes del fragmento que no sean contenido académico relevante.
5.  **Orden y Progresión del Fragmento:** El esquema debe seguir el orden de presentación DENTRO DE ESTE FRAGMENTO.
6.  **Claridad y Concisión:** Usa frases concisas.
7.  **Formato del Texto de los Ítems:** Escribe el texto de cada ítem del esquema (ej. "1.1 Detalle del Fragmento") directamente, SIN ningún formato especial como negritas (Markdown con **), cursivas (* o _), o cualquier otro tipo de marcado. El texto debe ser plano.
8.  **Formato de Salida Estricto:**
    *   Utiliza ÚNICAMENTE numeración jerárquica (1., 1.1., 1.1.1., 2., etc.) relativa a ESTE FRAGMENTO.
    *   Tu respuesta DEBE CONTENER ÚNICAMENTE el esquema de este fragmento. NO incluyas preámbulos, explicaciones adicionales o resúmenes.

--- FRAGMENTO DE TRANSCRIPCIÓN (Parte {chunk_numero} de {total_chunks}) ---
{texto_fragmento}
--- FIN FRAGMENTO DE TRANSCRIPCIÓN ---

ESQUEMA JERÁRQUICO DE ESTE FRAGMENTO (comienza con 1. y sigue estrictamente las instrucciones de formato):
"""

PROMPT_GENERAR_ESQUEMA_TEMPLATE = """Eres un asistente experto en análisis académico y estructuración de contenido.
Tu entrada es una transcripción COMPLETA de una clase universitaria.

--- OBJETIVO ---
Analiza la transcripción completa y genera un ESQUEMA JERÁRQUICO detallado.
El esquema debe usar numeración (1., 1.1., 1.1.1., 2., etc.) y reflejar los temas, subtemas, conceptos clave, definiciones y ejemplos de la clase, manteniendo el flujo lógico.

--- INSTRUCCIONES DETALLADAS ---
1.  **Identifica Temas Principales Globales:** Estos serán tus puntos de nivel 1 (ej. 1. Tema Global A).
2.  **Desglosa en Subtemas:** Dentro de cada tema principal, identifica componentes específicos (nivel 2, ej. 1.1. Subcomponente X).
3.  **Incluye Detalles Relevantes:** Para cada subtema, si aplica, añade conceptos, definiciones, ejemplos o preguntas/respuestas relevantes (nivel 3+, ej. 1.1.1. Detalle Y).
4.  **Filtra Contenido No Académico:** OMITE divagaciones no relacionadas, interrupciones logísticas y conversaciones administrativas.
5.  **Orden y Progresión:** El esquema debe seguir el orden de presentación de la clase.
6.  **Claridad y Concisión:** Usa frases concisas para cada punto. No escribas párrafos dentro del esquema.
7.  **Formato del Texto de los Ítems:** Escribe el texto de cada ítem del esquema (ej. "1.1 Definición de Función Objetivo") directamente, SIN ningún formato especial como negritas (Markdown con **), cursivas (* o _), o cualquier otro tipo de marcado. El texto debe ser plano.
8.  **Formato de Salida Estricto:**
    *   Utiliza ÚNICAMENTE numeración jerárquica (1., 1.1., 1.1.1., 2., etc.). NO uses viñetas (-, *).
    *   Tu respuesta DEBE CONTENER ÚNICAMENTE el esquema. NO incluyas preámbulos, explicaciones adicionales o resúmenes fuera del propio esquema numerado.

--- TRANSCRIPCIÓN COMPLETA ---
{texto_completo}
--- FIN TRANSCRIPCIÓN COMPLETA ---

ESQUEMA JERÁRQUICO DE LA CLASE (comienza con 1. y sigue estrictamente las instrucciones de formato):
"""


PROMPT_FUSIONAR_ESQUEMAS_TEMPLATE = """Eres un editor experto y un arquitecto de información académica.
Tu entrada es una lista de ESQUEMAS PARCIALES, generados consecutivamente a partir de fragmentos de una clase universitaria. Cada esquema parcial numera sus temas principales comenzando desde "1." en relación a su propio fragmento.

--- OBJETIVO PRINCIPAL DE LA FUSIÓN ---
Sintetiza y fusiona estos esquemas parciales en un ÚNICO ESQUEMA MAESTRO que represente la estructura completa, coherente y lógicamente jerarquizada de toda la clase.

--- INSTRUCCIONES DETALLADAS PARA LA FUSIÓN ---
1.  **Establece la Jerarquía Global del Esquema Maestro:**
    *   Analiza TODOS los esquemas parciales para identificar los verdaderos **temas principales de la clase completa**. Estos serán los puntos de nivel 1 (ej. "1. Tema Global A") en tu esquema maestro.
    *   Los temas que eran de nivel 1 en un esquema parcial pueden necesitar ser re-jerarquizados como subtemas (nivel 2 o inferior) en el esquema maestro si son parte de un tema global más amplio.
    *   La numeración (1., 1.1., 1.1.1., 2., etc.) debe ser continua y lógica a lo largo de TODO el esquema maestro.

2.  **Integración Inteligente y Eliminación de Redundancias:**
    *   Al procesar los esquemas parciales en orden, busca puntos de conexión y continuidad temática.
    *   Si un tema o subtema similar aparece al final de un esquema parcial y al inicio del siguiente (debido al solapamiento de los fragmentos originales), **combínalos en un único punto en el esquema maestro**. Elige la formulación más clara o completa, o sintetiza ambas. Asegúrate de que todos los sub-detalles relevantes de ambas menciones se conserven bajo el punto unificado. NO simplemente copies ambos puntos; intégralos.
    *   Si un concepto se introduce en un esquema parcial y se elabora en otro, la elaboración debe colocarse lógicamente bajo la introducción en el esquema maestro.

3.  **Preservación del Detalle y Flujo Lógico:**
    *   Conserva todos los conceptos, definiciones, ejemplos y subpuntos únicos de cada esquema parcial, ubicándolos correctamente en la nueva jerarquía global.
    *   El esquema maestro final debe leerse como si hubiera sido generado a partir del análisis de la clase completa de una sola vez, con una progresión natural de los temas.

4.  **Formato del Texto de los Ítems del Esquema Maestro:**
    *   Escribe el texto de cada ítem del esquema (ej. "1.1 Subtema Integrado") directamente, SIN ningún formato especial como negritas (Markdown con **), cursivas (* o _), o cualquier otro tipo de marcado. El texto debe ser plano.

5.  **Formato de Salida Estricto para el Esquema Maestro:**
    *   El resultado final debe ser un único bloque de texto que represente el esquema maestro.
    *   Utiliza ÚNICAMENTE numeración jerárquica (1., 1.1., 1.1.1., 2., etc.).
    *   Tu respuesta DEBE CONTENER ÚNICAMENTE el esquema maestro fusionado. NO incluyas ningún preámbulo, resumen de cambios, postámbulo, o cualquier otro texto explicativo fuera del propio esquema numerado.

--- ESQUEMAS PARCIALES A FUSIONAR (Presentados en el orden de la clase) ---
{texto_esquemas_parciales}
--- FIN ESQUEMAS PARCIALES ---

ESQUEMA MAESTRO FUSIONADO, COHERENTE Y COMPLETO (comienza con 1. y sigue estrictamente todas las instrucciones, especialmente las de formato y contenido de salida):
"""