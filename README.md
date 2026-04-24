# Codex Computer Use Plugin for Windows

[![Release](https://img.shields.io/github/v/release/twh66666/windows-computer-use)](https://github.com/twh66666/windows-computer-use/releases)
![Windows](https://img.shields.io/badge/platform-Windows-0078D6)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

`Windows Computer Use` is a local Codex plugin for Windows that exposes desktop automation tools through MCP.

这是一个面向 Windows 的 Codex 本地插件，通过 MCP 提供桌面自动化能力。

It is designed for users who want Codex to operate real Windows applications with screenshots, keyboard input, mouse control, scrolling, and window inspection.

它适合希望让 Codex 直接操作真实 Windows 应用的用户，包括截图、键盘输入、鼠标控制、滚动和窗口检测。

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

默认情况下，`screenshot` 会使用临时文件并在返回后立即删除；只有显式传入 `path` 时才会真正落盘保存。

## Features

- Windows desktop automation through MCP
- Screenshot capture
- Mouse movement and click control
- Keyboard input and hotkeys
- Window enumeration
- Portable installer for Codex Desktop

## 功能概览

- 通过 MCP 提供 Windows 桌面自动化
- 截图
- 鼠标移动与点击
- 键盘输入与快捷键
- 窗口枚举
- 面向 Codex Desktop 的便携安装脚本

## Quick Start

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Restart Codex Desktop after installation, then enable `Windows Computer Use` in the local plugin list if needed.

安装完成后重启 Codex Desktop；如果没有自动启用，就在本地插件列表里启用 `Windows Computer Use`。

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

这个插件会操作当前活动桌面，因此鼠标和键盘输入会直接作用到前台应用。

## Pack a Release ZIP

```powershell
powershell -ExecutionPolicy Bypass -File .\pack.ps1
```

## License

MIT
