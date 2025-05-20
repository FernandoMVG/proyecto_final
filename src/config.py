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
OUTPUT_ESQUEMA_FILENAME = "esquema_clase.txt"
OUTPUT_ESQUEMA_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_ESQUEMA_FILENAME)
OUTPUT_APUNTES_FILENAME = "apuntes_clase_final.md"
OUTPUT_APUNTES_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_APUNTES_FILENAME)

# --- Configuración del LLM ---
CONTEXT_SIZE = 8192 #16384
MAX_TOKENS_ESQUEMA_PARCIAL = 512
MAX_TOKENS_ESQUEMA_FUSIONADO = 2048
MAX_TOKENS_APUNTES_POR_SECCION = 2048 # Tokens para la *salida* de apuntes de una sección
N_GPU_LAYERS = -1  # -1 para cargar todas las capas posibles en GPU
N_THREADS = None     # None para que Llama.cpp decida (usualmente óptimo)
LLM_VERBOSE = False
LLM_TEMPERATURE_ESQUEMA = 0.3
LLM_TEMPERATURE_FUSION = 0.2
LLM_TEMPERATURE_APUNTES = 0.3
N_BATCH_LLAMA = 1024 # o 512. Asegurar que esté definido.

# --- Configuración del Mega-Chunking (para generación de esquema si es necesario) ---
MEGA_CHUNK_CONTEXT_FACTOR = 0.7
MEGA_CHUNK_OVERLAP_WORDS = 50
FACTOR_PALABRAS_A_TOKENS_APROX = 1.7 # Estimación conservadora (puede ser 1.3-1.5 para inglés, español un poco más)

# --- NUEVO: Configuración de la API de la Base de Datos Vectorial ---
VECTOR_DB_API_URL = "http://127.0.0.1:8000"
# Chunks para poblar la BD vectorial (más pequeños que los mega-chunks)
VECTOR_DB_POPULATE_CHUNK_SIZE_WORDS = 150 # Ajustado de 100, experimentar
VECTOR_DB_POPULATE_CHUNK_OVERLAP_WORDS = 30  # Ajustado de 20, experimentar
# Número de chunks relevantes a recuperar para el contexto de los apuntes
NUM_RELEVANT_CHUNKS_FOR_APUNTES = 7 # Ajustado de 12, experimentar