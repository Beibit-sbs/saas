SHELL := /bin/bash
COMPOSE := cd infra && docker compose --env-file .env

.PHONY: help up down logs ci test lint pipeline pipeline-force system-audit kill-host prod-up prod-down template-validate security-regression release-check release-gate rollback-check pilot-safe-gate pilot-bootstrap pilot-ldap-up pilot-ldap-down pilot-seed-demo

help:
	@echo "Targets: up down logs ci test lint pipeline pipeline-force kill-host"
	@echo "         system-audit"
	@echo "         prod-up prod-down template-validate"
	@echo "         security-regression release-check release-gate rollback-check pilot-safe-gate pilot-bootstrap"
	@echo "         pilot-ldap-up pilot-ldap-down"
	@echo "         pilot-seed-demo"
	@echo ""
	@echo "  kill-host           — kill host-side dev processes blocked by docker-only guard"
	@echo "  pipeline-force      — kill host-side dev processes, then run full pipeline"
	@echo "  system-audit        — one-shot full backend/frontend/parity quality gate"
	@echo "  pilot-ldap-up       — start stack with OpenLDAP mock for LDAP testing"
	@echo "  pilot-ldap-down     — stop LDAP stack"

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
	$(COMPOSE) run --rm --no-deps backend-tests pytest -q --disable-warnings
	$(COMPOSE) exec -T backend ruff check .
	$(COMPOSE) run --rm frontend-tests npm run lint
	$(COMPOSE) run --rm frontend-tests npm run test:frontend

test:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) run --rm --no-deps backend-tests pytest -q --disable-warnings

lint:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) exec -T backend ruff check .
	$(COMPOSE) run --rm frontend-tests npm run lint

pipeline:
	./scripts/pipeline.sh

kill-host:
	@echo "[kill-host] Stopping host-side dev processes..."
	@PROHIBITED='(uvicorn|hypercorn|gunicorn .*app\.main|next dev|vite( |$$)|webpack-dev-server|npm run dev|pnpm dev|yarn dev)'; \
	PIDS="$$(ps -eo pid=,args= | rg -i "$$PROHIBITED" | rg -vi "docker|container|guard|rg -i|grep -E" | awk '{print $$1}' || true)"; \
	if [ -z "$$PIDS" ]; then \
	  echo "[kill-host] No host dev processes found."; \
	else \
	  echo "[kill-host] Killing PIDs: $$PIDS"; \
	  echo "$$PIDS" | xargs kill -TERM 2>/dev/null || true; \
	  sleep 1; \
	  echo "$$PIDS" | xargs kill -KILL 2>/dev/null || true; \
	  echo "[kill-host] Done."; \
	fi

pipeline-force: kill-host
	./scripts/pipeline.sh

system-audit:
	./scripts/system_audit_gate.sh

template-validate:
	$(COMPOSE) run --rm --no-deps backend-tests pytest -q --disable-warnings tests/test_template_validation.py

security-regression:
	$(COMPOSE) run --rm --no-deps backend-tests pytest -q --disable-warnings -m security_regression

release-check:
	./scripts/release_check.sh

rollback-check:
	./scripts/rollback_check.sh

release-gate:
	./scripts/release_gate.sh

pilot-safe-gate:
	./scripts/university_pilot_safe_gate.sh

pilot-bootstrap:
	bash ./scripts/bootstrap_university_pilot_env.sh

prod-up:
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down

pilot-ldap-up:
	@echo "[pilot-ldap-up] Starting stack with mock OpenLDAP for LDAP testing..."
	bash ./scripts/docker_only_guard.sh
	$(COMPOSE) up -d --build ldap db redis backend worker scheduler frontend nginx
	@echo "[pilot-ldap-up] Waiting for LDAP to be ready..."
	@docker compose -f infra/docker-compose.yml --env-file infra/.env exec -T ldap ldapwhoami -H ldap://localhost -D cn=admin,dc=example,dc=local -w admin || sleep 5
	@echo "[pilot-ldap-up] ✓ Stack is ready with OpenLDAP"
	@echo "[pilot-ldap-up] LDAP credentials: bindDN=cn=admin,dc=example,dc=local password=admin"
	@echo "[pilot-ldap-up] Test users available: admin_user, inst_admin, acad_admin, support_user, dev_user, ops_user (all password=password123)"

pilot-ldap-down:
	@echo "[pilot-ldap-down] Stopping LDAP stack..."
	$(COMPOSE) down
	@echo "[pilot-ldap-down] Done"

pilot-seed-demo:
	@echo "[pilot-seed-demo] Seeding LDAP + academic risk demo dataset..."
	bash ./scripts/pilot_seed_demo_population.sh
