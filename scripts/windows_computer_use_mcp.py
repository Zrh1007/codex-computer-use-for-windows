#!/usr/bin/env python
"""Tiny MCP server for local Windows desktop control."""

from __future__ import annotations

import base64
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

from windows_use_backend import WindowsUseBackend

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "computer-use"
SERVER_VERSION = "0.2.1"
OUTPUT_FRAMED = False
BACKEND_NAME = "CursorTouch/Windows-Use"
backend = WindowsUseBackend()

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
KEYEVENTF_KEYUP = 0x0002
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


VK = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "win": 0x5B,
    "windows": 0x5B,
    "cmd": 0x5B,
    "meta": 0x5B,
    "apps": 0x5D,
    "numpad0": 0x60,
    "numpad1": 0x61,
    "numpad2": 0x62,
    "numpad3": 0x63,
    "numpad4": 0x64,
    "numpad5": 0x65,
    "numpad6": 0x66,
    "numpad7": 0x67,
    "numpad8": 0x68,
    "numpad9": 0x69,
    "multiply": 0x6A,
    "add": 0x6B,
    "subtract": 0x6D,
    "decimal": 0x6E,
    "divide": 0x6F,
    "numlock": 0x90,
    "scrolllock": 0x91,
}
for i in range(1, 25):
    VK[f"f{i}"] = 0x6F + i
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    VK[c.lower()] = ord(c)
for c in "0123456789":
    VK[c] = ord(c)


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.CloseClipboard.restype = wintypes.BOOL
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL


def _json_default(value: Any) -> str:
    return str(value)


def send(payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
    if OUTPUT_FRAMED:
        sys.stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    else:
        sys.stdout.buffer.write(data + b"\n")
        sys.stdout.buffer.flush()


def ok(request_id: Any, result: dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "result": result})


