# PASS / FAIL / WARNING Coverage Summary

- Timestamp UTC: 20260429T132508Z
- Profile: fast
- Pass: 2
- Fail: 1
- Warning: 0
- Skipped: 3
- Planned: 0

| Batch | Status | Exit | Log | Detail |
|-------|--------|------|-----|--------|
| preflight | PASS | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T132508Z/preflight.log | ok |
| permission-parity | PASS | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T132508Z/permission-parity.log | ok |
| compose-bootstrap | FAIL | 127 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T132508Z/compose-bootstrap.log | exit=127 |
| backend-lint | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T132508Z/backend-lint.log | compose-bootstrap did not pass |
| backend-pytest-shards | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T132508Z/backend-pytest-shards.log | compose-bootstrap did not pass |
| frontend-lint | SKIPPED | 0 | /home/sbs/AI/artifacts/audits/pass-fail-warning-coverage/20260429T132508Z/frontend-lint.log | compose-bootstrap did not pass |
