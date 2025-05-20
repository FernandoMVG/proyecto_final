# src/llm_processing.py
from llama_cpp import Llama
import os
import time
from src import config  # Usar import relativo
from src import prompts
from src import vector_db_client # Necesario para generar_apuntes_por_seccion_con_rag

llm_instance = None

# ... (cargar_modelo_llm se mantiene igual) ...
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
        return None, "llm_not_loaded", {} # Devolver un dict vacío para stats

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
        
        end_time_llm = time.time() # Mover aquí para medir solo la inferencia
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
            
            # Obtener estadísticas de tokens del objeto 'usage'
            # La estructura exacta puede variar ligeramente con versiones de llama-cpp-python
            # pero 'completion_tokens' (o 'generated_tokens') y 'prompt_tokens' son comunes.
            usage_stats = output.get('usage', {})
            tokens_generados = usage_stats.get('completion_tokens', 0) # Tokens en la respuesta
            if tokens_generados == 0 and texto_generado: # Fallback si 'completion_tokens' no está o es 0
                tokens_generados = len(llm_instance.tokenize(texto_generado.encode('utf-8')))

            tokens_prompt = usage_stats.get('prompt_tokens', 0) # Tokens en el prompt de entrada
            if tokens_prompt == 0: # Fallback si 'prompt_tokens' no está o es 0
                 tokens_prompt = len(llm_instance.tokenize(prompt_texto.encode('utf-8')))

        else:
            print(f"    ADVERTENCIA: La salida del LLM para '{descripcion_tarea}' fue inesperada o vacía. Output: {output}")
            return None, "empty_or_invalid_llm_output", {"tokens_prompt": tokens_prompt}

        # Calcular tokens por segundo
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
            print(f"    Últimos 150 caracteres generados: '...{texto_generado[-150:]}'")
        elif finish_reason not in ['stop', 'eos_token', 'completed_unknown'] and (stop_sequences is None or finish_reason not in stop_sequences):
             print(f"    ADVERTENCIA: Razón de finalización inusual para '{descripcion_tarea}': {finish_reason}")
        
        return texto_generado, finish_reason, stats

    except Exception as e:
        print(f"ERROR CRÍTICO durante la llamada al LLM para '{descripcion_tarea}': {e}")
        return None, f"exception_during_llm_call: {str(e)}", {}


# --- Modificar las funciones que llaman a _llamar_al_llm ---
# Ahora _llamar_al_llm devuelve tres valores: texto, razón, estadísticas

