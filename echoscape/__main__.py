"""Command-line entry point for EchoScape."""

from __future__ import annotations

import argparse
import sys


def _download_all() -> int:
    from . import downloader
    from .data import SOUNDS

    total = len(SOUNDS)
    failed = 0
    for i, snd in enumerate(SOUNDS.values(), 1):
        tag = f"[{i:>2}/{total}] {snd.label:<22}"
        if downloader.is_cached(snd):
            print(f"{tag} cached")
            continue
        try:
            downloader.download(snd, lambda p: print(f"\r{tag} {p * 100:5.1f}%", end="", flush=True))
            print(f"\r{tag} done  ")
        except Exception as exc:
            failed += 1
            print(f"\r{tag} FAILED ({exc})")
    print(f"\nCached in {downloader.CACHE_DIR}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="echoscape", description="EchoScape — ambient sound mixer for your terminal.")
    parser.add_argument("--ascii", action="store_true", help="use plain symbols instead of emoji icons")
    parser.add_argument("--download-all", action="store_true", help="pre-download every sound for offline use and exit")
    args = parser.parse_args()

    if args.download_all:
        return _download_all()

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

    from .app import EchoScapeApp

    EchoScapeApp(emoji=not args.ascii).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
