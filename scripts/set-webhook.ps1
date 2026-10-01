$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  throw ".env nicht gefunden."
}

$webhookUrl = Read-Host "Make Webhook URL"
if (-not $webhookUrl) {
  throw "Keine Webhook-URL eingegeben."
}

$content = Get-Content -Raw -LiteralPath $envPath
if ($content -match "(?m)^NOTIFICATION_WEBHOOK_URL=") {
  $content = $content -replace "(?m)^NOTIFICATION_WEBHOOK_URL=.*$", "NOTIFICATION_WEBHOOK_URL=$webhookUrl"
} else {
  $content = $content.TrimEnd() + "`r`nNOTIFICATION_WEBHOOK_URL=$webhookUrl`r`n"
}

Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8
Write-Host "Webhook-URL wurde in .env gesetzt."
