FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/dagster

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ADD https://artifacts-cli.infisical.com/setup.deb.sh /tmp/setup-infisical.sh

SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
RUN chmod +x /tmp/setup-infisical.sh && \
    /tmp/setup-infisical.sh && \
    apt-get update && \
    apt-get install -y --no-install-recommends infisical && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENTRYPOINT [ "/bin/bash", "-euxo", "pipefail" ]
