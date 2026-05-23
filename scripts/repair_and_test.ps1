param(
  [switch]$NoCacheSync,
  [string]$MarketplaceName = "local-windows-plugins"
)

$ErrorActionPreference = "Stop"

$PluginRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SourceMcp = Join-Path $PluginRoot ".mcp.json"
$Launcher = Join-Path $PluginRoot "scripts\run_windows_computer_use_mcp.cmd"
$Server = Join-Path $PluginRoot "scripts\windows_computer_use_mcp.py"
$EnsureVenv = Join-Path $PluginRoot "scripts\ensure_venv.ps1"
$PluginManifest = Get-Content -LiteralPath (Join-Path $PluginRoot ".codex-plugin\plugin.json") -Raw | ConvertFrom-Json
$CacheRoot = Join-Path $env:USERPROFILE ".codex\plugins\cache\$MarketplaceName\windows-computer-use\$($PluginManifest.version)"

if (!(Test-Path $Launcher)) {
  throw "Missing launcher: $Launcher"
}
if (!(Test-Path $Server)) {
  throw "Missing MCP server: $Server"
}
if (!(Test-Path $EnsureVenv)) {
  throw "Missing venv helper: $EnsureVenv"
}

$VenvPython = powershell -NoProfile -ExecutionPolicy Bypass -File $EnsureVenv
if (!(Test-Path $VenvPython)) {
  throw "Virtual environment was not created: $VenvPython"
}

& $VenvPython -m json.tool $SourceMcp | Out-Null
& $VenvPython -m py_compile $Server

$probe = @'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"cursor_position","arguments":{}}}
'@

$output = $probe | & $Launcher
if ($LASTEXITCODE -ne 0) {
  throw "Launcher failed with exit code $LASTEXITCODE"
}
if (($output -join "`n") -notmatch '"serverInfo"' -or ($output -join "`n") -notmatch '"cursor_position"|"\{\\?"x\\?"') {
  throw "MCP probe did not return the expected initialize/cursor response."
}

if (!$NoCacheSync) {
  New-Item -ItemType Directory -Force -Path $CacheRoot | Out-Null
  Get-ChildItem -LiteralPath $PluginRoot -Force | Where-Object {
    $_.Name -ne ".venv"
  } | ForEach-Object {
    $destination = Join-Path $CacheRoot $_.Name
    if ($_.PSIsContainer -and (Test-Path $destination)) {
      Remove-Item -LiteralPath $destination -Recurse -Force
    }
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
  }
  Get-ChildItem -LiteralPath $CacheRoot -Recurse -Force | Where-Object {
    $_.Name -eq "__pycache__" -or $_.Extension -eq ".pyc"
  } | Remove-Item -Recurse -Force
  $cacheMcp = Join-Path $CacheRoot ".mcp.json"
  $jsonText = Get-Content -LiteralPath $cacheMcp -Raw
  $jsonText = $jsonText.Replace("__PLUGIN_ROOT__", $CacheRoot.Replace("\", "\\"))
  $json = $jsonText | ConvertFrom-Json
  $json.mcpServers.'windows-computer-use'.command = "C:\Windows\System32\cmd.exe"
  $json.mcpServers.'windows-computer-use'.args = @(
    "/d",
    "/c",
    (Join-Path $CacheRoot "scripts\run_windows_computer_use_mcp.cmd")
  )
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($cacheMcp, ($json | ConvertTo-Json -Depth 20), $utf8NoBom)
}

Write-Output "Windows Computer Use MCP is healthy."
