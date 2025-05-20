# src/utils.py
import os
import time # Necesario para el gestor de contexto timed_phase (opcional)
from contextlib import contextmanager # Para timed_phase (opcional)
from src import config

def format_duration(seconds):
    """Formatea la duración en segundos a un string de minutos y segundos."""
    if seconds < 0:
        return "N/A (tiempo negativo)"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    if minutes == 0:
        return f"{remaining_seconds:.2f} seg"
    return f"{minutes} min {remaining_seconds:.2f} seg"

@contextmanager
def timed_phase(phase_name):
    """
    Gestor de contexto para medir e imprimir la duración de una fase del proceso.
    """
    print(f"\n--- Iniciando Fase: {phase_name} ---")
    start_time = time.time()
    yield
    duration = time.time() - start_time
    print(f"--- Fin Fase: {phase_name} (Duración: {format_duration(duration)}) ---")


def leer_archivo(ruta_archivo):
    """Lee el contenido de un archivo de texto."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Archivo no encontrado en {ruta_archivo}")
        if ruta_archivo == config.INPUT_FILE_PATH:
            print(f"Creando un archivo de ejemplo '{config.INPUT_FILE_NAME}' en la carpeta 'data'. Por favor, edítalo.")
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
            os.makedirs(os.path.dirname(config.INPUT_FILE_PATH), exist_ok=True) # Asegurar que 'data' exista
            with open(config.INPUT_FILE_PATH, 'w', encoding='utf-8') as f:
                 f.write(ejemplo_txt)
            return ejemplo_txt
        return None
    except Exception as e:
        print(f"ERROR al leer el archivo {ruta_archivo}: {e}")
        return None

def guardar_texto_a_archivo(texto_generado, ruta_archivo, descripcion_archivo="archivo"):
    """Guarda el texto generado en un archivo."""
    if texto_generado:
        print(f"\nGuardando {descripcion_archivo} en: {ruta_archivo}")
        try:
            os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True) # Asegurar que 'output' exista
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(texto_generado)
            print(f"¡{descripcion_archivo.capitalize()} guardado exitosamente!")
        except Exception as e:
            print(f"ERROR al guardar {descripcion_archivo}: {e}")
    else:
        print(f"\nNo se pudo guardar {descripcion_archivo} (contenido vacío o error previo).")

def crear_directorios_necesarios():
    """Crea las carpetas de data y output si no existen."""
    os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "output"), exist_ok=True)
    os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "data"), exist_ok=True)

def _dividir_texto_en_chunks_por_palabras_base(texto_completo, tamano_chunk_palabras, superposicion_palabras, origen_llamada="chunking"):
    """
    Función base para dividir texto en chunks de un número específico de palabras con solapamiento.
    """
    palabras = texto_completo.split()
    if not palabras:
        return []
    
    chunks_generados = []
    indice_actual = 0
    
    if tamano_chunk_palabras <= 0:
        print(f"ERROR ({origen_llamada}): tamano_chunk_palabras ({tamano_chunk_palabras}) debe ser positivo.")
        return []

    if superposicion_palabras < 0:
        print(f"ADVERTENCIA ({origen_llamada}): superposicion_palabras ({superposicion_palabras}) es negativa. Se usará 0.")
        superposicion_palabras = 0
        
    if tamano_chunk_palabras <= superposicion_palabras:
        print(f"ADVERTENCIA ({origen_llamada}): tamano_chunk_palabras ({tamano_chunk_palabras}) "
              f"es <= superposicion_palabras ({superposicion_palabras}). "
              f"Esto puede resultar en un avance de 0 o negativo. Ajustando superposición.")
        if tamano_chunk_palabras > 1:
            superposicion_palabras = tamano_chunk_palabras - 1
        else: # Si el tamaño del chunk es 1, no puede haber superposición útil.
            superposicion_palabras = 0
        print(f"    Nueva superposicion_palabras: {superposicion_palabras}")

    while indice_actual < len(palabras):
        inicio_chunk = indice_actual
        fin_chunk = min(indice_actual + tamano_chunk_palabras, len(palabras))
        chunk_palabras_actual = palabras[inicio_chunk:fin_chunk]
        chunks_generados.append(" ".join(chunk_palabras_actual))
        
        avance = max(1, tamano_chunk_palabras - superposicion_palabras)
        indice_actual += avance
            
    return chunks_generados

def dividir_en_mega_chunks(texto_completo, max_tokens_contenido_chunk_esquema, overlap_palabras):
    """
    Divide el texto en mega-chunks para la generación del esquema.
    Calcula el número de palabras objetivo basado en tokens.
    """
    if config.FACTOR_PALABRAS_A_TOKENS_APROX <= 0:
        print("ERROR (mega-chunks): FACTOR_PALABRAS_A_TOKENS_APROX debe ser positivo.")
        return []
        
    palabras_por_chunk_objetivo = int(max_tokens_contenido_chunk_esquema / config.FACTOR_PALABRAS_A_TOKENS_APROX)
    
    if palabras_por_chunk_objetivo <= 0:
        print(f"ERROR (mega-chunks): Calculo de palabras_por_chunk_objetivo ({palabras_por_chunk_objetivo}) "
              f"basado en max_tokens_contenido_chunk_esquema ({max_tokens_contenido_chunk_esquema}) es inválido. "
              f"Verifica los valores de configuración.")
        return []

    if palabras_por_chunk_objetivo <= overlap_palabras:
        original_calculado = palabras_por_chunk_objetivo
        # Asegura un tamaño mínimo razonable y que sea mayor que el overlap
        palabras_por_chunk_objetivo = overlap_palabras + min(100, max(1, overlap_palabras)) # Ajuste más dinámico
        print(f"ADVERTENCIA (mega-chunks): max_tokens_por_chunk_contenido resulta en {original_calculado} palabras/chunk, "
              f"que es <= overlap_palabras ({overlap_palabras}). Ajustando palabras_por_chunk_objetivo a {palabras_por_chunk_objetivo}")
    
    print(f"INFO (mega-chunks): Creando mega-chunks de aprox. {palabras_por_chunk_objetivo} palabras cada uno.")
    return _dividir_texto_en_chunks_por_palabras_base(
        texto_completo,
        palabras_por_chunk_objetivo,
        overlap_palabras,
        origen_llamada="mega-chunks"
    )

def dividir_texto_para_bd_vectorial(texto_completo, tamano_chunk_palabras, superposicion_palabras):
    """Divide el texto en chunks más pequeños para poblar la BD vectorial."""
    print(f"INFO (bd-vectorial): Creando chunks para BD vectorial de {tamano_chunk_palabras} palabras cada uno.")
    return _dividir_texto_en_chunks_por_palabras_base(
        texto_completo,
        tamano_chunk_palabras,
        superposicion_palabras,
        origen_llamada="bd-vectorial-chunks"
    )