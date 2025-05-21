# src/main.py
import time
import os
import re
from src import config
from src import utils # Contiene format_duration, timed_phase y funciones de chunking
from src import llm_processing
from src import prompts # Aunque no se usa directamente aquí, es parte del flujo
from src import vector_db_client

def main():
    script_start_time = time.time()
    print("--- INICIO DEL PROCESO DE GENERACIÓN DE ESQUEMA ---")

    with utils.timed_phase("Inicialización y Carga de Modelo"):
        utils.crear_directorios_necesarios()
        llm = llm_processing.cargar_modelo_llm()
        if llm is None:
            print("ERROR CRÍTICO: No se pudo cargar el modelo LLM. Saliendo.")
            return

    texto_completo_transcripcion = ""
    with utils.timed_phase("Preparación de Datos (Lectura de Transcripción)"):
        texto_completo_transcripcion = utils.leer_archivo(config.INPUT_FILE_PATH)
        if not texto_completo_transcripcion:
            print("ERROR CRÍTICO: No se pudo leer el archivo de transcripción. Saliendo.")
            return
        
        num_palabras_total = len(texto_completo_transcripcion.split())
        # Asegurarse de que FACTOR_PALABRAS_A_TOKENS_APROX no sea cero
        factor_conversion = config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else 1.5
        estimacion_tokens_transcripcion_total = int(num_palabras_total / factor_conversion)
        print(f"Transcripción leída: {num_palabras_total} palabras (~{estimacion_tokens_transcripcion_total} tokens estimados).")

    # --- Eliminada la Fase de Población de la Base de Datos Vectorial ---

    esquema_final_texto = None
    with utils.timed_phase("Carga o Generación de Esquema Jerárquico"):
        if os.path.exists(config.OUTPUT_ESQUEMA_PATH):
            print(f"INFO: Intentando cargar esquema existente desde: {config.OUTPUT_ESQUEMA_PATH}")
            esquema_final_texto = utils.leer_archivo(config.OUTPUT_ESQUEMA_PATH)
            if esquema_final_texto:
                print("INFO: Esquema existente cargado exitosamente.")
            else:
                print(f"ADVERTENCIA: No se pudo cargar el esquema desde {config.OUTPUT_ESQUEMA_PATH}. Se generará uno nuevo.")

        if not esquema_final_texto:
            print("INFO: No se encontró esquema previo o no se pudo cargar. Procediendo a generar nuevo esquema.")
            
            tokens_prompt_base_esquema_aprox = 200 # Estimación para PROMPT_GENERAR_ESQUEMA_TEMPLATE sin texto
            max_tokens_para_texto_en_mega_chunk = int(
                (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - tokens_prompt_base_esquema_aprox - config.MAX_TOKENS_ESQUEMA_PARCIAL
            )

            if max_tokens_para_texto_en_mega_chunk <=0:
                print(f"ERROR CRÍTICO: max_tokens_para_texto_en_mega_chunk ({max_tokens_para_texto_en_mega_chunk}) no es positivo. "
                      "Verifica CONTEXT_SIZE, MEGA_CHUNK_CONTEXT_FACTOR, y estimaciones de tokens. "
                      "No se puede proceder con el chunking.")
                return


            # Si la estimación de tokens de la transcripción total es menor o igual
            # a los tokens que puede tener el texto dentro de un mega-chunk (que ya considera el prompt y la salida)
            if estimacion_tokens_transcripcion_total <= max_tokens_para_texto_en_mega_chunk:
                print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) "
                      f"cabe en un solo pase para el esquema (max_tokens_texto_permitido: {max_tokens_para_texto_en_mega_chunk}).")
                esquema_final_texto = llm_processing.generar_esquema_de_texto(texto_completo_transcripcion, es_parcial=False)
            else:
                print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) excede el límite por chunk "
                      f"({max_tokens_para_texto_en_mega_chunk} tokens). Se procederá con mega-chunking.")
                
                mega_chunks = utils.dividir_en_mega_chunks(
                    texto_completo_transcripcion,
                    max_tokens_para_texto_en_mega_chunk, # Este es el límite de tokens para el *contenido* del chunk
                    config.MEGA_CHUNK_OVERLAP_WORDS
                )
                if not mega_chunks:
                    print("ERROR CRÍTICO: No se pudieron generar mega-chunks. Verifique la transcripción y configuración.")
                    return

                print(f"Transcripción dividida en {len(mega_chunks)} mega-chunks para la generación de esquemas parciales.")
                esquemas_parciales = []
                for i, mega_chunk_texto in enumerate(mega_chunks):
                    print(f"  Procesando mega-chunk {i+1}/{len(mega_chunks)} ({len(mega_chunk_texto.split())} palabras)")
                    esquema_parcial = llm_processing.generar_esquema_de_texto(
                        mega_chunk_texto, es_parcial=True, chunk_num=i + 1, total_chunks=len(mega_chunks)
                    )
                    if esquema_parcial:
                        esquemas_parciales.append(esquema_parcial)
                    else:
                        print(f"ADVERTENCIA: El esquema parcial para el mega-chunk {i+1} fue vacío o nulo.")
                
                if not esquemas_parciales:
                    print("ERROR CRÍTICO: No se pudieron generar esquemas parciales válidos. No se puede continuar.")
                    return
                
                print(f"Se generaron {len(esquemas_parciales)} esquemas parciales. Procediendo a fusionarlos.")
                esquema_final_texto = llm_processing.fusionar_esquemas(esquemas_parciales)
            
            if esquema_final_texto:
                utils.guardar_texto_a_archivo(esquema_final_texto, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")
            else:
                print("ERROR CRÍTICO: Falló la generación del esquema final.")
                return

    if not esquema_final_texto or not esquema_final_texto.strip():
        print("ERROR CRÍTICO: No hay esquema disponible (ni cargado ni generado válidamente). Saliendo.")
        return

    # --- Eliminada la Fase de Generación de Apuntes Detallados ---

    print("\n--- PROCESO DE GENERACIÓN DE ESQUEMA TERMINADO ---")
    script_total_duration = time.time() - script_start_time
    print(f"--- Duración Total del Script: {utils.format_duration(script_total_duration)} ---")

if __name__ == "__main__":
    main()