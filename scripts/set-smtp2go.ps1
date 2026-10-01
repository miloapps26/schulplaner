$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  throw ".env nicht gefunden."
}

$smtpUser = Read-Host "SMTP2GO SMTP username"
$securePassword = Read-Host "SMTP2GO SMTP password" -AsSecureString
$from = Read-Host "Absenderadresse" 
$replyTo = Read-Host "Reply-To Adresse, leer = Absenderadresse"
$to = Read-Host "Empfaengeradresse(n), Komma getrennt"
if (-not $replyTo) {
  $replyTo = $from
}

$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
$smtpPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto($passwordPtr)

try {
  $values = @{
    "SMTP_HOST" = "mail.smtp2go.com"
    "SMTP_PORT" = "2525"
    "SMTP_USERNAME" = $smtpUser
    "SMTP_PASSWORD" = $smtpPassword
    "SMTP_FROM" = $from
    "SMTP_REPLY_TO" = $replyTo
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
  Write-Host "SMTP2GO-Konfiguration wurde in .env gesetzt."
} finally {
  if ($passwordPtr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
  }
  $smtpPassword = $null
}
