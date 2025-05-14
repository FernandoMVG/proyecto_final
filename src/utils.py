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
        if ruta_archivo == config.INPUT_FILE_PATH:
            print(f"Creando un archivo de ejemplo '{config.INPUT_FILE_NAME}' en la carpeta 'data'. Por favor, edítalo.")
            ejemplo_txt = """Este es un texto de ejemplo para la transcripción de la clase de Optimización.
La Programación Lineal es una técnica matemática utilizada para encontrar la mejor solución posible (óptima) 
en un modelo matemático cuyos requisitos están representados por relaciones lineales. 
Se utiliza ampliamente en investigación de operaciones.
Un estudiante pregunta sobre la diferencia entre variables continuas y discretas. El profesor explica brevemente.
Luego, el profesor divaga un momento sobre el clima antes de retomar el tema del método Simplex.
""" # Ejemplo más corto para pruebas rápidas
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
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(texto_generado)
            print(f"¡{descripcion_archivo.capitalize()} generado y guardado exitosamente!")
        except Exception as e:
            print(f"ERROR al guardar {descripcion_archivo}: {e}")
    else:
        print(f"\nNo se pudo generar {descripcion_archivo} debido a errores previos o contenido vacío.")

def crear_directorios_necesarios():
    """Crea las carpetas de data y output si no existen."""
    os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "output"), exist_ok=True)
    os.makedirs(os.path.join(config.BASE_PROJECT_DIR, "data"), exist_ok=True)