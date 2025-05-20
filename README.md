# Proyecto Final - Transcripción y Guía de Estudio con LLM

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/FernandoMVG/proyecto_final)

Este proyecto utiliza un Modelo de Lenguaje Grande (LLM) local para procesar transcripciones de clases de Optimización, dividiéndolas en partes (Map) y luego sintetizando una guía de estudio en formato Markdown (Reduce).

## Prerrequisitos del Sistema

Antes de empezar, asegúrate de tener instalado lo siguiente en tu sistema:

1.  **Python:** Versión 3.9 o superior.
2.  **Git:** Para clonar el repositorio.
3.  **Herramientas de Compilación C++:** Necesarias para compilar `llama-cpp-python`.
    *   **Windows:** Instala [Build Tools for Visual Studio](https://visualstudio.microsoft.com/es/downloads/) (sección "Herramientas para Visual Studio"). Durante la instalación, selecciona la carga de trabajo **"Desarrollo para el escritorio con C++"**.
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install build-essential git cmake`
    *   **MacOS:** Instala Xcode Command Line Tools: `xcode-select --install` y `cmake` (ej. `brew install cmake`).
4.  **(Opcional - SOLO para Aceleración por GPU NVIDIA): NVIDIA CUDA Toolkit**
    *   Si tienes una GPU NVIDIA compatible y deseas acelerar el proceso, necesitas instalar el [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).
    *   **Importante:** Instala una versión compatible con tu driver y GPU. La instalación Express suele ser suficiente y debería añadir `nvcc` a tu PATH.
    *   **Verifica:** Después de instalar (y reiniciar si es necesario), abre una **nueva terminal** y ejecuta `nvcc --version`. Deberías ver la versión impresa. Si no, necesitas añadir la carpeta `bin` de CUDA a tu PATH manualmente.

## Instalación del Proyecto

1.  **Clona el Repositorio:**
    ```bash
    git clone <URL_DE_TU_REPOSITORIO>
    cd <NOMBRE_DE_LA_CARPETA_DEL_PROYECTO>
    ```

2.  **Crea y Activa un Entorno Virtual:**
    ```bash
    python -m venv .venv 
    # Windows (cmd/powershell):
    .\.venv\Scripts\activate
    # Linux/MacOS (bash/zsh):
    source .venv/bin/activate 
    ```
    *Verás `(.venv)` al inicio de tu línea de comandos.*

3.  **Instala las Dependencias Base:**
    ```bash
    pip install -r requirements.txt 
    ```
    *(Asegúrate de tener un archivo `requirements.txt` con las dependencias como `python-dotenv`, si la usas. **No incluyas `llama-cpp-python` aquí** para permitir la instalación condicional).*

4.  **Instala `llama-cpp-python` (¡Elige UNA opción!):**

    *   **Opción A: Instalación SOLO para CPU**
        *   Esta es la opción más sencilla si no tienes una GPU NVIDIA o si tienes problemas con la instalación de CUDA.
        ```bash
        pip install llama-cpp-python
        ```

    *   **Opción B: Instalación con Aceleración GPU (NVIDIA CUDA)**
        *   **Asegúrate** de haber completado el Prerrequisito #4 (CUDA Toolkit instalado y `nvcc` funcionando en una nueva terminal).
        *   Ejecuta el comando correspondiente a tu terminal para compilar con soporte CUDA:
            *   **PowerShell (Windows):**
                ```powershell
                $env:CMAKE_ARGS = "-DGGML_CUDA=on" 
                pip install --force-reinstall --no-cache-dir llama-cpp-python
                $env:CMAKE_ARGS = "" 
                ```
            *   **CMD (Windows):**
                ```cmd
                set CMAKE_ARGS=-DGGML_CUDA=on
                pip install --force-reinstall --no-cache-dir llama-cpp-python
                set CMAKE_ARGS=
                ```
            *   **Bash/Zsh (Linux/MacOS):**
                ```bash
                export CMAKE_ARGS="-DGGML_CUDA=on"
                pip install --force-reinstall --no-cache-dir llama-cpp-python
                unset CMAKE_ARGS 
                ```
        *   *Presta atención a la salida durante la instalación para verificar que detecta CUDA y compila correctamente.*

## Configuración del Modelo LLM

1.  **Descarga un Modelo:** Necesitas un modelo de lenguaje en formato **GGUF**. Puedes encontrar modelos cuantizados (más pequeños y rápidos) en [Hugging Face Hub](https://huggingface.co/). Busca versiones GGUF de modelos como `Mistral-7B-Instruct`, `Gemma-Instruct-2B`, etc. (ej. los de "TheBloke").
2.  **Coloca el Modelo:** Crea una carpeta llamada `models/` en la raíz del proyecto (si no existe) y coloca el archivo `.gguf` descargado dentro de ella.
3.  **Actualiza el Script:** Abre el archivo `src/main.py` y modifica la variable `MODEL_FILENAME` para que coincida **exactamente** con el nombre del archivo `.gguf` que descargaste:
    ```python
    # src/main.py
    MODEL_FILENAME = "nombre_de_tu_modelo.gguf" # ¡CAMBIA ESTO!
    # ... resto del código
    ```

## Ejecución

1.  **Prepara la Entrada:** Asegúrate de tener el archivo de transcripción que quieres procesar en la carpeta `data/`. Por defecto, el script busca `data/transcripcion_ejemplo.txt`. Puedes editar el script (`INPUT_FILE`) o renombrar tu archivo.
2.  **Navega a la Carpeta `src`:**
    ```bash
    cd src
    ```
3.  **Ejecuta el Script:**
    *   **Para usar GPU (si la instalaste con Opción B):**
        ```bash
        python main.py 
        ```
    *   **Para forzar el uso SÓLO de CPU (incluso si instalaste con Opción B):**
        ```bash
        python main.py --cpu-only
        ```
        *(Nota: El script `main.py` debe incluir la lógica de `argparse` para que el flag `--cpu-only` funcione)*

4.  **Salida:**
    *   Los resultados intermedios de la fase Map se guardarán en `output/map_results.txt`.
    *   La guía de estudio final en formato Markdown se guardará en `output/guia_estudio.md`.

## Solución de Problemas

*   Si la instalación de `llama-cpp-python` falla, revisa cuidadosamente que todos los **Prerrequisitos del Sistema** estén instalados correctamente (especialmente C++ Build Tools y, si aplica, CUDA Toolkit y su configuración en PATH).
*   Si la carga del modelo falla, verifica que la ruta y el nombre en `MODEL_FILENAME` sean correctos y que tengas suficiente RAM/VRAM.

