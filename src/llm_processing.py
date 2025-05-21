# src/llm_processing.py
from llama_cpp import Llama
import os
import time
from src import config  # Usar import relativo
from src import prompts

llm_instance = None

def cargar_modelo_llm():
    global llm_instance
    if llm_instance is not None:
        print("INFO: Modelo LLM ya está cargado.")
        return llm_instance

    print(f"Cargando modelo desde: {config.MODEL_PATH}")
    if not os.path.exists(config.MODEL_PATH):
        print(f"ERROR CRÍTICO: No se encontró el archivo del modelo en {config.MODEL_PATH}")
        return None
    try:
        start_time_carga = time.time()
        llm_instance = Llama(
            model_path=config.MODEL_PATH,
            n_ctx=config.CONTEXT_SIZE,
            n_threads=config.N_THREADS,
            n_gpu_layers=config.N_GPU_LAYERS,
            n_batch=config.N_BATCH_LLAMA,
            verbose=config.LLM_VERBOSE
        )
        end_time_carga = time.time()
        print(f"Modelo LLM cargado exitosamente en {end_time_carga - start_time_carga:.2f} segundos.")
        return llm_instance
    except Exception as e:
        print(f"ERROR CRÍTICO al cargar el modelo LLM: {e}")
        print("Posibles causas: CONTEXT_SIZE demasiado grande para la RAM/VRAM, archivo de modelo corrupto, o Llama.cpp no compilado con soporte GPU si N_GPU_LAYERS > 0.")
        llm_instance = None
        return None

def _llamar_al_llm(prompt_texto, max_tokens_salida, temperatura, descripcion_tarea, stop_sequences=None):
    if llm_instance is None:
        print(f"ERROR FATAL: Modelo LLM no cargado. No se puede procesar '{descripcion_tarea}'.")
        return None, "llm_not_loaded", {}

    print(f"    Enviando prompt al LLM para '{descripcion_tarea}' (max_tokens_out: {max_tokens_salida}, temp: {temperatura})...")
    
    start_time_llm = time.time()
    try:
        output = llm_instance(
            prompt_texto,
            max_tokens=max_tokens_salida,
            stop=stop_sequences,
            echo=False,
            temperature=temperatura
        )
        
        end_time_llm = time.time()
        processing_time = end_time_llm - start_time_llm

        texto_generado = ""
        finish_reason = "desconocido"
        tokens_generados = 0
        tokens_prompt = 0

        if output and 'choices' in output and len(output['choices']) > 0:
            texto_generado = output['choices'][0]['text'].strip()
            finish_reason = output['choices'][0].get('finish_reason', 'desconocido')
            if finish_reason is None:
                finish_reason = "completed_unknown"
            
            usage_stats = output.get('usage', {})
            tokens_generados = usage_stats.get('completion_tokens', 0)
            if tokens_generados == 0 and texto_generado and llm_instance: # Asegurar que llm_instance existe
                tokens_generados = len(llm_instance.tokenize(texto_generado.encode('utf-8', 'ignore')))

            tokens_prompt = usage_stats.get('prompt_tokens', 0)
            if tokens_prompt == 0 and llm_instance: # Asegurar que llm_instance existe
                 tokens_prompt = len(llm_instance.tokenize(prompt_texto.encode('utf-8', 'ignore')))
        else:
            print(f"    ADVERTENCIA: La salida del LLM para '{descripcion_tarea}' fue inesperada o vacía. Output: {output}")
            return None, "empty_or_invalid_llm_output", {"tokens_prompt": tokens_prompt if 'tokens_prompt' in locals() else 0}


        tokens_por_segundo = 0
        if processing_time > 0 and tokens_generados > 0:
            tokens_por_segundo = tokens_generados / processing_time
        
        stats = {
            "tokens_prompt": tokens_prompt,
            "tokens_generados": tokens_generados,
            "processing_time_seconds": processing_time,
            "tokens_por_segundo": tokens_por_segundo
        }

        print(f"--- LLM Task '{descripcion_tarea}' completada en {processing_time:.2f} seg. ---")
        print(f"    Stats: Prompt Tokens: {tokens_prompt}, Tokens Generados: {tokens_generados}, Tasa: {tokens_por_segundo:.2f} tokens/seg.")
        print(f"    Finish Reason: {finish_reason}")

        if finish_reason == 'length':
            print(f"    ¡¡¡ADVERTENCIA DE CORTE!!! La generación para '{descripcion_tarea}' se detuvo porque alcanzó el límite de max_tokens ({max_tokens_salida}).")
        elif finish_reason not in ['stop', 'eos_token', 'completed_unknown'] and (stop_sequences is None or finish_reason not in stop_sequences):
             print(f"    ADVERTENCIA: Razón de finalización inusual para '{descripcion_tarea}': {finish_reason}")
        
        return texto_generado, finish_reason, stats

    except Exception as e:
        print(f"ERROR CRÍTICO durante la llamada al LLM para '{descripcion_tarea}': {e}")
        return None, f"exception_during_llm_call: {str(e)}", {}


