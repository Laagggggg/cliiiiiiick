from __future__ import annotations

import argparse

from omega_quant.ops.paper_cycle import run_paper_cycle


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run paper trading cycle")
    parser.add_argument("--capital", type=float, default=5000.0, help="Starting paper capital")
    parser.add_argument("--cycles", type=int, default=1, help="Number of synthetic price cycles")
    args = parser.parse_args()

    print(run_paper_cycle(starting_capital=args.capital, cycles=args.cycles))
