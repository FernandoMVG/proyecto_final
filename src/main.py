# src/main.py
import time
import os
import re
from src import config 
from src import utils
from src import llm_processing
from src import prompts
from src import vector_db_client

def format_duration(seconds):
    """Formatea la duración en segundos a un string de minutos y segundos."""
    if seconds < 0:
        return "N/A (tiempo negativo)"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    if minutes == 0:
        return f"{remaining_seconds:.2f} seg"
    return f"{minutes} min {remaining_seconds:.2f} seg"

def main():
    script_start_time = time.time()
    # --- Fase de Inicialización ---
    print("--- Fase de Inicialización ---")
    fase_start_time = time.time()
    utils.crear_directorios_necesarios()
    llm = llm_processing.cargar_modelo_llm()
    if llm is None:
        print("ERROR CRÍTICO: No se pudo cargar el modelo LLM. Saliendo.")
        return
    print(f"--- Fin Fase de Inicialización (Duración: {format_duration(time.time() - fase_start_time)}) ---")

    # --- Fase de Preparación de Datos ---
    print("\n--- Fase de Preparación de Datos ---")
    fase_start_time = time.time()
    texto_completo_transcripcion = utils.leer_archivo(config.INPUT_FILE_PATH)
    if not texto_completo_transcripcion:
        print("ERROR CRÍTICO: No se pudo leer el archivo de transcripción. Saliendo.")
        return
    
    num_palabras_total = len(texto_completo_transcripcion.split())
    estimacion_tokens_transcripcion_total = int(num_palabras_total * config.FACTOR_PALABRAS_A_TOKENS_APROX)
    print(f"Transcripción leída: {num_palabras_total} palabras (~{estimacion_tokens_transcripcion_total} tokens estimados).")
    print(f"--- Fin Fase de Preparación de Datos (Duración: {format_duration(time.time() - fase_start_time)}) ---")

    # --- NUEVO: Fase de Población de la Base de Datos Vectorial ---
    # Esto debería hacerse idealmente solo una vez por transcripción,
    # o si la transcripción cambia. Para el prototipo, lo hacemos cada vez.
    print("\n--- Fase de Población de BD Vectorial ---")
    fase_start_time = time.time()
    chunks_para_bd = utils.dividir_texto_para_bd_vectorial(
        texto_completo_transcripcion,
        config.VECTOR_DB_POPULATE_CHUNK_SIZE_WORDS,
        config.VECTOR_DB_POPULATE_CHUNK_OVERLAP_WORDS
    )
    if chunks_para_bd:
        print(f"Dividida la transcripción en {len(chunks_para_bd)} chunks para la BD vectorial.")
        exito_poblacion = vector_db_client.poblar_bd_vectorial_con_transcripcion(chunks_para_bd)
        if not exito_poblacion:
            print("ADVERTENCIA: Falló la población de la BD vectorial. La generación de apuntes podría no tener contexto de la transcripción.")
            # Decidir si continuar o no. Por ahora, continuamos.
    else:
        print("ADVERTENCIA: No se generaron chunks para poblar la BD vectorial.")
    print(f"--- Fin Fase de Población de BD Vectorial (Duración: {format_duration(time.time() - fase_start_time)}) ---")


    # --- Cargar o Generar Esquema ---
    # (Mantendremos la lógica para poder generar el esquema si no existe, o cargar uno)
    fase_start_time = time.time()
    esquema_final_texto = None
    if os.path.exists(config.OUTPUT_ESQUEMA_PATH): # Intentar cargar primero si existe
        print(f"\nINFO: Intentando cargar esquema existente desde: {config.OUTPUT_ESQUEMA_PATH}")
        esquema_final_texto = utils.leer_archivo(config.OUTPUT_ESQUEMA_PATH)
        if esquema_final_texto:
            print("INFO: Esquema existente cargado exitosamente.")
        else:
            print(f"ADVERTENCIA: No se pudo cargar el esquema desde {config.OUTPUT_ESQUEMA_PATH}, se intentará generar uno nuevo.")

    if not esquema_final_texto: # Si no se cargó o no existía, generar
        print("\n--- Fase de Generación de Esquema ---")
        prompt_base_sin_texto_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
        prompt_base_esquema_len_tokens = len(prompt_base_sin_texto_esquema.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
        max_tokens_contenido_chunk_esquema = int((config.CONTEXT_SIZE - prompt_base_esquema_len_tokens) * config.MEGA_CHUNK_CONTEXT_FACTOR)

        if estimacion_tokens_transcripcion_total <= max_tokens_contenido_chunk_esquema:
            print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) parece caber en un solo pase para el esquema.")
            esquema_final_texto = llm_processing.generar_esquema_de_texto(texto_completo_transcripcion, es_parcial=False)
        else:
            print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) excede el límite por chunk para el esquema. Se procederá con mega-chunking.")
            mega_chunks = utils.dividir_en_mega_chunks(
                texto_completo_transcripcion, 
                max_tokens_contenido_chunk_esquema, 
                config.MEGA_CHUNK_OVERLAP_WORDS
            )
            print(f"Transcripción dividida en {len(mega_chunks)} mega-chunks para la generación de esquemas parciales.")
            esquemas_parciales = []
            for i, mega_chunk in enumerate(mega_chunks):
                esquema_parcial = llm_processing.generar_esquema_de_texto(
                    mega_chunk, es_parcial=True, chunk_num=i + 1, total_chunks=len(mega_chunks)
                )
                if esquema_parcial: esquemas_parciales.append(esquema_parcial)
            
            if not esquemas_parciales:
                print("ERROR CRÍTICO: No se pudieron generar esquemas parciales válidos. No se puede continuar.")
                return
            esquema_final_texto = llm_processing.fusionar_esquemas(esquemas_parciales)
        
        utils.guardar_texto_a_archivo(esquema_final_texto, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")
        print(f"--- Fin Fase de Carga o Generación de Esquema (Duración Total de Fase: {format_duration(time.time() - fase_start_time)}) ---")


    if not esquema_final_texto:
        print("ERROR CRÍTICO: No hay esquema disponible (ni cargado ni generado). No se pueden generar apuntes. Saliendo.")
        return

    # --- Fase de Generación de Apuntes Detallados (Por Sección del Esquema y con RAG) ---
    print("\n--- Fase de Generación de Apuntes Detallados (Con RAG por Sección) ---")
    fase_start_time = time.time()
    secciones_del_esquema = re.split(r"\n(?=\d+\.\s)", esquema_final_texto)
    secciones_del_esquema = [s.strip() for s in secciones_del_esquema if s.strip()]
    apuntes_completos_concatenados = f"# Guía de Estudio Detallada: Optimización\n\n"

    if not secciones_del_esquema:
        print("ADVERTENCIA: No se pudieron identificar secciones principales en el esquema. Se intentará generar apuntes para el esquema completo como una sola sección (puede ser menos efectivo).")
        apuntes_para_esta_seccion = llm_processing.generar_apuntes_por_seccion_con_rag(
            esquema_final_texto, 
            num_seccion=1 
        )
        if apuntes_para_esta_seccion:
            apuntes_completos_concatenados += f"## Resumen General de la Clase\n{apuntes_para_esta_seccion}\n\n"
    else:
        print(f"Esquema dividido en {len(secciones_del_esquema)} secciones principales para procesar.")
        for i, seccion_esq in enumerate(secciones_del_esquema):
            # --- AÑADE ESTOS PRINTS DE DEPURACIÓN AQUÍ ---
            print(f"\nDEBUG MAIN: Procesando para Apuntes - Sección del Esquema {i+1}/{len(secciones_del_esquema)}")
            print(f"DEBUG MAIN: Contenido de la 'seccion_esq' que se pasará a generar_apuntes_por_seccion_con_rag:\n'''\n{seccion_esq}\n'''")
            # --- FIN DE PRINTS DE DEPURACIÓN ---

            apuntes_para_esta_seccion = llm_processing.generar_apuntes_por_seccion_con_rag(
                seccion_esq, 
                num_seccion=i+1
            )
            if apuntes_para_esta_seccion:
                match_titulo_seccion = re.match(r"(\d+\..*?)(?:\n|$)", seccion_esq)
                if match_titulo_seccion:
                    apuntes_completos_concatenados += f"## {match_titulo_seccion.group(1)}\n{apuntes_para_esta_seccion}\n\n"
                else: 
                    # Si no coincide el patrón de título numerado (ej. si es el esquema completo como una sola sección)
                    # o si una sección del esquema no empieza con "X. YYY"
                    # Podríamos usar un encabezado más genérico o intentar extraer el primer título de otra forma.
                    # Por ahora, si no hay título numerado, usamos un encabezado genérico para la sección.
                    primer_linea_seccion = seccion_esq.split('\n')[0].strip()
                    apuntes_completos_concatenados += f"## {primer_linea_seccion if primer_linea_seccion else f'Sección Detallada {i+1}'}\n{apuntes_para_esta_seccion}\n\n"
            else:
                print(f"ADVERTENCIA: No se generaron apuntes para la sección del esquema: {seccion_esq.splitlines()[0] if seccion_esq else 'Sección vacía del esquema'}")

    utils.guardar_texto_a_archivo(apuntes_completos_concatenados.strip(), config.OUTPUT_APUNTES_PATH, "apuntes detallados de la clase")
    print(f"--- Fin Fase de Generación de Apuntes Detallados (Duración Total de Fase: {utils.format_duration(time.time() - fase_start_time)}) ---") # Usando tu función format_duration
    
    print("\n--- Proceso Completo Terminado ---")
    print(f"--- Duración Total del Script: {utils.format_duration(time.time() - script_start_time)} ---") # Usando tu función format_duration

if __name__ == "__main__":
    main()