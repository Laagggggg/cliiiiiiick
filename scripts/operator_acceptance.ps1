$ErrorActionPreference = "Stop"

function Step($name, $cmd) {
  Write-Host "==> $name"
  iex $cmd
}

try {
  Step "RUN_ME" "./RUN_ME.ps1"
  Step "doctor" "python main_doctor.py"
  Step "make live verified" "python -c \"import sys;sys.path.insert(0,'src');from omega_quant.ui_service import run_action;print(run_action('make_live_verified',{}))\""
  Step "broker daemon 60s" "python -c \"import sys;sys.path.insert(0,'src');from omega_quant.ops.broker_paper_daemon import run_broker_paper_daemon;print(run_broker_paper_daemon(seconds=60, interval_s=5))\""
  Step "audit pack" "python scripts/make_audit_pack.py"
  Write-Host "PASS: operator acceptance complete"
} catch {
  Write-Host "HALT: $($_.Exception.Message)"
  Write-Host "NEXT_ACTION: inspect failing step output, rerun doctor, and verify keys/dependencies"
  exit 1
}
