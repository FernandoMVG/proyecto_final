# src/utils.py
import os
import time
from contextlib import contextmanager
import logging
from src import config

logger = logging.getLogger(__name__)

def format_duration(seconds):
    if seconds < 0: return "N/A (tiempo negativo)"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    if minutes == 0: return f"{remaining_seconds:.2f} seg"
    return f"{minutes} min {remaining_seconds:.2f} seg"

@contextmanager
def timed_phase(phase_name):
    logger.info(f"--- Iniciando Fase: {phase_name} ---")
    start_time = time.time()
    yield
    duration = time.time() - start_time
    logger.info(f"--- Fin Fase: {phase_name} (Duración: {format_duration(duration)}) ---")

def _leer_contenido_template(template_path):
    # Esta función necesita config para TEMPLATE_TRANSCRIPCION_PATH
    # Si config solo se usa para eso, podríamos pasar la ruta directamente
    # o mantener la importación de config.
    # Por ahora, asumimos que config.py se importa en los módulos que lo necesitan.
    try:
        with open(template_path, 'r', encoding='utf-8') as f_template:
            return f_template.read()
    except FileNotFoundError:
        logger.error(f"Archivo template no encontrado en: {template_path}")
        return None
    except Exception as e_template:
        logger.error(f"Error al leer el archivo template '{template_path}': {e_template}", exc_info=True)
        return None

def leer_archivo(ruta_archivo):
    logger.debug(f"Intentando leer archivo: {ruta_archivo}")
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Archivo '{ruta_archivo}' leído exitosamente ({len(content)} caracteres).")
            return content
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado en {ruta_archivo}")
        if ruta_archivo == config.INPUT_FILE_PATH:
            logger.info(f"Creando un archivo de ejemplo '{config.INPUT_FILE_NAME}' en la carpeta 'data' "
                        f"usando el template de '{config.TEMPLATE_TRANSCRIPCION_PATH}'. Por favor, edítalo si es necesario.")
            ejemplo_txt = _leer_contenido_template(config.TEMPLATE_TRANSCRIPCION_PATH)
            if ejemplo_txt is None:
                logger.error("No se pudo leer el contenido del template. No se creará el archivo de ejemplo.")
                return None
            try:
                os.makedirs(os.path.dirname(config.INPUT_FILE_PATH), exist_ok=True)
                with open(config.INPUT_FILE_PATH, 'w', encoding='utf-8') as f_output:
                     f_output.write(ejemplo_txt)
                logger.info(f"Archivo de ejemplo '{config.INPUT_FILE_NAME}' creado exitosamente en '{config.INPUT_FILE_PATH}'.")
                return ejemplo_txt
            except Exception as e_create:
                logger.error(f"No se pudo crear el archivo de ejemplo en '{config.INPUT_FILE_PATH}': {e_create}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error inesperado al leer el archivo '{ruta_archivo}': {e}", exc_info=True)
        return None

def guardar_texto_a_archivo(texto_generado, ruta_archivo, descripcion_archivo="archivo"):
    if texto_generado:
        logger.info(f"Guardando {descripcion_archivo} en: {ruta_archivo}")
        try:
            os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(texto_generado)
            logger.info(f"¡{descripcion_archivo.capitalize()} guardado exitosamente!")
        except Exception as e:
            logger.error(f"Al guardar {descripcion_archivo} en '{ruta_archivo}': {e}", exc_info=True)
    else:
        logger.warning(f"No se pudo guardar {descripcion_archivo} en '{ruta_archivo}' (contenido vacío o error previo).")

def crear_directorios_necesarios():
    logger.debug(f"Asegurando que los directorios base existan: output y data en {config.BASE_PROJECT_DIR}")
    try:
        os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "output"), exist_ok=True)
        os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "data"), exist_ok=True)
        logger.debug("Directorios 'output' y 'data' listos.")
    except Exception as e:
        logger.error(f"No se pudieron crear los directorios necesarios: {e}", exc_info=True)


