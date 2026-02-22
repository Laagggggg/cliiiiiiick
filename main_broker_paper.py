from __future__ import annotations

import sys

sys.path.insert(0, 'src')

import argparse

from omega_quant.ops.broker_paper_cycle import run_broker_paper_cycle
from omega_quant.ops.broker_paper_daemon import run_broker_paper_daemon


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=1)
    p.add_argument("--daemon", action="store_true")
    p.add_argument("--seconds", type=int, default=30)
    p.add_argument("--interval", type=int, default=5)
    args = p.parse_args()
    if args.daemon:
        print(run_broker_paper_daemon(seconds=args.seconds, interval_s=args.interval))
    else:
        print(run_broker_paper_cycle(steps=args.steps))


if __name__ == "__main__":
    main()
