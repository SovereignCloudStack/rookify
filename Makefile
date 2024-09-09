COLOUR_GREEN=\033[0;32m
COLOUR_RED=\033[0;31m
COLOUR_BLUE=\033[0;34m
COLOUR_END=\033[0m

.DEFAULT_GOAL:=help
SHELL := /bin/bash

# Get needed paths and information from locally installed librados
export RADOSLIB_VERSION := 2.0.0
export GENERAL_LIB_LOCATION := ${shell pip show rados | grep -oP "(?<=Location: ).*"}
export RADOSLIB_INSTALLED_VERSION := ${shell pip show rados | grep Version | awk '{print $$2}'}

## checking if docker, or podman should be used. Podman is preferred.
ifeq ($(shell command -v podman 2> /dev/null),)
	CONTAINERCMD=docker
else
	CONTAINERCMD=podman
endif

## Export default rookify version
export ROOKIFY_VERSION ?= "0.0.0.dev1"

.PHONY: help
help: ## Display this help message
	@echo -e '${COLOUR_RED}Usage: make <command>${COLOUR_END}'
	@cat $(MAKEFILE_LIST) | grep '^[a-zA-Z]'  | \
	    awk -F ':.*?## ' 'NF==2 {printf "  %-26s%s\n\n", $$1, "${COLOUR_GREEN}"$$2"${COLOUR_END}"}'

.PHONY: setup
setup: check-radoslib setup-venv setup-pre-commit ## Setup the pre-commit environment and then the venv environment

.PHONY: setup-pre-commit
setup-pre-commit:
	./.venv/bin/pip install --user pre-commit && ./.venv/bin/python3.12 -m pre_commit install

.PHONY: setup-venv
setup-venv:
	python3 -m venv --system-site-packages ./.venv && \
	./.venv/bin/pip install -r requirements.txt

.PHONY: run-precommit
run-precommit: ## Run pre-commit to check if all files running through
	pre-commit run --all-files

.PHONY: update-requirements
update-requirements: ## Update the requirements.txt with newer versions of pip packages
	source ./.venv/bin/activate && \
	pip freeze -l > requirements.txt

.PHONY: check-radoslib
check-radoslib: ## Checks if radoslib is installed and if it contains the right version
	@if [ -z "${GENERAL_LIB_LOCATION}" ]; then \
		echo -e "${COLOUR_RED}ERROR: 'rados' library not found. Please make sure it's installed.${COLOUR_END}"; \
		exit 1; \
	else \
		echo -e "GENERAL_LIB_LOCATION: $(GENERAL_LIB_LOCATION)"; \
	fi
	@if [ "${RADOSLIB_INSTALLED_VERSION}" != "${RADOSLIB_VERSION}" ]; then \
		echo -e "${COLOUR_RED}ERROR: Incorrect version of 'rados' library found. Expected version $(RADOSLIB_VERSION), found $$RADOSLIB_INSTALLED_VERSION.${COLOUR_END}"; \
		exit 1; \
	else \
		echo -e "RADOSLIB_INSTALLED_VERSION: $(RADOSLIB_INSTALLED_VERSION)"; \
	fi

.PHONY: run-local-rookify
run-local-rookify: ## Runs rookify in the local development environment (requires setup-venv)
	$(eval PYTHONPATH="${PYTHONPATH}:$(pwd)/src")
	source ./.venv/bin/activate && \
	cd src && python3 -m rookify

.PHONY: run-rookify
run-rookify: ## Runs rookify in the container
	docker exec -it rookify-dev /app/rookify/.venv/bin/rookify

.PHONY: build-container
build-container: ## Build container from Dockerfile, add e.g. ROOKIFY_VERSION=0.0.1 to specify the version. Default value is 0.0.0.dev1
	${CONTAINERCMD} build --build-arg ROOKIFY_VERSION=$(ROOKIFY_VERSION) --target rookify -t rookify:latest -f Dockerfile .

.PHONY: run-tests-locally
run-tests-locally: ## Runs the tests in the tests directory. NB: check that your local setup is connected through vpn to the testbed!
	.venv/bin/python -m pytest

.PHONY: run-tests
run-tests: up ## Runs the tests in the container
	${CONTAINERCMD} exec -it rookify-dev bash -c "/app/rookify/.venv/bin/python -m pytest"

.PHONY: enter
enter: ## Enter the container
	${CONTAINERCMD} exec -it rookify-dev bash

.PHONY: logs
logs: ## Logs the container
	${CONTAINERCMD} logs -f rookify-dev

.PHONY: down
down: ## Remove the containers as setup by docker-compose.yml
	${CONTAINERCMD} compose down

.PHONY: up
up: ## Sets up the container as specified in docker-compose.yml and opens a bash terminal
	${CONTAINERCMD} compose up -d
