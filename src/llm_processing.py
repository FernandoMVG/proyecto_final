# src/llm_processing.py
from llama_cpp import Llama
import os
import time
import logging # <--- Importar logging
from src import config
from src import prompts

logger = logging.getLogger(__name__) # <--- Obtener logger para este módulo
llm_instance = None

def cargar_modelo_llm():
    global llm_instance
    if llm_instance is not None:
        logger.info("Modelo LLM ya está cargado.")
        return llm_instance

    logger.info(f"Cargando modelo desde: {config.MODEL_PATH}")
    if not os.path.exists(config.MODEL_PATH):
        logger.critical(f"No se encontró el archivo del modelo en {config.MODEL_PATH}")
        return None
    try:
        start_time_carga = time.time()
        llm_instance = Llama(
            model_path=config.MODEL_PATH,
            n_ctx=config.CONTEXT_SIZE,
            n_threads=config.N_THREADS,
            n_gpu_layers=config.N_GPU_LAYERS,
            n_batch=config.N_BATCH_LLAMA,
            verbose=config.LLM_VERBOSE # Controla el verbose de llama.cpp
        )
        end_time_carga = time.time()
        logger.info(f"Modelo LLM cargado exitosamente en {end_time_carga - start_time_carga:.2f} segundos.")
        return llm_instance
    except Exception as e:
        logger.critical(f"Al cargar el modelo LLM: {e}", exc_info=True)
        logger.info("Posibles causas: CONTEXT_SIZE, archivo corrupto, Llama.cpp sin soporte GPU.")
        llm_instance = None
        return None

def _llamar_al_llm(prompt_texto, max_tokens_salida, temperatura, descripcion_tarea, stop_sequences=None):
    if llm_instance is None:
        logger.critical(f"Modelo LLM no cargado. No se puede procesar '{descripcion_tarea}'.")
        return None, "llm_not_loaded", {}

    logger.info(f"Enviando prompt al LLM para '{descripcion_tarea}' (max_tokens_out: {max_tokens_salida}, temp: {temperatura}).")
    # Opcional: Loguear el prompt solo si el nivel DEBUG está activo
    if logger.isEnabledFor(logging.DEBUG):
        # Evitar tokenizar si el llm_instance aún no está cargado, aunque la guarda anterior debería prevenirlo.
        prompt_tokens_count_debug = 0
        if llm_instance:
            try:
                prompt_tokens_count_debug = len(llm_instance.tokenize(prompt_texto.encode('utf-8', 'ignore')))
            except Exception as e: # Captura cualquier error durante la tokenización para debug
                logger.debug(f"No se pudo tokenizar el prompt para debug: {e}")
        logger.debug(f"Prompt para '{descripcion_tarea}' ({prompt_tokens_count_debug} tokens aprox):\n'''\n{prompt_texto[:500]}...\n'''")
    
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
        tokens_prompt = 0 # Inicializar para el caso de error antes de obtener 'usage'

        if output and 'choices' in output and len(output['choices']) > 0:
            texto_generado = output['choices'][0]['text'].strip()
            finish_reason = output['choices'][0].get('finish_reason', 'desconocido')
            if finish_reason is None: # Llama.cpp puede devolver None
                finish_reason = "completed_unknown" # O "stop" si es más probable
            
            usage_stats = output.get('usage', {})
            tokens_generados = usage_stats.get('completion_tokens', 0)
            if tokens_generados == 0 and texto_generado and llm_instance:
                try:
                    tokens_generados = len(llm_instance.tokenize(texto_generado.encode('utf-8', 'ignore')))
                except Exception as e:
                     logger.debug(f"No se pudo tokenizar el texto generado para fallback: {e}")


            tokens_prompt = usage_stats.get('prompt_tokens', 0)
            # El fallback para tokens_prompt ya se hizo en el log DEBUG si estaba activo.
            # Si no, y 'prompt_tokens' es 0, podríamos tokenizar aquí también, pero
            # es menos crítico que los tokens_generados para la tasa.
            if tokens_prompt == 0 and llm_instance and 'prompt_tokens_count_debug' not in locals() : # Si no se calculó en debug
                try:
                    tokens_prompt = len(llm_instance.tokenize(prompt_texto.encode('utf-8', 'ignore')))
                except Exception as e:
                    logger.debug(f"No se pudo tokenizar el prompt para fallback de tokens_prompt: {e}")

        else:
            logger.warning(f"La salida del LLM para '{descripcion_tarea}' fue inesperada o vacía. Output: {output}")
            # Intentar obtener tokens_prompt si se calculó en debug
            calculated_tokens_prompt = 0
            if 'prompt_tokens_count_debug' in locals(): # Si el logger DEBUG estaba activo
                calculated_tokens_prompt = prompt_tokens_count_debug
            return None, "empty_or_invalid_llm_output", {"tokens_prompt": calculated_tokens_prompt}

        tokens_por_segundo = 0
        if processing_time > 0 and tokens_generados > 0:
            tokens_por_segundo = tokens_generados / processing_time
        
        stats = {
            "tokens_prompt": tokens_prompt,
            "tokens_generados": tokens_generados,
            "processing_time_seconds": processing_time,
            "tokens_por_segundo": tokens_por_segundo
        }

        logger.info(f"LLM Task '{descripcion_tarea}' completada en {processing_time:.2f} seg.")
        logger.info(f"  Stats: Prompt Tokens: {tokens_prompt}, Tokens Generados: {tokens_generados}, Tasa: {tokens_por_segundo:.2f} tokens/seg.")
        logger.info(f"  Finish Reason: {finish_reason}")

        if finish_reason == 'length':
            logger.warning(f"¡CORTE! La generación para '{descripcion_tarea}' se detuvo por max_tokens ({max_tokens_salida}).")
            if logger.isEnabledFor(logging.DEBUG):
                 logger.debug(f"  Últimos 150 caracteres generados: '...{texto_generado[-150:]}'")
        elif finish_reason not in ['stop', 'eos_token', 'completed_unknown'] and \
             (stop_sequences is None or finish_reason not in stop_sequences):
             logger.warning(f"Razón de finalización inusual para '{descripcion_tarea}': {finish_reason}")
        
        return texto_generado, finish_reason, stats

    except Exception as e:
        logger.error(f"Durante la llamada al LLM para '{descripcion_tarea}': {e}", exc_info=True)
        return None, f"exception_during_llm_call: {str(e)}", {}


