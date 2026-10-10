"""Parse the common Windows screen-saver command-line forms without Win32 calls."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SaverCommand:
    mode: str = "screen"  # screen, configure, preview
    parent_handle: int | None = None


def _parse_handle(value: str) -> int | None:
    try:
        # Windows generally passes decimal HWNDs; hexadecimal is accepted for diagnostics.
        return int(value, 0 if value.lower().startswith("0x") else 10)
    except (TypeError, ValueError):
        return None


def parse_saver_args(args: list[str]) -> SaverCommand:
    """Parse /s, /c[:hwnd], /p hwnd and /p:hwnd forms case-insensitively."""
    values = [str(arg).strip() for arg in args]
    lowered = [arg.lower() for arg in values]
    for index, arg in enumerate(lowered):
        token = arg.lstrip("-")
        if token == "/s" or token == "s":
            return SaverCommand("screen")
        if token in {"/c", "c"}:
            return SaverCommand("configure")
        if token.startswith("/c:") or token.startswith("c:"):
            return SaverCommand("configure", _parse_handle(values[index].split(":", 1)[1]))
        if token in {"/p", "p"}:
            parent = _parse_handle(values[index + 1]) if index + 1 < len(values) else None
            return SaverCommand("preview", parent)
        if token.startswith("/p:") or token.startswith("p:"):
            return SaverCommand("preview", _parse_handle(values[index].split(":", 1)[1]))
    return SaverCommand("screen")
