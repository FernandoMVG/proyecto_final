# src/main.py
import time
from src import config
from src import utils
from src import llm_processing
from src import prompts

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
    
    num_palabras_total = len(texto_completo.split())
    
    # Estimación de tokens para el prompt de generación de esquema (sin el texto de la transcripción)
    # Tomamos el prompt y reemplazamos el placeholder para tener una idea de su longitud base
    # Asumimos que FACTOR_PALABRAS_A_TOKENS_APROX está en config.py o definido
    # Si no, puedes añadirlo a config.py: FACTOR_PALABRAS_A_TOKENS_APROX = 1.7 (o el valor que uses)
    prompt_base_esquema_len_tokens = len(prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "").split()) * config.FACTOR_PALABRAS_A_TOKENS_APROX
    
    # Máximos tokens que podemos dedicar al contenido del texto de un mega-chunk
    max_tokens_contenido_chunk = int((config.CONTEXT_SIZE - prompt_base_esquema_len_tokens) * config.MEGA_CHUNK_CONTEXT_FACTOR)

    print(f"Transcripción leída: {num_palabras_total} palabras.")
    # El siguiente print se movió para que solo se imprima una vez la decisión
    # print(f"Contexto máximo para contenido de mega-chunk: {max_tokens_contenido_chunk} tokens (aprox).") 

    esquema_final = None # Inicializar
    
    # Convertir palabras a una estimación de tokens para la transcripción completa
    estimacion_tokens_transcripcion_total = int(num_palabras_total * config.FACTOR_PALABRAS_A_TOKENS_APROX)

    # --- Decisión de Estrategia (Imprimir una sola vez) ---
    if estimacion_tokens_transcripcion_total <= max_tokens_contenido_chunk:
        print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) parece caber en un solo pase. "
              f"(Límite de contenido del chunk: {max_tokens_contenido_chunk} tokens est.).")
        # La función generar_esquema_de_texto imprimirá sus propios mensajes de inicio
        esquema_final = llm_processing.generar_esquema_de_texto(texto_completo, es_parcial=False)
    else:
        print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) excede el límite por chunk ({max_tokens_contenido_chunk} tokens est.). "
              "Se procederá con mega-chunking.")
        
        mega_chunks = utils.dividir_en_mega_chunks(
            texto_completo, 
            max_tokens_contenido_chunk, 
            config.MEGA_CHUNK_OVERLAP_WORDS # Esta constante debe estar en config.py
        )
        print(f"Transcripción dividida en {len(mega_chunks)} mega-chunks.")

        esquemas_parciales = []
        for i, mega_chunk in enumerate(mega_chunks):
            # El mensaje de "Procesando mega-chunk..." ahora está dentro de generar_esquema_de_texto
            # si pasamos los parámetros chunk_num y total_chunks
            esquema_parcial = llm_processing.generar_esquema_de_texto(
                mega_chunk, 
                es_parcial=True,
                chunk_num=i + 1,       # Pasar número de chunk actual
                total_chunks=len(mega_chunks) # Pasar total de chunks
            )
            if esquema_parcial:
                esquemas_parciales.append(esquema_parcial)
            else:
                print(f"ADVERTENCIA: No se pudo generar esquema para el mega-chunk {i+1}.")
        
        if not esquemas_parciales:
            print("ERROR: No se pudieron generar esquemas parciales. Terminando.")
            return # Salir si no hay esquemas parciales
        
        # La función fusionar_esquemas imprimirá sus propios mensajes de inicio
        esquema_final = llm_processing.fusionar_esquemas(esquemas_parciales)

    utils.guardar_texto_a_archivo(esquema_final, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")
    print("\n--- Proceso de Generación de Esquema Terminado ---")

if __name__ == "__main__":
    main()
