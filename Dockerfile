# Etapa de construcción (builder) con soporte CUDA
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04 AS builder

# Instalar Python y dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    git \
    ninja-build \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app_build

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN python3.10 -m pip install --upgrade pip
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

# Instalar llama-cpp-python compilando con soporte CUDA (GPU)
RUN echo "Building llama-cpp-python with CUDA support..." && \
    CMAKE_ARGS="-DLLAMA_CUBLAS=on" python3.10 -m pip install --no-cache-dir llama-cpp-python

# Etapa final: runtime con CUDA y Python
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL="INFO"
ENV N_GPU_LAYERS="-1"

# Instalar Python y dependencias necesarias para runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar todos los directorios donde podría estar instalado Python
COPY --from=builder /usr/local/lib/python3.10/ /usr/local/lib/python3.10/
COPY --from=builder /usr/lib/python3/ /usr/lib/python3/

# Copiar el código de la aplicación
COPY ./src /app/src
COPY ./templates /app/templates

RUN mkdir -p /app/data /app/output /app/models

EXPOSE 8080

CMD ["python3.10", "-m", "uvicorn", "src.api_main:app", "--host", "0.0.0.0", "--port", "8080"]