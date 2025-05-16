# src/config.py
import os

# --- Directorios Base ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")

# --- Configuración del Modelo y Rutas ---
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
MODEL_PATH = os.path.join(BASE_PROJECT_DIR, "models", MODEL_FILENAME)
INPUT_FILE_NAME = "transcripcion_ejemplo.txt"
INPUT_FILE_PATH = os.path.join(BASE_PROJECT_DIR, "data", INPUT_FILE_NAME)
# Cambiamos el nombre del archivo de salida para reflejar que es un esquema
OUTPUT_ESQUEMA_FILENAME = "esquema_clase.txt" 
OUTPUT_ESQUEMA_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_ESQUEMA_FILENAME)
# OUTPUT_APUNTES_FILENAME = "apuntes_clase.md" # Para el futuro
# OUTPUT_APUNTES_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_APUNTES_FILENAME)
OUTPUT_APUNTES_FILENAME = "apuntes_clase_final.md" # Nuevo
OUTPUT_APUNTES_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_APUNTES_FILENAME) 


# --- Configuración del LLM ---
# ¡IMPORTANTE! Aumenta CONTEXT_SIZE al máximo que tu modelo y hardware soporten
CONTEXT_SIZE = 16384  # Esto es el tamaño máximo de contexto del modelo
                      
# Necesitaremos muchos tokens para generar un esquema detallado de una clase larga
# MAX_TOKENS_ESQUEMA = 4096 # Empieza con esto, podrías necesitar aumentarlo a 8192 o más.
MAX_TOKENS_APUNTES = 8192 # Para cuando generes los apuntes (más adelante)
MAX_TOKENS_APUNTES_POR_SECCION = 1024

MAX_TOKENS_ESQUEMA_PARCIAL = 2048 # Tokens para el esquema de un mega-chunk
MAX_TOKENS_ESQUEMA_FUSIONADO = 4096 # Tokens para el esquema final fusionado

N_GPU_LAYERS = -1
N_THREADS = None
LLM_VERBOSE = False
LLM_TEMPERATURE_ESQUEMA = 0.3 # Temperatura para la generación del esquema
LLM_TEMPERATURE_FUSION = 0.2 # Más bajo para una fusión más literal
LLM_TEMPERATURE_APUNTES = 0.5

# --- Configuración del Mega-Chunking ---
# Factor de seguridad: qué porcentaje del CONTEXT_SIZE podemos usar para texto + prompt
# dejando el resto para la generación de la respuesta del esquema parcial.
# Un valor más bajo es más seguro pero puede generar más mega-chunks.
MEGA_CHUNK_CONTEXT_FACTOR = 0.7 
# Solapamiento entre mega-chunks (en número de palabras)
MEGA_CHUNK_OVERLAP_WORDS = 200
FACTOR_PALABRAS_A_TOKENS_APROX = 1.7 