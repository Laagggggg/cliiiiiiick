from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class AlpacaPaperBroker:
    def __init__(self) -> None:
        self.key = os.getenv("ALPACA_API_KEY", "")
        self.secret = os.getenv("ALPACA_API_SECRET", "")
        self.base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        self._last_call_ts = 0.0

    def enabled(self) -> bool:
        return bool(self.key and self.secret)

    def _headers(self) -> dict[str, str]:
        if not self.enabled():
            raise RuntimeError("broker disabled: missing ALPACA keys")
        return {
            "APCA-API-KEY-ID": self.key,
            "APCA-API-SECRET-KEY": self.secret,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, payload: dict | None = None, query: dict[str, str] | None = None) -> dict | list:
        q = f"?{urlencode(query)}" if query else ""
        url = f"{self.base}{path}{q}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        for attempt in range(4):
            now = time.time()
            if now - self._last_call_ts < 0.2:
                time.sleep(0.2 - (now - self._last_call_ts))
            self._last_call_ts = time.time()
            req = Request(url, data=data, headers=self._headers(), method=method)
            try:
                with urlopen(req, timeout=20) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="ignore")
                if exc.code == 429 and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"alpaca broker error {exc.code}: {body}") from exc

        raise RuntimeError("alpaca broker error: retries_exhausted")

    def get_account(self) -> dict:
        return self._request("GET", "/v2/account")  # type: ignore[return-value]

    def list_orders(self, status: str = "open", limit: int = 50) -> list[dict]:
        out = self._request("GET", "/v2/orders", query={"status": status, "limit": str(limit), "direction": "desc"})
        return out if isinstance(out, list) else []

    def list_positions(self) -> list[dict]:
        out = self._request("GET", "/v2/positions")
        return out if isinstance(out, list) else []

    def place_market_order(self, symbol: str, side: str, qty: float, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": "market",
            "time_in_force": "day",
        }
        if client_order_id:
            payload["client_order_id"] = client_order_id
        return self._request("POST", "/v2/orders", payload)  # type: ignore[return-value]

    def get_order(self, order_id: str) -> dict:
        return self._request("GET", f"/v2/orders/{order_id}")  # type: ignore[return-value]

    def get_order_by_client_id(self, client_order_id: str) -> dict | None:
        try:
            return self._request("GET", "/v2/orders:by_client_order_id", query={"client_order_id": client_order_id})  # type: ignore[return-value]
        except Exception:  # noqa: BLE001
            return None
