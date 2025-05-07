# src/main.py
import time
from src import config
from src import utils
from src import llm_processing

def main():
    """Función principal para orquestar el proceso completo."""
    
    # 0. Crear directorios necesarios
    utils.crear_directorios_necesarios()

    # 1. Cargar el modelo LLM
    llm = llm_processing.cargar_modelo_llm()
    if llm is None: # Si la carga falla, cargar_modelo_llm retorna None
        print("Saliendo del programa debido a un error en la carga del modelo.")
        return # Salir si el modelo no se carga

    # 2. Leer Transcripción
    print("\n--- Iniciando Proceso Map-Reduce ---")
    texto_completo = utils.leer_archivo(config.INPUT_FILE_PATH)
    if not texto_completo:
        return # Salir si no hay texto
    print(f"Transcripción leída ({len(texto_completo)} caracteres).")

    # 3. Dividir en Chunks
    chunks = utils.dividir_en_chunks(texto_completo, config.CHUNK_SIZE_WORDS, config.CHUNK_OVERLAP_WORDS)
    if not chunks:
        print("ERROR: No se pudieron generar chunks del texto.")
        return
    print(f"Texto dividido en {len(chunks)} chunks.")

    # 4. Fase Map: Procesar cada chunk
    print("\n--- Fase Map: Procesando Chunks ---")
    resultados_map = []
    start_map_time = time.time()

    for i, chunk in enumerate(chunks):
        print(f"Procesando chunk {i+1}/{len(chunks)}...")
        # Pasamos la instancia del LLM cargada (aunque llm_processing.py la tiene global)
        resultado_chunk = llm_processing.procesar_chunk_map(chunk) 
        resultados_map.append(resultado_chunk)
        print(f"  Conceptos: {resultado_chunk.get('conceptos', [])}")
        print(f"  Resumen: {resultado_chunk.get('resumen_breve', '')[:50]}...")

    end_map_time = time.time()
    print(f"--- Fase Map completada en {end_map_time - start_map_time:.2f} segundos ---")

    # 5. Guardar Resultados Intermedios (Map)
    utils.guardar_resultados_map(resultados_map, config.OUTPUT_MAP_RESULTS_PATH)

    # 6. Fase Reduce: Sintetizar la guía final
    # Pasamos la instancia del LLM cargada (aunque llm_processing.py la tiene global)
    guia_final_markdown = llm_processing.sintetizar_guia_reduce(resultados_map)

    # 7. Guardar Guía Final
    utils.guardar_guia_final(guia_final_markdown, config.FINAL_OUTPUT_PATH)

    print("\n--- Proceso Completo Terminado ---")

if __name__ == "__main__":
    main()