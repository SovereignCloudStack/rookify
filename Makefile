COLOUR_GREEN=\033[0;32m
COLOUR_RED=\033[0;31m
COLOUR_BLUE=\033[0;34m
COLOUR_END=\033[0m

.DEFAULT_GOAL:=help

#SHELL := /bin/bash

# Get needed paths and information from locally installed librados
GENERAL_LIB_LOCATION := $(shell pip show rados | grep -oP "(?<=Location: ).*")
LIBRADOS_LOCATION := $(shell find "${GENERAL_LIB_LOCATION}" -name 'rados*.so' -print)
LIBRADOS_EGGINFO_LOCATION := $(shell find "${GENERAL_LIB_LOCATION}" -name 'rados*.egg-info' -print)
LIBRADOS_NAME := $(shell basename "${LIBRADOS_LOCATION}")
LIBRADOS_EGGINFO_NAME := $(shell basename "${LIBRADOS_EGGINFO_LOCATION}")

.PHONY: help
help: ## Display this help message
	@echo -e '${COLOUR_RED}Usage: make <command>${COLOUR_END}'
	@cat $(MAKEFILE_LIST) | grep '^[a-zA-Z]'  | \
	    awk -F ':.*?## ' 'NF==2 {printf "  %-26s%s\n\n", $$1, "${COLOUR_GREEN}"$$2"${COLOUR_END}"}'

.PHONY: setup
setup: setup-pre-commit setup-venv install-into-venv ## Setup the pre-commit environment and then the venv environment

setup-pre-commit:
	pip install --user pre-commit && pre-commit install

setup-venv:
	python -m venv ./.venv && \
	source ./.venv/bin/activate

install-into-venv:
	$(eval PYTHON_VERSION := $(shell grep '^version' ./.venv/pyvenv.cfg | cut -d ' ' -f 3 | cut -d '.' -f 1,2))
	echo -e 'PYTHON_VERSION: $(PYTHON_VERSION)'
	echo -e 'GENERAL_LIB_LOCATION: ${GENERAL_LIB_LOCATION}'
	echo -e 'LIBRADOS_LOCATION: ${LIBRADOS_LOCATION}'
	echo -e 'LIBRADOS_EGGINFO_LOCATION: ${LIBRADOS_EGGINFO_LOCATION}'
	ln -s "${LIBRADOS_LOCATION}" "./.venv/lib/python$(PYTHON_VERSION)/site-packages/${LIBRADOS_NAME}"
	ln -s "${LIBRADOS_EGGINFO_LOCATION}" "./.venv/lib/python$(PYTHON_VERSION)/site-packages/${LIBRADOS_EGGINFO_NAME}"
	pip install -r requirements.txt
