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
CONTEXT_SIZE = 16384
MAX_TOKENS_ESQUEMA_PARCIAL = 2048
MAX_TOKENS_ESQUEMA_FUSIONADO = 4096
MAX_TOKENS_APUNTES_POR_SECCION = 1024 # Tokens para la *salida* de apuntes de una sección
N_GPU_LAYERS = -1
N_THREADS = None
LLM_VERBOSE = False
LLM_TEMPERATURE_ESQUEMA = 0.3
LLM_TEMPERATURE_FUSION = 0.2
LLM_TEMPERATURE_APUNTES = 0.5
N_BATCH_LLAMA = 1024 # o 512

# --- Configuración del Mega-Chunking (para generación de esquema si es necesario) ---
MEGA_CHUNK_CONTEXT_FACTOR = 0.7 
MEGA_CHUNK_OVERLAP_WORDS = 200
FACTOR_PALABRAS_A_TOKENS_APROX = 1.7

# --- NUEVO: Configuración de la API de la Base de Datos Vectorial ---
VECTOR_DB_API_URL = "http://127.0.0.1:8000" 
# Chunks para poblar la BD vectorial (más pequeños que los mega-chunks)
VECTOR_DB_POPULATE_CHUNK_SIZE_WORDS = 200 
VECTOR_DB_POPULATE_CHUNK_OVERLAP_WORDS = 30
# Número de chunks relevantes a recuperar para el contexto de los apuntes
NUM_RELEVANT_CHUNKS_FOR_APUNTES = 3