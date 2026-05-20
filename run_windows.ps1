Write-Host "Starting PhotoConverter..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Install Python 3.11+ and try again." -ForegroundColor Red
    exit 1
}

$reqs = Join-Path $PSScriptRoot "requirements.txt"
python -m pip install -q -r $reqs

python (Join-Path $PSScriptRoot "main.py")
