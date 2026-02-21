from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from omega_quant.ui_service import run_action

HTML = """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>OMEGA-QUANT v5 Control Panel</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 0 16px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 14px; }
    button { padding: 10px 14px; margin: 4px; border-radius: 6px; border: 1px solid #333; cursor: pointer; }
    input { padding: 8px; margin: 4px; width: 220px; }
    pre { background: #111; color: #0f0; padding: 12px; border-radius: 8px; overflow: auto; }
    .warn { color: #a00; }
  </style>
</head>
<body>
  <h1>OMEGA-QUANT v5 — Dummy-Proof Control Panel</h1>
  <p class='warn'><strong>Warning:</strong> Live trading is blocked unless all safety gates pass.</p>

  <div class='card'>
    <h3>1) Safe actions</h3>
    <button onclick="runAction('validate')">Run Full Validation</button>
    <button onclick="runAction('report')">Generate Reports</button>
    <label>Paper Start $: <input id='starting_capital' value='5000'></label>
    <label>Paper Cycles: <input id='cycles' value='2'></label><br>
    <button onclick="runPaper()">Paper Trading Mode (Run Auto Trader)</button>
    <button onclick="runAction('paper_review')">View Paper Trade Reviews</button>
    <button onclick="runAction('proof_check')">Verify Proof Integrity</button>
    <button onclick="runAction('dry_run')">Dry Run Execution</button>
  </div>

  <div class='card'>
    <h3>2) Live Readiness Check (does NOT place real orders)</h3>
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
  document.getElementById('out').textContent = JSON.stringify(await resp.json(), null, 2);
}
async function runPaper(){
  const starting_capital = document.getElementById('starting_capital').value;
  const cycles = document.getElementById('cycles').value;
  const body = `action=paper&starting_capital=${encodeURIComponent(starting_capital)}&cycles=${encodeURIComponent(cycles)}`;
  const resp = await fetch('/api/run', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body });
  document.getElementById('out').textContent = JSON.stringify(await resp.json(), null, 2);
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
