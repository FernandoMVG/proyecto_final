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
OUTPUT_ESQUEMA_FILENAME = "esquema_clase_2.Q4_K_M.txt"
OUTPUT_ESQUEMA_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_ESQUEMA_FILENAME)
TEMPLATE_TRANSCRIPCION_FILENAME = "ejemplo_transcripcion_template.txt"
TEMPLATE_TRANSCRIPCION_PATH = os.path.join(BASE_PROJECT_DIR, "templates", TEMPLATE_TRANSCRIPCION_FILENAME) 
OUTPUT_APUNTES_FILENAME = "apuntes_clase_final.md"
OUTPUT_APUNTES_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_APUNTES_FILENAME)


# --- Configuración del LLM ---
CONTEXT_SIZE = 8192 # Tamaño máximo de contexto para el modelo local (ajustar según memoria y modelo)
MAX_TOKENS_ESQUEMA_PARCIAL = 1024
MAX_TOKENS_ESQUEMA_FUSIONADO = 2048
MAX_TOKENS_APUNTES_POR_SECCION = 1024
N_GPU_LAYERS = 0
N_THREADS = 4     # None para que Llama.cpp decida (usualmente óptimo)
LLM_VERBOSE = False
LLM_TEMPERATURE_ESQUEMA = 0.3
LLM_TEMPERATURE_FUSION = 0.2
LLM_TEMPERATURE_APUNTES = 0.4
N_BATCH_LLAMA = 512

# --- Configuración del Mega-Chunking (para generación de esquema si es necesario) ---
MEGA_CHUNK_CONTEXT_FACTOR = 0.7
MEGA_CHUNK_OVERLAP_TOKENS = 200 # Solapamiento de tokens para mega-chunks

# --- Configuración específica de Gemini ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20" # O el modelo que vayas a usa

# --- Configuración de la Base de Datos Vectorial ---
VECTOR_DB_BASE_URL = os.getenv("VECTOR_DB_URL", "http://localhost:9000") # URL base para el servicio de búsqueda vectorial
MAX_SCHEMA_TERMS_TO_QUERY = 3 # Número máximo de términos a extraer del esquema para consultar la BD vectorial
VECTOR_DB_TOP_K_PER_TERM = 1 # Número de resultados a obtener de la BD vectorial por cada término del esquema consultado