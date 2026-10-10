"""Deterministic image-source discovery for wallpaper and screensaver features."""
from __future__ import annotations
from pathlib import Path
from collections.abc import Iterable

IMAGE_SUFFIXES = frozenset({'.png', '.jpg', '.jpeg', '.bmp', '.webp'})


def image_files_from_paths(paths: Iterable[object]) -> list[Path]:
    """Keep existing image files only, preserving user-selected order and removing duplicates."""
    result: list[Path] = []
    seen: set[str] = set()
    for raw in paths:
        if not isinstance(raw, (str, Path)) or not str(raw).strip():
            continue
        path = Path(str(raw).strip()).expanduser()
        try:
            if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            # resolve(strict=True) makes aliases to the same file deduplicate.
            canonical = str(path.resolve(strict=True))
        except (OSError, RuntimeError):
            continue
        key = canonical.casefold()
        if key not in seen:
            result.append(path)
            seen.add(key)
    return result


def image_files_in_folder(folder: object) -> list[Path]:
    """Return supported image files from a folder in stable, case-insensitive order."""
    if not isinstance(folder, (str, Path)) or not str(folder).strip():
        return []
    root = Path(str(folder).strip()).expanduser()
    try:
        if not root.is_dir():
            return []
        candidates = sorted(root.iterdir(), key=lambda p: (p.name.casefold(), p.name))
    except OSError:
        return []
    return image_files_from_paths(candidates)


def discover_screensaver_images(source: object) -> list[Path]:
    """Accept either newline-separated favorite paths or a separate folder path."""
    if not isinstance(source, (str, Path)):
        return []
    raw = str(source)
    if not raw.strip():
        return []
    if '\n' in raw or '\r' in raw:
        return image_files_from_paths(raw.splitlines())
    return image_files_in_folder(raw)