def err(request_id: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def text_result(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _sleep(seconds: float | int | None) -> None:
    if seconds:
        time.sleep(float(seconds))


def vk_code(key: str) -> int:
    normalized = str(key).strip().lower()
    if normalized in VK:
        return VK[normalized]
    if len(normalized) == 1:
        scan = user32.VkKeyScanW(ord(normalized))
        if scan != -1:
            return scan & 0xFF
    raise ValueError(f"Unknown key: {key!r}")


def key_down(vk: int) -> None:
    user32.keybd_event(vk, 0, 0, 0)


def key_up(vk: int) -> None:
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def tap_key(key: str, duration: float = 0.03) -> None:
    vk = vk_code(key)
    key_down(vk)
    time.sleep(duration)
    key_up(vk)


def set_clipboard_text(text: str) -> None:
    data = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        locked = kernel32.GlobalLock(handle)
        if not locked:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(locked, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        user32.CloseClipboard()


def tool_screenshot(args: dict[str, Any]) -> dict[str, Any]:
    include_image = bool(args.get("include_image", True))
    output_path = args.get("path")
    ephemeral = not output_path
    if output_path:
        path = Path(output_path).expanduser()
    else:
        path = Path(tempfile.gettempdir()) / f"codex-windows-computer-use-{int(time.time() * 1000)}.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    script = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$path = $env:WCU_SCREENSHOT_PATH
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bounds.Size)
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bmp.Dispose()
"""
    env = os.environ.copy()
    env["WCU_SCREENSHOT_PATH"] = str(path)
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Screenshot failed")

    image_bytes = path.read_bytes()
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": "Screenshot captured temporarily." if ephemeral else f"Screenshot saved to {path}",
        }
    ]
    if include_image:
        content.append(
            {
                "type": "image",
                "data": base64.b64encode(image_bytes).decode("ascii"),
                "mimeType": "image/png",
            }
        )
    if ephemeral:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    return {"content": content}


def tool_move_mouse(args: dict[str, Any]) -> dict[str, Any]:
    x = int(args["x"])
    y = int(args["y"])
    backend.move_to(
        x,
        y,
        move_speed=float(args.get("speed", 10)),
        duration=args.get("duration"),
        steps=args.get("steps"),
        wait_time=float(args.get("wait_time", 0.05)),
    )
    _sleep(args.get("delay"))
    return text_result(f"Smoothly moved cursor to ({x}, {y}) using {BACKEND_NAME}.")


def tool_click(args: dict[str, Any]) -> dict[str, Any]:
    x = args.get("x")
    y = args.get("y")
    if x is not None and y is not None:
        backend.move_to(
            int(x),
            int(y),
            move_speed=float(args.get("speed", 10)),
            duration=args.get("duration"),
            steps=args.get("steps"),
            wait_time=float(args.get("wait_time", 0.02)),
        )
    button = str(args.get("button", "left")).lower()
    clicks = int(args.get("clicks", 1))
    interval = float(args.get("interval", 0.08))
    backend.click(button=button, clicks=clicks, interval=interval)
    _sleep(args.get("delay"))
    point = cursor_point()
    return text_result(
        f"Clicked {button} {clicks} time(s) at ({point.x}, {point.y}) using {BACKEND_NAME}."
    )


def tool_scroll(args: dict[str, Any]) -> dict[str, Any]:
    amount = int(args.get("amount", -3))
    x = args.get("x")
    y = args.get("y")
    if x is not None and y is not None:
        backend.move_to(
            int(x),
            int(y),
            move_speed=float(args.get("speed", 10)),
            duration=args.get("duration"),
            steps=args.get("steps"),
            wait_time=float(args.get("wait_time", 0.02)),
        )
    backend.scroll(amount)
    _sleep(args.get("delay"))
    return text_result(f"Scrolled {amount} wheel notch(es) using {BACKEND_NAME}.")


def tool_press_key(args: dict[str, Any]) -> dict[str, Any]:
    key = str(args["key"])
    tap_key(key, float(args.get("duration", 0.03)))
    _sleep(args.get("delay"))
    return text_result(f"Pressed {key}.")


def tool_hotkey(args: dict[str, Any]) -> dict[str, Any]:
    keys = args.get("keys")
    if isinstance(keys, str):
        parts = [part.strip() for part in keys.replace("+", " ").split() if part.strip()]
    else:
        parts = [str(part) for part in keys]
    vks = [vk_code(part) for part in parts]
    for vk in vks:
        key_down(vk)
        time.sleep(0.02)
    for vk in reversed(vks):
        key_up(vk)
        time.sleep(0.02)
    _sleep(args.get("delay"))
    return text_result(f"Pressed hotkey {'+'.join(parts)}.")


def tool_type_text(args: dict[str, Any]) -> dict[str, Any]:
    text = str(args.get("text", ""))
    set_clipboard_text(text)
    tool_hotkey({"keys": ["ctrl", "v"]})
    _sleep(args.get("delay"))
    return text_result(f"Pasted {len(text)} character(s) into the focused app.")


def cursor_point() -> POINT:
    x, y = backend.get_cursor_pos()
    point = POINT(x=x, y=y)
    return point


def tool_cursor_position(args: dict[str, Any]) -> dict[str, Any]:
    point = cursor_point()
    return text_result(json.dumps({"x": point.x, "y": point.y}, ensure_ascii=False))


def tool_list_windows(args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 50))
    script = f"""
Get-Process |
  Where-Object {{ $_.MainWindowTitle }} |
  Select-Object -First {limit} Id, ProcessName, MainWindowTitle |
  ConvertTo-Json -Depth 2
"""
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Unable to list windows")
    raw = completed.stdout.strip() or "[]"
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]
        text = json.dumps(parsed, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        text = raw
    return text_result(text)


TOOLS = {
    "screenshot": {
        "description": "Capture the Windows virtual desktop as a PNG.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Optional output PNG path."},
                "include_image": {"type": "boolean", "default": True},
            },
        },
        "handler": tool_screenshot,
    },
    "move_mouse": {
        "description": "Smoothly move the mouse cursor to absolute screen coordinates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "speed": {
                    "type": "number",
                    "default": 10,
                    "description": "Windows-Use style movement speed. Higher is faster.",
                },
                "duration": {
                    "type": "number",
                    "description": "Optional exact movement duration in seconds.",
                },
                "steps": {
                    "type": "integer",
                    "description": "Optional number of interpolation steps for the move.",
                },
                "wait_time": {
                    "type": "number",
                    "default": 0.05,
                    "description": "Pause after movement in seconds.",
                },
                "delay": {"type": "number"},
            },
            "required": ["x", "y"],
        },
        "handler": tool_move_mouse,
    },
    "click": {
        "description": "Click at the current cursor position or at absolute coordinates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "clicks": {"type": "integer", "default": 1},
                "interval": {"type": "number", "default": 0.08},
                "speed": {"type": "number", "default": 10},
                "duration": {"type": "number"},
                "steps": {"type": "integer"},
                "wait_time": {"type": "number", "default": 0.02},
                "delay": {"type": "number"},
            },
        },
        "handler": tool_click,
    },
    "scroll": {
        "description": "Scroll the mouse wheel. Positive values scroll up, negative values scroll down.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "integer", "default": -3},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "speed": {"type": "number", "default": 10},
                "duration": {"type": "number"},
                "steps": {"type": "integer"},
                "wait_time": {"type": "number", "default": 0.02},
                "delay": {"type": "number"},
            },
        },
        "handler": tool_scroll,
    },
    "press_key": {
        "description": "Press a single keyboard key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "duration": {"type": "number", "default": 0.03},
                "delay": {"type": "number"},
            },
            "required": ["key"],
        },
        "handler": tool_press_key,
    },
    "hotkey": {
        "description": "Press a keyboard shortcut, for example ctrl+l or ['ctrl','shift','esc'].",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keys": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ]
                },
                "delay": {"type": "number"},
            },
            "required": ["keys"],
        },
        "handler": tool_hotkey,
    },
    "type_text": {
        "description": "Paste Unicode text into the focused application using the clipboard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "delay": {"type": "number"},
            },
            "required": ["text"],
        },
        "handler": tool_type_text,
    },
    "cursor_position": {
        "description": "Return the current cursor position.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_cursor_position,
    },
    "list_windows": {
        "description": "List visible top-level windows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50},
            },
        },
        "handler": tool_list_windows,
    },
}


def tool_descriptions() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def handle(message: dict[str, Any]) -> None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if request_id is None and method and method.startswith("notifications/"):
        return

    try:
        if method == "initialize":
            ok(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        elif method == "tools/list":
            ok(request_id, {"tools": tool_descriptions()})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            if name not in TOOLS:
                raise ValueError(f"Unknown tool: {name}")
            ok(request_id, TOOLS[name]["handler"](args))
        else:
            err(request_id, -32601, f"Method not found: {method}")
    except Exception as exc:
        err(request_id, -32000, str(exc))


def _handle_json_bytes(data: bytes) -> None:
    try:
        handle(json.loads(data.decode("utf-8-sig")))
    except Exception as exc:
        err(None, -32700, f"Parse or dispatch error: {exc}")


def _read_framed_body(first_header: bytes) -> bytes | None:
    headers = [first_header]
    while True:
        line = sys.stdin.buffer.readline()
        if line == b"":
            return None
        if line in (b"\r\n", b"\n"):
            break
        headers.append(line)

    content_length = None
    for header in headers:
        name, _, value = header.decode("ascii", errors="replace").partition(":")
        if name.strip().lower() == "content-length":
            content_length = int(value.strip())
            break
    if content_length is None:
        raise ValueError("Missing Content-Length header")
    return sys.stdin.buffer.read(content_length)


def main() -> None:
    global OUTPUT_FRAMED

    first_line = sys.stdin.buffer.readline()
    if first_line == b"":
        return

    if first_line.lower().startswith(b"content-length:"):
        OUTPUT_FRAMED = True
        current_header: bytes | None = first_line
        while current_header:
            try:
                body = _read_framed_body(current_header)
                if body is None:
                    return
                _handle_json_bytes(body)
            except Exception as exc:
                err(None, -32700, f"Parse or dispatch error: {exc}")
                return

            while True:
                current_header = sys.stdin.buffer.readline()
                if current_header == b"":
                    return
                if current_header.strip():
                    break
    else:
        line = first_line.strip()
        if line:
            _handle_json_bytes(line)
        for line in sys.stdin.buffer:
            line = line.strip()
            if not line:
                continue
            _handle_json_bytes(line)


if __name__ == "__main__":
    main()
