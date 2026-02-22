$ErrorActionPreference = "Stop"

function Require-File($path, $msg) {
  if (-not (Test-Path $path)) { throw $msg }
}

# Find repo root containing pyproject.toml
$root = Get-Location
while ($null -ne $root -and -not (Test-Path (Join-Path $root "pyproject.toml"))) {
  $root = $root.Parent
}
if ($null -eq $root) { throw "Could not find repo root (pyproject.toml)." }
Set-Location $root

Require-File "pyproject.toml" "pyproject.toml missing. Open the repository root first."

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .[dev]
$env:PYTHONPATH = "src"

python -m compileall src
python main_doctor.py
python main_ui.py
