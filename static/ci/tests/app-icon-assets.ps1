$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$required = @(
  @{ Path = 'assets\apple-touch-icon.png'; Size = 180 },
  @{ Path = 'assets\app-icon-192.png'; Size = 192 },
  @{ Path = 'assets\app-icon-512.png'; Size = 512 }
)

Add-Type -AssemblyName System.Drawing

foreach ($item in $required) {
  $path = Join-Path $root $item.Path
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing app icon: $($item.Path)"
  }

  $image = [System.Drawing.Image]::FromFile($path)
  try {
    if ($image.Width -ne $item.Size -or $image.Height -ne $item.Size) {
      throw "$($item.Path) must be $($item.Size)x$($item.Size), got $($image.Width)x$($image.Height)"
    }
  } finally {
    $image.Dispose()
  }
}

$manifestPath = Join-Path $root 'site.webmanifest'
if (-not (Test-Path -LiteralPath $manifestPath)) {
  throw 'Missing site.webmanifest'
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($src in @('assets/app-icon-192.png', 'assets/app-icon-512.png')) {
  if (-not (@($manifest.icons) | Where-Object { $_.src -eq $src })) {
    throw "site.webmanifest does not include $src"
  }
}

Write-Host 'App icon regression passed.'

