# src/llm_processing.py
from llama_cpp import Llama
import os
import time
import re
from src import config  # Importa configuraciones
from src import prompts # Importa plantillas de prompts

# --- Carga del Modelo LLM ---
llm_instance = None

def cargar_modelo_llm():
    """Carga el modelo LLM globalmente."""
    global llm_instance
    if llm_instance is not None:
        # print("Modelo LLM ya cargado.") # Opcional, para no repetir el mensaje
        return llm_instance

    print(f"Cargando modelo desde: {config.MODEL_PATH}")
    if not os.path.exists(config.MODEL_PATH):
        print(f"ERROR: No se encontró el archivo del modelo en {config.MODEL_PATH}")
        return None
    try:
        start_time = time.time()
        llm_instance = Llama(
            model_path=config.MODEL_PATH,
            n_ctx=config.CONTEXT_SIZE,
            n_threads=config.N_THREADS,
            n_gpu_layers=config.N_GPU_LAYERS,
            verbose=config.LLM_VERBOSE
        )
        end_time = time.time()
        print(f"Modelo LLM cargado en {end_time - start_time:.2f} segundos.")
        return llm_instance
    except Exception as e:
        print(f"ERROR al cargar el modelo LLM: {e}")
        print("Posibles causas: CONTEXT_SIZE demasiado grande para la RAM/VRAM, o el modelo no soporta ese tamaño.")
        llm_instance = None
        return None

def generar_esquema_desde_transcripcion(texto_completo):
    """
    Pide al LLM que genere un esquema jerárquico de los temas de la transcripción.
    """
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado. Llama a cargar_modelo_llm() primero.")
        return None

    print("\n--- Iniciando Generación de Esquema Estructurado ---")
    
    prompt_final_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.format(texto_completo=texto_completo)
    
    print("Enviando transcripción completa al LLM para generar el esquema... Esto puede tardar.")
    start_schema_time = time.time()
    try:
        output = llm_instance(
            prompt_final_esquema,
            max_tokens=config.MAX_TOKENS_ESQUEMA,
            stop=None, 
            echo=False,
            temperature=config.LLM_TEMPERATURE_ESQUEMA
        )
        esquema_generado = output['choices'][0]['text'].strip()
        end_schema_time = time.time()
        print(f"--- Esquema generado en {end_schema_time - start_schema_time:.2f} segundos ---")
        return esquema_generado

    except Exception as e:
        print(f"ERROR durante la generación del esquema con LLM: {e}")
        return None