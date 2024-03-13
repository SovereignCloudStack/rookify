# Builder
FROM python:3.11 as builder

# Note: this value currenlty needs to be the same as the value returned from get_version() from setup.py
ARG ROOKIFY_VERSION=0.0.1

WORKDIR /app/rookify

RUN pip install build
COPY . /app/rookify/
RUN python -m build /app/rookify/


# Base
From quay.io/ceph/ceph:v17.2.7 as base

COPY requirements.txt /app/rookify/src/

# Install Librados:
# Get rados version from requirements.txt and install it using apt,
# because librados does not exist as pip package
RUN cat /etc/os-release && dnf install -y python39-pip python3-virtualenv

# Install package with requirements including systempackages with simlinks
RUN /usr/bin/python3.9 -m venv --system-site-packages /app/rookify/.venv && \
    /app/rookify/.venv/bin/pip3.9 install --ignore-installed -r /app/rookify/src/requirements.txt

# Rookify
FROM base AS rookify
LABEL org.opencontainers.image.source="https://github.com/SovereignCloudStack/rookify"
ARG ROOKIFY_VERSION=0.0.1

WORKDIR /app/rookify

COPY --from=builder /app/rookify/dist/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl ./src/
RUN .venv/bin/pip3.9 install ./src/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl

# This is for debugging and will not be used when ENTRYPOINT is set
CMD ["sleep", "infinity"]

# Set the ENTRYPOINT to activate the venv and then run the 'rookify' command
ENTRYPOINT ["/app/rookify/bin/rookify"]
