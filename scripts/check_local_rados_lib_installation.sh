#!/bin/env bash

# Check if a version argument is provided
if [ $# -eq 1 ]; then
    RADOSLIB_VERSION="$1"
else
    # Default version if no argument is provided
    RADOSLIB_VERSION="2.0.0"
fi

# Get the location of the installed rados library
GENERAL_LIB_LOCATION=$(pip show rados | grep -oP "(?<=Location: ).*")

# Get the installed version of the rados library
RADOSLIB_INSTALLED_VERSION=$(pip show rados | grep Version | awk '{print $2}')

# Check if the rados library is installed
if [ -z "$GENERAL_LIB_LOCATION" ]; then
    echo -e "\033[0;31mERROR: 'rados' library not found. Please make sure it's installed.\033[0m"
    exit 1
fi

# Check if the installed version matches the expected version
if [ "$RADOSLIB_INSTALLED_VERSION" != "$RADOSLIB_VERSION" ]; then
    echo -e "\033[0;31mERROR: 'rados' library version $RADOSLIB_INSTALLED_VERSION does not match the expected version $RADOSLIB_VERSION.\033[0m"
    exit 1
else
    echo -e "\033[0;32m'rados' library version $RADOSLIB_INSTALLED_VERSION is correct.\033[0m"
fi
