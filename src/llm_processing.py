# src/llm_processing.py
from llama_cpp import Llama
import os
import time
import logging # <--- Importar logging
from src import config
from src import prompts

logger = logging.getLogger(__name__)
llm_instance = None # Esta será la instancia global del modelo cargado

def cargar_modelo_llm():
    global llm_instance
    if llm_instance is not None:
        logger.info("Modelo LLM ya está cargado.")
        return llm_instance # Devuelve la instancia existente

    logger.info(f"Cargando modelo desde: {config.MODEL_PATH}")
    if not os.path.exists(config.MODEL_PATH):
        logger.critical(f"No se encontró el archivo del modelo en {config.MODEL_PATH}")
        return None
    try:
        start_time_carga = time.time()
        # Asignar a la variable global para que otros módulos puedan acceder a ella
        llm_instance = Llama(
            model_path=config.MODEL_PATH,
            n_ctx=config.CONTEXT_SIZE,
            n_threads=config.N_THREADS,
            n_gpu_layers=config.N_GPU_LAYERS,
            n_batch=config.N_BATCH_LLAMA,
            verbose=config.LLM_VERBOSE
        )
        end_time_carga = time.time()
        logger.info(f"Modelo LLM cargado exitosamente en {end_time_carga - start_time_carga:.2f} segundos.")
        return llm_instance # Devolver la instancia también
    except Exception as e:
        logger.critical(f"Al cargar el modelo LLM: {e}", exc_info=True)
        logger.info("Posibles causas: CONTEXT_SIZE, archivo corrupto, Llama.cpp sin soporte GPU.")
        llm_instance = None
        return None

def _llamar_al_llm(prompt_texto, max_tokens_salida, temperatura, descripcion_tarea, stop_sequences=None):
    if llm_instance is None:
        logger.critical(f"Modelo LLM no cargado. No se puede procesar '{descripcion_tarea}'.")
        return None, "llm_not_loaded", {}

    # Contar tokens del prompt real para logging y posible advertencia
    num_tokens_prompt_reales = 0
    try:
        # Asegurarse de que llm_instance esté disponible para tokenizar
        if llm_instance:
            num_tokens_prompt_reales = len(llm_instance.tokenize(prompt_texto.encode('utf-8', 'ignore')))
        else:
            logger.warning(f"llm_instance no disponible para tokenizar prompt para '{descripcion_tarea}' (conteo previo).")
    except Exception as e_tok:
        logger.warning(f"No se pudo tokenizar el prompt para '{descripcion_tarea}' para conteo previo: {e_tok}")

    logger.info(f"Enviando prompt al LLM para '{descripcion_tarea}' (~{num_tokens_prompt_reales} tokens), "
                f"max_tokens_out: {max_tokens_salida}, temp: {temperatura}.")

    # Advertencia si el prompt real + salida excede el contexto
    # Usamos un factor de seguridad un poco menor aquí (ej. 0.98) porque es una verificación final
    # y num_tokens_prompt_reales es ahora más preciso.
    if num_tokens_prompt_reales > 0 and \
       (num_tokens_prompt_reales + max_tokens_salida) > config.CONTEXT_SIZE * 0.98:
        logger.warning(f"El prompt actual ({num_tokens_prompt_reales} tokens) + salida ({max_tokens_salida}) "
                       f"podría exceder CONTEXT_SIZE ({config.CONTEXT_SIZE}). Total: {num_tokens_prompt_reales + max_tokens_salida}")
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Prompt para '{descripcion_tarea}':\n'''\n{prompt_texto[:500]}...\n'''")
    
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
        tokens_prompt_from_usage = 0 # Tokens del prompt según 'usage'

        if output and 'choices' in output and len(output['choices']) > 0:
            texto_generado = output['choices'][0]['text'].strip()
            finish_reason = output['choices'][0].get('finish_reason', 'desconocido')
            if finish_reason is None: finish_reason = "completed_unknown"
            
            usage_stats = output.get('usage', {})
            tokens_generados = usage_stats.get('completion_tokens', 0)
            if tokens_generados == 0 and texto_generado:
                try:
                    tokens_generados = len(llm_instance.tokenize(texto_generado.encode('utf-8', 'ignore')))
                except Exception as e:
                     logger.debug(f"No se pudo tokenizar el texto generado para fallback: {e}")

            tokens_prompt_from_usage = usage_stats.get('prompt_tokens', 0)
        
        else:
            logger.warning(f"La salida del LLM para '{descripcion_tarea}' fue inesperada o vacía. Output: {output}")
            # Usar el conteo pre-calculado si la salida es vacía
            return None, "empty_or_invalid_llm_output", {"tokens_prompt": num_tokens_prompt_reales}

        # Determinar el conteo final de tokens del prompt para stats
        # Priorizar 'usage', luego el pre-cálculo, luego un nuevo intento de tokenizar si todo es 0
        final_tokens_prompt_stat = tokens_prompt_from_usage
        if final_tokens_prompt_stat == 0:
            if num_tokens_prompt_reales > 0:
                final_tokens_prompt_stat = num_tokens_prompt_reales
            elif llm_instance: # Si ambos son 0, intentar tokenizar de nuevo como último recurso
                try:
                    final_tokens_prompt_stat = len(llm_instance.tokenize(prompt_texto.encode('utf-8', 'ignore')))
                except Exception:
                    pass # Mantener 0 si falla

        tokens_por_segundo = 0
        if processing_time > 0 and tokens_generados > 0:
            tokens_por_segundo = tokens_generados / processing_time
        
        stats = {
            "tokens_prompt": final_tokens_prompt_stat,
            "tokens_generados": tokens_generados,
            "processing_time_seconds": processing_time,
            "tokens_por_segundo": tokens_por_segundo
        }

        logger.info(f"LLM Task '{descripcion_tarea}' completada en {processing_time:.2f} seg.")
        logger.info(f"  Stats: Prompt Tokens: {stats['tokens_prompt']}, Tokens Generados: {tokens_generados}, Tasa: {tokens_por_segundo:.2f} tokens/seg.")
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
        # Devolver el conteo pre-calculado de tokens del prompt si está disponible
        return None, f"exception_during_llm_call: {str(e)}", {"tokens_prompt": num_tokens_prompt_reales}


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
    
    # Ya no se hacen estimaciones de tokens de prompt aquí basadas en factor.
    # _llamar_al_llm ahora maneja un conteo más preciso y las advertencias.

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
    
    # Ya no se hacen estimaciones de tokens de prompt aquí basadas en factor.

    esquema_fusionado, _, _ = _llamar_al_llm(
        prompt_texto=prompt_final_fusion,
        max_tokens_salida=config.MAX_TOKENS_ESQUEMA_FUSIONADO,
        temperatura=config.LLM_TEMPERATURE_FUSION,
        descripcion_tarea="Fusión de Esquemas"
    )
    return esquema_fusionado