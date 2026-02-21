from __future__ import annotations

from omega_quant.live_gates import live_gates


if __name__ == "__main__":
    result = live_gates(confirm_live=False, risk_ack="", paper_days=0, micro_live_days=0)
    print(result)
