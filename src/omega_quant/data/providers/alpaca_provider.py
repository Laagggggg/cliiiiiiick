from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from omega_quant.config.alpaca_config import get_alpaca_config
from omega_quant.data.providers.base import Bar, MarketDataProvider, Quote


class AlpacaMarketDataProvider(MarketDataProvider):
    def __init__(self) -> None:
        cfg = get_alpaca_config()
        self.key = cfg["api_key"]
        self.secret = cfg["api_secret"]
        self.base = cfg["data_base_url"]

    def source_name(self) -> str:
        return "alpaca"

    def _headers(self) -> dict[str, str]:
        if not self.key or not self.secret:
            raise RuntimeError("missing alpaca keys")
        return {"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret}

    def _get_json(self, path: str, query: dict[str, str]) -> dict:
        url = f"{self.base}{path}?{urlencode(query)}"
        req = Request(url, headers=self._headers())
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:  # noqa: PERF203
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"alpaca http error {exc.code}: {body}") from exc

    def get_bars(self, symbol: str, timeframe: str, limit: int = 300) -> list[Bar]:
        tf = "1Hour" if timeframe == "1h" else "1Day"
        payload = self._get_json(f"/v2/stocks/{symbol}/bars", {"timeframe": tf, "limit": str(limit), "feed": "iex"})
        bars = payload.get("bars", [])
        return [
            Bar(timestamp=b["t"], open=float(b["o"]), high=float(b["h"]), low=float(b["l"]), close=float(b["c"]), volume=float(b["v"]))
            for b in bars
        ]

    def get_latest_bar(self, symbol: str, timeframe: str) -> Bar:
        payload = self._get_json(f"/v2/stocks/{symbol}/bars/latest", {"feed": "iex"})
        b = payload.get("bar")
        if not b:
            raise RuntimeError("latest bar unavailable")
        return Bar(timestamp=b["t"], open=float(b["o"]), high=float(b["h"]), low=float(b["l"]), close=float(b["c"]), volume=float(b["v"]))

    def get_quote(self, symbol: str) -> Quote | None:
        payload = self._get_json(f"/v2/stocks/{symbol}/quotes/latest", {"feed": "iex"})
        q = payload.get("quote")
        if not q:
            return None
        return Quote(timestamp=q["t"], bid=float(q["bp"]), ask=float(q["ap"]))

    def freshness_seconds(self, bar_ts: str) -> int:
        ts = datetime.fromisoformat(bar_ts.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - ts).total_seconds())
