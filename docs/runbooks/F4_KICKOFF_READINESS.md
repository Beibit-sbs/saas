# F4 Kickoff Readiness

## ⚠️ CRITICAL: F4 Development is FROZEN Until 2026-05-22

**F4 (AI Academic Advisor) is blocked on F3.10 DoD sign-off (2026-05-22).**

- ❌ NO feature branches or code implementation before 2026-05-22
- ❌ NO F4 PRs or merges before 2026-05-22
- ❌ NO F4 phases (Phase 1, 2, 3...) start before 2026-05-22

---

## Two-Phase Entry Model

### Phase A: Status Check (2026-04-20 — optional, informational only)

After F1/F2 day7 due date (2026-04-20), verify readiness status:

```bash
make f4-kickoff-readiness
```

**Purpose:** Confirm F1.9 + F2.9 gates passed and DoD artifacts exist.

**Output:** PASS or BLOCKED (informational, no action taken).

**Action:** None. Only log the status.

### Phase B: Actual F4 Kickoff (2026-05-23 onwards)

Only after F3.10 DoD sign-off is COMPLETE (2026-05-22 target):

1. Run readiness check one final time:
```bash
make f4-kickoff-readiness
```

2. Once PASS, start F4 Phase 1 implementation per F4 Implementation Guide.

---

## Entry Criteria (both phases)

1. F1.9 post-release gate is PASS.
2. F2.9 post-release gate is PASS.
3. F1.10 DoD sign-off artifact exists.
4. F2.10 DoD sign-off artifact exists.

Additionally, for Phase B (actual development):
5. ✅ F3.10 DoD sign-off is COMPLETE and SIGNED.

---

## One-Shot Command

```bash
bash scripts/f4_kickoff_readiness.sh
# or
make f4-kickoff-readiness
```

## Expected Output

- F4_ENTRY_READY=PASS
- F1_9_GATE=PASS
- F2_9_GATE=PASS
- F1_10_DOD=<artifact file>
- F2_10_DOD=<artifact file>

## Expected FAIL Output (current pre-day7 scenario)

- F4_ENTRY_READY=FAIL
- F1_9_GATE=FAIL
- F2_9_GATE=FAIL
- F1_10_DOD=MISSING or file
- F2_10_DOD=MISSING or file

## Recovery Path

### If FAIL before 2026-04-20 (F1/F2 day7 due)

1. Execute official F1/F2 day7 cycle when due (2026-04-20):

```bash
make day7-f1f2-one-shot
```

2. Re-run readiness gate:

```bash
make f4-kickoff-readiness
```

3. Expect PASS output (Phase A complete).

### If FAIL at 2026-05-23 (F4 actual kickoff)

This indicates F3.10 DoD sign-off was not completed. Investigate with F3 team.

**Do NOT start F4 development** until:
- F3.10 DoD sign-off is formally COMPLETE
- AND f4-kickoff-readiness returns PASS

---

## Blocking Policy

**Freeze enforcement:** F4 feature branches, PRs, and code changes are forbidden until 2026-05-23.

How to enforce:
- GitHub branch protection: block merges to `main` if PR title contains "F4" before 2026-05-23.
- Code review: reject any F4-scoped PR with message: "F4 is frozen until 2026-05-22 DoD sign-off."
- CI: add optional gate `--f4-blocked` to fail CI if F4 code is detected before 2026-05-23.

---

## Timeline Summary

| Date | Milestone | Action |
|------|-----------|--------|
| 2026-04-20 | F1/F2 day7 due | Execute `make day7-f1f2-one-shot` |
| 2026-04-20 | F1/F2 DoD artifact | Check `make f4-kickoff-readiness` (status only) |
| 2026-05-05 | F3.4/F3.5 delivery | F3.6 security phase begins |
| 2026-05-22 | F3.10 DoD sign-off | F3 frozen; gate ready for F4 |
| 2026-05-23 | F4 Kickoff Day | Run `make f4-kickoff-readiness` (go/no-go decision) |
| 2026-05-23 onwards | F4 Phase 1 | Start only if readiness PASS |

