# Builder
FROM python:3.11 AS builder

ARG ROOKIFY_VERSION=0.0.0.dev1
ENV ROOKIFY_VERSION=$ROOKIFY_VERSION

WORKDIR /app/rookify

RUN pip install build
COPY . /app/rookify/
RUN python -m build /app/rookify/


# Base
FROM ubuntu:24.04 AS base

# Update packages required for Rookify
RUN apt-get update && apt-get install -qy python3-pip-whl python3-rados python3-venv && apt-get clean

# Generate virtualenv including system packages with simlinks
RUN /usr/bin/python3 -m venv --system-site-packages /app/rookify/.venv


# Rookify
FROM base AS rookify
LABEL org.opencontainers.image.source="https://github.com/SovereignCloudStack/rookify"

ARG ROOKIFY_VERSION=0.0.0.dev1
ENV ROOKIFY_VERSION=$ROOKIFY_VERSION

WORKDIR /app/rookify

COPY --from=builder /app/rookify/dist/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl ./src/
RUN .venv/bin/pip3 install ./src/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl

# Set the ENTRYPOINT to activate the venv and then run the 'rookify' command
ENTRYPOINT ["/app/rookify/.venv/bin/rookify"]


# Rookify extended
FROM rookify AS rookify-dev
RUN .venv/bin/pip3 install ./src/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl[tests]
