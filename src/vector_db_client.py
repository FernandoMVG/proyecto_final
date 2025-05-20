# src/vector_db_client.py
import requests
from . import config # Usar import relativo

def _hacer_solicitud_post_api(endpoint_path, payload, timeout_seg, descripcion_solicitud):
    """
    Helper para hacer solicitudes POST a la API de la BD vectorial y manejar errores comunes.
    Devuelve el JSON de la respuesta en caso de éxito, o None en caso de error.
    """
    url = config.VECTOR_DB_API_URL.rstrip('/') + "/" + endpoint_path.lstrip('/')

    print(f"API {descripcion_solicitud}: Enviando a {url}...")
    try:
        response = requests.post(url, json=payload, timeout=timeout_seg)
        response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
        
        # Intentar decodificar JSON, manejar el caso de que no sea JSON válido
        try:
            response_json = response.json()
            print(f"API {descripcion_solicitud}: Respuesta - {response.status_code} - {response_json}")
            return response_json
        except requests.exceptions.JSONDecodeError:
            print(f"API {descripcion_solicitud}: Respuesta - {response.status_code} - Pero no es JSON válido: {response.text[:200]}")
            return {"error": "Respuesta no JSON", "status_code": response.status_code, "text": response.text}

    except requests.exceptions.Timeout:
        print(f"API {descripcion_solicitud}: ERROR - Timeout después de {timeout_seg} segundos al conectar con {url}")
    except requests.exceptions.ConnectionError:
        print(f"API {descripcion_solicitud}: ERROR - No se pudo conectar a {url}. ¿Está el servicio API de la BD vectorial corriendo?")
    except requests.exceptions.HTTPError as e:
        # El error ya incluye response.status_code y a menudo response.text o response.reason
        print(f"API {descripcion_solicitud}: ERROR HTTP - {e.response.status_code} - {e.response.reason}. Detalles: {e.response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"API {descripcion_solicitud}: ERROR Genérico de Request - {e}")
    return None # Devuelve None en caso de cualquier error

def poblar_bd_vectorial_con_transcripcion(chunks_de_transcripcion):
    """Envía chunks de la transcripción al servicio API para poblar la BD vectorial."""
    if not chunks_de_transcripcion:
        print("API /populate: No hay chunks para enviar.")
        return False
        
    payload = {"texts": chunks_de_transcripcion}
    descripcion = f"/populate ({len(chunks_de_transcripcion)} chunks)"
    
    resultado_api = _hacer_solicitud_post_api(
        "populate", # endpoint_path relativo
        payload, 
        timeout_seg=300, 
        descripcion_solicitud=descripcion
    )
    # Consideramos éxito si la API devuelve algo (incluso un JSON de error que no sea None)
    # pero idealmente la API debería devolver un status claro en su JSON
    return resultado_api is not None and resultado_api.get("status") == "success" # Asumiendo que la API devuelve {"status": "success"}

def obtener_contexto_relevante_de_api(texto_consulta_esquema):
    """Obtiene chunks relevantes de la transcripción desde la API de la BD vectorial."""
    if not texto_consulta_esquema:
        print("API /search: Texto de consulta vacío.")
        return []

    payload = {
        "query_text": texto_consulta_esquema,
        "n_results": config.NUM_RELEVANT_CHUNKS_FOR_APUNTES 
    }
    descripcion = f"/search (query: '{texto_consulta_esquema[:40].replace('\n', ' ')}...')"
    
    data = _hacer_solicitud_post_api(
        "search", # endpoint_path relativo
        payload, 
        timeout_seg=60, 
        descripcion_solicitud=descripcion
    )
    
    if data and isinstance(data.get('documents'), list):
        documentos = [item['document'] for item in data['documents'] if isinstance(item, dict) and 'document' in item]
        print(f"API /search: Encontrados {len(documentos)} chunks relevantes.")
        return documentos
    else:
        print(f"API /search: No se encontraron documentos o la respuesta no tuvo el formato esperado. Data: {data}")
    return []