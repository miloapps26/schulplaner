param(
  [Parameter(Mandatory = $true)]
  [string]$ServerHost,
  [string]$AppDomain = "",
  [string]$AppName = "stundenplaninfo",
  [int]$AppPort = 8000,
  [string]$ServiceUser = "stundenplan",
  [string]$AdminUsername = "azureuser"
)

$ErrorActionPreference = "Stop"

function Resolve-OpenSshCommand {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  $candidatePaths = @(
    (Join-Path $env:WINDIR "System32\OpenSSH\$Name.exe"),
    (Join-Path $env:WINDIR "Sysnative\OpenSSH\$Name.exe"),
    "C:\Program Files\Git\usr\bin\$Name.exe"
  )

  foreach ($path in $candidatePaths) {
    if (Test-Path -LiteralPath $path) {
      return $path
    }
  }

  $checked = $candidatePaths -join ", "
  throw "OpenSSH $Name wurde nicht gefunden. Gepruefte Pfade: $checked. Installiere den OpenSSH Client oder fuege C:\Windows\System32\OpenSSH zum PATH hinzu."
}

$ssh = Resolve-OpenSshCommand -Name "ssh"
$scp = Resolve-OpenSshCommand -Name "scp"
$remote = "$AdminUsername@$ServerHost"
$caddyHost = if ($AppDomain) { $AppDomain } else { $ServerHost }
$localUploadRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("stundenplaninfo-upload-" + [guid]::NewGuid().ToString("N"))

Write-Host "SSH: $ssh"
Write-Host "SCP: $scp"
Write-Host "Ziel: $remote"
Write-Host "App-Name: $AppName"
Write-Host "Interner Port: $AppPort"
Write-Host "Oeffentlicher Host in Caddy: $caddyHost"
Write-Host ""

Write-Host "[1/3] Bereite Upload-Ordner auf dem Server vor..."
& $ssh -o ConnectTimeout=20 $remote "rm -rf /tmp/stundenplaninfo-app && mkdir -p /tmp/stundenplaninfo-app"
if ($LASTEXITCODE -ne 0) {
  throw "Server-Upload-Ordner konnte nicht vorbereitet werden."
}

Write-Host "[2/3] Kopiere App-Dateien auf den Server..."
try {
  New-Item -ItemType Directory -Path $localUploadRoot -Force | Out-Null
  foreach ($item in @("src", "static", "tests", "deployment", "CHANGELOG.md", ".env.example", "requirements.txt", "pyproject.toml", "README.md")) {
    Copy-Item -LiteralPath $item -Destination $localUploadRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Path (Join-Path $localUploadRoot "config") -Force | Out-Null
  Copy-Item -LiteralPath "config\tenants.example.json" -Destination (Join-Path $localUploadRoot "config") -Force

  $uploadSource = Join-Path $localUploadRoot "*"
  & $scp -v -r $uploadSource "${remote}:/tmp/stundenplaninfo-app/"
  if ($LASTEXITCODE -ne 0) {
    throw "App-Dateien konnten nicht auf den Server kopiert werden."
  }
} finally {
  if (Test-Path -LiteralPath $localUploadRoot) {
    Remove-Item -LiteralPath $localUploadRoot -Recurse -Force
  }
}

Write-Host "[3/3] Installiere App und lade Caddy neu..."
& $ssh -o ConnectTimeout=20 $remote "sudo bash /tmp/stundenplaninfo-app/deployment/azure/server-setup.sh $caddyHost $AppName $AppPort $ServiceUser"
if ($LASTEXITCODE -ne 0) {
  throw "Server-Setup ist fehlgeschlagen."
}

Write-Host ""
Write-Host "App wurde installiert."
Write-Host "App-Name: $AppName"
Write-Host "Oeffentlicher Host in Caddy: $caddyHost"
Write-Host "Naechster Schritt:"
Write-Host ".\deployment\azure\upload-env.ps1 -ServerHost `"$ServerHost`" -AppName `"$AppName`""
