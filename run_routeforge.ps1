$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv313\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python 3.13 environment not found. Create it with: py -3.13 -m venv .venv313"
}

& $python -m streamlit run (Join-Path $PSScriptRoot "app.py")
