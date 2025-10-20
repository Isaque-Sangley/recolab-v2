# Multi-stage build para otimizar tamanho da imagem

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instala dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt requirements-dev.txt ./

# Instala dependências em /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Cria usuário não-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copia dependências do builder
COPY --from=builder /install /usr/local

# Copia código da aplicação
COPY --chown=appuser:appuser . .

# Muda para usuário não-root
USER appuser

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando padrão
CMD ["uvicorn", "src.presentation.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]