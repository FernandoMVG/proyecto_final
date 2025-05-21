# src/utils.py
import os
import time
from contextlib import contextmanager
import logging # <--- Importar
from src import config

logger = logging.getLogger(__name__) # <--- Logger para este módulo

def format_duration(seconds):
    """Formatea la duración en segundos a un string de minutos y segundos."""
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
            logger.info(f"Creando un archivo de ejemplo '{config.INPUT_FILE_NAME}' en la carpeta 'data'. Por favor, edítalo.")
            ejemplo_txt = """Este es un texto de ejemplo para la transcripción de la clase de Optimización.
La Programación Lineal es una técnica matemática utilizada para encontrar la mejor solución posible (óptima) 
en un modelo matemático cuyos requisitos están representados por relaciones lineales. 
Se utiliza ampliamente en investigación de operaciones.
Un estudiante pregunta sobre la diferencia entre variables continuas y discretas. El profesor explica brevemente.
Luego, el profesor divaga un momento sobre el clima antes de retomar el tema del método Simplex.
El método Simplex es un algoritmo popular para resolver problemas de programación lineal.
Se discuten los conceptos de variables básicas y no básicas, y cómo se itera para encontrar la solución óptima.
Se presenta un ejemplo simple de un problema de maximización de beneficios con dos variables y tres restricciones.
El profesor enfatiza la importancia de entender las condiciones de optimalidad y factibilidad.
"""
            try:
                os.makedirs(os.path.dirname(config.INPUT_FILE_PATH), exist_ok=True)
                with open(config.INPUT_FILE_PATH, 'w', encoding='utf-8') as f:
                     f.write(ejemplo_txt)
                logger.info(f"Archivo de ejemplo '{config.INPUT_FILE_NAME}' creado.")
                return ejemplo_txt
            except Exception as e_create:
                logger.error(f"No se pudo crear el archivo de ejemplo: {e_create}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Al leer el archivo {ruta_archivo}: {e}", exc_info=True)
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


def _dividir_texto_en_chunks_por_palabras_base(texto_completo, tamano_chunk_palabras, superposicion_palabras, origen_llamada="chunking"):
    palabras = texto_completo.split()
    if not palabras:
        logger.warning(f"({origen_llamada}): El texto a dividir está vacío.")
        return []
    
    chunks_generados = []
    indice_actual = 0
    
    if tamano_chunk_palabras <= 0:
        logger.error(f"({origen_llamada}): tamano_chunk_palabras ({tamano_chunk_palabras}) debe ser positivo.")
        return []

    if superposicion_palabras < 0:
        logger.warning(f"({origen_llamada}): superposicion_palabras ({superposicion_palabras}) es negativa. Se usará 0.")
        superposicion_palabras = 0
        
    if tamano_chunk_palabras <= superposicion_palabras:
        logger.warning(f"({origen_llamada}): tamano_chunk_palabras ({tamano_chunk_palabras}) "
                       f"es <= superposicion_palabras ({superposicion_palabras}). Ajustando superposición.")
        if tamano_chunk_palabras > 1:
            superposicion_palabras = tamano_chunk_palabras - 1
        else:
            superposicion_palabras = 0
        logger.debug(f"    Nueva superposicion_palabras para ({origen_llamada}): {superposicion_palabras}")

    while indice_actual < len(palabras):
        inicio_chunk = indice_actual
        fin_chunk = min(indice_actual + tamano_chunk_palabras, len(palabras))
        chunk_palabras_actual = palabras[inicio_chunk:fin_chunk]
        chunks_generados.append(" ".join(chunk_palabras_actual))
        
        avance = max(1, tamano_chunk_palabras - superposicion_palabras)
        indice_actual += avance
    
    logger.debug(f"({origen_llamada}): Texto dividido en {len(chunks_generados)} chunks.")
    return chunks_generados

def dividir_en_mega_chunks(texto_completo, max_tokens_contenido_chunk_esquema, overlap_palabras):
    if config.FACTOR_PALABRAS_A_TOKENS_APROX <= 0:
        logger.error("(mega-chunks): FACTOR_PALABRAS_A_TOKENS_APROX debe ser positivo.")
        palabras_por_chunk_objetivo = 500 
    else:
        # Si FACTOR_PALABRAS_A_TOKENS_APROX es PALABRAS / TOKEN (ej. 1.7),
        # entonces PALABRAS = TOKENS * FACTOR_PALABRAS_A_TOKENS_APROX
        palabras_por_chunk_objetivo = int(max_tokens_contenido_chunk_esquema * config.FACTOR_PALABRAS_A_TOKENS_APROX)
        
    if palabras_por_chunk_objetivo <= 0:
        logger.error(f"(mega-chunks): Calculo de palabras_por_chunk_objetivo ({palabras_por_chunk_objetivo}) "
                     f"basado en max_tokens_contenido_chunk_esquema ({max_tokens_contenido_chunk_esquema}) es inválido. "
                     f"Usando fallback de 100 palabras.")
        palabras_por_chunk_objetivo = 100

    if palabras_por_chunk_objetivo <= overlap_palabras:
        original_calculado = palabras_por_chunk_objetivo
        # Asegurar que sea al menos 1 más que el overlap para que haya nuevo contenido
        palabras_por_chunk_objetivo = overlap_palabras + min(100, max(1, int(overlap_palabras * 0.2) + 1))
        logger.warning(f"(mega-chunks): palabras_por_chunk_objetivo ({original_calculado}) "
                       f"es <= overlap_palabras ({overlap_palabras}). Ajustando a {palabras_por_chunk_objetivo}")
    
    logger.info(f"(mega-chunks): Creando mega-chunks de aprox. {palabras_por_chunk_objetivo} palabras cada uno.")
    return _dividir_texto_en_chunks_por_palabras_base(
        texto_completo,
        palabras_por_chunk_objetivo,
        overlap_palabras,
        origen_llamada="mega-chunks"
    )