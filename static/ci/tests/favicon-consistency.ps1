$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$pngRequired = @(
  @{ Path = 'assets\favicon-16.png'; Size = 16 },
  @{ Path = 'assets\favicon-32.png'; Size = 32 },
  @{ Path = 'assets\favicon-48.png'; Size = 48 }
)

Add-Type -AssemblyName System.Drawing

foreach ($item in $pngRequired) {
  $path = Join-Path $root $item.Path
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing favicon asset: $($item.Path)"
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

$icoPath = Join-Path $root 'assets\favicon.ico'
if (-not (Test-Path -LiteralPath $icoPath)) {
  throw 'Missing favicon asset: assets\favicon.ico'
}
if ((Get-Item -LiteralPath $icoPath).Length -lt 100) {
  throw 'assets\favicon.ico looks too small to be a valid favicon fallback.'
}

$faviconSvg = Get-Content -LiteralPath (Join-Path $root 'assets\favicon.svg') -Raw
foreach ($requiredText in @('fill="#ffffff"', 'fill="#0d1117"', '>Milo<')) {
  if ($faviconSvg -notlike "*$requiredText*") {
    throw "favicon.svg does not match the current Milo icon requirement: $requiredText"
  }
}

$htmlFiles = Get-ChildItem -Path $root -Filter '*.html' -File
foreach ($file in $htmlFiles) {
  $html = Get-Content -LiteralPath $file.FullName -Raw
  foreach ($requiredLink in @('assets/favicon.svg?v=1.4.0', 'assets/favicon-32.png?v=1.4.0', 'assets/favicon.ico?v=1.4.0')) {
    if ($html -notlike "*$requiredLink*") {
      throw "$($file.Name) is missing current favicon link $requiredLink"
    }
  }
}

Write-Host 'Favicon consistency regression passed.'

