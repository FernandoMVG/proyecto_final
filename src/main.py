# src/main.py
import time
from src import config 
from src import utils
from src import llm_processing
from src import prompts

def main():
    # --- Fase de Inicialización ---
    print("--- Fase de Inicialización ---")
    utils.crear_directorios_necesarios()
    llm = llm_processing.cargar_modelo_llm()
    if llm is None:
        print("ERROR CRÍTICO: No se pudo cargar el modelo LLM. Saliendo.")
        return
    print("--- Fin Fase de Inicialización ---")

    # --- Fase de Preparación de Datos ---
    print("\n--- Fase de Preparación de Datos ---")
    texto_completo = utils.leer_archivo(config.INPUT_FILE_PATH)
    if not texto_completo:
        print("ERROR CRÍTICO: No se pudo leer el archivo de transcripción. Saliendo.")
        return
    
    num_palabras_total = len(texto_completo.split())
    # Las siguientes líneas son para la estimación del esquema, podemos comentarlas si no generamos esquema
    prompt_base_sin_texto_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
    prompt_base_esquema_len_tokens = len(prompt_base_sin_texto_esquema.split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    max_tokens_contenido_chunk = int((config.CONTEXT_SIZE - prompt_base_esquema_len_tokens) * config.MEGA_CHUNK_CONTEXT_FACTOR)
    estimacion_tokens_transcripcion_total = int(num_palabras_total * config.FACTOR_PALABRAS_A_TOKENS_APROX)

    print(f"Transcripción leída: {num_palabras_total} palabras (~{estimacion_tokens_transcripcion_total} tokens estimados).")
    # print(f"Contexto máximo utilizable para contenido de cada mega-chunk (para esquema): ~{max_tokens_contenido_chunk} tokens.")
    print("--- Fin Fase de Preparación de Datos ---")

    esquema_final = None
    
    # --- INICIO: SECCIÓN A MODIFICAR PARA CARGAR ESQUEMA EXISTENTE ---
    # Comentamos toda la lógica de generación de esquema
    
    print("\n--- Fase de Generación de Esquema ---") # Comentado
    if estimacion_tokens_transcripcion_total <= max_tokens_contenido_chunk:
        print(f"\nINFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) parece caber en un solo pase para el esquema.")
        esquema_final = llm_processing.generar_esquema_de_texto(texto_completo, es_parcial=False)
    else:
        print(f"\nINFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) excede el límite por chunk para el esquema. Se procederá con mega-chunking.")
        mega_chunks = utils.dividir_en_mega_chunks(
            texto_completo, 
            max_tokens_contenido_chunk, 
            config.MEGA_CHUNK_OVERLAP_WORDS
        )
        print(f"Transcripción dividida en {len(mega_chunks)} mega-chunks para la generación de esquemas parciales.")
        esquemas_parciales = []
        for i, mega_chunk in enumerate(mega_chunks):
            esquema_parcial = llm_processing.generar_esquema_de_texto(
                mega_chunk, 
                es_parcial=True,
                chunk_num=i + 1,
                total_chunks=len(mega_chunks)
            )
            if esquema_parcial:
                esquemas_parciales.append(esquema_parcial)
            else:
                print(f"ADVERTENCIA ADICIONAL en main: No se generó esquema para el mega-chunk {i+1}.")
        
        if not esquemas_parciales:
            print("ERROR CRÍTICO: No se pudieron generar esquemas parciales válidos. No se puede continuar a la fusión ni a la generación de apuntes.")
            return
        esquema_final = llm_processing.fusionar_esquemas(esquemas_parciales)

    utils.guardar_texto_a_archivo(esquema_final, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")
    
    # # --- NUEVO: Cargar esquema existente ---
    # print(f"\nINFO: Intentando cargar esquema existente desde: {config.OUTPUT_ESQUEMA_PATH}")
    # esquema_final = utils.leer_archivo(config.OUTPUT_ESQUEMA_PATH) # Usamos la misma función de leer_archivo
    
    # if not esquema_final:
    #     print(f"ERROR CRÍTICO: No se pudo cargar el esquema desde {config.OUTPUT_ESQUEMA_PATH}. "
    #           "Asegúrate de que el archivo exista y la ruta en config.py sea correcta. No se pueden generar apuntes. Saliendo.")
    #     return
    # else:
    #     print("INFO: Esquema existente cargado exitosamente.")
    
    # # print("\n--- Fin Fase de Generación de Esquema ---") # Comentado o renombrar a "Carga de Esquema"
    # # --- FIN: SECCIÓN MODIFICADA ---
    
    # # --- Fase de Generación de Apuntes Detallados ---
    # # Esta parte permanece igual, pero ahora usará el esquema_final cargado
    # print("\n--- Fase de Generación de Apuntes Detallados ---")
    # apuntes_completos = llm_processing.generar_apuntes_desde_esquema(texto_completo, esquema_final)
    
    # utils.guardar_texto_a_archivo(apuntes_completos, config.OUTPUT_APUNTES_PATH, "apuntes detallados de la clase")
    # print("--- Fin Fase de Generación de Apuntes Detallados ---")
    
    print("\n--- Proceso Completo Terminado (Solo Generación de Apuntes) ---")

if __name__ == "__main__":
    main()