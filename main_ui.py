from __future__ import annotations

import sys

sys.path.insert(0, 'src')

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import json

from omega_quant.ui_service import run_action

HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>OMEGA QUANT Proof Terminal</title>
<style>body{font-family:Arial;margin:18px;max-width:1280px}.card{border:1px solid #ccc;border-radius:10px;padding:12px;margin-bottom:10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}button{margin:3px;padding:8px}pre{background:#111;color:#0f0;padding:10px;border-radius:8px;overflow:auto}.danger{color:#a00}.banner{background:#222;color:#fff;padding:10px;border-radius:8px;margin-bottom:10px}</style>
</head><body>
<h1>OMEGA-QUANT ULTRA — Proof Terminal</h1>
<div class='banner'>MODE_TRUTH=<b id='mode_truth'>-</b> | TRANSPORT=<b id='transport'>-</b> | PRIMARY=<b id='primary'>-</b> | SECONDARY=<b id='secondary'>-</b> | RECON=<b id='recon'>-</b> | FRESHNESS_SECONDS=<b id='fresh'>-</b> | LAST_BAR_TS=<b id='last_bar_ts'>-</b> | NEXT_ACTION=<b id='next_action'>-</b></div>
<p class='danger'><b>Fail-Closed:</b> paper runs blocked when proof verification fails.</p>
<div class='grid'>
<div class='card'><h3>Profit Box</h3><div>Current Equity: <b id='equity'>$-</b></div><div>Initial Equity: <b id='initial'>$-</b></div><div>Session P&L: <b id='session_pnl'>-</b></div><div>Total Return %: <b id='ret'>-</b></div><div>Realized/Unrealized: <b id='ru'>-</b></div></div>
<div class='card'><h3>Trade Stats</h3><div>Filled Trades: <b id='trades'>-</b></div><div>Win Rate: <b id='win'>-</b></div><div>Avg Win/Loss: <b id='awl'>-</b></div><div>Expectancy: <b id='exp'>-</b></div><div>Profit Factor: <b id='pf'>-</b></div></div>
<div class='card'><h3>Last Decision</h3><div id='decision'>-</div></div>
<div class='card'><h3>Data Provenance</h3><div id='prov'>-</div></div>
</div>
<div class='card'><h3>Actions</h3>
<label>Paper Start $ <input id='starting_capital' value='5000'></label>
<label>Cycles/Steps <input id='cycles' value='2'></label><br>
<button onclick='runWizard()'>First-Run Wizard</button>
<button onclick='resetPaper()'>Reset Paper Account</button>
<button onclick='runPaper(1)'>Historical Sim Run (1)</button>
<button onclick='runPaper()'>Historical Sim Run (N)</button>
<button onclick='runBroker()'>Broker Paper Run (N)</button>
<button onclick='runBrokerDaemon(30)'>Broker Daemon 30s</button>
<button onclick='runBrokerDaemon(300)'>Broker Daemon 5m</button>
<button onclick="runAction('proof_check')">Verify Proof</button>
<button onclick="runAction('download_audit_pack')">Download Audit Pack</button>
<button onclick="runAction('api_doctor')">Run API Doctor</button>
<button onclick="runAction('live_monitor')">Live Monitor (Polling)</button>
<button onclick="runAction('websocket_monitor')">Live Monitor (Websocket)</button>
<button onclick="runAction('replay_live_stream')">Replay Live Stream</button>
</div>
<div class='card'><h3>Charts</h3><a href='artifacts/equity_curve.png'>equity_curve.png</a> | <a href='artifacts/drawdown.png'>drawdown.png</a> | <a href='artifacts/trade_markers.png'>trade_markers.png</a></div>
<div class='card'><h3>Output</h3><pre id='out'>Ready</pre></div>
<script>
function fmt(n){return Number(n||0).toFixed(2)}
async function api(body){const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});return await r.json();}
async function runAction(action){const p=await api(`action=${encodeURIComponent(action)}`);document.getElementById('out').textContent=JSON.stringify(p,null,2);if(action.includes('monitor')) setTruthFromMonitor(p); await refresh();}

