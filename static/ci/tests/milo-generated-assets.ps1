$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$assetDir = Join-Path $root 'assets\milo'

$required = @(
  'milo-mark-white.svg',
  'milo-mark-alpha.svg',
  'milo-mark-white-256.png',
  'milo-mark-white-512.png',
  'milo-mark-white-1024.png',
  'milo-mark-alpha-256.png',
  'milo-mark-alpha-512.png',
  'milo-mark-alpha-1024.png',
  'milo-mark-white-512.jpg',
  'milo-mark-white-1024.jpg',
  'README.md'
)

foreach ($name in $required) {
  $path = Join-Path $assetDir $name
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing Milo generated asset: $name"
  }
}

$whiteSvg = Get-Content -LiteralPath (Join-Path $assetDir 'milo-mark-white.svg') -Raw
$alphaSvg = Get-Content -LiteralPath (Join-Path $assetDir 'milo-mark-alpha.svg') -Raw
if ($whiteSvg -notmatch 'fill="#ffffff"') {
  throw 'White SVG is missing the white background.'
}
if ($alphaSvg -match '<rect[^>]+fill="#ffffff"') {
  throw 'Alpha SVG still contains the white background rectangle.'
}
foreach ($svg in @($whiteSvg, $alphaSvg)) {
  foreach ($requiredText in @('fill="#0d1117"', '>Milo<')) {
    if ($svg -notlike "*$requiredText*") {
      throw "Milo SVG variant is missing $requiredText"
    }
  }
}

Write-Host 'Milo generated asset regression passed.'
