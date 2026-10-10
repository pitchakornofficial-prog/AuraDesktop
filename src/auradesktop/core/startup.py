"""Windows per-user startup integration, separated for deterministic testing."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "AuraDesktop"


def build_startup_command(
    executable: str | Path,
    *,
    frozen: bool,
    entry_script: str | Path | None = None,
) -> str:
    """Build a quoted command for the Windows Run key without shell interpolation."""
    exe = Path(executable).resolve()
    if frozen:
        return f'"{exe}"'
    if entry_script is None:
        raise ValueError("entry_script is required when running from source")
    script = Path(entry_script).resolve()
    return f'"{exe}" "{script}"'


def set_windows_startup(
    enabled: bool,
    *,
    executable: str | Path | None = None,
    frozen: bool | None = None,
    entry_script: str | Path | None = None,
    winreg_module: Any = None,
) -> None:
    """Set or remove the per-user Run entry. Does not require administrator rights."""
    if os.name != "nt" and winreg_module is None:
        if enabled:
            raise RuntimeError("Windows startup integration is available only on Windows.")
        return
    if winreg_module is None:
        import winreg as winreg_module  # type: ignore[import-not-found]

    access = winreg_module.KEY_SET_VALUE
    with_key = winreg_module.OpenKey(
        winreg_module.HKEY_CURRENT_USER, RUN_KEY, 0, access
    )
    try:
        if enabled:
            exe = Path(executable or sys.executable)
            is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
            command = build_startup_command(
                exe,
                frozen=is_frozen,
                entry_script=entry_script,
            )
            winreg_module.SetValueEx(
                with_key, VALUE_NAME, 0, winreg_module.REG_SZ, command
            )
        else:
            try:
                winreg_module.DeleteValue(with_key, VALUE_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg_module.CloseKey(with_key)
