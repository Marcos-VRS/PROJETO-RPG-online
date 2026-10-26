# Imagem do app Django (daphne ASGI).
# Inclui deps de RAG (sentence-transformers, pymupdf) por padrão para paridade dev/prod.
# Em prod, se quiser imagem mais leve, remover instalação de requirements-ml.txt.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Pacotes de sistema necessários: libpq pra Postgres, build-essential pra wheels nativas,
# libstdc++ pra sentence-transformers/torch, curl pra healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install -r requirements-ml.txt

COPY . .

EXPOSE 8000

# Daphne para ASGI (Channels + DRF coexistem).
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "project.asgi:application"]
