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
        print(f"Modelo LLM cargado en {end_time - start_time:.2f} segundos. Aproximadamente {(config.CONTEXT_SIZE / 60):.2f} minutos.")
        return llm_instance
    except Exception as e:
        print(f"ERROR al cargar el modelo LLM: {e}")
        print("Posibles causas: CONTEXT_SIZE demasiado grande para la RAM/VRAM, o el modelo no soporta ese tamaño.")
        llm_instance = None
        return None

def generar_esquema_de_texto(texto_para_esquema, es_parcial=False, chunk_num=None, total_chunks=None): # Nuevos parámetros opcionales
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado.")
        return None

    # Construir descripción del proceso dinámicamente
    if es_parcial:
        if chunk_num and total_chunks:
            descripcion_proceso = f"Esquema Parcial (Mega-Chunk {chunk_num}/{total_chunks})"
        else:
            descripcion_proceso = "Esquema Parcial (Mega-Chunk no especificado)"
    else:
        descripcion_proceso = "Esquema Completo"
    
    print(f"\n--- Iniciando Generación de {descripcion_proceso} ---")
    
    prompt_final_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.format(texto_completo=texto_para_esquema)
    
    # Determinar max_tokens basado en si es parcial o final (fusión usa otro)
    # Esta función es solo para generar esquema de *un* texto, la fusión es separada.
    # Si es parcial, usa MAX_TOKENS_ESQUEMA_PARCIAL. Si es el esquema final de un solo pase, usa MAX_TOKENS_ESQUEMA_FUSIONADO.
    max_tokens_para_este_esquema = config.MAX_TOKENS_ESQUEMA_PARCIAL if es_parcial else config.MAX_TOKENS_ESQUEMA_FUSIONADO
    
    print(f"Enviando texto al LLM para generar {descripcion_proceso.lower()}...")
    start_time = time.time()
    try:
        output = llm_instance(
            prompt_final_esquema,
            max_tokens=max_tokens_para_este_esquema,
            stop=None, 
            echo=False,
            temperature=config.LLM_TEMPERATURE_ESQUEMA
        )
        esquema_generado = output['choices'][0]['text'].strip()
        end_time = time.time()
        print(f"--- {descripcion_proceso} generado en {end_time - start_time:.2f} segundos ---")
        return esquema_generado
    except Exception as e:
        print(f"ERROR durante la generación de {descripcion_proceso.lower()} con LLM: {e}")
        return None

def fusionar_esquemas(lista_esquemas_parciales):
    """
    Toma una lista de esquemas parciales y le pide al LLM que los fusione.
    """
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado.")
        return None
    if not lista_esquemas_parciales:
        print("ERROR: No hay esquemas parciales para fusionar.")
        return None
    if len(lista_esquemas_parciales) == 1:
        print("INFO: Solo hay un esquema parcial, no se necesita fusión.")
        return lista_esquemas_parciales[0]

    print("\n--- Iniciando Fusión de Esquemas Parciales ---")
    
    texto_esquemas_concatenados = ""
    for i, esquema_p in enumerate(lista_esquemas_parciales):
        texto_esquemas_concatenados += f"--- ESQUEMA PARCIAL {i+1} ---\n{esquema_p}\n\n"
    
    prompt_final_fusion = prompts.PROMPT_FUSIONAR_ESQUEMAS_TEMPLATE.format(texto_esquemas_parciales=texto_esquemas_concatenados)

    # Verificar si los esquemas concatenados + prompt caben en el contexto
    estimacion_tokens_prompt_fusion = len(prompt_final_fusion.split()) * 1.7 # Estimación muy burda
    if estimacion_tokens_prompt_fusion > config.CONTEXT_SIZE * 0.9:
        print(f"ADVERTENCIA: El conjunto de esquemas parciales para fusionar ({estimacion_tokens_prompt_fusion} tokens estimados) "
              f"es demasiado largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}). La fusión podría fallar o ser incompleta.")
        # Aquí se podría implementar una fusión jerárquica de esquemas si fuera necesario
        # (fusionar de 2 en 2, luego los resultados, etc.) pero es más complejo.

    print("Enviando esquemas parciales al LLM para fusión...")
    start_time = time.time()
    try:
        output = llm_instance(
            prompt_final_fusion,
            max_tokens=config.MAX_TOKENS_ESQUEMA_FUSIONADO,
            stop=None,
            echo=False,
            temperature=config.LLM_TEMPERATURE_FUSION
        )
        esquema_fusionado = output['choices'][0]['text'].strip()
        end_time = time.time()
        print(f"--- Fusión de esquemas completada en {end_time - start_time:.2f} segundos --- Minutos aproximados: {(end_time - start_time) / 60:.2f}")
        return esquema_fusionado
    except Exception as e:
        print(f"ERROR durante la fusión de esquemas con LLM: {e}")
        return None