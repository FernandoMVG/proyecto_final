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


# --- Configuración del LLM ---
# ¡IMPORTANTE! Aumenta CONTEXT_SIZE al máximo que tu modelo y hardware soporten
CONTEXT_SIZE = 16384  # Ejemplo: 30k tokens. Prueba con 16384, 32768 según tu Mistral 7B.
                      # Verifica la documentación de tu modelo GGUF específico.
# Necesitaremos muchos tokens para generar un esquema detallado de una clase larga
MAX_TOKENS_ESQUEMA = 4096 # Empieza con esto, podrías necesitar aumentarlo a 8192 o más.
# MAX_TOKENS_APUNTES = 8192 # Para cuando generes los apuntes (más adelante)
N_GPU_LAYERS = -1
N_THREADS = None
LLM_VERBOSE = False
LLM_TEMPERATURE_ESQUEMA = 0.3 # Temperatura para la generación del esquema

# --- Ya no necesitamos configuración de chunking ---
# CHUNK_SIZE_WORDS = 700
# CHUNK_OVERLAP_WORDS = 50