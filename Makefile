COLOUR_GREEN=\033[0;32m
COLOUR_RED=\033[0;31m
COLOUR_BLUE=\033[0;34m
COLOUR_END=\033[0m

.DEFAULT_GOAL:=help

# Get needed paths and information from locally installed librados
RADOSLIB_VERSION := 2.0.0
GENERAL_LIB_LOCATION := $(shell pip show rados | grep -oP "(?<=Location: ).*")
RADOSLIB_INSTALLED_VERSION := $(shell pip show rados | grep Version | awk '{print $$2}')

.PHONY: help
help: ## Display this help message
	@echo -e '${COLOUR_RED}Usage: make <command>${COLOUR_END}'
	@cat $(MAKEFILE_LIST) | grep '^[a-zA-Z]'  | \
	    awk -F ':.*?## ' 'NF==2 {printf "  %-26s%s\n\n", $$1, "${COLOUR_GREEN}"$$2"${COLOUR_END}"}'

.PHONY: setup
setup: setup-pre-commit check-radoslib setup-venv ## Setup the pre-commit environment and then the venv environment

setup-pre-commit:
	pip install --user pre-commit && pre-commit install

setup-venv:
	python -m venv --system-site-packages ./.venv && \
	source ./.venv/bin/activate && \
	pip install --ignore-installed -r requirements.txt

.PHONY: update-requirements
update-requirements: ## Update the requirements.txt with newer versions of pip packages
	source ./.venv/bin/activate && \
	pip freeze -l > requirements.txt

check-radoslib: ## Checks if radoslib is installed and if it contains the right version
	@if [ -z "$(GENERAL_LIB_LOCATION)" ]; then \
		echo -e "${COLOUR_RED}ERROR: 'rados' library not found. Please make sure it's installed.${COLOUR_END}"; \
		exit 1; \
	fi
	@if [ "$(RADOSLIB_INSTALLED_VERSION)" != "$(RADOSLIB_VERSION)" ]; then \
		echo -e "${COLOUR_RED}ERROR: Incorrect version of 'rados' library found. Expected version $(RADOSLIB_VERSION), found $$RADOSLIB_INSTALLED_VERSION.${COLOUR_END}"; \
		exit 1; \
	fi

.PHONY: run-local-rookify
run-local-rookify: ## Runs rookify in the local development environment (requires setup-venv)
	$(eval PYTHONPATH="${PYTHONPATH}:$(pwd)/src")
	source ./.venv/bin/activate && \
	cd src && python3 -m rookify
