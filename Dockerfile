# Etapa de construcción (builder) para CPU
FROM python:3.12-slim-bookworm AS builder

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    ninja-build \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app_build

# Copiar requirements e instalar dependencias de Python
# IMPORTANTE: Asegúrate que tu requirements.txt no especifique versiones GPU
# de librerías (ej. torch+cu118). Usa versiones CPU.
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instalar llama-cpp-python compilando para CPU (sin CUBLAS)
RUN echo "Building llama-cpp-python for CPU..." && \
    pip install --no-cache-dir llama-cpp-python

# Etapa final: runtime para CPU
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL="INFO"
# ENV N_GPU_LAYERS="-1" # Eliminado, es específico para GPU

# Instalar dependencias de runtime (libgomp1 para OpenMP en llama.cpp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar los paquetes de Python instalados desde la etapa builder
# Esto asume que los paquetes se instalan en site-packages, lo cual es estándar
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/


# Copiar el código de la aplicación
COPY ./src /app/src
COPY ./templates /app/templates

RUN mkdir -p /app/data /app/output /app/models

EXPOSE 8080

# Usar 'python' ya que en la imagen python:3.10-slim-bullseye, 'python' apunta a python3.10
CMD ["python", "-m", "uvicorn", "src.api_main:app", "--host", "0.0.0.0", "--port", "8080"]