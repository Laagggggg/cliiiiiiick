from __future__ import annotations

import argparse

from omega_quant.ops.broker_paper_cycle import run_broker_paper_cycle


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=1)
    args = p.parse_args()
    print(run_broker_paper_cycle(steps=args.steps))


if __name__ == "__main__":
    main()
