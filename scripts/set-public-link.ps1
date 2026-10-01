$ErrorActionPreference = "Stop"

function New-RandomHex {
  param(
    [Parameter(Mandatory = $true)]
    [int]$ByteCount
  )

  $bytes = New-Object byte[] $ByteCount
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  } finally {
    $rng.Dispose()
  }

  return -join ($bytes | ForEach-Object { $_.ToString("x2") })
}

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  throw ".env nicht gefunden."
}

$publicUrl = Read-Host "Oeffentliche Stundenplan-URL, z.B. https://stundenplan.example.de"
if (-not $publicUrl) {
  throw "Keine URL eingegeben."
}

$publicUri = [Uri]$publicUrl
if (-not $publicUri.IsAbsoluteUri -or -not $publicUri.Host) {
  throw "Bitte eine vollstaendige URL mit https:// und Hostnamen eingeben."
}

$tokenInput = Read-Host "Elternlink Token, leer = automatisch erzeugen"
if ($tokenInput) {
  $token = $tokenInput
} else {
  $token = New-RandomHex -ByteCount 24
}

$values = @{
  "PUBLIC_TIMETABLE_URL" = $publicUrl
  "PUBLIC_TIMETABLE_TOKEN" = $token
  "ALLOWED_HOSTS" = $publicUri.Host
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

$separator = "?"
if ($publicUrl.Contains("?")) {
  $separator = "&"
}
Write-Host "Elternlink wurde gesetzt:"
Write-Host "$publicUrl${separator}token=$token"
