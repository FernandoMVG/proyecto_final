# src/main.py
import time
import os
import logging # <--- Importar logging
from src import config
from src import utils
from src import llm_processing
from src import prompts # prompts es usado por llm_processing

# --- Configuración del Logging ---
LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.DEBUG # Descomentar para más detalle

log_format = "%(asctime)s [%(levelname)-5s] %(name)-20s %(funcName)-25s L%(lineno)-4d: %(message)s"
logging.basicConfig(
    level=LOG_LEVEL,
    format=log_format,
    handlers=[
        logging.StreamHandler()
        # logging.FileHandler(os.path.join(config.BASE_PROJECT_DIR, "output", "schema_generator.log"), mode='a', encoding='utf-8')
    ]
)
module_logger = logging.getLogger(__name__)

def main():
    script_start_time = time.time()
    module_logger.info("--- INICIO DEL PROCESO DE GENERACIÓN DE ESQUEMA ---")

    with utils.timed_phase("Inicialización y Carga de Modelo"):
        utils.crear_directorios_necesarios()
        # La función cargar_modelo_llm ahora asigna a llm_processing.llm_instance
        llm_processing.cargar_modelo_llm() 
        if llm_processing.llm_instance is None:
            module_logger.critical("No se pudo cargar el modelo LLM o la instancia no está disponible. Saliendo.")
            return

    texto_completo_transcripcion = ""
    with utils.timed_phase("Preparación de Datos (Lectura de Transcripción)"):
        texto_completo_transcripcion = utils.leer_archivo(config.INPUT_FILE_PATH)
        if not texto_completo_transcripcion:
            module_logger.critical("No se pudo leer el archivo de transcripción. Saliendo.")
            return
        
        num_palabras_total_leidas = len(texto_completo_transcripcion.split())
        # Eliminado el log de tokens estimados por factor, ya que ahora usamos conteo real.
        module_logger.info(f"Transcripción leída: {num_palabras_total_leidas} palabras.")


    num_tokens_prompt_base = 0
    num_tokens_contenido_transcripcion = 0

    with utils.timed_phase("Análisis de Tokens para Decisión de Procesamiento"):
        prompt_template_base_texto = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
        try:
            tokens_prompt_base = llm_processing.llm_instance.tokenize(prompt_template_base_texto.encode('utf-8', 'ignore'))
            num_tokens_prompt_base = len(tokens_prompt_base)
            module_logger.info(f"Tokens reales del prompt base (sin contenido): {num_tokens_prompt_base}")
        except Exception as e:
            module_logger.critical(f"Error CRÍTICO al tokenizar el prompt base: {e}. No se puede continuar.", exc_info=True)
            return # Terminar si no podemos obtener este conteo esencial

        try:
            tokens_contenido_transcripcion = llm_processing.llm_instance.tokenize(texto_completo_transcripcion.encode('utf-8', 'ignore'))
            num_tokens_contenido_transcripcion = len(tokens_contenido_transcripcion)
            module_logger.info(f"Tokens reales del contenido de la transcripción: {num_tokens_contenido_transcripcion}")
        except Exception as e:
            module_logger.critical(f"Error CRÍTICO al tokenizar el contenido de la transcripción: {e}. No se puede continuar.", exc_info=True)
            return # Terminar si no podemos obtener este conteo esencial


    esquema_final_texto = None
    with utils.timed_phase("Generación de Esquema Jerárquico"):
        module_logger.info("Procediendo a generar nuevo esquema.")
            
        tokens_salida_pase_unico = config.MAX_TOKENS_ESQUEMA_FUSIONADO
        max_tokens_para_contenido_en_pase_unico = int(
            (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - num_tokens_prompt_base - tokens_salida_pase_unico
        )

        max_tokens_para_contenido_en_mega_chunk_individual = int(
             (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - num_tokens_prompt_base - config.MAX_TOKENS_ESQUEMA_PARCIAL
        )

        if max_tokens_para_contenido_en_pase_unico <=0 or max_tokens_para_contenido_en_mega_chunk_individual <= 0:
            module_logger.critical(f"Cálculo de tokens para contenido resultó no positivo. "
                                   f"Pase único: {max_tokens_para_contenido_en_pase_unico}, "
                                   f"Chunk individual: {max_tokens_para_contenido_en_mega_chunk_individual}. "
                                   "Verifica CONTEXT_SIZE, factores y max_tokens de salida.")
            return

        if num_tokens_contenido_transcripcion <= max_tokens_para_contenido_en_pase_unico:
            module_logger.info(f"La transcripción ({num_tokens_contenido_transcripcion} tokens reales de contenido) "
                               f"cabe en un solo pase para el esquema (max_tokens_texto_permitido: {max_tokens_para_contenido_en_pase_unico}).")
            esquema_final_texto = llm_processing.generar_esquema_de_texto(texto_completo_transcripcion, es_parcial=False)
        else:
            module_logger.info(f"La transcripción ({num_tokens_contenido_transcripcion} tokens reales de contenido) excede el límite para pase único "
                               f"({max_tokens_para_contenido_en_pase_unico} tokens). Se procederá con mega-chunking usando "
                               f"max_tokens_contenido_chunk: {max_tokens_para_contenido_en_mega_chunk_individual}.")
            
            if llm_processing.llm_instance is None:
                module_logger.critical("La instancia del LLM no está disponible para el chunking. Saliendo.")
                return

            mega_chunks = utils.dividir_en_mega_chunks(
                texto_completo_transcripcion,
                max_tokens_para_contenido_en_mega_chunk_individual,
                config.MEGA_CHUNK_OVERLAP_WORDS,
                llm_tokenizer_instance=llm_processing.llm_instance
            )
            if not mega_chunks:
                module_logger.critical("No se pudieron generar mega-chunks. Verifique la transcripción y configuración.")
                return

            module_logger.info(f"Transcripción dividida en {len(mega_chunks)} mega-chunks para la generación de esquemas parciales.")
            esquemas_parciales = []
            for i, mega_chunk_texto in enumerate(mega_chunks):
                palabras_chunk_actual = len(mega_chunk_texto.split())
                tokens_chunk_actual_reales = 0 # Inicializar
                try:
                    if llm_processing.llm_instance: # Asegurarse de que la instancia existe
                        tokens_chunk_actual_reales = len(llm_processing.llm_instance.tokenize(mega_chunk_texto.encode('utf-8','ignore')))
                except Exception as e_tok_chunk:
                    module_logger.warning(f"No se pudo tokenizar el mega-chunk {i+1} para logging: {e_tok_chunk}")
                    tokens_chunk_actual_reales = "N/A" # Indicar que no se pudo calcular

                module_logger.info(f"  Procesando mega-chunk {i+1}/{len(mega_chunks)} ({palabras_chunk_actual} palabras, ~{tokens_chunk_actual_reales} tokens).")
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
            module_logger.critical("Falló la generación del esquema final.")
            return

    if not esquema_final_texto or not esquema_final_texto.strip():
        module_logger.critical("No hay esquema disponible (falló la generación). Saliendo.")
        return

    module_logger.info("--- PROCESO DE GENERACIÓN DE ESQUEMA TERMINADO ---")
    script_total_duration = time.time() - script_start_time
    module_logger.info(f"--- Duración Total del Script: {utils.format_duration(script_total_duration)} ---")

if __name__ == "__main__":
    main()