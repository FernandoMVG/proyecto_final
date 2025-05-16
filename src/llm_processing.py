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
            n_batch=getattr(config, 'N_BATCH_LLAMA', 512), # Usar n_batch de config si existe, sino default 512
            verbose=config.LLM_VERBOSE
        )
        end_time = time.time()
        # Eliminado el print de minutos aproximados que era confuso
        print(f"Modelo LLM cargado en {end_time - start_time:.2f} segundos.")
        return llm_instance
    except Exception as e:
        print(f"ERROR al cargar el modelo LLM: {e}")
        print("Posibles causas: CONTEXT_SIZE demasiado grande para la RAM/VRAM, o el modelo no soporta ese tamaño.")
        llm_instance = None
        return None

def generar_esquema_de_texto(texto_para_esquema, es_parcial=False, chunk_num=None, total_chunks=None):
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado en generar_esquema_de_texto.")
        return None

    if es_parcial:
        if chunk_num and total_chunks:
            descripcion_proceso = f"Esquema Parcial (Mega-Chunk {chunk_num}/{total_chunks})"
        else:
            descripcion_proceso = "Esquema Parcial (Mega-Chunk no especificado)"
    else:
        descripcion_proceso = "Esquema Completo (Pase Único)"
    
    print(f"\n--- Iniciando Generación de {descripcion_proceso} ---")
    
    prompt_final_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.format(texto_completo=texto_para_esquema)
    max_tokens_para_este_esquema = config.MAX_TOKENS_ESQUEMA_PARCIAL if es_parcial else config.MAX_TOKENS_ESQUEMA_FUSIONADO
    
    print(f"Enviando texto al LLM para generar {descripcion_proceso.lower()} (max_tokens: {max_tokens_para_este_esquema})...")
    start_time = time.time()
    try:
        output = llm_instance(
            prompt_final_esquema,
            max_tokens=max_tokens_para_este_esquema,
            stop=None, 
            echo=False,
            temperature=config.LLM_TEMPERATURE_ESQUEMA
        )
        
        esquema_generado = ""
        finish_reason = "desconocido"

        if output and 'choices' in output and len(output['choices']) > 0:
            esquema_generado = output['choices'][0]['text'].strip()
            finish_reason = output['choices'][0].get('finish_reason', 'desconocido')
        else:
            print(f"ADVERTENCIA: La salida del LLM para {descripcion_proceso.lower()} fue inesperada o vacía.")
            return None # Importante retornar None si no hay salida válida

        end_time = time.time()
        print(f"--- {descripcion_proceso} generado en {end_time - start_time:.2f} segundos (Finish Reason: {finish_reason}) ---")

        if finish_reason == 'length':
            print(f"    ¡¡¡ADVERTENCIA DE CORTE!!! La generación se detuvo porque alcanzó el límite de max_tokens ({max_tokens_para_este_esquema}).")
            print(f"    Últimos 100 caracteres generados: '...{esquema_generado[-100:]}'")
        elif finish_reason not in ['stop', 'eos_token', 'desconocido']:
             print(f"    ADVERTENCIA: Razón de finalización inusual para {descripcion_proceso.lower()}: {finish_reason}")
        
        return esquema_generado

    except Exception as e:
        print(f"ERROR durante la generación de {descripcion_proceso.lower()} con LLM: {e}")
        return None

