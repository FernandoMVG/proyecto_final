# src/main.py

from llama_cpp import Llama
import os
import time
import re # Usaremos expresiones regulares básicas para parsear la salida del LLM

# --- Configuración del Modelo y Rutas ---
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf" # Asegúrate que sea tu modelo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "models", MODEL_FILENAME)
INPUT_FILE = os.path.join(SCRIPT_DIR, "..", "data", "transcripcion_ejemplo.txt") # Necesitarás crear este archivo
OUTPUT_MAP_RESULTS_FILE = os.path.join(SCRIPT_DIR, "..", "output", "map_results.txt") # Guardaremos resultados intermedios aquí
FINAL_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "..", "output", "guia_estudio.md") # La guía final

# --- Configuración del LLM ---
CONTEXT_SIZE = 4096
MAX_TOKENS_MAP = 150      # Límite para el resumen/conceptos de cada chunk (Fase Map)
MAX_TOKENS_REDUCE = 1536  # Límite más grande para la guía final (Fase Reduce) - Ajustar según necesidad
N_GPU_LAYERS = -1
N_THREADS = None

# --- Configuración del Procesamiento ---
CHUNK_SIZE_WORDS = 700  # Número de palabras por chunk (ajusta según ventana de contexto y memoria)
CHUNK_OVERLAP_WORDS = 50 # Superposición para no perder contexto

# --- Crear Carpetas si no Existen ---
os.makedirs(os.path.join(SCRIPT_DIR, "..", "output"), exist_ok=True)
os.makedirs(os.path.join(SCRIPT_DIR, "..", "data"), exist_ok=True)

# --- Cargar Modelo ---
# (Esta parte es igual a test_llm.py, verifica que MODEL_PATH sea correcto)
print(f"Cargando modelo desde: {MODEL_PATH}")
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: No se encontró el archivo del modelo en {MODEL_PATH}")
    exit()
try:
    start_time = time.time()
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=CONTEXT_SIZE,
        n_threads=N_THREADS,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False # Podemos ponerlo en False para menos ruido en la consola
    )
    end_time = time.time()
    print(f"Modelo cargado en {end_time - start_time:.2f} segundos.")
except Exception as e:
    print(f"ERROR al cargar el modelo: {e}")
    exit()

# --- Funciones (Las definiremos a continuación) ---

def leer_archivo(ruta_archivo):
    """Lee el contenido de un archivo de texto."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Archivo no encontrado en {ruta_archivo}")
        # Crear un archivo de ejemplo si no existe
        print("Creando un archivo de ejemplo 'transcripcion_ejemplo.txt' en la carpeta 'data'. Por favor, edítalo.")
        ejemplo_txt = """Este es un texto de ejemplo para la transcripción de la clase de Optimización.
La Programación Lineal es una técnica matemática utilizada para encontrar la mejor solución posible (óptima) 
en un modelo matemático cuyos requisitos están representados por relaciones lineales. 
Se utiliza ampliamente en investigación de operaciones.

Un problema típico de PL consiste en maximizar o minimizar una función objetivo lineal, sujeta a un conjunto 
de restricciones también lineales. Por ejemplo, maximizar beneficios o minimizar costos.

Los componentes clave son: variables de decisión, función objetivo y restricciones. 
Veremos el método Simplex más adelante, que es un algoritmo popular para resolver estos problemas.
También existen métodos gráficos para problemas pequeños con dos variables. Es importante entender la región factible.
"""
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
             f.write(ejemplo_txt)
        return ejemplo_txt
    except Exception as e:
        print(f"ERROR al leer el archivo {ruta_archivo}: {e}")
        return None

def dividir_en_chunks(texto, tamano_chunk_palabras, superposicion_palabras):
    """Divide el texto en chunks por número de palabras con superposición."""
    palabras = texto.split()
    if not palabras:
        return []
    
    chunks = []
    indice_actual = 0
    while indice_actual < len(palabras):
        inicio_chunk = indice_actual
        fin_chunk = min(indice_actual + tamano_chunk_palabras, len(palabras))
        chunk_palabras = palabras[inicio_chunk:fin_chunk]
        chunks.append(" ".join(chunk_palabras))
        
        # Avanzar, asegurándose de no quedarse atascado si el overlap es >= tamaño
        avance = max(1, tamano_chunk_palabras - superposicion_palabras) 
        indice_actual += avance
        
    return chunks

def procesar_chunk_map(chunk_texto, llm_instance):
    """Procesa un chunk individual para extraer conceptos y resumen (Fase Map)."""
    prompt = f"""Contexto: Eres un asistente analizando fragmentos de una transcripción de clase de Optimización.
