MODE ?= prod

COMPOSE_DIR := deployment
COMPOSE_FILE := $(COMPOSE_DIR)/docker-compose.${MODE}.yaml

.PHONY: lint
lint:
	ruff check --fix
	ruff format

.PHONY: run
run:
	docker-compose -f $(COMPOSE_FILE) up --build --force-recreate -d
