# Windows Computer Use

Use this skill when the user invokes `@windows-computer-use`, asks Codex to control the Windows desktop, or asks for screenshots, mouse, keyboard, scrolling, cursor position, or visible window inspection on the local Windows machine.

## Preferred path

If MCP tools from the `windows-computer-use` server are available in the current tool list, use them directly:

- `screenshot`
- `move_mouse`
- `click`
- `scroll`
- `press_key`
- `hotkey`
- `type_text`
- `cursor_position`
- `list_windows`

Be conservative with real desktop control. Prefer listing windows and screenshots before clicking or typing. Avoid destructive actions unless the user explicitly asks for them.

## Fallback path

If the MCP tools are not exposed as first-class tools in the current session, call the installed local MCP script through PowerShell and JSON-RPC.

Default installed launcher:

```powershell
$env:USERPROFILE\plugins\windows-computer-use\scripts\run_windows_computer_use_mcp.cmd
```

Example tool call:

```powershell
'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_windows","arguments":{"limit":20}}}' | & "$env:USERPROFILE\plugins\windows-computer-use\scripts\run_windows_computer_use_mcp.cmd"
```

For screenshots, pass an explicit `path` under the current workspace when you want a persistent PNG:

```powershell
$path = "$env:TEMP\codex-computer-use-screenshot.png"
$json = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"screenshot","arguments":{"path":"' + $path.Replace('\','\\') + '","include_image":false}}}'
$json | & "$env:USERPROFILE\plugins\windows-computer-use\scripts\run_windows_computer_use_mcp.cmd"
```

Use `type_text` only after focusing a safe target app or after the user confirms the active target.
