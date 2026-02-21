from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import json

from omega_quant.ui_service import run_action

HTML = """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>OMEGA-QUANT v5 Control Panel</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; max-width: 1100px; }
    .card { border:1px solid #ccc; border-radius:10px; padding:14px; margin-bottom:12px; }
    button { margin: 4px 6px 4px 0; padding: 8px 12px; }
    pre { background: #111; color: #0f0; padding: 12px; border-radius: 8px; overflow: auto; }
    .warn { color: #a00; }
    .metric { font-size: 1.1rem; margin: 4px 0; }
  </style>
</head>
<body>
  <h1>OMEGA-QUANT v5 — Paper Trading Console</h1>
  <p class='warn'><strong>Warning:</strong> Live trading is blocked unless all safety gates pass.</p>

  <div class='card'>
    <h3>Profit Box (Persistent Paper Account)</h3>
    <div class='metric'>Current Equity: <strong id='equity'>$-</strong></div>
    <div class='metric'>Trades Filled: <strong id='trades'>-</strong></div>
    <div class='metric'>Win Rate: <strong id='winrate'>-</strong></div>
    <button onclick="refreshAccount()">Refresh Account</button>
  </div>

  <div class='card'>
    <h3>Paper Cycle Controls</h3>
    <label>Paper Start $ (used only for reset/first run): <input id='starting_capital' value='5000'></label>
    <label>Cycles: <input id='cycles' value='2'></label><br>
    <button onclick="runPaper()">Run N Cycles</button>
    <button onclick="runAction('proof_check')">Verify Proof</button>
    <button onclick="runAction('paper_review')">View Paper Trade Reviews</button>
    <button onclick="runAction('download_audit_pack')">Download Audit Pack</button>
    <button onclick="resetPaper()">Reset Paper Account</button>
  </div>

  <div class='card'>
    <h3>Monitoring</h3>
    <button onclick="runAction('validate')">Run Full Validation</button>
    <button onclick="runAction('report')">Generate Reports</button>
    <button onclick="runAction('live_monitor')">Live Monitor</button>
    <button onclick="runAction('dry_run')">Dry Run Execution</button>
  </div>

  <div class='card'>
    <h3>Live Readiness Check (does NOT place real orders)</h3>
    <label>Confirm Live: <input id='confirm_live' value='true'></label><br>
    <label>Risk Acknowledgement: <input id='risk_ack' value='I UNDERSTAND THIS SYSTEM CAN AND WILL LOSE MONEY'></label><br>
    <label>Paper Days: <input id='paper_days' value='45'></label>
    <label>Micro-live Days: <input id='micro_live_days' value='45'></label><br>
    <button onclick="runLiveCheck()">Check Live Gates</button>
  </div>

  <div class='card'>
    <h3>Output</h3>
    <pre id='out'>Click a button…</pre>
  </div>

<script>
async function runAction(action){
  const resp = await fetch('/api/run', {
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:`action=${encodeURIComponent(action)}`
  });
  const payload = await resp.json();
  document.getElementById('out').textContent = JSON.stringify(payload, null, 2);
  if (action === 'paper' || action === 'paper_account' || action === 'reset_paper') { await refreshAccount(); }
}

async function runPaper(){
  const starting_capital = document.getElementById('starting_capital').value;
  const cycles = document.getElementById('cycles').value;
  const body = `action=paper&starting_capital=${encodeURIComponent(starting_capital)}&cycles=${encodeURIComponent(cycles)}`;
  const resp = await fetch('/api/run', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body });
  document.getElementById('out').textContent = JSON.stringify(await resp.json(), null, 2);
  await refreshAccount();
}

async function resetPaper(){
  const starting_capital = document.getElementById('starting_capital').value;
  const body = `action=reset_paper&starting_capital=${encodeURIComponent(starting_capital)}`;
  const resp = await fetch('/api/run', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body });
  document.getElementById('out').textContent = JSON.stringify(await resp.json(), null, 2);
  await refreshAccount();
}

async function refreshAccount(){
  const resp = await fetch('/api/run', {
    method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:'action=paper_account'
  });
  const payload = await resp.json();
  const acct = payload.account || {};
  document.getElementById('equity').textContent = `$${Number(acct.equity || 0).toFixed(2)}`;
  document.getElementById('trades').textContent = acct.trade_count ?? 0;
  document.getElementById('winrate').textContent = `${Number(acct.win_rate_pct || 0).toFixed(2)}%`;
}

async function runLiveCheck(){
  const confirm_live = document.getElementById('confirm_live').value === 'true';
  const risk_ack = document.getElementById('risk_ack').value;
  const paper_days = document.getElementById('paper_days').value;
  const micro_live_days = document.getElementById('micro_live_days').value;
  const body = `action=live_check&confirm_live=${encodeURIComponent(confirm_live)}&risk_ack=${encodeURIComponent(risk_ack)}&paper_days=${encodeURIComponent(paper_days)}&micro_live_days=${encodeURIComponent(micro_live_days)}`;
  const resp = await fetch('/api/run', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body });
  document.getElementById('out').textContent = JSON.stringify(await resp.json(), null, 2);
}

refreshAccount();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj: dict, status: int = 200) -> None:
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            payload = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self._send_json({"error": "not_found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(body)
        action = form.get("action", [""])[0]
        params = {
            "confirm_live": form.get("confirm_live", ["false"])[0] == "true",
            "risk_ack": form.get("risk_ack", [""])[0],
            "paper_days": form.get("paper_days", ["0"])[0],
            "micro_live_days": form.get("micro_live_days", ["0"])[0],
            "starting_capital": form.get("starting_capital", ["5000"])[0],
            "cycles": form.get("cycles", ["1"])[0],
        }
        self._send_json(run_action(action, params))


def main() -> None:
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    print("UI running on http://localhost:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