def generar_esquema_de_texto(texto_para_esquema, es_parcial=False, chunk_num=None, total_chunks=None):
    # ... (lógica de descripción y prompt igual) ...
    if es_parcial:
        num_str = str(chunk_num) if chunk_num is not None else "?"
        total_str = str(total_chunks) if total_chunks is not None else "?"
        descripcion_proceso_base = f"Esquema Parcial (Mega-Chunk {num_str}/{total_str})"
    else:
        descripcion_proceso_base = "Esquema Completo (Pase Único)"
    
    print(f"\n--- Iniciando Generación de {descripcion_proceso_base} ---")
    
    prompt_final_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.format(texto_completo=texto_para_esquema)
    max_tokens_para_este_esquema = config.MAX_TOKENS_ESQUEMA_PARCIAL if es_parcial else config.MAX_TOKENS_ESQUEMA_FUSIONADO
    
    prompt_template_sin_texto = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
    tokens_prompt_template_aprox = len(prompt_template_sin_texto.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    tokens_texto_contenido_aprox = len(texto_para_esquema.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    tokens_totales_prompt_aprox = tokens_prompt_template_aprox + tokens_texto_contenido_aprox

    if tokens_totales_prompt_aprox + max_tokens_para_este_esquema > config.CONTEXT_SIZE:
        print(f"    ADVERTENCIA: El prompt ({tokens_totales_prompt_aprox:.0f} tokens) + salida ({max_tokens_para_este_esquema}) "
              f"EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). La calidad podría verse afectada o fallar.")
    elif tokens_totales_prompt_aprox > config.CONTEXT_SIZE * 0.9:
         print(f"    AVISO: El prompt ({tokens_totales_prompt_aprox:.0f} tokens) ocupa una gran parte del CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    esquema_generado, _, stats = _llamar_al_llm( # Ignoramos finish_reason aquí si no la usamos directamente
        prompt_texto=prompt_final_esquema,
        max_tokens_salida=max_tokens_para_este_esquema,
        temperatura=config.LLM_TEMPERATURE_ESQUEMA,
        descripcion_tarea=descripcion_proceso_base
    )
    # El logging de stats ya se hace dentro de _llamar_al_llm
    return esquema_generado

def fusionar_esquemas(lista_esquemas_parciales):
    # ... (lógica de preparación igual) ...
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
    
    tokens_prompt_fusion_aprox = len(prompt_final_fusion.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    if tokens_prompt_fusion_aprox + config.MAX_TOKENS_ESQUEMA_FUSIONADO > config.CONTEXT_SIZE:
        print(f"    ADVERTENCIA: El prompt de fusión ({tokens_prompt_fusion_aprox:.0f} tokens) + salida ({config.MAX_TOKENS_ESQUEMA_FUSIONADO}) "
              f"EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). La fusión podría fallar o ser incompleta.")
    elif tokens_prompt_fusion_aprox > config.CONTEXT_SIZE * 0.85:
        print(f"    AVISO: El prompt de esquemas parciales para fusionar ({tokens_prompt_fusion_aprox:.0f} tokens est.) "
              f"es muy largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    esquema_fusionado, _, stats = _llamar_al_llm(
        prompt_texto=prompt_final_fusion,
        max_tokens_salida=config.MAX_TOKENS_ESQUEMA_FUSIONADO,
        temperatura=config.LLM_TEMPERATURE_FUSION,
        descripcion_tarea="Fusión de Esquemas"
    )
    return esquema_fusionado
    
def generar_apuntes_por_seccion_con_rag(seccion_esquema, num_seccion=None):
    # ... (lógica de preparación igual) ...
    if not seccion_esquema or not seccion_esquema.strip():
        print(f"ERROR: La sección del esquema (para sección {num_seccion or 'desconocida'}) está vacía o solo espacios.")
        return "" 

    consulta_para_bd = seccion_esquema.strip()
    nombre_seccion_log = f"Sección {num_seccion}" if num_seccion else "Sección sin numerar"
    consulta_log = f"'{consulta_para_bd[:60].replace('\n', ' ')}...'"
    
    print(f"\n--- Iniciando Generación de Apuntes para: {nombre_seccion_log} (Consulta BD: {consulta_log}) ---")

    print("    Obteniendo contexto relevante de la BD vectorial...")
    chunks_contexto_relevante = vector_db_client.obtener_contexto_relevante_de_api(consulta_para_bd)
    
    contexto_para_prompt = "No se encontró contexto adicional en la transcripción para esta sección específica."
    if chunks_contexto_relevante:
        contexto_para_prompt = "\n\n---\n\n".join(chunks_contexto_relevante)
        print(f"    Contexto obtenido para {nombre_seccion_log}: {len(chunks_contexto_relevante)} chunks, "
              f"~{len(contexto_para_prompt.split())} palabras.")
    else:
        print(f"    ADVERTENCIA: No se encontraron chunks de contexto relevantes para {nombre_seccion_log} "
              f"con consulta {consulta_log}. Los apuntes podrían ser menos detallados.")

    prompt_final_apuntes = prompts.PROMPT_GENERAR_APUNTES_TEMPLATE.format(
        seccion_del_esquema_actual=seccion_esquema,
        contexto_relevante_de_transcripcion=contexto_para_prompt
    )

    tokens_prompt_apuntes_aprox = len(prompt_final_apuntes.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    if tokens_prompt_apuntes_aprox + config.MAX_TOKENS_APUNTES_POR_SECCION > config.CONTEXT_SIZE:
         print(f"    ADVERTENCIA MUY SERIA: El prompt para {nombre_seccion_log} ({tokens_prompt_apuntes_aprox:.0f} tokens est.) "
              f" + salida ({config.MAX_TOKENS_APUNTES_POR_SECCION}) EXCEDEN CONTEXT_SIZE ({config.CONTEXT_SIZE}). "
              "Los apuntes podrían ser incompletos, de baja calidad o fallar.")
    elif tokens_prompt_apuntes_aprox > config.CONTEXT_SIZE * 0.85:
        print(f"    AVISO: El prompt para {nombre_seccion_log} ({tokens_prompt_apuntes_aprox:.0f} tokens est.) "
              f"es muy largo para el CONTEXT_SIZE ({config.CONTEXT_SIZE}).")

    descripcion_tarea_apuntes = f"Apuntes para {nombre_seccion_log}"
    apuntes_seccion, _, stats = _llamar_al_llm(
        prompt_texto=prompt_final_apuntes,
        max_tokens_salida=config.MAX_TOKENS_APUNTES_POR_SECCION,
        temperatura=config.LLM_TEMPERATURE_APUNTES,
        descripcion_tarea=descripcion_tarea_apuntes
    )
    return apuntes_seccion if apuntes_seccion else ""