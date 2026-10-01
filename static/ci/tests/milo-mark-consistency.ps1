$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$markPath = Join-Path $root 'assets\milo-mark.svg'
$faviconPath = Join-Path $root 'assets\favicon.svg'
foreach ($path in @($markPath, $faviconPath)) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing Milo mark asset: $path"
  }
  $svg = Get-Content -LiteralPath $path -Raw
  foreach ($required in @('fill="#ffffff"', 'fill="#0d1117"', '>Milo<')) {
    if ($svg -notlike "*$required*") {
      throw "$path does not match the standard Milo mark requirement: $required"
    }
  }
}

$htmlFiles = Get-ChildItem -Path $root -Filter '*.html' -File
foreach ($file in $htmlFiles) {
  $html = Get-Content -LiteralPath $file.FullName -Raw
  if ($html -match 'class="[^"]*\bci-mark\b') {
    if ($html -notmatch 'class="[^"]*\bci-mark-img\b[^"]*"[^>]+src="[^"]*assets/milo-mark\.svg"') {
      throw "$($file.Name) uses ci-mark without the official assets/milo-mark.svg image."
    }
    if ($html -match 'ci-mark-bars') {
      throw "$($file.Name) still uses the deprecated ci-mark-bars fallback."
    }
  }
}

Write-Host 'Milo mark consistency regression passed.'
