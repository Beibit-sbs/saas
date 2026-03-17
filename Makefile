SHELL := /bin/bash

.PHONY: help up down logs ci test lint pipeline prod-up prod-down template-validate

help:
	@echo "Targets: up down logs ci test lint pipeline prod-up prod-down template-validate"

up:
	cd infra && docker compose --env-file .env up -d --build

down:
	cd infra && docker compose --env-file .env down

logs:
	cd infra && docker compose --env-file .env logs -f --tail=100

ci:
	cd backend && pytest -q && ruff check .
	cd frontend && npm run lint

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

pipeline:
	./scripts/pipeline.sh

template-validate:
	cd backend && .venv/bin/pytest -q tests/test_template_validation.py

prod-up:
	cd infra && docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	cd infra && docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml down
