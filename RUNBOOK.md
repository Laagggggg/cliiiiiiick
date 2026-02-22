# Incident Runbook

## Immediate halt conditions
- `guard_all_v5()` fails
- trade expectancy <= 0
- consecutive losses >= 5
- equity curve gate = HALT

## Actions
1. Cancel new entries.
2. Persist engine state (`ops/state_persistence.py`).
3. Log failed guard and diagnostics.
4. Reconcile positions before restart.

## Gap-risk protocol
- Run `assess_gap_risk()` before close.
- HIGH: reduce overnight risk immediately.

## Partial-fill protocol
- `handle_partial_fill()` decides ACCEPT / REQUEUE / CANCEL_REMAINDER based on fill fraction and signal edge.
