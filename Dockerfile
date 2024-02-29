FROM python:3.11
WORKDIR /app/rookify 
COPY . /app/rookify/

# Install Librados:
# Get rados version from requirements.txt and install it using apt,
# because librados does not exist as pip package
RUN apt-get update && apt-get install -y python3-rados && \
    # Save the path to PKG-INFO file to a variable
    PKG_INFO_PATH=$(dpkg -L python3-rados | grep -E '/rados-[0-9.]+\.egg-info/PKG-INFO') && \
    # Extract the installed version from the PKG-INFO file
    INSTALLED_VERSION=$(grep -oP '(?<=Version: )\d+\.\d+\.\d+' "$PKG_INFO_PATH") && \
    # Extract the required version from the requirements.txt file
    REQUIRED_VERSION=$(grep -oP '(?<=rados==)\d+\.\d+\.\d+' /app/rookify/requirements.txt) && \
    # Check if the installed version matches the required version, if not than give a warning and exit process
    if [ "$INSTALLED_VERSION" != "$REQUIRED_VERSION" ]; then \
        echo "WARNING: Installed version of rados Python package ($INSTALLED_VERSION) does not match required version ($REQUIRED_VERSION)." >&2; \
        exit 1; \
    fi

# Note: librados does not exist as a package, so this will fail when trying to install rados
# Comment out the 'rados' requirement in requirements.txt
RUN sed -i '/rados/s/^/#/' /app/rookify/requirements.txt

# Currently pip simply installed all the requirements
RUN pip install --no-cache-dir -r /app/rookify/requirements.txt

# DEBUGGIN: Add a sleep command to keep the container running
CMD ["sleep", "infinity"]
