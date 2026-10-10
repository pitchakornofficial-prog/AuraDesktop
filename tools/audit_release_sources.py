"""Static pre-installer audit. Does not compile executables or run NSIS."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from auradesktop.core.release_audit import audit_release_sources  # noqa: E402


def main() -> int:
    issues = audit_release_sources(ROOT)
    print("AuraDesktop pre-installer source audit")
    if issues:
        for issue in issues:
            print(f"FAIL  {issue}")
        print("\nDo not proceed to installer creation until blocking issues are fixed.")
        return 1
    print("PASS  Build script enforces exact Python 3.15.0")
    print("PASS  Screensaver executable and .scr output are configured")
    print("PASS  NSIS uses per-user installation and has an uninstall section")
    print("\nStatic audit passed only. Windows build and runtime are not certified by this check.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
