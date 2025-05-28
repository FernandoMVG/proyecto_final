# src/prompts.py

PROMPT_GENERAR_ESQUEMA_PARCIAL_TEMPLATE = """Eres un asistente experto en análisis académico y estructuración de contenido.
Tu entrada es un FRAGMENTO de una transcripción de una clase universitaria (Parte {chunk_numero} de {total_chunks}).

--- OBJETIVO ---
Analizar el FRAGMENTO y generar un ESQUEMA JERÁRQUICO detallado del contenido.
El esquema debe usar numeración (1., 1.1., 1.1.1., etc.) relativa a ESTE FRAGMENTO. Comienza siempre desde "1." No uses numeración global.

--- INSTRUCCIONES ---
1.  Identificar temas principales del fragmento (nivel 1).
2.  Desglosar en subtemas relevantes (nivel 2).
3.  Incluir conceptos, definiciones o ejemplos si aplica (nivel 3+).
4.  Omitir partes sin contenido académico relevante.
5.  Mantener el orden original del fragmento.
6.  Usar frases concisas.
7.  Escribir cada ítem como texto plano, sin formato (negritas, cursivas, etc.).
8.  La salida debe ser exclusivamente el esquema, sin títulos, sin resúmenes ni texto explicativo.

--- FRAGMENTO DE TRANSCRIPCIÓN (Parte {chunk_numero} de {total_chunks}) ---
{texto_fragmento}
--- FIN DEL FRAGMENTO ---

ESQUEMA JERÁRQUICO DEL FRAGMENTO:
"""

PROMPT_GENERAR_ESQUEMA_TEMPLATE = """Eres un asistente experto en análisis académico y estructuración de contenido.
Tu entrada es una transcripción COMPLETA de una clase universitaria.

--- OBJETIVO ---
Analizar la transcripción completa y generar un ESQUEMA JERÁRQUICO detallado del contenido.
El esquema debe usar numeración jerárquica (1., 1.1., 1.1.1., etc.) y reflejar los temas, subtemas, conceptos clave, definiciones y ejemplos de la clase, siguiendo el flujo lógico.

--- INSTRUCCIONES ---
1.  Identificar los temas principales globales de la clase (nivel 1).
2.  Desglosar cada tema en subtemas específicos (nivel 2).
3.  Incluir detalles relevantes como definiciones, conceptos, ejemplos o preguntas/respuestas (nivel 3+).
4.  Omitir contenido no académico, como divagaciones, interrupciones logísticas y conversaciones administrativas.
5.  Mantener el orden original de la presentación.
6.  Usar frases concisas en cada punto. No escribir párrafos.
7.  Escribir los ítems como texto plano, sin negritas, cursivas u otro tipo de marcado.
8.  Utilizar únicamente numeración jerárquica (1., 1.1., 1.1.1., etc.). No utilizar viñetas ni símbolos adicionales.
9.  La salida debe ser exclusivamente el esquema. No incluir resúmenes, títulos ni explicaciones externas.

--- TRANSCRIPCIÓN COMPLETA ---
{texto_completo}
--- FIN TRANSCRIPCIÓN COMPLETA ---

ESQUEMA JERÁRQUICO DE LA CLASE (comenzar directamente con 1.):
"""


PROMPT_FUSIONAR_ESQUEMAS_TEMPLATE = """Eres un editor experto y arquitecto de información académica.
Tu entrada es una lista de ESQUEMAS PARCIALES generados consecutivamente a partir de fragmentos de una clase universitaria. Cada esquema parcial numera sus temas principales comenzando desde "1." en relación con su propio fragmento.

--- OBJETIVO ---
Fusionar y sintetizar los esquemas parciales en un ÚNICO ESQUEMA MAESTRO que represente la estructura completa, coherente y jerarquizada de la clase.

--- INSTRUCCIONES ---
1.  Establecer la jerarquía global:
    - Identificar los temas verdaderamente globales que representen el nivel 1 del esquema maestro.
    - Reubicar los temas locales de los esquemas parciales como subtemas si corresponde.
    - Aplicar numeración continua, lógica y jerárquica en todo el esquema (1., 1.1., 1.1.1., etc.).

2.  Integrar contenido y eliminar redundancias:
    - Detectar solapamientos temáticos entre esquemas consecutivos y fusionarlos.
    - Combinar subtemas repetidos en un solo ítem con sus respectivos detalles consolidados.
    - Agrupar elaboraciones posteriores bajo la introducción correspondiente.

3.  Preservar detalle y coherencia:
    - Conservar todos los conceptos, definiciones y ejemplos relevantes.
    - Organizar los puntos según el orden lógico de la clase.

4.  Formato del texto:
    - Escribir todos los ítems como texto plano, sin formato (sin negritas, cursivas, etc.).

5.  Formato de salida:
    - La salida debe consistir únicamente en el esquema maestro.
    - Usar numeración jerárquica (1., 1.1., 1.1.1., etc.). No utilizar viñetas ni símbolos especiales.
    - No incluir títulos, introducciones, explicaciones ni resúmenes.
    - La respuesta debe comenzar directamente con el ítem 1.

--- ESQUEMAS PARCIALES A FUSIONAR (ordenados cronológicamente) ---
{texto_esquemas_parciales}
--- FIN ESQUEMAS PARCIALES ---

ESQUEMA MAESTRO FUSIONADO (comenzar directamente con 1.):
"""

