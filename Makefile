SHELL := /bin/bash
COMPOSE := cd infra && docker compose --env-file .env

.PHONY: help up down logs ci test lint pipeline pipeline-force system-audit kill-host prod-up prod-down template-validate security-regression domain-layer-gate data-layer-gate f3-unfreeze-validation f3-4-frontend-kickoff f3-5-observability-kickoff f3-kickoff-readiness f3-4-f3-5-prep-snapshot f3-alert-gate day7-f1f2-pre-validation day7-f1f2-one-shot f4-kickoff-readiness release-check release-gate rollback-check rollback-previous prune-remote-releases pilot-safe-gate pilot-full-gate pilot-to-prod-promote pilot-bootstrap pilot-ldap-up pilot-ldap-down pilot-seed-demo

help:
	@echo "Targets: up down logs ci test lint pipeline pipeline-force kill-host"
	@echo "         system-audit"
	@echo "         prod-up prod-down template-validate"
	@echo "         security-regression domain-layer-gate data-layer-gate"
	@echo "         f3-unfreeze-validation f3-4-frontend-kickoff f3-5-observability-kickoff"
	@echo "         f3-kickoff-readiness f3-alert-gate"
	@echo "         f3-4-f3-5-prep-snapshot"
	@echo "         day7-f1f2-pre-validation day7-f1f2-one-shot f4-kickoff-readiness"
	@echo "         release-check release-gate rollback-check rollback-previous prune-remote-releases"
	@echo "         pilot-safe-gate pilot-full-gate pilot-to-prod-promote pilot-bootstrap"
	@echo "         pilot-ldap-up pilot-ldap-down"
	@echo "         pilot-seed-demo"
	@echo ""
	@echo "  kill-host           — kill host-side dev processes blocked by docker-only guard"
	@echo "  pipeline-force      — kill host-side dev processes, then run full pipeline"
	@echo "  system-audit        — one-shot full backend/frontend/parity quality gate"
	@echo "  day7-f1f2-pre-validation  — verify docker/scripts/env ready before 2026-04-20 day7 run"
	@echo "  f3-kickoff-readiness      — unified gate for F3.3/F3.4/F3.5 before 2026-04-21 Phase 1"
	@echo "  f3-4-f3-5-prep-snapshot   — generate pre-day7 prep artifact for F3.4/F3.5"
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

domain-layer-gate:
	./scripts/domain_layer_gate.sh

data-layer-gate:
	./scripts/data_layer_gate.sh

f3-unfreeze-validation:
	./scripts/f3_unfreeze_validation.sh

f3-4-frontend-kickoff:
	./scripts/f3_4_frontend_kickoff_readiness.sh

f3-5-observability-kickoff:
	./scripts/f3_5_observability_kickoff_readiness.sh

f3-kickoff-readiness:
	./scripts/f3_kickoff_readiness.sh

f3-4-f3-5-prep-snapshot:
	./scripts/f3_4_f3_5_pre_day7_prep.sh

f3-alert-gate:
	./scripts/f3_observability_alerts_gate.sh

day7-f1f2-pre-validation:
	./scripts/f1_f2_day7_pre_execution_validation.sh

day7-f1f2-one-shot:
	./scripts/f1_f2_day7_official_one_shot.sh

f4-kickoff-readiness:
	./scripts/f4_kickoff_readiness.sh

release-check:
	./scripts/release_check.sh

rollback-check:
	./scripts/rollback_check.sh

rollback-previous:
	./scripts/rollback_to_previous_release.sh $(TARGET)

prune-remote-releases:
	./scripts/prune_remote_releases.sh $(TARGET) $(KEEP)

release-gate:
	./scripts/release_gate.sh

pilot-safe-gate:
	./scripts/university_pilot_safe_gate.sh

pilot-full-gate:
	./scripts/pilot_full_function_gate.sh

pilot-to-prod-promote:
	./scripts/pilot_to_prod_promotion.sh

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
