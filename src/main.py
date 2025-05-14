# src/main.py
import time
from src import config
from src import utils
from src import llm_processing

def main():
    """Función principal para orquestar el proceso de generación de esquema."""
    
    utils.crear_directorios_necesarios()

    llm = llm_processing.cargar_modelo_llm()
    if llm is None:
        print("Saliendo del programa debido a un error en la carga del modelo.")
        return

    print("\n--- Iniciando Proceso de Generación de Esquema ---")
    texto_completo = utils.leer_archivo(config.INPUT_FILE_PATH)
    if not texto_completo:
        return
    
    num_palabras = len(texto_completo.split())
    estimacion_tokens = int(num_palabras * 1.5) # Factor de estimación aproximado
    print(f"Transcripción leída: {len(texto_completo)} caracteres, ~{num_palabras} palabras, ~{estimacion_tokens} tokens estimados.")

    # Advertencia si la estimación de tokens es muy cercana o excede el contexto
    # Dejar un margen para el prompt y la salida generada
    margen_prompt_salida = 4096 # Estimación conservadora para el prompt y algo de salida
    if estimacion_tokens > (config.CONTEXT_SIZE - margen_prompt_salida):
        print(f"ADVERTENCIA: La transcripción estimada ({estimacion_tokens} tokens) más el margen para prompt/salida "
              f"podría ser demasiado larga para el CONTEXT_SIZE configurado ({config.CONTEXT_SIZE} tokens).")
        print("El resultado podría ser incompleto o podrían ocurrir errores de memoria.")
        # Considerar una estrategia de "mega-chunking" aquí si esto se vuelve un problema recurrente.

    esquema_clase = llm_processing.generar_esquema_desde_transcripcion(texto_completo)

    utils.guardar_texto_a_archivo(esquema_clase, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")

    print("\n--- Proceso de Generación de Esquema Terminado ---")

    # --- Paso Futuro: Generar Apuntes ---
    # if esquema_clase:
    #     print("\n--- Iniciando Generación de Apuntes Detallados (Paso Futuro) ---")
    #     apuntes_completos = llm_processing.generar_apuntes_desde_esquema(texto_completo, esquema_clase)
    #     utils.guardar_texto_a_archivo(apuntes_completos, config.OUTPUT_APUNTES_PATH, "apuntes de la clase")
    #     print("\n--- Proceso Completo Terminado ---")

if __name__ == "__main__":
    main()