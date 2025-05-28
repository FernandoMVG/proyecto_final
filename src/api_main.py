# src/api_main.py
import time
import os
import logging
from typing import Optional
import re # Ensure re is imported

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv # Importar load_dotenv
import google.generativeai as genai # Importar Gemini SDK

# Importar módulos de tu proyecto
from src import config
from src import utils
from src import llm_processing
from src import prompts

# Cargar variables de entorno del archivo .env
load_dotenv()

# --- Configuración del Logging ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
# Convertir string a nivel de logging
log_level_int = getattr(logging, LOG_LEVEL, logging.INFO)

log_format = "%(asctime)s [%(levelname)-5s] %(name)-25s %(funcName)-25s L%(lineno)-4d: %(message)s"

# Obtener el logger raíz para configurarlo
root_logger = logging.getLogger()
root_logger.setLevel(log_level_int)

# Limpiar handlers existentes para evitar duplicados si se recarga (con --reload)
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# Handler para la consola
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(log_format))
root_logger.addHandler(stream_handler)

# Opcional: Handler para archivo
# log_file_path = os.path.join(config.BASE_PROJECT_DIR, "output", "api_process.log")
# file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
# file_handler.setFormatter(logging.Formatter(log_format))
# root_logger.addHandler(file_handler)

api_logger = logging.getLogger("api.service") # Logger específico para la lógica de la API

# Crear la aplicación FastAPI
app = FastAPI(
    title="API de Generación de Esquemas y Apuntes de Clases",
    description="Procesa transcripciones para generar esquemas jerárquicos y, opcionalmente, apuntes detallados.",
    version="0.2.0"
)

# --- Funciones Helper para la API ---

async def _call_gemini_api_with_schema_and_transcription(
    esquema_contenido: str, 
    transcripcion_contenido: str, 
    prompt_texto: str,
    informacion_contextual: Optional[str] = None  # Nuevo parámetro
) -> str:
    """
    Llama a la API de Gemini para generar apuntes, opcionalmente con información contextual.
    """
    api_logger.info("Iniciando llamada a la API de Gemini...")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        api_logger.error("GEMINI_API_KEY no encontrada en las variables de entorno.")
        raise HTTPException(status_code=500, detail="Error de configuración: GEMINI_API_KEY no encontrada.")

    try:
        genai.configure(api_key=gemini_api_key)

        # Formatear el prompt final con el esquema, la transcripción y la información contextual si existe
        prompt_completo = prompt_texto.format(
            esquema_contenido=esquema_contenido,
            transcripcion_contenido=transcripcion_contenido,
            informacion_contextual_adicional=informacion_contextual if informacion_contextual else "" 
        )
        
        model = genai.GenerativeModel(config.GEMINI_MODEL_NAME) # ej: 'gemini-1.5-flash'
        
        api_logger.debug(f"Prompt completo enviado a Gemini: \\n{prompt_completo[:500]}...") # Loguea una parte del prompt

        response = await model.generate_content_async(prompt_completo) # Usar async para no bloquear

        if response and response.text:
            api_logger.info("Respuesta recibida de la API de Gemini.")
            return response.text
        elif response and not response.text and response.prompt_feedback:
            api_logger.error(f"Llamada a Gemini no devolvió texto. Feedback: {response.prompt_feedback}")
            raise HTTPException(status_code=500, detail=f"Error de la API de Gemini: No se generó contenido. Feedback: {response.prompt_feedback}")
        else:
            api_logger.error("Respuesta inesperada o vacía de la API de Gemini.")
            raise HTTPException(status_code=500, detail="Error de la API de Gemini: Respuesta inesperada o vacía.")

    except Exception as e:
        api_logger.error(f"Error durante la llamada a la API de Gemini: {e}", exc_info=True)
        # Considerar si se quiere exponer detalles del error al cliente o un mensaje genérico
        raise HTTPException(status_code=500, detail=f"Error interno al contactar la API de Gemini: {str(e)}")


