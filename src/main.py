# src/main.py
import time
import os
import logging # <--- Importar logging
from src import config
from src import utils
from src import llm_processing
# from src import prompts # prompts es usado por llm_processing

# --- Configuración del Logging ---
# Definir esto a nivel de módulo para que esté disponible inmediatamente.
# Ajustar el formato y el nivel según sea necesario.
LOG_LEVEL = logging.INFO # Cambiar a logging.DEBUG para más detalle
# LOG_LEVEL = logging.DEBUG # Descomentar para ver logs de DEBUG

log_format = "%(asctime)s [%(levelname)-8s] %(name)-25s %(funcName)-25s L%(lineno)-4d: %(message)s"
logging.basicConfig(
    level=LOG_LEVEL,
    format=log_format,
    handlers=[
        logging.StreamHandler() # Salida a consola
        # Descomentar para añadir logging a un archivo:
        # logging.FileHandler(os.path.join(config.BASE_PROJECT_DIR, "output", "schema_generator.log"), mode='a', encoding='utf-8')
    ]
)
# Crear un logger específico para este módulo
module_logger = logging.getLogger(__name__) # Se resolverá a '__main__' cuando se ejecute directamente

def main():
    script_start_time = time.time()
    module_logger.info("--- INICIO DEL PROCESO DE GENERACIÓN DE ESQUEMA ---")

    with utils.timed_phase("Inicialización y Carga de Modelo"):
        utils.crear_directorios_necesarios()
        llm = llm_processing.cargar_modelo_llm()
        if llm is None:
            module_logger.critical("No se pudo cargar el modelo LLM. Saliendo.")
            return

    texto_completo_transcripcion = ""
    with utils.timed_phase("Preparación de Datos (Lectura de Transcripción)"):
        texto_completo_transcripcion = utils.leer_archivo(config.INPUT_FILE_PATH)
        if not texto_completo_transcripcion:
            module_logger.critical("No se pudo leer el archivo de transcripción. Saliendo.")
            return
        
        num_palabras_total = len(texto_completo_transcripcion.split())
        factor_conversion = config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else 1.5
        estimacion_tokens_transcripcion_total = int(num_palabras_total / factor_conversion)
        module_logger.info(f"Transcripción leída: {num_palabras_total} palabras (~{estimacion_tokens_transcripcion_total} tokens estimados).")

    esquema_final_texto = None
    # --- MODIFICACIÓN AQUÍ: Eliminada la carga de esquema existente ---
    with utils.timed_phase("Generación de Esquema Jerárquico"):
        module_logger.info("Procediendo a generar nuevo esquema.") # Mensaje directo
            
        tokens_prompt_base_esquema_aprox = 200 
        max_tokens_para_texto_en_mega_chunk = int(
            (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - tokens_prompt_base_esquema_aprox - config.MAX_TOKENS_ESQUEMA_PARCIAL
        )

        if max_tokens_para_texto_en_mega_chunk <=0:
            module_logger.critical(f"max_tokens_para_texto_en_mega_chunk ({max_tokens_para_texto_en_mega_chunk}) no es positivo. "
                                   "Verifica CONTEXT_SIZE, MEGA_CHUNK_CONTEXT_FACTOR, y estimaciones. No se puede proceder.")
            return

        if estimacion_tokens_transcripcion_total <= max_tokens_para_texto_en_mega_chunk:
            module_logger.info(f"La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) "
                               f"cabe en un solo pase para el esquema (max_tokens_texto_permitido: {max_tokens_para_texto_en_mega_chunk}).")
            esquema_final_texto = llm_processing.generar_esquema_de_texto(texto_completo_transcripcion, es_parcial=False)
        else:
            module_logger.info(f"La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) excede el límite por chunk "
                               f"({max_tokens_para_texto_en_mega_chunk} tokens). Se procederá con mega-chunking.")
            
            mega_chunks = utils.dividir_en_mega_chunks(
                texto_completo_transcripcion,
                max_tokens_para_texto_en_mega_chunk,
                config.MEGA_CHUNK_OVERLAP_WORDS
            )
            if not mega_chunks:
                module_logger.critical("No se pudieron generar mega-chunks. Verifique la transcripción y configuración.")
                return

            module_logger.info(f"Transcripción dividida en {len(mega_chunks)} mega-chunks para la generación de esquemas parciales.")
            esquemas_parciales = []
            for i, mega_chunk_texto in enumerate(mega_chunks):
                module_logger.info(f"  Procesando mega-chunk {i+1}/{len(mega_chunks)} ({len(mega_chunk_texto.split())} palabras)")
                esquema_parcial = llm_processing.generar_esquema_de_texto(
                    mega_chunk_texto, es_parcial=True, chunk_num=i + 1, total_chunks=len(mega_chunks)
                )
                if esquema_parcial:
                    esquemas_parciales.append(esquema_parcial)
                else:
                    module_logger.warning(f"El esquema parcial para el mega-chunk {i+1} fue vacío o nulo.")
            
            if not esquemas_parciales:
                module_logger.critical("No se pudieron generar esquemas parciales válidos. No se puede continuar.")
                return
            
            module_logger.info(f"Se generaron {len(esquemas_parciales)} esquemas parciales válidos. Procediendo a fusionarlos.")
            esquema_final_texto = llm_processing.fusionar_esquemas(esquemas_parciales)
        
        if esquema_final_texto:
            utils.guardar_texto_a_archivo(esquema_final_texto, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")
        else:
            module_logger.critical("Falló la generación del esquema final.") # Este log ya existía, se mantiene
            return # Asegurar que salimos si falla la generación

    if not esquema_final_texto or not esquema_final_texto.strip(): # Este chequeo sigue siendo útil por si la generación falla y devuelve None/vacío
        module_logger.critical("No hay esquema disponible (falló la generación). Saliendo.")
        return

    module_logger.info("--- PROCESO DE GENERACIÓN DE ESQUEMA TERMINADO ---")
    script_total_duration = time.time() - script_start_time
    module_logger.info(f"--- Duración Total del Script: {utils.format_duration(script_total_duration)} ---")

if __name__ == "__main__":
    main()