PROMPT_GENERAR_APUNTES_POR_SECCION_TEMPLATE = """Eres un asistente experto en redacción académica y creación de material de estudio detallado.
Tu tarea es generar apuntes EN ESPAÑOL de clase en formato Markdown para UNA SECCIÓN ESPECÍFICA del esquema de una clase, utilizando la transcripción completa como referencia principal.

--- ENTRADAS ---
1.  **SECCIÓN DEL ESQUEMA A DESARROLLAR:**
    {seccion_del_esquema_actual}

2.  **CONTEXTO DE LA TRANSCRIPCIÓN COMPLETA (para referencia):**
    {contexto_relevante_de_transcripcion} 

--- OBJETIVO ---
Generar apuntes completos, claros y pedagógicos para la "SECCIÓN DEL ESQUEMA A DESARROLLAR", basados exclusivamente en el contenido del "CONTEXTO DE LA TRANSCRIPCIÓN COMPLETA".

--- INSTRUCCIONES ---
1.  Seguir la estructura del esquema:
    - Tomar la "SECCIÓN DEL ESQUEMA A DESARROLLAR" como guía de estructura.
    - Usar el primer ítem como encabezado Markdown principal (`##`).
    - Desarrollar subpuntos con encabezados (`###`, `####`) o listas con viñetas, según corresponda.

2.  Elaborar contenido desde la transcripción:
    - Buscar la información correspondiente para cada punto en el contexto de transcripción.
    - Sintetizar y desarrollar explicaciones claras. Definir conceptos, explicar procesos, incluir ejemplos.
    - No copiar ni parafrasear literalmente.

3.  Manejar la falta de información:
    - Si no hay información clara para un punto, indicarlo así:  
      `(No se encontró información detallada en la transcripción proporcionada para este punto específico del esquema).`
    - No inventar ni completar con contenido genérico.

4.  Formatear en Markdown:
    - Usar `##`, `###`, `####`, etc para jerarquía.
    - Usar `-` o `*` para listas clave.
    - Resaltar términos importantes con **negrita** dentro de párrafos.
    - Usar bloques de código para ejemplos técnicos.

5.  Control de la salida:
    - La salida debe contener únicamente los apuntes de la sección.
    - No incluir preámbulos, explicaciones adicionales ni conclusiones.
    - Comenzar directamente con el primer encabezado Markdown (`## ...`)

--- INICIO DE APUNTES PARA LA SECCIÓN DEL ESQUEMA ---
"""

PROMPT_GEMINI_APUNTES_DESDE_ESQUEMA_Y_TRANSCRIPCION = """
Generar apuntes detallados en formato Markdown basados en el siguiente esquema y transcripción.

--- INSTRUCCIONES ---

1. Estructura:
   - Seguir estrictamente la jerarquía y los títulos del ESQUEMA para organizar los apuntes.
   - Usar encabezados Markdown (`##`, `###`, etc.) para reflejar la estructura jerárquica del esquema.

2. Contenido:
   - Desarrollar completamente cada punto del esquema utilizando la información relevante extraída de la TRANSCRIPCIÓN.
   - Escribir en estilo descriptivo y fluido, como una guía o libro didáctico.
   - Priorizar párrafos continuos para explicar ideas. Usar listas con viñetas (`-`) solo cuando sea estrictamente necesario para enumerar elementos concretos.
   - Explicar brevemente los términos técnicos si no son evidentes por contexto.

3. Formato Markdown:
   - Aplicar encabezados jerárquicos correctamente.
   - Usar negritas (`**texto**`) para resaltar conceptos clave, definiciones o nombres de secciones relevantes.
   - Incluir bloques de código (```código```) únicamente si el esquema o transcripción lo requieren (por ejemplo, ejemplos de código o sintaxis).
   - Garantizar claridad y organización visual.

4. Salida:
   - Incluir únicamente los apuntes generados. 
   - No agregar títulos como “APUNTES GENERADOS” ni comentarios externos.
   - Comenzar directamente con el primer encabezado Markdown (`## ...`) correspondiente al primer punto del esquema.

--- ESQUEMA ---
{esquema_contenido}

--- TRANSCRIPCIÓN ---
{transcripcion_contenido}

"""