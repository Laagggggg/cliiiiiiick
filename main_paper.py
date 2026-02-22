from __future__ import annotations

import argparse
import sys

sys.path.insert(0, 'src')

from omega_quant.ops.paper_cycle import run_paper_cycle
from omega_quant.ops.env_loader import load_dotenv_if_present
from omega_quant.ops.repo_guard import ensure_repo_root_or_exit


if __name__ == "__main__":
    load_dotenv_if_present()
    ensure_repo_root_or_exit("main_paper.py")
    parser = argparse.ArgumentParser(description="Run paper trading cycle")
    parser.add_argument("--capital", type=float, default=5000.0, help="Starting paper capital")
    parser.add_argument("--cycles", type=int, default=1, help="Number of synthetic price cycles")
    args = parser.parse_args()

    print(run_paper_cycle(starting_capital=args.capital, cycles=args.cycles))
