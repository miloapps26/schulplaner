$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  throw ".env nicht gefunden."
}

$address = Read-Host "GMX Adresse"
if (-not $address) {
  $address = "stundenplaninfo@gmx.de"
}

$securePassword = Read-Host "GMX Passwort" -AsSecureString
$to = Read-Host "Empfaengeradresse(n), Komma getrennt"
if (-not $to) {
  $to = "eltern@example.com"
}

$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
$smtpPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto($passwordPtr)

try {
  $values = @{
    "SMTP_HOST" = "mail.gmx.net"
    "SMTP_PORT" = "587"
    "SMTP_USERNAME" = $address
    "SMTP_PASSWORD" = $smtpPassword
    "SMTP_FROM" = "Schulplaner <$address>"
    "SMTP_REPLY_TO" = ""
    "SMTP_USE_TLS" = "true"
    "EMAIL_TO" = $to
  }

  $content = Get-Content -Raw -LiteralPath $envPath
  foreach ($key in $values.Keys) {
    $value = $values[$key]
    if ($content -match "(?m)^$key=") {
      $content = $content -replace "(?m)^$key=.*$", "$key=$value"
    } else {
      $content = $content.TrimEnd() + "`r`n$key=$value`r`n"
    }
  }

  Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8
  Write-Host "GMX-Konfiguration wurde in .env gesetzt."
} finally {
  if ($passwordPtr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
  }
  $smtpPassword = $null
}