def generar_esquema_de_texto(texto_para_esquema, es_parcial=False, chunk_num=None, total_chunks=None):
    if es_parcial:
        num_str = str(chunk_num) if chunk_num is not None else "?"
        total_str = str(total_chunks) if total_chunks is not None else "?"
        descripcion_proceso_base = f"Esquema Parcial (Mega-Chunk {num_str}/{total_str})"
    else:
        descripcion_proceso_base = "Esquema Completo (Pase Único)"
    
    print(f"\n--- Iniciando Generación de {descripcion_proceso_base} ---")
    
    prompt_final_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.format(texto_completo=texto_para_esquema)
    max_tokens_para_este_esquema = config.MAX_TOKENS_ESQUEMA_PARCIAL if es_parcial else config.MAX_TOKENS_ESQUEMA_FUSIONADO
    
    # Estimación de tokens del prompt
    # (código de estimación de tokens del prompt se mantiene igual)
    prompt_template_sin_texto = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
    # Usar config.FACTOR_PALABRAS_A_TOKENS_APROX para la estimación si es mayor a cero
    factor_conversion = config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else 1.5
    tokens_prompt_template_aprox = len(prompt_template_sin_texto.split()) / factor_conversion
    tokens_texto_contenido_aprox = len(texto_para_esquema.split()) / factor_conversion
    tokens_totales_prompt_aprox = tokens_prompt_template_aprox + tokens_texto_contenido_aprox


    if tokens_totales_prompt_aprox + max_tokens_para_este_esquema > config.CONTEXT_SIZE:
        print(f"    ADVERTENCIA: El prompt ({tokens_totales_prompt_aprox:.0f} tokens) + salida ({max_tokens_para_este_esquema}) "
              f"EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). La calidad podría verse afectada o fallar.")
    elif tokens_totales_prompt_aprox > config.CONTEXT_SIZE * 0.9:
         print(f"    AVISO: El prompt ({tokens_totales_prompt_aprox:.0f} tokens) ocupa una gran parte del CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    esquema_generado, _, _ = _llamar_al_llm(
        prompt_texto=prompt_final_esquema,
        max_tokens_salida=max_tokens_para_este_esquema,
        temperatura=config.LLM_TEMPERATURE_ESQUEMA,
        descripcion_tarea=descripcion_proceso_base
    )
    return esquema_generado

def fusionar_esquemas(lista_esquemas_parciales):
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
    
    factor_conversion = config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else 1.5
    tokens_prompt_fusion_aprox = len(prompt_final_fusion.split()) / factor_conversion
    if tokens_prompt_fusion_aprox + config.MAX_TOKENS_ESQUEMA_FUSIONADO > config.CONTEXT_SIZE:
        print(f"    ADVERTENCIA: El prompt de fusión ({tokens_prompt_fusion_aprox:.0f} tokens) + salida ({config.MAX_TOKENS_ESQUEMA_FUSIONADO}) "
              f"EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). La fusión podría fallar o ser incompleta.")
    elif tokens_prompt_fusion_aprox > config.CONTEXT_SIZE * 0.85:
        print(f"    AVISO: El prompt de esquemas parciales para fusionar ({tokens_prompt_fusion_aprox:.0f} tokens est.) "
              f"es muy largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    esquema_fusionado, _, _ = _llamar_al_llm(
        prompt_texto=prompt_final_fusion,
        max_tokens_salida=config.MAX_TOKENS_ESQUEMA_FUSIONADO,
        temperatura=config.LLM_TEMPERATURE_FUSION,
        descripcion_tarea="Fusión de Esquemas"
    )
    return esquema_fusionado
    