def fusionar_esquemas(lista_esquemas_parciales):
    """
    Toma una lista de esquemas parciales y le pide al LLM que los fusione.
    """
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado en fusionar_esquemas.")
        return None
    if not lista_esquemas_parciales:
        print("ERROR: No hay esquemas parciales para fusionar.")
        return None
    if len(lista_esquemas_parciales) == 1:
        print("INFO: Solo hay un esquema parcial, devolviéndolo directamente (no se necesita fusión).")
        return lista_esquemas_parciales[0]

    print("\n--- Iniciando Fusión de Esquemas Parciales ---")
    
    texto_esquemas_concatenados = ""
    for i, esquema_p in enumerate(lista_esquemas_parciales):
        texto_esquemas_concatenados += f"--- ESQUEMA PARCIAL {i+1} ---\n{esquema_p}\n\n"
    
    prompt_final_fusion = prompts.PROMPT_FUSIONAR_ESQUEMAS_TEMPLATE.format(texto_esquemas_parciales=texto_esquemas_concatenados)
    
    estimacion_tokens_prompt_fusion = len(prompt_final_fusion.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX 
    if estimacion_tokens_prompt_fusion > config.CONTEXT_SIZE * 0.9: # Dejar 10% para la respuesta
        print(f"ADVERTENCIA: El conjunto de esquemas parciales para fusionar ({estimacion_tokens_prompt_fusion:.0f} tokens estimados) "
              f"podría ser demasiado largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}). La fusión podría fallar o ser incompleta.")

    print(f"Enviando esquemas parciales al LLM para fusión (max_tokens: {config.MAX_TOKENS_ESQUEMA_FUSIONADO})...")
    start_time = time.time()
    try:
        output = llm_instance(
            prompt_final_fusion,
            max_tokens=config.MAX_TOKENS_ESQUEMA_FUSIONADO,
            stop=None,
            echo=False,
            temperature=config.LLM_TEMPERATURE_FUSION
        )

        esquema_fusionado = ""
        finish_reason = "desconocido"

        if output and 'choices' in output and len(output['choices']) > 0:
            esquema_fusionado = output['choices'][0]['text'].strip()
            finish_reason = output['choices'][0].get('finish_reason', 'desconocido')
        else:
            print(f"ADVERTENCIA: La salida del LLM para la fusión fue inesperada o vacía.")
            return None # Importante retornar None

        end_time = time.time()
        minutos_fusion = (end_time - start_time) / 60
        print(f"--- Fusión de esquemas completada en {end_time - start_time:.2f} segundos --- Minutos aproximados: {minutos_fusion:.2f} (Finish Reason: {finish_reason}) ---")

        if finish_reason == 'length':
            print(f"    ¡¡¡ADVERTENCIA DE CORTE!!! La fusión se detuvo porque alcanzó el límite de max_tokens ({config.MAX_TOKENS_ESQUEMA_FUSIONADO}).")
            print(f"    Últimos 100 caracteres generados: '...{esquema_fusionado[-100:]}'")
        elif finish_reason not in ['stop', 'eos_token', 'desconocido']:
             print(f"    ADVERTENCIA: Razón de finalización inusual para la fusión: {finish_reason}")

        return esquema_fusionado
    except Exception as e:
        print(f"ERROR durante la fusión de esquemas con LLM: {e}")
        return None
    
def generar_apuntes_desde_esquema(texto_completo, esquema_clase):
    """
    Genera apuntes detallados en Markdown usando la transcripción completa y un esquema.
    """
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado en generar_apuntes_desde_esquema.")
        return None
    if not texto_completo or not esquema_clase:
        print("ERROR: Se requiere la transcripción completa y el esquema de la clase para generar apuntes.")
        return None

    print("\n--- Iniciando Generación de Apuntes Detallados ---")
    
    prompt_final_apuntes = prompts.PROMPT_GENERAR_APUNTES_TEMPLATE.format(
        esquema_clase=esquema_clase,
        texto_completo=texto_completo
    )

    # Estimación de tokens para el prompt de apuntes (puede ser muy grande)
    estimacion_tokens_prompt_apuntes = len(prompt_final_apuntes.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    if estimacion_tokens_prompt_apuntes > config.CONTEXT_SIZE * 0.9: # Dejar 10% para la respuesta
        print(f"ADVERTENCIA MUY SERIA: El prompt para generar apuntes ({estimacion_tokens_prompt_apuntes:.0f} tokens est.) "
              f"es demasiado largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}). Los apuntes podrían ser muy incompletos o fallar.")
        # Considerar estrategias más avanzadas si esto ocurre (ej. generar apuntes por sección del esquema)

    print(f"Enviando transcripción y esquema al LLM para generar apuntes (max_tokens: {config.MAX_TOKENS_APUNTES})... Esto puede tardar MUCHO tiempo.")
    start_time = time.time()
    try:
        output = llm_instance(
            prompt_final_apuntes,
            max_tokens=config.MAX_TOKENS_APUNTES, # Necesitará muchos tokens para la salida
            stop=None, 
            echo=False,
            temperature=config.LLM_TEMPERATURE_APUNTES # Temperatura para los apuntes
        )
        
        apuntes_generados = ""
        finish_reason = "desconocido"

        if output and 'choices' in output and len(output['choices']) > 0:
            apuntes_generados = output['choices'][0]['text'].strip()
            finish_reason = output['choices'][0].get('finish_reason', 'desconocido')
        else:
            print(f"ADVERTENCIA: La salida del LLM para los apuntes fue inesperada o vacía.")
            return None

        end_time = time.time()
        minutos_apuntes = (end_time - start_time) / 60
        print(f"--- Apuntes detallados generados en {end_time - start_time:.2f} segundos --- Minutos aproximados: {minutos_apuntes:.2f} (Finish Reason: {finish_reason}) ---")

        if finish_reason == 'length':
            print(f"    ¡¡¡ADVERTENCIA DE CORTE!!! La generación de apuntes se detuvo porque alcanzó el límite de max_tokens ({config.MAX_TOKENS_APUNTES}).")
            print(f"    Últimos 100 caracteres generados: '...{apuntes_generados[-100:]}'")
        elif finish_reason not in ['stop', 'eos_token', 'desconocido']:
             print(f"    ADVERTENCIA: Razón de finalización inusual para los apuntes: {finish_reason}")
        
        return apuntes_generados

    except Exception as e:
        print(f"ERROR durante la generación de apuntes con LLM: {e}")
        return None    