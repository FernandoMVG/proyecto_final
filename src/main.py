# src/main.py
import time
import os
import re
from src import config
from src import utils # Contiene format_duration, timed_phase y funciones de chunking
from src import llm_processing
from src import prompts # Aunque no se usa directamente aquí, es parte del flujo
from src import vector_db_client

def main():
    script_start_time = time.time()
    print("--- INICIO DEL PROCESO DE GENERACIÓN DE GUÍA DE ESTUDIO ---")

    with utils.timed_phase("Inicialización y Carga de Modelo"):
        utils.crear_directorios_necesarios()
        llm = llm_processing.cargar_modelo_llm()
        if llm is None:
            print("ERROR CRÍTICO: No se pudo cargar el modelo LLM. Saliendo.")
            return

    texto_completo_transcripcion = ""
    with utils.timed_phase("Preparación de Datos (Lectura de Transcripción)"):
        texto_completo_transcripcion = utils.leer_archivo(config.INPUT_FILE_PATH)
        if not texto_completo_transcripcion:
            print("ERROR CRÍTICO: No se pudo leer el archivo de transcripción. Saliendo.")
            return
        
        num_palabras_total = len(texto_completo_transcripcion.split())
        estimacion_tokens_transcripcion_total = int(num_palabras_total / config.FACTOR_PALABRAS_A_TOKENS_APROX if config.FACTOR_PALABRAS_A_TOKENS_APROX > 0 else num_palabras_total * 1.5) # Evitar división por cero
        print(f"Transcripción leída: {num_palabras_total} palabras (~{estimacion_tokens_transcripcion_total} tokens estimados).")

    # --- Fase de Población de la Base de Datos Vectorial ---
    # Idealmente, esto se hace solo una vez por transcripción si no cambia.
    # Para el prototipo, se ejecuta cada vez.
    with utils.timed_phase("Población de Base de Datos Vectorial"):
        chunks_para_bd = utils.dividir_texto_para_bd_vectorial(
            texto_completo_transcripcion,
            config.VECTOR_DB_POPULATE_CHUNK_SIZE_WORDS,
            config.VECTOR_DB_POPULATE_CHUNK_OVERLAP_WORDS
        )
        if chunks_para_bd:
            print(f"Dividida la transcripción en {len(chunks_para_bd)} chunks para la BD vectorial.")
            # Asumiendo que tu API de poblar retorna un booleano o algo evaluable
            # La función refactorizada en vector_db_client ya imprime el resultado
            exito_poblacion = vector_db_client.poblar_bd_vectorial_con_transcripcion(chunks_para_bd)
            if not exito_poblacion:
                print("ADVERTENCIA: Falló la población de la BD vectorial. La generación de apuntes podría no tener contexto suficiente.")
                # Decidir si continuar. Por ahora, continuamos.
        else:
            print("ADVERTENCIA: No se generaron chunks para poblar la BD vectorial (transcripción vacía o error en chunking).")

    esquema_final_texto = None
    with utils.timed_phase("Carga o Generación de Esquema Jerárquico"):
        if os.path.exists(config.OUTPUT_ESQUEMA_PATH):
            print(f"INFO: Intentando cargar esquema existente desde: {config.OUTPUT_ESQUEMA_PATH}")
            esquema_final_texto = utils.leer_archivo(config.OUTPUT_ESQUEMA_PATH)
            if esquema_final_texto:
                print("INFO: Esquema existente cargado exitosamente.")
            else:
                print(f"ADVERTENCIA: No se pudo cargar el esquema desde {config.OUTPUT_ESQUEMA_PATH}. Se generará uno nuevo.")

        if not esquema_final_texto:
            print("INFO: No se encontró esquema previo o no se pudo cargar. Procediendo a generar nuevo esquema.")
            
            # Cálculo de tokens disponibles para el contenido del mega-chunk
            # prompt_base_sin_texto_esquema = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
            # prompt_base_esquema_len_palabras = len(prompt_base_sin_texto_esquema.split())
            # prompt_base_esquema_len_tokens_aprox = prompt_base_esquema_len_palabras / config.FACTOR_PALABRAS_A_TOKENS_APROX
            
            # max_tokens_para_contenido_real_en_prompt = config.CONTEXT_SIZE - prompt_base_esquema_len_tokens_aprox - config.MAX_TOKENS_ESQUEMA_PARCIAL # Dejar espacio para prompt y salida
            # max_palabras_contenido_chunk_esquema = int(max_tokens_para_contenido_real_en_prompt * config.FACTOR_PALABRAS_A_TOKENS_APROX * config.MEGA_CHUNK_CONTEXT_FACTOR) # Aplicar factor de seguridad

            # Simplificando el cálculo de tokens para mega-chunks (más robusto)
            # Se asume que el LLM puede manejar el prompt base + el texto del mega-chunk si el texto del mega-chunk es X% del CONTEXT_SIZE
            # El prompt de esquema es relativamente corto.
            # El LLM necesita espacio para el prompt + el texto del chunk + la salida.
            # El mega_chunk debe ser tal que (prompt + mega_chunk + salida_esperada) < CONTEXT_SIZE
            # Entonces, tamaño_mega_chunk_tokens ~ CONTEXT_SIZE * FACTOR - tokens_prompt_base - tokens_salida_esperada
            tokens_prompt_base_esquema_aprox = 200 # Estimación aproximada para el PROMPT_GENERAR_ESQUEMA_TEMPLATE sin el texto.
            max_tokens_para_texto_en_mega_chunk = int(
                (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - tokens_prompt_base_esquema_aprox - config.MAX_TOKENS_ESQUEMA_PARCIAL
            )


            if estimacion_tokens_transcripcion_total <= max_tokens_para_texto_en_mega_chunk :
                print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) "
                      f"cabe en un solo pase para el esquema (max_tokens_texto_chunk: {max_tokens_para_texto_en_mega_chunk}).")
                esquema_final_texto = llm_processing.generar_esquema_de_texto(texto_completo_transcripcion, es_parcial=False)
            else:
                print(f"INFO: La transcripción ({estimacion_tokens_transcripcion_total} tokens est.) excede el límite por chunk "
                      f"({max_tokens_para_texto_en_mega_chunk} tokens). Se procederá con mega-chunking.")
                mega_chunks = utils.dividir_en_mega_chunks(
                    texto_completo_transcripcion,
                    max_tokens_para_texto_en_mega_chunk, # Pasamos tokens directamente para el contenido
                    config.MEGA_CHUNK_OVERLAP_WORDS
                )
                if not mega_chunks:
                    print("ERROR CRÍTICO: No se pudieron generar mega-chunks. Verifique la transcripción y configuración.")
                    return

                print(f"Transcripción dividida en {len(mega_chunks)} mega-chunks para la generación de esquemas parciales.")
                esquemas_parciales = []
                for i, mega_chunk_texto in enumerate(mega_chunks):
                    print(f"  Procesando mega-chunk {i+1}/{len(mega_chunks)} ({len(mega_chunk_texto.split())} palabras)")
                    esquema_parcial = llm_processing.generar_esquema_de_texto(
                        mega_chunk_texto, es_parcial=True, chunk_num=i + 1, total_chunks=len(mega_chunks)
                    )
                    if esquema_parcial:
                        esquemas_parciales.append(esquema_parcial)
                    else:
                        print(f"ADVERTENCIA: El esquema parcial para el mega-chunk {i+1} fue vacío o nulo.")
                
                if not esquemas_parciales:
                    print("ERROR CRÍTICO: No se pudieron generar esquemas parciales válidos. No se puede continuar.")
                    return
                
                print(f"Se generaron {len(esquemas_parciales)} esquemas parciales. Procediendo a fusionarlos.")
                esquema_final_texto = llm_processing.fusionar_esquemas(esquemas_parciales)
            
            if esquema_final_texto:
                utils.guardar_texto_a_archivo(esquema_final_texto, config.OUTPUT_ESQUEMA_PATH, "esquema de la clase")
            else:
                print("ERROR CRÍTICO: Falló la generación del esquema final.")
                return

    if not esquema_final_texto or not esquema_final_texto.strip():
        print("ERROR CRÍTICO: No hay esquema disponible (ni cargado ni generado válidamente). No se pueden generar apuntes. Saliendo.")
        return

    with utils.timed_phase("Generación de Apuntes Detallados (Con RAG por Sección)"):
        # Dividir el esquema en secciones principales (ej. "1. Tema A", "2. Tema B")
        # Este regex busca una línea que comience con uno o más dígitos, un punto, y un espacio.
        secciones_del_esquema = re.split(r"\n(?=\d+\.\s)", esquema_final_texto.strip())
        secciones_del_esquema = [s.strip() for s in secciones_del_esquema if s.strip()]
        
        # Determinar el título principal de la clase para el Markdown
        # Intenta tomar la primera línea del esquema si no es un punto numerado,
        # o un título genérico si el esquema está vacío o no tiene un título claro.
        titulo_clase = "Optimización" # Default
        primeras_lineas_esquema = esquema_final_texto.strip().split('\n')
        if primeras_lineas_esquema:
            primera_linea = primeras_lineas_esquema[0].strip()
            if not re.match(r"^\d+\.", primera_linea): # Si no empieza con "1.", etc.
                titulo_clase = primera_linea # Asumir que es el título de la clase/documento
        
        apuntes_completos_md = f"# Guía de Estudio Detallada: {titulo_clase}\n\n"

        if not secciones_del_esquema:
            print("ADVERTENCIA: No se pudieron identificar secciones principales numeradas en el esquema. "
                  "Se intentará generar apuntes para el esquema completo como una sola sección (puede ser menos efectivo).")
            if esquema_final_texto.strip(): # Solo si hay algo en el esquema
                apuntes_para_seccion_unica = llm_processing.generar_apuntes_por_seccion_con_rag(
                    esquema_final_texto, 
                    num_seccion=None # O num_seccion="General"
                )
                if apuntes_para_seccion_unica:
                    # Si el esquema original no tenía un "1. Tema", el prompt de apuntes debería generar un H2
                    # Si el LLM no genera el H2 apropiado, podríamos añadirlo aquí
                    if not apuntes_para_seccion_unica.strip().startswith("##"):
                         apuntes_completos_md += f"## Resumen General de la Clase\n{apuntes_para_seccion_unica}\n\n"
                    else:
                         apuntes_completos_md += f"{apuntes_para_seccion_unica}\n\n"
        else:
            print(f"Esquema dividido en {len(secciones_del_esquema)} secciones principales para procesar.")
            for i, seccion_esq_texto in enumerate(secciones_del_esquema):
                print(f"\n  Procesando para Apuntes - Sección del Esquema {i+1}/{len(secciones_del_esquema)}")
                # print(f"  Contenido de la 'seccion_esq_texto':\n'''\n{seccion_esq_texto[:300]}...\n'''") # Para depuración

                apuntes_para_esta_seccion = llm_processing.generar_apuntes_por_seccion_con_rag(
                    seccion_esq_texto, 
                    num_seccion=i+1 # Para logging y potencialmente para el prompt si fuera necesario
                )
                if apuntes_para_esta_seccion:
                    # El prompt PROMPT_GENERAR_APUNTES_TEMPLATE ya instruye al LLM
                    # para que use el título de la sección del esquema como encabezado H2.
                    # Así que simplemente concatenamos.
                    apuntes_completos_md += f"{apuntes_para_esta_seccion.strip()}\n\n"
                else:
                    titulo_seccion_err = seccion_esq_texto.splitlines()[0] if seccion_esq_texto.splitlines() else f"Sección vacía {i+1}"
                    print(f"ADVERTENCIA: No se generaron apuntes para la sección del esquema: '{titulo_seccion_err}'")
                    # Podríamos añadir un placeholder en el MD final si quisiéramos
                    # apuntes_completos_md += f"## {titulo_seccion_err}\n\n_(No se pudieron generar apuntes para esta sección)_\n\n"


        utils.guardar_texto_a_archivo(apuntes_completos_md.strip(), config.OUTPUT_APUNTES_PATH, "apuntes detallados de la clase")

    print("\n--- PROCESO COMPLETO TERMINADO ---")
    script_total_duration = time.time() - script_start_time
    print(f"--- Duración Total del Script: {utils.format_duration(script_total_duration)} ---")

if __name__ == "__main__":
    main()