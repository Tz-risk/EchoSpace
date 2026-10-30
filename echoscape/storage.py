"""Persistent state (favourites, presets, notes, todos, last session)."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any


def _base_dir(env: str, fallback: str) -> Path:
    root = os.environ.get(env)
    return Path(root) if root else Path.home() / fallback


_HOME_OVERRIDE = os.environ.get("ECHOSCAPE_HOME") or os.environ.get("MOODIST_TUI_HOME")
if _HOME_OVERRIDE:
    CONFIG_DIR = Path(_HOME_OVERRIDE)
    CACHE_DIR = Path(_HOME_OVERRIDE) / "sounds"
else:
    _legacy_cfg = _base_dir("APPDATA", ".config") / "moodist-tui"
    _legacy_cache = _base_dir("LOCALAPPDATA", ".cache") / "moodist-tui" / "sounds"
    CONFIG_DIR = _legacy_cfg if _legacy_cfg.exists() else _base_dir("APPDATA", ".config") / "echoscape"
    CACHE_DIR = _legacy_cache if _legacy_cache.exists() else _base_dir("LOCALAPPDATA", ".cache") / "echoscape" / "sounds"
STATE_FILE = CONFIG_DIR / "state.json"

DEFAULT_STATE: dict[str, Any] = {
    "master_volume": 0.8,
    "selected": {},  # sound_id -> volume
    "favorites": [],
    "presets": [],  # [{"name": str, "sounds": {id: vol}}]
    "notes": "",
    "todos": [],  # [{"text": str, "done": bool}]
    "pomodoro": {"pomodoro": 25, "short": 5, "long": 15},
    "breathing": "4-7-8 Breathing",
}


class Store:
    def __init__(self, path: Path = STATE_FILE) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.data: dict[str, Any] = json.loads(json.dumps(DEFAULT_STATE))
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self.data.update(raw)
        except (OSError, ValueError):
            pass

    def save(self) -> None:
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
                tmp.replace(self.path)
            except OSError:
                pass

    def __getitem__(self, key: str) -> Any:
        return self.data.get(key, DEFAULT_STATE.get(key))

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value
