# src/utils.py
import os
# Importa INPUT_FILE_PATH desde config para la creación del ejemplo
from src import config # Usamos import relativo porque estamos en el mismo paquete (src)

def leer_archivo(ruta_archivo):
    """Lee el contenido de un archivo de texto."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Archivo no encontrado en {ruta_archivo}")
        if ruta_archivo == config.INPUT_FILE_PATH: # Solo crea ejemplo para el archivo de entrada principal
            print(f"Creando un archivo de ejemplo '{config.INPUT_FILE_NAME}' en la carpeta 'data'. Por favor, edítalo.")
            ejemplo_txt = """Este es un texto de ejemplo para la transcripción de la clase de Optimización.
La Programación Lineal es una técnica matemática utilizada para encontrar la mejor solución posible (óptima) 
en un modelo matemático cuyos requisitos están representados por relaciones lineales. 
Se utiliza ampliamente en investigación de operaciones.

Un problema típico de PL consiste en maximizar o minimizar una función objetivo lineal, sujeta a un conjunto 
de restricciones también lineales. Por ejemplo, maximizar beneficios o minimizar costos.

Los componentes clave son: variables de decisión, función objetivo y restricciones. 
Veremos el método Simplex más adelante, que es un algoritmo popular para resolver estos problemas.
También existen métodos gráficos para problemas pequeños con dos variables. Es importante entender la región factible.
"""
            with open(config.INPUT_FILE_PATH, 'w', encoding='utf-8') as f:
                 f.write(ejemplo_txt)
            return ejemplo_txt
        return None
    except Exception as e:
        print(f"ERROR al leer el archivo {ruta_archivo}: {e}")
        return None

def dividir_en_chunks(texto, tamano_chunk_palabras, superposicion_palabras):
    """Divide el texto en chunks por número de palabras con superposición."""
    palabras = texto.split()
    if not palabras:
        return []
    
    chunks = []
    indice_actual = 0
    while indice_actual < len(palabras):
        inicio_chunk = indice_actual
        fin_chunk = min(indice_actual + tamano_chunk_palabras, len(palabras))
        chunk_palabras = palabras[inicio_chunk:fin_chunk]
        chunks.append(" ".join(chunk_palabras))
        
        avance = max(1, tamano_chunk_palabras - superposicion_palabras) 
        indice_actual += avance
        
    return chunks

def guardar_resultados_map(resultados_map, ruta_archivo):
    """Guarda los resultados intermedios de la Fase Map en un archivo."""
    print(f"\nGuardando resultados intermedios del Map en: {ruta_archivo}")
    try:
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            for i, res in enumerate(resultados_map):
                f.write(f"--- CHUNK {i+1} ---\n")
                f.write(f"Conceptos: {res.get('conceptos', 'N/A')}\n")
                f.write(f"Resumen Breve: {res.get('resumen_breve', 'N/A')}\n")
                if res.get('error_parseo'):
                     f.write("ADVERTENCIA: Hubo un error al parsear la salida de este chunk.\n")
                f.write("\n")
    except Exception as e:
        print(f"ERROR al guardar los resultados del Map: {e}")

def guardar_guia_final(guia_markdown, ruta_archivo):
    """Guarda la guía final en formato Markdown."""
    if guia_markdown:
        print(f"\nGuardando la guía de estudio final en: {ruta_archivo}")
        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(guia_markdown)
            print("¡Guía de estudio generada exitosamente!")
        except Exception as e:
            print(f"ERROR al guardar la guía final: {e}")
    else:
        print("\nNo se pudo generar la guía de estudio final debido a errores previos.")

def crear_directorios_necesarios():
    """Crea las carpetas de data y output si no existen."""
    os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "output"), exist_ok=True)
    os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "data"), exist_ok=True)