# Windows Computer Use for Codex

`Windows Computer Use` is a local Codex plugin for Windows that exposes desktop automation tools through MCP.

It provides:

- `screenshot`
- `move_mouse`
- `click`
- `scroll`
- `press_key`
- `hotkey`
- `type_text`
- `cursor_position`
- `list_windows`

By default, `screenshot` uses a temporary file and deletes it immediately after returning the image to Codex. A screenshot is only kept on disk when a `path` is explicitly provided.

## Requirements

- Windows 10 or 11
- Codex Desktop for Windows
- Python 3.10+ available as one of:
  - `C:\Python313\python.exe`
  - `py -3`
  - `python`

## Install

1. Clone this repo or download the ZIP.
2. Open PowerShell in the repo root.
3. Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

4. Restart Codex Desktop.

The installer will:

- copy the plugin into `%USERPROFILE%\plugins\windows-computer-use`
- rewrite `.mcp.json` to the installed path
- add or update `%USERPROFILE%\.agents\plugins\marketplace.json`
- mark the plugin enabled in `%USERPROFILE%\.codex\config.toml`

## Install to a custom location

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -InstallRoot "D:\CodexPlugins"
```

## Test install without touching your real Codex profile

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 `
  -InstallRoot "$PWD\.test-home\plugins" `
  -UserHome "$PWD\.test-home"
```

## Repair

If Codex updates and the plugin stops responding, run:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\windows-computer-use\scripts\repair_and_test.ps1"
```

## Screenshot Storage Behavior

- Default behavior: temporary screenshot, auto-deleted after use
- Persistent behavior: only when the caller passes `path`
- This keeps step-by-step visual automation possible without filling the disk with PNGs

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

## Repository

GitHub repository:

- [twh66666/windows-computer-use](https://github.com/twh66666/windows-computer-use)

## Safety

This plugin controls the active Windows desktop. Mouse and keyboard actions affect the currently focused app.

## Pack a Release ZIP

```powershell
powershell -ExecutionPolicy Bypass -File .\pack.ps1
```
