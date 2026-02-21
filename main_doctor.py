from __future__ import annotations

import os
import subprocess


def run(cmd: str) -> tuple[bool, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def api_doctor() -> tuple[bool, str]:
    required = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        return False, f"BROKER DISABLED / USING FALLBACK DATA (missing env: {missing})"

    cmd = "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker\nfrom omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider\nb=AlpacaPaperBroker(); print('account', bool(b.get_account().get('id')))\np=AlpacaMarketDataProvider(); print('bars', len(p.get_bars('SPY','1h',limit=100))); print('quote', p.get_quote('SPY') is not None)\nPY"
    return run(cmd)


def main() -> int:
    checks = [
        ("compile", "python -m py_compile $(rg --files -g '*.py')"),
        ("tests", "pytest -q"),
        ("paper", "PYTHONPATH=src python main_paper.py --capital 3000 --cycles 1"),
        ("proof", "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.ops.proof_check import verify_paper_result\nprint(verify_paper_result())\nPY"),
    ]
    ok_all = True
    for name, cmd in checks:
        ok, out = run(cmd)
        print(f"[{name}] {'PASS' if ok else 'FAIL'}")
        print(out)
        print('-' * 60)
        ok_all = ok_all and ok

    aok, aout = api_doctor()
    print(f"[api_doctor] {'PASS' if aok else 'WARN'}")
    print(aout)
    print('-' * 60)
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
