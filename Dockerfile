# builder
FROM python:3.11 as builder
ARG ROOKIFY_VERSION=0.0.0-dev

WORKDIR /app/rookify

RUN pip install build
COPY . /app/rookify/
RUN python -m build /app/rookify/

# base
FROM debian:stable-slim as base

COPY requirements.txt /app/rookify/src/

# Install Librados:
# Get rados version from requirements.txt and install it using apt,
# because librados does not exist as pip package
RUN apt-get update && apt-get install -y python3-pip python3-rados python3-venv && \
    # Save the path to PKG-INFO file to a variable
    PKG_INFO_PATH=$(dpkg -L python3-rados | grep -E '/rados-[0-9.]+\.egg-info/PKG-INFO') && \
    # Extract the installed version from the PKG-INFO file
    INSTALLED_VERSION=$(grep -oP '(?<=Version: )\d+\.\d+\.\d+' "$PKG_INFO_PATH") && \
    # Extract the required version from the requirements.txt file
    REQUIRED_VERSION=$(grep -oP '(?<=rados==)\d+\.\d+\.\d+' /app/rookify/src/requirements.txt) && \
    # Check if the installed version matches the required version, if not than give a warning and exit process
    if [ "$INSTALLED_VERSION" != "$REQUIRED_VERSION" ]; then \
        echo "WARNING: Installed version of rados Python package ($INSTALLED_VERSION) does not match required version ($REQUIRED_VERSION)." >&2; \
        exit 1; \
    fi

# Currently pip simply installed all the requirements
RUN python3 -m venv --system-site-packages --symlinks /app/rookify/
RUN /app/rookify/bin/pip install -r /app/rookify/src/requirements.txt

# rookify
FROM base AS rookify
LABEL org.opencontainers.image.source="https://github.com/SovereignCloudStack/rookify"
ARG ROOKIFY_VERSION=0.0.0

WORKDIR /app/rookify

COPY --from=builder /app/rookify/dist/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl ./src/
RUN ./bin/pip install ./src/Rookify-${ROOKIFY_VERSION}-py3-none-any.whl

CMD ["sleep", "infinity"]
#ENTRYPOINT ["./bin/rookify", "run"]
