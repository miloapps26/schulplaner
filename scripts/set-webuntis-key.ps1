$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  throw ".env nicht gefunden."
}

$secure = Read-Host "WebUntis App-/QR-Schluessel" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
)

try {
  $content = Get-Content -Raw -LiteralPath $envPath
  if ($content -match "(?m)^WEBUNTIS_APP_SECRET=") {
    $content = $content -replace "(?m)^WEBUNTIS_APP_SECRET=.*$", "WEBUNTIS_APP_SECRET=$plain"
  } else {
    $content = $content.TrimEnd() + "`r`nWEBUNTIS_APP_SECRET=$plain`r`n"
  }
  Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8
  Write-Host "WEBUNTIS_APP_SECRET wurde in .env gesetzt."
} finally {
  if ($plain) {
    $plain = $null
  }
}
