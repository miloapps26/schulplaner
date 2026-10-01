$ErrorActionPreference = "Stop"
$env:PYTHONPATH = Join-Path (Get-Location) "src"
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests
