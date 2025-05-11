MODE ?= local

COMPOSE_DIR := deployment
COMPOSE_FILE := $(COMPOSE_DIR)/docker-compose.${MODE}.yaml

DOCKER := docker-compose -f $(COMPOSE_FILE)

.PHONY: lint
lint:
	ruff check --fix --unsafe-fixes
	ruff format

.PHONY: run
run: build up clean

.PHONY: build
build:
	${DOCKER} build

.PHONY: up
up:
	${DOCKER} up --force-recreate -d

.PHONY: clean
clean: clean-container
	docker builder prune -f
	docker image prune -f

.PHONY: test
test: clean-container
	${DOCKER} run app ./scripts/test.sh

.PHONY: benchmark
benchmark: clean-container
	${DOCKER} run app ./scripts/benchmark.sh

COMMIT ?= migrate

.PHONY: migrate-create
migrate-create: clean-container
	${DOCKER} run app python -m cli.migrate revision -m "${COMMIT}"

.PHONY: migrate-upgrade
migrate-upgrade: clean-container
	${DOCKER} run app python -m cli.migrate upgrade head

.PHONY: clean-container
clean-container:
	docker container prune -f
