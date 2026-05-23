"""Lightweight Windows-Use style backend for Codex desktop control.

Mouse behavior is adapted from CursorTouch/Windows-Use's UIA core helpers:
https://github.com/CursorTouch/Windows-Use
"""

from __future__ import annotations

import ctypes
import math
import time
from ctypes import wintypes


MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800

OPERATION_WAIT_TIME = 0.05
MAX_MOVE_SECOND = 1.0

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class WindowsUseBackend:
    def get_cursor_pos(self) -> tuple[int, int]:
        point = POINT()
        if not user32.GetCursorPos(ctypes.byref(point)):
            raise ctypes.WinError(ctypes.get_last_error())
        return point.x, point.y

    def set_cursor_pos(self, x: int, y: int) -> None:
        if not user32.SetCursorPos(int(x), int(y)):
            raise ctypes.WinError(ctypes.get_last_error())

    def move_to(
        self,
        x: int,
        y: int,
        *,
        move_speed: float = 10,
        duration: float | None = None,
        steps: int | None = None,
        wait_time: float = OPERATION_WAIT_TIME,
    ) -> None:
        """Smoothly move to a point, following Windows-Use's MoveTo behavior."""
        start_x, start_y = self.get_cursor_pos()
        x = int(x)
        y = int(y)

        distance = math.hypot(x - start_x, y - start_y)
        if distance < 1:
            self.set_cursor_pos(x, y)
            time.sleep(wait_time)
            return

        if duration is None:
            duration = 0.0 if move_speed <= 0 else MAX_MOVE_SECOND / move_speed
            duration = min(MAX_MOVE_SECOND, max(0.03, duration * min(distance, 1600) / 1600))
        else:
            duration = max(0.0, float(duration))

        if steps is None:
            steps = max(4, min(80, int(distance / 18)))
        steps = max(1, int(steps))

        delay = duration / steps if steps else 0
        for index in range(1, steps + 1):
            progress = index / steps
            eased = 0.5 - math.cos(progress * math.pi) / 2
            cx = round(start_x + (x - start_x) * eased)
            cy = round(start_y + (y - start_y) * eased)
            self.set_cursor_pos(cx, cy)
            if delay:
                time.sleep(delay)

        self.set_cursor_pos(x, y)
        time.sleep(wait_time)

    def click(self, button: str = "left", clicks: int = 1, interval: float = 0.08) -> None:
        flags = {
            "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
            "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
            "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        }.get(button)
        if flags is None:
            raise ValueError("button must be left, right, or middle")

        for _ in range(max(1, int(clicks))):
            user32.mouse_event(flags[0], 0, 0, 0, 0)
            time.sleep(0.03)
            user32.mouse_event(flags[1], 0, 0, 0, 0)
            time.sleep(float(interval))

    def scroll(self, amount: int) -> None:
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(amount) * 120, 0)
