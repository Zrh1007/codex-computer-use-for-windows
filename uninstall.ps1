param(
  [string]$InstallRoot = "$env:USERPROFILE\\plugins",
  [string]$MarketplaceName = "local-windows-plugins",
  [string]$UserHome = $env:USERPROFILE
)

$ErrorActionPreference = "Stop"

$PluginName = "windows-computer-use"
$TargetRoot = Join-Path $InstallRoot $PluginName
$MarketplacePath = Join-Path $UserHome ".agents\\plugins\\marketplace.json"

if (Test-Path $TargetRoot) {
  Remove-Item -LiteralPath $TargetRoot -Recurse -Force
}

if (Test-Path $MarketplacePath) {
  $marketplace = Get-Content -LiteralPath $MarketplacePath -Raw | ConvertFrom-Json
  if ($marketplace.plugins) {
    $marketplace.plugins = @($marketplace.plugins | Where-Object { $_.name -ne $PluginName })
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($MarketplacePath, ($marketplace | ConvertTo-Json -Depth 20), $utf8NoBom)
  }
}

Write-Host "Removed $PluginName. Restart Codex Desktop to refresh plugins."
