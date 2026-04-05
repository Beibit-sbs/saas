SHELL := /bin/bash
COMPOSE := cd infra && docker compose --env-file .env

.PHONY: help up down logs ci test lint pipeline prod-up prod-down template-validate security-regression release-check release-gate rollback-check

help:
	@echo "Targets: up down logs ci test lint pipeline prod-up prod-down template-validate"
	@echo "         security-regression release-check release-gate rollback-check"

up:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

ci:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) up -d --build
	$(COMPOSE) exec -T backend pytest -q
	$(COMPOSE) exec -T backend ruff check .
	$(COMPOSE) run --rm frontend-tests npm run lint
	$(COMPOSE) run --rm frontend-tests npm run test:frontend

test:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) exec -T backend pytest -q

lint:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) exec -T backend ruff check .
	$(COMPOSE) run --rm frontend-tests npm run lint

pipeline:
	./scripts/pipeline.sh

template-validate:
	$(COMPOSE) exec -T backend pytest -q tests/test_template_validation.py

security-regression:
	$(COMPOSE) exec -T backend pytest -q -m security_regression

release-check:
	./scripts/release_check.sh

rollback-check:
	./scripts/rollback_check.sh

release-gate:
	./scripts/release_gate.sh

prod-up:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down
