$ErrorActionPreference = "Stop"

function Halt-Step($Reason, $NextAction) {
  Write-Host "HALT: $Reason" -ForegroundColor Red
  Write-Host "NEXT_ACTION: $NextAction" -ForegroundColor Yellow
  exit 1
}

try {
  if (-not (Test-Path "pyproject.toml")) {
    Halt-Step "pyproject.toml not found in current directory." "PowerShell: cd <repo_root_with_pyproject>; .\\RUN_ME.ps1"
  }

  if (-not (Test-Path ".venv")) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Halt-Step "Failed to create .venv." "Install Python 3.11+ and rerun .\\RUN_ME.ps1" }
  }

  . .\.venv\Scripts\Activate.ps1
  if ($LASTEXITCODE -ne 0) { Halt-Step "Failed to activate .venv." "Run PowerShell as user with script execution enabled, then rerun." }

  python -m pip install -U pip
  if ($LASTEXITCODE -ne 0) { Halt-Step "pip upgrade failed." "Check internet/pip config, then rerun .\\RUN_ME.ps1" }

  python -m pip install -e .[dev]
  if ($LASTEXITCODE -ne 0) { Halt-Step "Dependency install failed." "Review pip error output, fix package issues, rerun .\\RUN_ME.ps1" }

  $env:PYTHONPATH = "src"

  python -m compileall -q .
  if ($LASTEXITCODE -ne 0) { Halt-Step "Compile check failed." "Run: python -m compileall -q . and fix syntax errors." }

  pytest -q
  if ($LASTEXITCODE -ne 0) { Halt-Step "pytest failed." "Run: pytest -q, fix failing tests, rerun .\\RUN_ME.ps1" }

  python main_doctor.py
  if ($LASTEXITCODE -ne 0) { Halt-Step "Doctor checks failed." "Run: python main_doctor.py and resolve reported errors." }

  python main_ui.py
  if ($LASTEXITCODE -ne 0) { Halt-Step "UI launch failed." "Run: python main_ui.py and resolve startup error." }
}
catch {
  Halt-Step $_.Exception.Message "Review error and rerun .\\RUN_ME.ps1 from repo root."
}