def generar_esquema_de_texto(texto_para_esquema, es_parcial=False, chunk_num=None, total_chunks=None):
    if es_parcial:
        num_str = str(chunk_num) if chunk_num is not None else "?"
        total_str = str(total_chunks) if total_chunks is not None else "?"
        descripcion_proceso_base = f"Esquema Parcial (Mega-Chunk {num_str}/{total_str})"
    else:
        descripcion_proceso_base = "Esquema Completo (Pase Único)"
    
    logger.info(f"Iniciando Generación de {descripcion_proceso_base}")
    
    prompt_final_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.format(texto_completo=texto_para_esquema)
    max_tokens_para_este_esquema = config.MAX_TOKENS_ESQUEMA_PARCIAL if es_parcial else config.MAX_TOKENS_ESQUEMA_FUSIONADO
    
    prompt_template_sin_texto = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
    factor_conversion = config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else 1.5
    
    # Estimación de tokens del prompt
    # Si factor_conversion es PALABRAS / TOKEN (ej. 1.7), entonces TOKENS = PALABRAS / factor_conversion
    tokens_prompt_template_aprox = len(prompt_template_sin_texto.split()) / factor_conversion
    tokens_texto_contenido_aprox = len(texto_para_esquema.split()) / factor_conversion
    tokens_totales_prompt_aprox = tokens_prompt_template_aprox + tokens_texto_contenido_aprox

    if tokens_totales_prompt_aprox + max_tokens_para_este_esquema > config.CONTEXT_SIZE:
        logger.warning(f"El prompt ({tokens_totales_prompt_aprox:.0f} tokens) + salida ({max_tokens_para_este_esquema}) "
                       f"EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). La calidad podría verse afectada o fallar.")
    elif tokens_totales_prompt_aprox > config.CONTEXT_SIZE * 0.9:
         logger.info(f"El prompt ({tokens_totales_prompt_aprox:.0f} tokens) ocupa una gran parte del CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    esquema_generado, _, _ = _llamar_al_llm(
        prompt_texto=prompt_final_esquema,
        max_tokens_salida=max_tokens_para_este_esquema,
        temperatura=config.LLM_TEMPERATURE_ESQUEMA,
        descripcion_tarea=descripcion_proceso_base
    )
    return esquema_generado

def fusionar_esquemas(lista_esquemas_parciales):
    if not lista_esquemas_parciales:
        logger.error("No hay esquemas parciales para fusionar.")
        return None
    if len(lista_esquemas_parciales) == 1:
        logger.info("Solo hay un esquema parcial, devolviéndolo directamente (no se necesita fusión).")
        return lista_esquemas_parciales[0]

    logger.info("Iniciando Fusión de Esquemas Parciales")
    
    texto_esquemas_concatenados = ""
    for i, esquema_p in enumerate(lista_esquemas_parciales):
        texto_esquemas_concatenados += f"--- ESQUEMA PARCIAL {i+1} ---\n{esquema_p}\n\n"
    
    prompt_final_fusion = prompts.PROMPT_FUSIONAR_ESQUEMAS_TEMPLATE.format(texto_esquemas_parciales=texto_esquemas_concatenados)
    
    factor_conversion = config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else 1.5
    tokens_prompt_fusion_aprox = len(prompt_final_fusion.split()) / factor_conversion

    if tokens_prompt_fusion_aprox + config.MAX_TOKENS_ESQUEMA_FUSIONADO > config.CONTEXT_SIZE:
        logger.warning(f"El prompt de fusión ({tokens_prompt_fusion_aprox:.0f} tokens) + salida ({config.MAX_TOKENS_ESQUEMA_FUSIONADO}) "
                       f"EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). La fusión podría fallar o ser incompleta.")
    elif tokens_prompt_fusion_aprox > config.CONTEXT_SIZE * 0.85:
        logger.info(f"El prompt de esquemas parciales para fusionar ({tokens_prompt_fusion_aprox:.0f} tokens est.) "
                       f"es muy largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    esquema_fusionado, _, _ = _llamar_al_llm(
        prompt_texto=prompt_final_fusion,
        max_tokens_salida=config.MAX_TOKENS_ESQUEMA_FUSIONADO,
        temperatura=config.LLM_TEMPERATURE_FUSION,
        descripcion_tarea="Fusión de Esquemas"
    )
    return esquema_fusionado