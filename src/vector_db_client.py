# src/vector_db_client.py
import requests
from . import config # Usar import relativo

def poblar_bd_vectorial_con_transcripcion(chunks_de_transcripcion):
    """Envía chunks de la transcripción al servicio API para poblar la BD vectorial."""
    if not chunks_de_transcripcion:
        print("API /populate: No hay chunks para enviar.")
        return False
        
    payload = {"texts": chunks_de_transcripcion}
    url = f"{config.VECTOR_DB_API_URL}/populate"
    print(f"API /populate: Enviando {len(chunks_de_transcripcion)} chunks a {url}...")
    try:
        # Aumentar el timeout para la población, ya que puede tardar si son muchos chunks
        response = requests.post(url, json=payload, timeout=300) # Timeout de 5 minutos
        response.raise_for_status() 
        print(f"API /populate: Respuesta - {response.status_code}", response.json())
        return True
    except requests.exceptions.Timeout:
        print(f"API /populate: ERROR - Timeout después de 300 segundos al conectar con {url}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"API /populate: ERROR - No se pudo conectar a {url}. ¿Está el servicio API de la BD vectorial corriendo?")
        return False
    except requests.exceptions.RequestException as e:
        print(f"API /populate: ERROR - {e}")
        return False

def obtener_contexto_relevante_de_api(texto_consulta_esquema):
    """Obtiene chunks relevantes de la transcripción desde la API de la BD vectorial."""
    payload = {
        "query_text": texto_consulta_esquema,
        "n_results": config.NUM_RELEVANT_CHUNKS_FOR_APUNTES 
    }
    url = f"{config.VECTOR_DB_API_URL}/search"
    # print(f"API /search: Buscando contexto para: '{texto_consulta_esquema[:50]}...' en {url}") # Opcional, puede ser muy verboso
    try:
        response = requests.post(url, json=payload, timeout=60) # Timeout de 1 minuto
        response.raise_for_status()
        data = response.json()
        # Extraer solo el texto del documento
        documentos = [item['document'] for item in data.get('documents', []) if 'document' in item]
        # print(f"API /search: Encontrados {len(documentos)} chunks relevantes.") # Opcional
        return documentos
    except requests.exceptions.Timeout:
        print(f"API /search: ERROR - Timeout después de 60 segundos al conectar con {url}")
        return []
    except requests.exceptions.ConnectionError:
        print(f"API /search: ERROR - No se pudo conectar a {url}. ¿Está el servicio API de la BD vectorial corriendo?")
        return []
    except requests.exceptions.RequestException as e:
        print(f"API /search: ERROR - {e}")
        return []