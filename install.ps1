param(
  [string]$InstallRoot = "$env:USERPROFILE\\plugins",
  [string]$MarketplaceName = "local-windows-plugins",
  [string]$UserHome = $env:USERPROFILE,
  [switch]$NoConfigUpdate
)

$ErrorActionPreference = "Stop"

$SourceRoot = Split-Path -Parent $PSCommandPath
$PluginName = "windows-computer-use"
$TargetRoot = Join-Path $InstallRoot $PluginName
$MarketplaceDir = Join-Path $UserHome ".agents\\plugins"
$MarketplacePath = Join-Path $MarketplaceDir "marketplace.json"
$ConfigPath = Join-Path $UserHome ".codex\\config.toml"

Write-Host "Installing $PluginName to $TargetRoot"

$normalizedSource = [System.IO.Path]::GetFullPath($SourceRoot)
$normalizedTarget = [System.IO.Path]::GetFullPath($TargetRoot)
if ($normalizedTarget.StartsWith($normalizedSource, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "InstallRoot cannot be inside the repository folder. Choose another location."
}

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

Get-ChildItem -LiteralPath $SourceRoot -Force | Where-Object {
  $_.Name -notin @(".git", ".github", "__pycache__", ".venv", ".test-home", ".pack-tmp", "windows-computer-use-github.zip")
} | ForEach-Object {
  $destination = Join-Path $TargetRoot $_.Name
  if ($_.PSIsContainer) {
    if (Test-Path $destination) {
      Remove-Item -LiteralPath $destination -Recurse -Force
    }
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
  } else {
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
  }
}

Get-ChildItem -LiteralPath $TargetRoot -Recurse -Force | Where-Object {
  $_.Name -eq "__pycache__" -or $_.Extension -eq ".pyc"
} | Remove-Item -Recurse -Force

$EnsureVenv = Join-Path $TargetRoot "scripts\ensure_venv.ps1"
if (Test-Path $EnsureVenv) {
  powershell -NoProfile -ExecutionPolicy Bypass -File $EnsureVenv | Out-Null
}

$McpPath = Join-Path $TargetRoot ".mcp.json"
$mcp = Get-Content -LiteralPath $McpPath -Raw
$escapedRoot = $TargetRoot.Replace("\", "\\")
$mcp = $mcp.Replace("__PLUGIN_ROOT__", $escapedRoot)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($McpPath, $mcp, $utf8NoBom)

New-Item -ItemType Directory -Force -Path $MarketplaceDir | Out-Null

if (Test-Path $MarketplacePath) {
  $marketplace = Get-Content -LiteralPath $MarketplacePath -Raw | ConvertFrom-Json
} else {
  $marketplace = [pscustomobject]@{
    name = $MarketplaceName
    interface = [pscustomobject]@{
      displayName = "Local Windows Plugins"
    }
    plugins = @()
  }
}

if (-not $marketplace.PSObject.Properties['interface']) {
  $marketplace | Add-Member -NotePropertyName interface -NotePropertyValue ([pscustomobject]@{ displayName = "Local Windows Plugins" })
}
if (-not $marketplace.PSObject.Properties['plugins']) {
  $marketplace | Add-Member -NotePropertyName plugins -NotePropertyValue @()
}

$existing = @($marketplace.plugins | Where-Object { $_.name -eq $PluginName })
$remaining = @($marketplace.plugins | Where-Object { $_.name -ne $PluginName })
$entry = [pscustomobject]@{
  name = $PluginName
  source = [pscustomobject]@{
    source = "local"
    path = "./plugins/$PluginName"
  }
  policy = [pscustomobject]@{
    installation = "AVAILABLE"
    authentication = "ON_INSTALL"
  }
  category = "Productivity"
}
$marketplace.plugins = @($remaining + $entry)
[System.IO.File]::WriteAllText($MarketplacePath, ($marketplace | ConvertTo-Json -Depth 20), $utf8NoBom)

if (-not $NoConfigUpdate) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ConfigPath) | Out-Null
  if (Test-Path $ConfigPath) {
    $config = Get-Content -LiteralPath $ConfigPath -Raw
  } else {
    $config = ""
  }
  $pluginHeader = "[plugins.""$PluginName@$MarketplaceName""]"
  if ($config -notmatch [regex]::Escape($pluginHeader)) {
    $addition = "`r`n$pluginHeader`r`nenabled = true`r`n"
    [System.IO.File]::WriteAllText($ConfigPath, ($config + $addition), $utf8NoBom)
  }
}

Write-Host ""
Write-Host "Install complete."
Write-Host "1. Restart Codex Desktop."
Write-Host "2. Open the plugin picker and confirm Computer Use is enabled."
Write-Host "3. If needed, run scripts\\repair_and_test.ps1 from the installed plugin folder."