def dividir_en_mega_chunks(texto_completo, max_tokens_contenido_chunk, overlap_tokens, llm_tokenizer_instance):
    """
    Divide el texto en mega-chunks, respetando un límite de tokens para el contenido de cada chunk.
    Intenta hacer los chunks lo más grandes posible (cercanos a max_tokens_contenido_chunk)
    y aplica el overlap en tokens.
    """
    if not llm_tokenizer_instance:
        logger.error("(mega-chunks): Se requiere una instancia de tokenizador LLM.")
        return []
    if max_tokens_contenido_chunk <= 0:
        logger.error(f"(mega-chunks): max_tokens_contenido_chunk ({max_tokens_contenido_chunk}) debe ser positivo.")
        return []
    if overlap_tokens < 0:
        logger.warning("(mega-chunks): overlap_tokens es negativo, se usará 0.")
        overlap_tokens = 0

    # Tokenizar todo el texto de una vez para trabajar con tokens directamente
    try:
        # Asegurarse de que el texto sea string antes de encodear
        if not isinstance(texto_completo, str):
            logger.error(f"(mega-chunks): El texto_completo no es una cadena (tipo: {type(texto_completo)}). No se puede tokenizar.")
            return []
        tokens_originales = llm_tokenizer_instance.tokenize(texto_completo.encode('utf-8', 'ignore'))
        if not tokens_originales:
            logger.warning("(mega-chunks): Texto a dividir resultó en cero tokens.")
            return []
    except Exception as e_tok_full:
        logger.error(f"(mega-chunks): Error al tokenizar el texto completo. Error: {e_tok_full}", exc_info=True)
        return []
    
    num_tokens_total = len(tokens_originales)
    logger.info(f"(mega-chunks): Texto original tokenizado: {num_tokens_total} tokens.")

    mega_chunks_finales = []
    indice_token_actual = 0
    iteracion_chunk_num = 0

    logger.info(f"(mega-chunks): Dividiendo texto. Objetivo por chunk: <= {max_tokens_contenido_chunk} tokens. "
                f"Overlap tokens: {overlap_tokens}.")

    while indice_token_actual < num_tokens_total:
        iteracion_chunk_num += 1
        logger.debug(f"[Chunk Iter {iteracion_chunk_num}] Iniciando en token índice: {indice_token_actual}")

        # Determinar el final del chunk actual
        # El chunk no puede exceder max_tokens_contenido_chunk
        # ni ir más allá del final del texto
        fin_chunk_candidato = min(indice_token_actual + max_tokens_contenido_chunk, num_tokens_total)
        
        tokens_candidatos = tokens_originales[indice_token_actual:fin_chunk_candidato]
        
        if not tokens_candidatos:
            logger.debug(f"[Chunk Iter {iteracion_chunk_num}] No quedan suficientes tokens para formar un chunk. Finalizando.")
            break

        try:
            texto_chunk_final_bytes = llm_tokenizer_instance.detokenize(tokens_candidatos)
            texto_chunk_final = texto_chunk_final_bytes.decode('utf-8', 'ignore')
        except Exception as e_detok:
            logger.error(f"(mega-chunks) Error al decodificar tokens del chunk {iteracion_chunk_num} (índices {indice_token_actual}-{fin_chunk_candidato-1}). Error: {e_detok}. Saltando este intento de chunk.", exc_info=True)
            indice_token_actual += 1 
            continue
            
        if texto_chunk_final.strip():
            mega_chunks_finales.append(texto_chunk_final)
            num_tokens_en_chunk_final = len(tokens_candidatos)
            logger.debug(f"  Mega-chunk Creado ({iteracion_chunk_num}): {num_tokens_en_chunk_final} tokens. "
                         f"Inició en token {indice_token_actual}. Texto: '{texto_chunk_final[:50].replace('\n', ' ')}...'")
            
            avance_tokens = max(1, num_tokens_en_chunk_final - overlap_tokens)
            
            if indice_token_actual + avance_tokens > num_tokens_total:
                avance_tokens = num_tokens_total - indice_token_actual
            
            indice_token_actual += avance_tokens
            logger.debug(f"  Nuevo índice_token_actual: {indice_token_actual} (avance: {avance_tokens} tokens)")

        elif indice_token_actual < num_tokens_total: 
            logger.warning(f"(mega-chunks): Chunk decodificado vacío o solo espacios en iteración {iteracion_chunk_num} "
                           f"(índice token: {indice_token_actual}). Avanzando 1 token para evitar bucle.")
            indice_token_actual += 1 
        else: 
            break

    if not mega_chunks_finales and texto_completo and texto_completo.strip():
        logger.warning("(mega-chunks): No se generó ningún mega-chunk, pero el texto original no estaba vacío. "
                       "Esto podría indicar que max_tokens_contenido_chunk es demasiado pequeño o hay problemas con la tokenización/decodificación.")

    logger.info(f"(mega-chunks): Texto dividido en {len(mega_chunks_finales)} mega-chunks.")
    return mega_chunks_finales


def contar_tokens_llama_cpp(texto, llm_instance):
    """
    Cuenta el número de tokens en un texto dado utilizando una instancia de LLM.
    Esta función es un envoltorio para la tokenización específica de LLM.
    """