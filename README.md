# Computer Use for Windows

[![Windows](https://img.shields.io/badge/platform-Windows-0078D6)](#requirements)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)](#requirements)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

`Computer Use` is a local Codex plugin for Windows. It exposes desktop control tools through MCP so Codex can inspect windows, capture screenshots, move the mouse, click, scroll, type, and press hotkeys.

This build keeps the Codex plugin ID as `windows-computer-use` for compatibility, but the displayed plugin name is `Computer Use`.

The mouse backend uses Windows-Use style Win32 behavior inspired by [CursorTouch/Windows-Use](https://github.com/CursorTouch/Windows-Use), including smooth cursor movement.

## Tools

- `screenshot`
- `move_mouse`
- `click`
- `scroll`
- `press_key`
- `hotkey`
- `type_text`
- `cursor_position`
- `list_windows`

## Requirements

- Windows 10 or 11
- Codex Desktop for Windows
- Python 3.10+ available as one of:
  - `C:\Python313\python.exe`
  - `py -3`
  - `python`

If Python is missing, install it with:

```powershell
winget install --id Python.Python.3.13 --scope user
```

Close and reopen PowerShell after installing Python so the updated `PATH` is available.

## Install From GitHub

Run this in PowerShell:

```powershell
$ProgressPreference = "SilentlyContinue"
$zip = "$env:TEMP\computer-use-for-windows.zip"
$src = "$env:TEMP\computer-use-for-windows"
Remove-Item -Recurse -Force $src -ErrorAction SilentlyContinue
Invoke-WebRequest `
  -Uri "https://github.com/Zrh1007/codex-computer-use-for-windows/archive/refs/heads/main.zip" `
  -OutFile $zip
Expand-Archive -Path $zip -DestinationPath $src -Force
powershell -ExecutionPolicy Bypass -File "$src\codex-computer-use-for-windows-main\install.ps1"
```

Then restart Codex Desktop and enable `Computer Use` in the plugin picker if it is not enabled automatically.

## Install From a Local Clone

```powershell
git clone https://github.com/Zrh1007/codex-computer-use-for-windows.git
cd codex-computer-use-for-windows
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer will:

- copy the plugin into `%USERPROFILE%\plugins\windows-computer-use`
- rewrite `.mcp.json` to the installed path
- add or update `%USERPROFILE%\.agents\plugins\marketplace.json`
- enable `[plugins."windows-computer-use@local-windows-plugins"]` in `%USERPROFILE%\.codex\config.toml`

## Custom Install Location

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -InstallRoot "D:\CodexPlugins"
```

## Test or Repair

After installing, run:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\windows-computer-use\scripts\repair_and_test.ps1"
```

Expected output:

```text
Windows Computer Use MCP is healthy.
```

## Screenshot Storage

By default, `screenshot` uses a temporary file and deletes it immediately after returning the image to Codex. A screenshot is only kept on disk when the caller passes a `path`.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

## Development

Pack a release ZIP:

```powershell
powershell -ExecutionPolicy Bypass -File .\pack.ps1
```

Run a local MCP probe:

```powershell
$probe = @'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"cursor_position","arguments":{}}}
'@
$probe | & "$env:USERPROFILE\plugins\windows-computer-use\scripts\run_windows_computer_use_mcp.cmd"
```

## Safety

This plugin controls the active Windows desktop. Mouse and keyboard actions affect the currently focused app.

## License

MIT
