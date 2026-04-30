# PASS / FAIL / WARNING Coverage Summary

- Timestamp UTC: 20260429T103958Z
- Profile: standard
- Pass: 0
- Fail: 0
- Warning: 0
- Skipped: 0
- Planned: 28

| Batch | Status | Exit | Log | Detail |
|-------|--------|------|-----|--------|
| preflight | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/preflight.log | bash /home/sbs/AI/scripts/preflight_checks.sh |
| permission-parity | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/permission-parity.log | bash /home/sbs/AI/scripts/check_permission_parity.sh |
| compose-bootstrap | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/compose-bootstrap.log | compose_cmd up -d db redis backend frontend nginx |
| backend-lint | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-lint.log | compose_cmd exec -T backend ruff check . |
| backend-pytest-shard-01 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-01.log | dynamic backend pytest shard 1/18 |
| backend-pytest-shard-02 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-02.log | dynamic backend pytest shard 2/18 |
| backend-pytest-shard-03 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-03.log | dynamic backend pytest shard 3/18 |
| backend-pytest-shard-04 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-04.log | dynamic backend pytest shard 4/18 |
| backend-pytest-shard-05 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-05.log | dynamic backend pytest shard 5/18 |
| backend-pytest-shard-06 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-06.log | dynamic backend pytest shard 6/18 |
| backend-pytest-shard-07 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-07.log | dynamic backend pytest shard 7/18 |
| backend-pytest-shard-08 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-08.log | dynamic backend pytest shard 8/18 |
| backend-pytest-shard-09 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-09.log | dynamic backend pytest shard 9/18 |
| backend-pytest-shard-10 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-10.log | dynamic backend pytest shard 10/18 |
| backend-pytest-shard-11 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-11.log | dynamic backend pytest shard 11/18 |
| backend-pytest-shard-12 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-12.log | dynamic backend pytest shard 12/18 |
| backend-pytest-shard-13 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-13.log | dynamic backend pytest shard 13/18 |
| backend-pytest-shard-14 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-14.log | dynamic backend pytest shard 14/18 |
| backend-pytest-shard-15 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-15.log | dynamic backend pytest shard 15/18 |
| backend-pytest-shard-16 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-16.log | dynamic backend pytest shard 16/18 |
| backend-pytest-shard-17 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-17.log | dynamic backend pytest shard 17/18 |
| backend-pytest-shard-18 | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shard-18.log | dynamic backend pytest shard 18/18 |
| backend-pytest-shards | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/backend-pytest-shards.log | 426 files across 18 shards |
| frontend-lint | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/frontend-lint.log | compose_cmd run --rm -T frontend-tests npm run lint |
| frontend-tests | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/frontend-tests.log | compose_cmd run --rm -T frontend-tests npm run test:frontend |
| domain-layer-gate | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/domain-layer-gate.log | bash /home/sbs/AI/scripts/domain_layer_gate.sh |
| data-layer-gate | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/data-layer-gate.log | bash /home/sbs/AI/scripts/data_layer_gate.sh |
| smoke-gate | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103958Z/smoke-gate.log | bash /home/sbs/AI/scripts/platform_smoke_check.sh |
