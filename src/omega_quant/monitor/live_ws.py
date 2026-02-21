from __future__ import annotations


def run_live_websocket(symbol: str = "SPY") -> dict:
    """Best-effort websocket monitor probe.

    Returns FAIL-safe fallback directive when websocket transport is unavailable.
    """
    try:
        import websockets  # type: ignore  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "transport": "WEBSOCKET FAILED -> POLLING",
            "reason": f"websocket_dependency_unavailable:{exc}",
            "symbol": symbol,
        }

    # Runtime websocket handshake intentionally conservative: if not explicitly wired,
    # fail closed to polling.
    return {
        "ok": False,
        "transport": "WEBSOCKET FAILED -> POLLING",
        "reason": "websocket_not_configured_in_this_environment",
        "symbol": symbol,
    }
