$ErrorActionPreference = "Stop"
$env:PYTHONPATH = Join-Path (Get-Location) "src"
& ".\.venv\Scripts\python.exe" -m milo_webuntis.app
