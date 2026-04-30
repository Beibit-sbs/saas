# PASS / FAIL / WARNING Coverage Summary

- Timestamp UTC: 20260429T103923Z
- Profile: standard
- Pass: 0
- Fail: 0
- Warning: 0
- Skipped: 4
- Planned: 6

| Batch | Status | Exit | Log | Detail |
|-------|--------|------|-----|--------|
| preflight | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/preflight.log | bash /home/sbs/AI/scripts/preflight_checks.sh |
| permission-parity | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/permission-parity.log | bash /home/sbs/AI/scripts/check_permission_parity.sh |
| compose-bootstrap | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/compose-bootstrap.log | compose_cmd up -d db redis backend frontend nginx |
| backend-lint | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/backend-lint.log | compose-bootstrap did not pass |
| backend-pytest-shards | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/backend-pytest-shards.log | compose-bootstrap did not pass |
| frontend-lint | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/frontend-lint.log | compose-bootstrap did not pass |
| frontend-tests | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/frontend-tests.log | compose-bootstrap did not pass |
| domain-layer-gate | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/domain-layer-gate.log | bash /home/sbs/AI/scripts/domain_layer_gate.sh |
| data-layer-gate | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/data-layer-gate.log | bash /home/sbs/AI/scripts/data_layer_gate.sh |
| smoke-gate | PLANNED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T103923Z/smoke-gate.log | bash /home/sbs/AI/scripts/platform_smoke_check.sh |
