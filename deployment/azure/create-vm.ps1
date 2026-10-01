param(
  [string]$ResourceGroup = "rg-stundenplaninfo",
  [string]$Location = "germanywestcentral",
  [string]$VmName = "vm-stundenplaninfo",
  [string]$AdminUsername = "azureuser",
  [string]$VmSize = "Standard_B1s",
  [string]$DnsLabel = ""
)

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

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  throw "Azure CLI ist nicht installiert. Installiere zuerst die Azure CLI und starte PowerShell neu."
}

if (-not $DnsLabel) {
  $suffix = New-RandomHex -ByteCount 3
  $DnsLabel = "stundenplaninfo-$suffix"
}

try {
  & az account show --output none
} catch {
  & az login
}

& az group create `
  --name $ResourceGroup `
  --location $Location `
  --output table

& az vm create `
  --resource-group $ResourceGroup `
  --name $VmName `
  --image Ubuntu2204 `
  --size $VmSize `
  --admin-username $AdminUsername `
  --generate-ssh-keys `
  --public-ip-sku Standard `
  --public-ip-address-dns-name $DnsLabel `
  --output table

& az vm open-port --resource-group $ResourceGroup --name $VmName --port 80 --priority 1001 --output table
& az vm open-port --resource-group $ResourceGroup --name $VmName --port 443 --priority 1002 --output table

$fqdn = & az vm show `
  --resource-group $ResourceGroup `
  --name $VmName `
  --show-details `
  --query fqdns `
  --output tsv

$ip = & az vm show `
  --resource-group $ResourceGroup `
  --name $VmName `
  --show-details `
  --query publicIps `
  --output tsv

Write-Host ""
Write-Host "Azure VM ist bereit."
Write-Host "IP: $ip"
Write-Host "FQDN: $fqdn"
Write-Host ""
Write-Host "Naechster Schritt:"
Write-Host ".\deployment\azure\upload-app.ps1 -ServerHost `"$fqdn`""
