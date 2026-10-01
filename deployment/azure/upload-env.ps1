param(
  [Parameter(Mandatory = $true)]
  [string]$ServerHost,
  [string]$AppName = "stundenplaninfo",
  [string]$ServiceUser = "stundenplan",
  [string]$AdminUsername = "azureuser"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath ".env")) {
  throw ".env nicht gefunden."
}

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

& $scp ".env" "${remote}:/tmp/stundenplaninfo.env"
& $ssh $remote "sudo install -m 600 -o $ServiceUser -g $ServiceUser /tmp/stundenplaninfo.env /srv/apps/$AppName/app/.env && rm -f /tmp/stundenplaninfo.env && sudo systemctl enable --now $AppName && sudo systemctl restart $AppName && sudo systemctl status $AppName --no-pager"

Write-Host ""
Write-Host "Secrets wurden hochgeladen und die App wurde gestartet."
Write-Host "App-Name: $AppName"
Write-Host "Elternansicht: PUBLIC_TIMETABLE_URL aus .env plus /app"
Write-Host "Admin: PUBLIC_TIMETABLE_URL aus .env plus /admin"
