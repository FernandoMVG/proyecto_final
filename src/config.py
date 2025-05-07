# src/config.py
import os

# --- Directorios Base ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # Directorio de src/
BASE_PROJECT_DIR = os.path.join(SCRIPT_DIR, "..") # Directorio raíz del proyecto

# --- Configuración del Modelo y Rutas ---
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
MODEL_PATH = os.path.join(BASE_PROJECT_DIR, "models", MODEL_FILENAME)
INPUT_FILE_NAME = "transcripcion_ejemplo.txt"
INPUT_FILE_PATH = os.path.join(BASE_PROJECT_DIR, "data", INPUT_FILE_NAME)
OUTPUT_MAP_RESULTS_FILENAME = "map_results.txt"
OUTPUT_MAP_RESULTS_PATH = os.path.join(BASE_PROJECT_DIR, "output", OUTPUT_MAP_RESULTS_FILENAME)
FINAL_OUTPUT_FILENAME = "guia_estudio.md"
FINAL_OUTPUT_PATH = os.path.join(BASE_PROJECT_DIR, "output", FINAL_OUTPUT_FILENAME)

# --- Configuración del LLM ---
CONTEXT_SIZE = 4096
MAX_TOKENS_MAP = 250      # Aumenté un poco por si el prompt más largo lo necesita
MAX_TOKENS_REDUCE = 1536
N_GPU_LAYERS = -1
N_THREADS = None
LLM_VERBOSE = False # Para la carga del modelo Llama

# --- Configuración del Procesamiento ---
CHUNK_SIZE_WORDS = 700
CHUNK_OVERLAP_WORDS = 50