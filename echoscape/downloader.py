"""Download + cache EchoScape sound files."""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Callable

from .data import Sound
from .storage import CACHE_DIR

USER_AGENT = "Mozilla/5.0 (EchoScape/1.0)"


def cache_path(sound: Sound) -> Path:
    return CACHE_DIR / sound.filename


def is_cached(sound: Sound) -> bool:
    p = cache_path(sound)
    return p.exists() and p.stat().st_size > 0


def download(sound: Sound, progress: Callable[[float], None] | None = None, timeout: float = 30) -> Path:
    """Download *sound* into the cache (if needed) and return the local path."""
    target = cache_path(sound)
    if is_cached(sound):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    req = urllib.request.Request(sound.url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(part, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(64 * 1024)
            if not chunk:
                break
            fh.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(min(done / total, 1.0))
    part.replace(target)
    if progress:
        progress(1.0)
    return target
