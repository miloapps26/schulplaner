$ErrorActionPreference = "Stop"

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  throw ".env nicht gefunden."
}

$username = Read-Host "Admin Benutzername"
if (-not $username) {
  $username = "admin"
}

$securePassword = Read-Host "Admin Passwort" -AsSecureString
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
$adminPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto($passwordPtr)
if (-not $adminPassword) {
  throw "Admin Passwort darf nicht leer sein."
}

try {
  $values = @{
    "ADMIN_USERNAME" = $username
    "ADMIN_PASSWORD" = $adminPassword
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
  Write-Host "Admin-Login wurde in .env gesetzt."
} finally {
  if ($passwordPtr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
  }
  $adminPassword = $null
}
