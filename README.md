# OMEGA-QUANT ULTRA v5 (Implementation)

This repository now includes a production-grade **trading bot foundation** implementing the core architecture from the v5 prompt:

- Fail-closed guard system (20 checks + expectancy/cooldown gates)
- Hurst + autocorrelation regime tooling
- Adaptive signal weighting and adaptive entry thresholds
- Composite signal pipeline with MTF gating behavior
- Portfolio heat, equity curve gating, and MAE/MFE stop utilities
- Partial-fill and overnight gap-risk handlers
- Walk-forward efficiency metric and simple backtest runner
- Regime state machine transitions and infrastructure health checks

## Quickstart

```bash
python -m pip install -e .[dev]
pytest
python main_backtest.py
python main_paper.py
python main_dry_run.py
python main_validate.py  # runs master_validation aggregate gate
python main_report.py  # writes RESEARCH_REPORT.md + GO_NO_GO_CHECKLIST.md
python main_live.py
python main_ui.py  # open http://localhost:8080
python main_start.py  # easiest: auto-opens browser + starts UI
```

## Structure

- `src/omega_quant/config.py`: v5 configuration fields
- `src/omega_quant/strategy/*`: regime + adaptive signal logic
- `src/omega_quant/risk/*`: risk rings core utilities and guard system
- `src/omega_quant/execution/*`: partial fills + gap-risk handlers + cost model + paper broker
- `src/omega_quant/research/*`: WFE, DSR/GT/RC/SPA proxies, Monte Carlo, CPCV/PBO proxy, factor decomposition, recovery factor, and backtest primitives
- `src/omega_quant/ops/*`: state persistence, logger, alerts, drift, health, and A/B utilities

## Note

This is a robust base implementation focused on correctness and fail-closed behavior, now including reconciliation, sentiment overlay, signal correlation guard, A/B testing utilities, and recovery-factor research metric. It remains ready to extend with broker adapters, richer data providers, and the full statistical research battery.


## Compliance & Release Gates

- `GO_NO_GO_CHECKLIST.md` contains the production release checklist aligned to v5 fail-closed policy.
- `main_live.py` enforces mandatory live-trading gates (env flag, confirmations, phase duration, risk acknowledgment, guard pass).


## Validation Aggregator

- `src/omega_quant/ops/master_validation.py` combines health, guard, research, drift, and live-gate checks into a single `release_ready` decision.


## Dummy-Proof UI (Button Based)

1. Run `python main_ui.py`.
2. Open `http://localhost:8080`.
3. Click **Run Full Validation** first (must pass safety).
4. Use **Paper Trading Mode** for safe simulation.
5. Use **Dry Run Execution** to test order logic without real trading.
6. Use **Check Live Gates** only after 45+ paper and 45+ micro-live days.

### About "wallet" / broker keys
- This repo currently uses a **paper broker simulator** by default.
- Do **not** enter real exchange keys until broker adapters and secrets storage are configured.
- Live mode remains fail-closed unless all gates are satisfied.


## Super Easy (Dummy-Proof) Run

1. Run: `python main_start.py`
2. Browser opens to the control panel automatically.
3. Click buttons in this order:
   - **Run Full Validation**
   - **Paper Trading Mode (Run Auto Trader)**
   - **View Paper Trade Reviews**

### How to know if a trade was successful
- The UI output includes `status` from pipeline cycle:
  - `TRADE` = order filled
  - `NO_FILL` = signal passed but no fill
  - `NO_TRADE` = signal/size gate blocked
  - `HALT` = fail-closed safety stopped trading
- Detailed paper reviews are saved to:
  - `artifacts/paper_trades.jsonl`
  - `artifacts/paper_trade_reviews.md`
- Use **View Paper Trade Reviews** button to see per-cycle reason, score, and threshold.


### Configure paper capital (important)
- In UI, set:
  - **Paper Start $** (your starting paper balance)
  - **Paper Cycles** (more cycles = more simulated trades)
- Then click **Paper Trading Mode (Run Auto Trader)**.

### Proof files generated each paper run
- `artifacts/paper_cycle_result.json` → raw per-trade numbers
- `artifacts/paper_proof_report.md` → human-readable proof table
- `artifacts/paper_trade_reviews.md` → reason log per trade

## Reality Upgrade Notes

- Historical paper mode is forward-time and fail-closed; decisions use bars up to `i-1` and fills use real market bar closes at `i`.
- Paper equity is persisted in `artifacts/paper_account.sqlite` and does **not** reset between runs unless `Reset Paper Account` is used.
- `Verify Proof Integrity` recomputes equity from the ledger and blocks future paper runs if verification fails.
- Live monitor is read-only (`shadow_decision`) and does not place orders.

### Windows PowerShell quickstart

```powershell
python -m pip install -e .[dev]
$env:PYTHONPATH = "src"
python main_ui.py
```

### Core commands

```powershell
$env:PYTHONPATH = "src"
python main_paper.py --capital 5000 --cycles 2
python -c "from omega_quant.ops.proof_check import verify_paper_result; print(verify_paper_result())"
python scripts/make_audit_pack.py
pytest -q
```