async function runWizard(){
  const s=document.getElementById('starting_capital').value;
  const c=document.getElementById('cycles').value;
  const steps=[];
  steps.push({step:'doctor', out: await api('action=api_doctor')});
  steps.push({step:'reset_paper', out: await api(`action=reset_paper&starting_capital=${encodeURIComponent(s)}`)});
  steps.push({step:'paper', out: await api(`action=paper&starting_capital=${encodeURIComponent(s)}&cycles=${encodeURIComponent(c)}`)});
  steps.push({step:'proof_check', out: await api('action=proof_check')});
  steps.push({step:'download_audit_pack', out: await api('action=download_audit_pack')});
  document.getElementById('out').textContent=JSON.stringify({wizard:'complete',steps},null,2);
  await refresh();
}
async function runPaper(c1){const c=c1||document.getElementById('cycles').value;const s=document.getElementById('starting_capital').value;const p=await api(`action=paper&starting_capital=${encodeURIComponent(s)}&cycles=${encodeURIComponent(c)}`);document.getElementById('out').textContent=JSON.stringify(p,null,2);await refresh();}
async function runBroker(){const c=document.getElementById('cycles').value;const p=await api(`action=broker_paper_run&steps=${encodeURIComponent(c)}`);document.getElementById('out').textContent=JSON.stringify(p,null,2);await refresh();}
async function runBrokerDaemon(seconds){const p=await api(`action=broker_paper_daemon&seconds=${encodeURIComponent(seconds)}&interval=5`);document.getElementById('out').textContent=JSON.stringify(p,null,2);await refresh();}
async function resetPaper(){const s=document.getElementById('starting_capital').value;const p=await api(`action=reset_paper&starting_capital=${encodeURIComponent(s)}`);document.getElementById('out').textContent=JSON.stringify(p,null,2);await refresh();}
function setTruth(p){const prov=(p.provenance||{});document.getElementById('mode_truth').textContent=p.mode_truth||'SIMULATED FILLS';document.getElementById('transport').textContent=p.transport||'POLLING (run websocket monitor)';document.getElementById('primary').textContent=p.provider_primary||(prov.source_primary||'fallback (run monitor)');document.getElementById('secondary').textContent=p.provider_secondary||(prov.source_secondary||'none');const r=(p.reconciliation||(prov.reconciliation)||{});document.getElementById('recon').textContent=(r.passed===undefined||r.passed===null)?'unknown (run broker daemon)':`${r.passed?'PASS':'FAIL'} max_diff_pct=${r.max_diff_pct??'n/a'}`;document.getElementById('fresh').textContent=(p.freshness_seconds??prov.freshness_seconds??'not loaded (run monitor)');document.getElementById('last_bar_ts').textContent=(p.last_bar_ts??prov.end??'UNKNOWN (run monitor)');document.getElementById('next_action').textContent=(p.next_action??'Run API Doctor');}
function setTruthFromMonitor(p){setTruth({mode_truth:p.mode_truth,transport:p.transport,provider_primary:p.provider_primary||p.source,provider_secondary:p.provider_secondary||p.source_secondary,reconciliation:p.reconciliation,freshness_seconds:p.freshness_seconds,last_bar_ts:p.last_bar_ts});}
async function refresh(){const p=await api('action=paper_account');const a=p.account||{};setTruth(p);document.getElementById('equity').textContent=`$${fmt(a.equity)}`;document.getElementById('initial').textContent=`$${fmt(a.initial_equity)}`;document.getElementById('session_pnl').textContent=fmt((a.equity||0)-(a.initial_equity||0));document.getElementById('ret').textContent=`${fmt(a.return_pct)}%`;document.getElementById('ru').textContent=`${fmt(a.realized_pnl)} / ${fmt(a.unrealized_pnl)}`;document.getElementById('trades').textContent=a.trade_count??0;document.getElementById('win').textContent=`${fmt(a.win_rate_pct)}%`;document.getElementById('awl').textContent=`${fmt(a.avg_win)} / ${fmt(a.avg_loss)}`;document.getElementById('exp').textContent=fmt(a.expectancy);document.getElementById('pf').textContent=fmt(a.profit_factor);document.getElementById('decision').textContent=JSON.stringify(p.last_decision||{});document.getElementById('prov').textContent=JSON.stringify(p.provenance||{});}refresh();
</script></body></html>
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
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload); return
        if self.path.startswith("/artifacts/"):
            p = self.path.lstrip("/")
            try:
                data = open(p, "rb").read(); self.send_response(200); self.send_header("Content-Type", "image/png"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            except FileNotFoundError:
                pass
        self.send_response(404); self.end_headers()
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run": self._send_json({"error": "not_found"}, 404); return
        length = int(self.headers.get("Content-Length", "0")); body = self.rfile.read(length).decode("utf-8"); form = parse_qs(body)
        action = form.get("action", [""])[0]
        params = {"confirm_live": form.get("confirm_live", ["false"])[0] == "true", "risk_ack": form.get("risk_ack", [""])[0], "paper_days": form.get("paper_days", ["0"])[0], "micro_live_days": form.get("micro_live_days", ["0"])[0], "starting_capital": form.get("starting_capital", ["5000"])[0], "cycles": form.get("cycles", ["1"])[0], "steps": form.get("steps", ["1"])[0], "seconds": form.get("seconds", ["30"])[0], "interval": form.get("interval", ["5"])[0]}
        self._send_json(run_action(action, params))

def main() -> None:
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    print("UI running on http://localhost:8080")
    server.serve_forever()

if __name__ == "__main__":
    main()
