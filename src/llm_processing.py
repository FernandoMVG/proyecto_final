# src/llm_processing.py
from llama_cpp import Llama
import os
import time
import re
from src import config  # Importa configuraciones
from src import prompts # Importa plantillas de prompts

# --- Carga del Modelo LLM ---
llm_instance = None

def cargar_modelo_llm():
    """Carga el modelo LLM globalmente."""
    global llm_instance # Para modificar la variable global
    if llm_instance is not None:
        print("Modelo LLM ya cargado.")
        return llm_instance

    print(f"Cargando modelo desde: {config.MODEL_PATH}")
    if not os.path.exists(config.MODEL_PATH):
        print(f"ERROR: No se encontró el archivo del modelo en {config.MODEL_PATH}")
        return None # Retorna None si no se puede cargar
    try:
        start_time = time.time()
        llm_instance = Llama(
            model_path=config.MODEL_PATH,
            n_ctx=config.CONTEXT_SIZE,
            n_threads=config.N_THREADS,
            n_gpu_layers=config.N_GPU_LAYERS,
            verbose=config.LLM_VERBOSE
        )
        end_time = time.time()
        print(f"Modelo LLM cargado en {end_time - start_time:.2f} segundos.")
        return llm_instance
    except Exception as e:
        print(f"ERROR al cargar el modelo LLM: {e}")
        llm_instance = None # Asegura que sea None si falla
        return None

# --- Funciones de Procesamiento con LLM ---
def procesar_chunk_map(chunk_texto):
    """Procesa un chunk individual para extraer conceptos y resumen (Fase Map)."""
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado. Llama a cargar_modelo_llm() primero.")
        return {'conceptos': [], 'resumen_breve': "", 'error_parseo': True}

    # Usamos la plantilla del prompt desde prompts.py
    prompt_map_final = prompts.PROMPT_MAP_REFINADO_TEMPLATE.format(chunk_texto=chunk_texto)

    try:
        output = llm_instance(
            prompt_map_final,
            max_tokens=config.MAX_TOKENS_MAP,
            stop=None,
            echo=False
        )
        texto_generado = output['choices'][0]['text'].strip()
        
        conceptos = []
        resumen = ""
        
        idx_conceptos_start = -1
        match_conceptos_label = re.search(r"conceptos clave:", texto_generado, flags=re.IGNORECASE)
        if match_conceptos_label:
            idx_conceptos_start = match_conceptos_label.end()

        idx_resumen_start = -1
        match_resumen_label = re.search(r"resumen breve:", texto_generado, flags=re.IGNORECASE)
        if match_resumen_label:
            idx_resumen_start = match_resumen_label.end()
        
        texto_seccion_conceptos = ""
        if idx_conceptos_start != -1:
            if idx_resumen_start != -1 and idx_resumen_start > idx_conceptos_start:
                texto_seccion_conceptos = texto_generado[idx_conceptos_start:match_resumen_label.start()].strip()
            else:
                texto_seccion_conceptos = texto_generado[idx_conceptos_start:].strip()
        
        if texto_seccion_conceptos:
            # Limpiar la etiqueta "Conceptos Clave:" si el LLM la repitió al inicio de esta sección
            texto_seccion_conceptos_limpio = re.sub(r"^Conceptos Clave:\s*", "", texto_seccion_conceptos, flags=re.IGNORECASE | re.MULTILINE).strip()
            match_conceptos_encontrados = re.findall(r"^[-\*]\s*(.*)", texto_seccion_conceptos_limpio, re.MULTILINE)
            if match_conceptos_encontrados:
                conceptos = [c.strip() for c in match_conceptos_encontrados]

        if idx_resumen_start != -1:
            resumen = texto_generado[idx_resumen_start:].strip()
        
        if not (conceptos or resumen) and texto_generado:
             print(f"ADVERTENCIA: Parseo estructurado falló. Salida cruda: {texto_generado[:100]}...")
             if not (match_conceptos_label and match_resumen_label):
                return {'conceptos': [], 'resumen_breve': texto_generado, 'error_parseo': True}

        return {'conceptos': conceptos, 'resumen_breve': resumen, 'error_parseo': not (conceptos or resumen)}

    except Exception as e:
        print(f"ERROR al procesar chunk con LLM: {e}")
        return {'conceptos': [], 'resumen_breve': "", 'error_parseo': True}
    
def sintetizar_guia_reduce(lista_resultados_map):
    """Sintetiza la guía de estudio final a partir de los resultados de la Fase Map."""
    if llm_instance is None:
        print("ERROR: Modelo LLM no cargado. Llama a cargar_modelo_llm() primero.")
        return None
        
    print("\n--- Iniciando Fase Reduce ---")
    
    texto_consolidado = ""
    for i, res in enumerate(lista_resultados_map):
        if res.get('error_parseo'):
            continue 
        texto_consolidado += f"Resumen Parte {i+1}: {res.get('resumen_breve', 'N/A')}\n"
        conceptos_chunk = res.get('conceptos', [])
        if conceptos_chunk:
             texto_consolidado += f"Conceptos Clave Parte {i+1}: {', '.join(conceptos_chunk)}\n"
        texto_consolidado += "---\n"

    if not texto_consolidado:
        print("ERROR: No hay resultados válidos de la Fase Map para procesar en Reduce.")
        return None

    prompt_reduce_final = prompts.PROMPT_REDUCE_TEMPLATE.format(texto_consolidado=texto_consolidado)
    
    print("Generando la guía de estudio final (Fase Reduce)... Esto puede tardar.")
    start_reduce_time = time.time()
    try:
        output = llm_instance(
            prompt_reduce_final,
            max_tokens=config.MAX_TOKENS_REDUCE,
            stop=None,
            echo=False
        )
        guia_markdown = output['choices'][0]['text'].strip()
        
        if guia_markdown.startswith("# Guía de Estudio: Optimización"):
            guia_markdown = "# Guía de Estudio: Optimización" + guia_markdown[len("# Guía de Estudio: Optimización"):].lstrip()
        else:
             guia_markdown = "# Guía de Estudio: Optimización\n" + guia_markdown

        end_reduce_time = time.time()
        print(f"--- Fase Reduce completada en {end_reduce_time - start_reduce_time:.2f} segundos ---")
        return guia_markdown

    except Exception as e:
        print(f"ERROR durante la Fase Reduce con LLM: {e}")
        return None