Aquí tienes un fragmento:
--- FRAGMENTO ---
{chunk_texto}
--- FIN FRAGMENTO ---

Tarea:
1. Lista los 3-5 conceptos o temas clave más importantes discutidos en ESTE FRAGMENTO. Usa guiones (-) para cada concepto.
2. Escribe un resumen muy breve (2-3 frases) de lo principal dicho en ESTE FRAGMENTO.

Respuesta:
Conceptos Clave:
""" # El LLM debería continuar desde aquí

    try:
        output = llm_instance(
            prompt,
            max_tokens=MAX_TOKENS_MAP,
            stop=["Resumen Breve:", "\n\n"], # Detenerse antes de que invente demasiado
            echo=False
        )
        texto_generado = output['choices'][0]['text'].strip()

        # Parsear la salida (esto puede necesitar ajustes según cómo responda el LLM)
        conceptos = []
        resumen = ""
        
        # Buscar conceptos clave (líneas que empiezan con - o *)
        match_conceptos = re.findall(r"^[-\*]\s*(.*)", texto_generado, re.MULTILINE)
        if match_conceptos:
            conceptos = [c.strip() for c in match_conceptos]

        # Buscar el resumen (lo que viene después de "Resumen Breve:", si lo genera)
        # O tomar el texto restante después de los conceptos
        partes = re.split(r"resumen breve:", texto_generado, flags=re.IGNORECASE)
        if len(partes) > 1:
             resumen = partes[1].strip()
        else:
             # Intenta tomar el texto que no son los conceptos
             lineas_texto = texto_generado.split('\n')
             lineas_resumen = [linea for linea in lineas_texto if not linea.strip().startswith(('-', '*')) and linea.strip()]
             resumen = " ".join(lineas_resumen).strip()
             # Si sigue vacío, puede que el LLM solo diera conceptos
             if not resumen and not conceptos:
                 resumen = texto_generado # fallback muy básico

        # Fallback si el parseo falla mucho
        if not conceptos and not resumen:
             print(f"ADVERTENCIA: No se pudo parsear bien la salida del Map para el chunk. Salida cruda: {texto_generado[:100]}...")
             # Podríamos retornar la salida cruda o un diccionario vacío/marcado
             return {'conceptos': [], 'resumen_breve': texto_generado, 'error_parseo': True}


        return {'conceptos': conceptos, 'resumen_breve': resumen, 'error_parseo': False}

    except Exception as e:
        print(f"ERROR al procesar chunk con LLM: {e}")
        return {'conceptos': [], 'resumen_breve': "", 'error_parseo': True}

# --- NUEVA FUNCIÓN: Fase Reduce ---
def sintetizar_guia_reduce(lista_resultados_map, llm_instance):
    """Sintetiza la guía de estudio final a partir de los resultados de la Fase Map."""
    print("\n--- Iniciando Fase Reduce ---")
    
    # 1. Consolidar información del Map
    texto_consolidado = ""
    todos_los_conceptos = set() # Usamos un set para evitar conceptos duplicados en la lista final

    for i, res in enumerate(lista_resultados_map):
        if res.get('error_parseo'): # Omitir chunks con errores de parseo
            continue 
        texto_consolidado += f"Resumen Parte {i+1}: {res.get('resumen_breve', 'N/A')}\n"
        conceptos_chunk = res.get('conceptos', [])
        if conceptos_chunk:
             texto_consolidado += f"Conceptos Clave Parte {i+1}: {', '.join(conceptos_chunk)}\n"
             todos_los_conceptos.update(conceptos_chunk) # Añadir al set
        texto_consolidado += "---\n"

    if not texto_consolidado:
        print("ERROR: No hay resultados válidos de la Fase Map para procesar.")
        return None

    # 2. Preparar el Prompt "Reduce"
    # (Aquí asumimos que no hay bibliografía externa por ahora, como acordamos)
    prompt_reduce = f"""Contexto: Eres un asistente experto creando una guía de estudio concisa y bien estructurada en formato Markdown para una clase de Optimización.
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
""" # El LLM debería continuar desde aquí, idealmente siguiendo el formato

    # 3. Llamar al LLM para la síntesis final
    print("Generando la guía de estudio final (Fase Reduce)... Esto puede tardar.")
    start_reduce_time = time.time()
    try:
        output = llm_instance(
            prompt_reduce,
            max_tokens=MAX_TOKENS_REDUCE,
            stop=None, # Dejar que genere hasta el límite o termine naturalmente
            echo=False
        )
        guia_markdown = output['choices'][0]['text'].strip()
        
        # Pequeña limpieza por si añade el título que ya pusimos
        if guia_markdown.startswith("# Guía de Estudio: Optimización"):
            guia_markdown = "# Guía de Estudio: Optimización" + guia_markdown[len("# Guía de Estudio: Optimización"):].lstrip()
        else:
             # Si no empieza con el título, lo añadimos nosotros
             guia_markdown = "# Guía de Estudio: Optimización\n" + guia_markdown

        end_reduce_time = time.time()
        print(f"--- Fase Reduce completada en {end_reduce_time - start_reduce_time:.2f} segundos ---")
        return guia_markdown

    except Exception as e:
        print(f"ERROR durante la Fase Reduce con LLM: {e}")
        return None

# --- Flujo Principal ---

print("\n--- Iniciando Proceso Map-Reduce ---")

# 1. Leer Transcripción
texto_completo = leer_archivo(INPUT_FILE)
if not texto_completo:
    exit()
print(f"Transcripción leída ({len(texto_completo)} caracteres).")

# 2. Dividir en Chunks
chunks = dividir_en_chunks(texto_completo, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
if not chunks:
    print("ERROR: No se pudieron generar chunks del texto.")
    exit()
print(f"Texto dividido en {len(chunks)} chunks.")

# 3. Fase Map: Procesar cada chunk
print("\n--- Fase Map: Procesando Chunks ---")
resultados_map = []
start_map_time = time.time()

for i, chunk in enumerate(chunks):
    print(f"Procesando chunk {i+1}/{len(chunks)}...")
    resultado_chunk = procesar_chunk_map(chunk, llm)
    resultados_map.append(resultado_chunk)
    # Opcional: Imprimir progreso
    # print(f"  Conceptos: {resultado_chunk.get('conceptos', [])}")
    # print(f"  Resumen: {resultado_chunk.get('resumen_breve', '')[:50]}...")

end_map_time = time.time()
print(f"--- Fase Map completada en {end_map_time - start_map_time:.2f} segundos ---")

# 4. Guardar Resultados Intermedios (Map)
print(f"\nGuardando resultados intermedios del Map en: {OUTPUT_MAP_RESULTS_FILE}")
with open(OUTPUT_MAP_RESULTS_FILE, 'w', encoding='utf-8') as f:
    for i, res in enumerate(resultados_map):
        f.write(f"--- CHUNK {i+1} ---\n")
        f.write(f"Conceptos: {res.get('conceptos', 'N/A')}\n")
        f.write(f"Resumen Breve: {res.get('resumen_breve', 'N/A')}\n")
        if res.get('error_parseo'):
             f.write("ADVERTENCIA: Hubo un error al parsear la salida de este chunk.\n")
        f.write("\n")

# 5. Fase Reduce: Sintetizar la guía final (PRÓXIMO PASO)
print("\n--- Fase Reduce: (Pendiente) ---")
# Aquí vendrá la lógica para tomar 'resultados_map' y generar la guía final en Markdown.

# --- NUEVO: 5. Fase Reduce: Sintetizar la guía final ---
guia_final_markdown = sintetizar_guia_reduce(resultados_map, llm)

# --- NUEVO: 6. Guardar Guía Final ---
if guia_final_markdown:
    print(f"\nGuardando la guía de estudio final en: {FINAL_OUTPUT_FILE}")
    try:
        with open(FINAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(guia_final_markdown)
        print("¡Guía de estudio generada exitosamente!")
    except Exception as e:
        print(f"ERROR al guardar la guía final: {e}")
else:
    print("\nNo se pudo generar la guía de estudio final debido a errores previos.")

# Por ahora, terminamos aquí.
print("\n--- Proceso Map completado. Revisa 'output/map_results.txt' ---")