# --- Evento de Inicio de la Aplicación ---
@app.on_event("startup")
async def startup_event():
    api_logger.info("Iniciando API y cargando modelo LLM...")
    utils.crear_directorios_necesarios() # Asegura que data/ y output/ existan
    # _ensure_output_dir_exists() # Específicamente para archivos temporales de la API si se guardan ahí
    
    # Cargar modelo con GPU por defecto al inicio. El flag --cpu se maneja por endpoint.
    llm_processing.cargar_modelo_llm(use_cpu_only=False) 
    if llm_processing.llm_instance is None:
        api_logger.error("FALLO CRÍTICO: No se pudo cargar el modelo LLM al iniciar la API.")
    else:
        api_logger.info("Modelo LLM cargado y listo para la API.")

# --- Endpoint para Generar Esquema ---
@app.post("/generar_esquema/", response_class=FileResponse)
async def generar_esquema_endpoint(
    # background_tasks: BackgroundTasks, # Removed
    file: UploadFile = File(..., description="Archivo de transcripción en formato .txt"),
    usar_cpu: bool = Query(False, description="Forzar el uso de CPU para esta solicitud.")
):
    request_start_time = time.time()
    original_filename = file.filename
    api_logger.info(f"Solicitud para generar esquema de: {original_filename}")

    # Manejo de carga de modelo CPU/GPU (simplificado por ahora)
    # La carga inicial en startup usa GPU. Si se pide CPU aquí, idealmente se recargaría.
    # Por ahora, si se pide CPU y el modelo ya está en GPU, se usará GPU.
    # Una solución más robusta requeriría gestionar instancias de modelo separadas o recargas.
    if usar_cpu and not llm_processing.llm_instance.model_params.n_gpu_layers == 0:
        api_logger.warning("Se solicitó CPU, pero el modelo ya está cargado con GPU. Usando GPU.")
    
    if llm_processing.llm_instance is None:
        api_logger.error("Modelo LLM no está disponible.")
        raise HTTPException(status_code=503, detail="Servicio no disponible: Modelo LLM no cargado.")

    try:
        contenido_bytes = await file.read()
        texto_completo_transcripcion = contenido_bytes.decode("utf-8")
    except Exception as e:
        api_logger.error(f"Error al leer/decodificar archivo \'{original_filename}\': {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error al procesar archivo: {e}")
    finally:
        await file.close()

    api_logger.info(f"Transcripción \'{original_filename}\' leída: {len(texto_completo_transcripcion.split())} palabras.")

    # --- Lógica de Generación de Esquema ---
    esquema_final_texto = None
    try:
        # Análisis de Tokens para Esquema
        prompt_template_base_texto = prompts.PROMPT_GENERAR_ESQUEMA_TEMPLATE.replace("{texto_completo}", "")
        tokens_prompt_base = llm_processing.llm_instance.tokenize(prompt_template_base_texto.encode('utf-8', 'ignore'))
        num_tokens_prompt_base = len(tokens_prompt_base)
        tokens_contenido_transcripcion = llm_processing.llm_instance.tokenize(texto_completo_transcripcion.encode('utf-8', 'ignore'))
        num_tokens_contenido_transcripcion = len(tokens_contenido_transcripcion)
        api_logger.info(f"Tokens para esquema: Base={num_tokens_prompt_base}, Contenido={num_tokens_contenido_transcripcion}")

        tokens_salida_pase_unico = config.MAX_TOKENS_ESQUEMA_FUSIONADO
        max_tokens_para_contenido_en_pase_unico = int(
            (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - num_tokens_prompt_base - tokens_salida_pase_unico
        )
        max_tokens_para_contenido_en_mega_chunk_individual = int(
             (config.CONTEXT_SIZE * config.MEGA_CHUNK_CONTEXT_FACTOR) - num_tokens_prompt_base - config.MAX_TOKENS_ESQUEMA_PARCIAL
        )

        if max_tokens_para_contenido_en_pase_unico <=0 or max_tokens_para_contenido_en_mega_chunk_individual <= 0:
            raise HTTPException(status_code=500, detail="Cálculo de tokens para contenido de esquema resultó no positivo.")

        if num_tokens_contenido_transcripcion <= max_tokens_para_contenido_en_pase_unico:
            api_logger.info("Generando esquema en un solo pase.")
            esquema_final_texto = llm_processing.generar_esquema_de_texto(texto_completo_transcripcion, es_parcial=False)
        else:
            api_logger.info("Generando esquema con mega-chunking.")
            mega_chunks = utils.dividir_en_mega_chunks(
                texto_completo_transcripcion,
                max_tokens_para_contenido_en_mega_chunk_individual,
                config.MEGA_CHUNK_OVERLAP_TOKENS,
                llm_tokenizer_instance=llm_processing.llm_instance
            )
            if not mega_chunks: raise HTTPException(status_code=500, detail="No se generaron mega-chunks.")
            
            esquemas_parciales = []
            for i, mega_chunk_texto in enumerate(mega_chunks):
                esquema_parcial = llm_processing.generar_esquema_de_texto(
                    mega_chunk_texto, es_parcial=True, chunk_num=i + 1, total_chunks=len(mega_chunks)
                )
                if esquema_parcial: esquemas_parciales.append(esquema_parcial)
            
            if not esquemas_parciales: raise HTTPException(status_code=500, detail="No se generaron esquemas parciales.")
            esquema_final_texto = llm_processing.fusionar_esquemas(esquemas_parciales)

        if not esquema_final_texto or not esquema_final_texto.strip():
            raise HTTPException(status_code=500, detail="Fallo en la generación del esquema final.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e_esquema:
        api_logger.error(f"Error durante la generación del esquema para \'{original_filename}\': {e_esquema}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al generar el esquema: {str(e_esquema)}")

    # Guardar en archivo permanente en la carpeta output
    nombre_base_salida = os.path.splitext(original_filename)[0]
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_filename = f"{nombre_base_salida}_esquema_local_{timestamp}.txt"
    output_dir_path = os.path.join(config.BASE_PROJECT_DIR, "output")
    permanent_file_path = os.path.join(output_dir_path, output_filename)

    try:
        utils._ensure_output_dir_exists() # Ensure output dir exists
        with open(permanent_file_path, "w", encoding="utf-8") as f:
            f.write(esquema_final_texto)
        api_logger.info(f"Esquema para \'{original_filename}\' guardado permanentemente en: {permanent_file_path}")
        
        # background_tasks.add_task(utils._cleanup_temp_file, temp_file_path) # Removed
        
        api_logger.info(f"Devolviendo archivo de esquema: {output_filename}")
        processing_time = round(time.time() - request_start_time, 2)
        api_logger.info(f"Tiempo total para generar esquema de \'{original_filename}\': {processing_time} seg.")

        return FileResponse(
            path=permanent_file_path,
            filename=output_filename,
            media_type='text/plain'
        )
    except Exception as e_file_resp:
        api_logger.error(f"Error al preparar FileResponse para esquema de \'{original_filename}\': {e_file_resp}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al servir el archivo de esquema: {str(e_file_resp)}")


# --- Endpoint para Generar Apuntes ---
@app.post("/generar_apuntes/", response_class=FileResponse)
async def generar_apuntes_endpoint(
    # background_tasks: BackgroundTasks, # Removed
    transcripcion_file: UploadFile = File(..., description="Archivo de transcripción original (.txt)"),
    esquema_file: UploadFile = File(..., description="Archivo de esquema generado previamente (.txt)"),
    usar_cpu: bool = Query(False, description="Forzar el uso de CPU para esta solicitud.")
):
    request_start_time = time.time()
    original_transcripcion_filename = transcripcion_file.filename
    original_esquema_filename = esquema_file.filename
    api_logger.info(f"Solicitud para generar apuntes basada en esquema para: {original_transcripcion_filename} y esquema: {original_esquema_filename}")

    # Similar manejo de CPU que en el endpoint de esquema
    if usar_cpu and not llm_processing.llm_instance.model_params.n_gpu_layers == 0:
        api_logger.warning("Se solicitó CPU, pero el modelo ya está cargado con GPU. Usando GPU.")

    if llm_processing.llm_instance is None:
        api_logger.error("Modelo LLM no está disponible.")
        raise HTTPException(status_code=503, detail="Servicio no disponible: Modelo LLM no cargado.")

    try:
        contenido_bytes_transcripcion = await transcripcion_file.read()
        texto_completo_transcripcion = contenido_bytes_transcripcion.decode("utf-8")
    except Exception as e:
        api_logger.error(f"Error al leer/decodificar archivo de transcripción \'{original_transcripcion_filename}\': {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error al procesar archivo de transcripción: {e}")
    finally:
        await transcripcion_file.close()

    try:
        contenido_bytes_esquema = await esquema_file.read()
        esquema_texto = contenido_bytes_esquema.decode("utf-8")
    except Exception as e:
        api_logger.error(f"Error al leer/decodificar archivo de esquema \'{original_esquema_filename}\': {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error al procesar archivo de esquema: {e}")
    finally:
        await esquema_file.close()

    if not esquema_texto or not esquema_texto.strip():
        raise HTTPException(status_code=400, detail="El archivo de esquema no puede estar vacío.")

    # --- Lógica de Generación de Apuntes ---
    apuntes_texto_final_md = None
    try:
        api_logger.info("Dividiendo el esquema en secciones para generar apuntes.")
        secciones_del_esquema = re.split(r"\n(?=\d+\.\s)", esquema_texto.strip()) # Ensure re is imported
        secciones_del_esquema = [s.strip() for s in secciones_del_esquema if s.strip()]

        apuntes_completos_md_list = []
        if not secciones_del_esquema and esquema_texto.strip():
            apuntes_para_seccion_unica = llm_processing.generar_apuntes_por_seccion(
                esquema_texto, texto_completo_transcripcion, 1, 1
            )
            if apuntes_para_seccion_unica:
                apuntes_completos_md_list.append(f"## Resumen General de la Clase\\n{apuntes_para_seccion_unica.strip()}")
        elif secciones_del_esquema:
            for i, seccion_esq_texto in enumerate(secciones_del_esquema):
                apuntes_para_esta_seccion = llm_processing.generar_apuntes_por_seccion(
                    seccion_esq_texto, texto_completo_transcripcion, i + 1, len(secciones_del_esquema)
                )
                if apuntes_para_esta_seccion:
                    apuntes_completos_md_list.append(apuntes_para_esta_seccion.strip())

        if apuntes_completos_md_list:
            nombre_base_salida = os.path.splitext(original_transcripcion_filename)[0]
            apuntes_texto_final_md = f"# Guía de Estudio Detallada: {nombre_base_salida}\\n\\n" + "\\n\\n".join(apuntes_completos_md_list)
        else:
            api_logger.warning("No se generó contenido para los apuntes.")
            raise HTTPException(status_code=500, detail="No se pudo generar contenido para los apuntes.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e_apuntes:
        api_logger.error(f"Error durante la generación de apuntes para \'{original_transcripcion_filename}\': {e_apuntes}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al generar apuntes: {str(e_apuntes)}")

    # Guardar en archivo permanente en la carpeta output
    nombre_base_salida = os.path.splitext(original_transcripcion_filename)[0]
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_filename = f"{nombre_base_salida}_apuntes_local_{timestamp}.md"
    output_dir_path = os.path.join(config.BASE_PROJECT_DIR, "output")
    permanent_file_path_apuntes = os.path.join(output_dir_path, output_filename)

    try:
        utils._ensure_output_dir_exists() # Ensure output dir exists
        with open(permanent_file_path_apuntes, "w", encoding="utf-8") as f:
            f.write(apuntes_texto_final_md)
        api_logger.info(f"Apuntes para \'{original_transcripcion_filename}\' guardados permanentemente en: {permanent_file_path_apuntes}")

        # background_tasks.add_task(utils._cleanup_temp_file, temp_file_path_apuntes) # Removed

        api_logger.info(f"Devolviendo archivo de apuntes: {output_filename}")
        processing_time = round(time.time() - request_start_time, 2)
        api_logger.info(f"Tiempo total para generar apuntes de \'{original_transcripcion_filename}\': {processing_time} seg.")

        return FileResponse(
            path=permanent_file_path_apuntes,
            filename=output_filename,
            media_type='text/markdown'
        )
    except Exception as e_file_resp_apuntes:
        api_logger.error(f"Error al preparar FileResponse para apuntes de \'{original_transcripcion_filename}\': {e_file_resp_apuntes}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al servir el archivo de apuntes: {str(e_file_resp_apuntes)}")


# --- Endpoint para Generar Apuntes con Gemini (Simulado) ---
@app.post("/generar_apuntes_gemini/")
async def generar_apuntes_gemini_endpoint(
    esquema_file: UploadFile = File(..., description="Archivo de esquema (.txt o .md)"),
    transcripcion_file: UploadFile = File(..., description="Archivo de transcripción (.txt)"),
):
    request_start_time = time.time()
    log_message = f"Solicitud para generar apuntes con Gemini. Esquema: {esquema_file.filename}, Transcripción: {transcripcion_file.filename}. Se realizará consulta automática a BD vectorial basada en esquema."
    api_logger.info(log_message)

    try:
        contenido_esquema_bytes = await esquema_file.read()
        esquema_contenido = contenido_esquema_bytes.decode("utf-8")
    except Exception as e:
        api_logger.error(f"Error al leer/decodificar archivo de esquema \'{esquema_file.filename}\': {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error al procesar archivo de esquema: {e}")

    try:
        contenido_transcripcion_bytes = await transcripcion_file.read()
        transcripcion_contenido = contenido_transcripcion_bytes.decode("utf-8")
    except Exception as e:
        api_logger.error(f"Error al leer/decodificar archivo de transcripción \'{transcripcion_file.filename}\': {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error al procesar archivo de transcripción: {e}")

    # Usar directamente el prompt definido en prompts.py
    prompt_texto = prompts.PROMPT_GEMINI_APUNTES_DESDE_ESQUEMA_Y_TRANSCRIPCION
    if not prompt_texto: # Verificación por si el prompt estuviera vacío o no definido correctamente
        api_logger.error("El prompt PROMPT_GEMINI_APUNTES_DESDE_ESQUEMA_Y_TRANSCRIPCION no está definido o está vacío en src/prompts.py.")
        raise HTTPException(status_code=500, detail="Error de configuración: Prompt para Gemini no encontrado o vacío.")

    if not esquema_contenido.strip():
        raise HTTPException(status_code=400, detail="El archivo de esquema no puede estar vacío.")
    if not transcripcion_contenido.strip():
        raise HTTPException(status_code=400, detail="El archivo de transcripción no puede estar vacío.")

    # --- Consultar Base de Datos Vectorial automáticamente basada en el esquema ---
    # Los parámetros max_terminos_consulta y top_k_por_termino pueden ser configurables si se desea,
    # por ejemplo, a través de config.py o como parámetros del endpoint (aunque la idea es que sea automático).
    # Por ahora, usamos valores por defecto (ej: 3 términos del esquema, 1 resultado por término).
    informacion_contextual_formateada = await utils._extraer_y_consultar_terminos_esquema(
        esquema_contenido, 
        max_terminos_consulta=config.MAX_SCHEMA_TERMS_TO_QUERY if hasattr(config, 'MAX_SCHEMA_TERMS_TO_QUERY') else 3,
        top_k_por_termino=config.VECTOR_DB_TOP_K_PER_TERM if hasattr(config, 'VECTOR_DB_TOP_K_PER_TERM') else 1
    )

    # --- Lógica de Generación de Apuntes con Gemini ---
    apuntes_markdown_gemini = None
    try:
        apuntes_markdown_gemini = await _call_gemini_api_with_schema_and_transcription(
            esquema_contenido=esquema_contenido,
            transcripcion_contenido=transcripcion_contenido,
            prompt_texto=prompt_texto,
            informacion_contextual=informacion_contextual_formateada # Pasar la información formateada
        )
        if not apuntes_markdown_gemini or not apuntes_markdown_gemini.strip():
            # api_logger.warning("La simulación de Gemini no devolvió contenido.") # Comentado o eliminado si se prefiere error directo
            raise HTTPException(status_code=500, detail="La API de Gemini no devolvió contenido.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e_gemini:
        api_logger.error(f"Error durante la llamada a Gemini para \'{transcripcion_file.filename}\': {e_gemini}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al generar apuntes con Gemini: {str(e_gemini)}")

    # Guardar en archivo permanente en la carpeta output
    nombre_base_salida = os.path.splitext(transcripcion_file.filename)[0]
    output_filename = f"{nombre_base_salida}_apuntes_gemini.md"
    output_dir_path = os.path.join(config.BASE_PROJECT_DIR, "output") # Corrected variable name
    permanent_file_path_apuntes = os.path.join(output_dir_path, output_filename)

    try:
        utils._ensure_output_dir_exists() 

        with open(permanent_file_path_apuntes, "w", encoding="utf-8") as f:
            f.write(apuntes_markdown_gemini)
        
        api_logger.info(f"Apuntes de Gemini para \'{transcripcion_file.filename}\' guardados permanentemente en: {permanent_file_path_apuntes}")

        api_logger.info(f"Devolviendo archivo de apuntes (Gemini): {output_filename}")
        processing_time = round(time.time() - request_start_time, 2)
        api_logger.info(f"Tiempo total para generar apuntes con Gemini para \'{transcripcion_file.filename}\': {processing_time} seg.")

        return FileResponse(
            path=permanent_file_path_apuntes,
            filename=output_filename,
            media_type='text/markdown'
        )
    except Exception as e_file_resp_apuntes:
        api_logger.error(f"Error al preparar FileResponse para apuntes de Gemini \'{transcripcion_file.filename}\': {e_file_resp_apuntes}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al servir el archivo de apuntes (Gemini): {str(e_file_resp_apuntes)}")


# Add this endpoint to your api_main.py
@app.get("/get_file/{filename}")
async def get_file(filename: str):
    """
    Retrieve a file from the output directory by filename.
    
    Parameters:
    - filename: The name of the file to retrieve (must exist in /app/output directory)
    
    Returns:
    - FileResponse if file exists
    - 404 if file doesn't exist
    """
    # Security check
    if '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators")
    
    # Use absolute path to the output directory
    output_dir = "./output"
    file_path = os.path.join(output_dir, filename)
    
    # Debugging info
    api_logger.info(f"Absolute file path: {file_path}")
    api_logger.info(f"Directory contents: {os.listdir(output_dir)}")
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File not found. Checked path: {file_path}"
        )

    return FileResponse(
        path=file_path,
        filename=filename,
    )


# Add this endpoint to your api_main.py
@app.get("/list_files/")
async def list_files():
    """
    List all files in the output directory.
    
    Returns:
    - List of filenames in the /app/output directory
    """
    # Use absolute path to the output directory
    output_dir = "./output"
    
    # Get the list of files in the directory
    filenames = os.listdir(output_dir)
    
    return {"filenames": filenames}

# Para ejecutar desde la raíz del proyecto: uvicorn src.api_main:app --reload