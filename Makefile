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
clean:
	docker container prune -f
	docker image prune -f

.PHONY: test
test: clean
	${DOCKER} run app ./scripts/test.sh

.PHONY: benchmark
benchmark: clean
	${DOCKER} run app ./scripts/benchmark.sh

COMMIT ?= migrate

.PHONY: migrate-create
migrate-create: clean
	${DOCKER} run app python -m cli.migrate revision -m "${COMMIT}"

.PHONY: migrate-upgrade
migrate-upgrade: clean
	${DOCKER} run app python -m cli.migrate upgrade head
