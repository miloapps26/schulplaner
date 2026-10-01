$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$cssPath = Join-Path $root 'ci.css'
$css = Get-Content -LiteralPath $cssPath -Raw

$hiddenMatch = [regex]::Match($css, '(?s)\[hidden\]\s*\{\s*display\s*:\s*none\s*!important\s*;\s*\}')
if (-not $hiddenMatch.Success) {
  throw 'ci.css must define [hidden] { display: none !important; }'
}

$componentDisplayMatch = [regex]::Match($css, '(?m)^\.ci-[^{]+\{[^}]*display\s*:', 'IgnoreCase')
if ($componentDisplayMatch.Success -and $hiddenMatch.Index -gt $componentDisplayMatch.Index) {
  throw '[hidden] override must be defined before component display rules so it is easy to audit as a base rule.'
}

$demoPath = Join-Path $root 'hidden-regression.html'
if (-not (Test-Path -LiteralPath $demoPath)) {
  throw 'hidden-regression.html demo is missing.'
}

$demo = Get-Content -LiteralPath $demoPath -Raw
foreach ($required in @('ci-workspace', 'ci-tabs', 'ci-button', 'ci-activity')) {
  if ($demo -notmatch ('class="[^"]*' + [regex]::Escape($required)) -or $demo -notmatch ('data-hidden-case="' + [regex]::Escape($required) + '"')) {
    throw "hidden-regression.html must include a hidden $required case."
  }
}

'Hidden attribute regression passed.'
