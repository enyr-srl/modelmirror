ARG BASE_IMAGE=registry.gitlab.com/n-model/base-images/python:3.12
ARG UV_VERSION=0.7.2
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# BASE STAGE
FROM ${BASE_IMAGE}  AS base
USER root
RUN chown -R $USERNAME:$USERNAME /workspace
RUN chown -R $USERNAME:$USERNAME /run
RUN apt-get update && \
    apt-get install -y gnupg2 gettext && \
    rm -rf /var/lib/apt/lists/*
USER $USERNAME

# DEV STAGE
FROM base  AS dev
COPY --from=uv /uv /uvx /bin/

# BUILD STAGE (for optimization)
FROM dev AS builder
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY ./pyproject.toml ./uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# PROD STAGE
FROM base AS prod
COPY --from=builder /workspace/.venv /workspace/.venv
COPY ./app ./app
ENV PYTHONPATH=./app
CMD [".venv/bin/fastapi", "run", "./app/main.py", "--port", "8088"]
