"""Audio engine: looping multi-track mixer (pygame) + real-time spectrum data (numpy)."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

BANDS = 32  # spectrum resolution
FPS = 20  # analysis frames per second of audio
WINDOW = 2048


@dataclass
class Track:
    sound: "pygame.mixer.Sound"
    duration: float
    spectrum: np.ndarray | None = None  # (frames, BANDS) in 0..1
    level: np.ndarray | None = None  # (frames,) in 0..1
    channel: "pygame.mixer.Channel | None" = None
    start_clock: float = 0.0
    volume: float = 0.5
    extra: dict = field(default_factory=dict)


def analyze(snd: "pygame.mixer.Sound") -> tuple[np.ndarray, np.ndarray] | None:
    """Pre-compute a log-frequency spectrogram + loudness envelope for visualisation."""
    init = pygame.mixer.get_init()
    if not init:
        return None
    freq = init[0]
    arr = pygame.sndarray.array(snd)
    if arr.ndim == 2:
        mono = arr.mean(axis=1, dtype=np.float32)
    else:
        mono = arr.astype(np.float32)
    del arr
    scale = 32768.0 if np.abs(mono).max(initial=0) > 2 else 1.0
    mono /= scale
    hop = freq // FPS
    n = len(mono) // hop
    if n < 2:
        return None
    win = min(WINDOW, hop)
    frames = mono[: n * hop].reshape(n, hop)[:, :win]
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1)).astype(np.float32)
    frames = frames * np.hanning(win).astype(np.float32)
    mag = np.abs(np.fft.rfft(frames, axis=1)).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1.0 / freq)
    edges = np.geomspace(45, min(15000, freq / 2 - 1), BANDS + 1)
    bands = np.empty((n, BANDS), dtype=np.float32)
    for i in range(BANDS):
        lo, hi = edges[i], edges[i + 1]
        idx = np.nonzero((freqs >= lo) & (freqs < hi))[0]
        if idx.size == 0:
            idx = np.array([int(np.argmin(np.abs(freqs - (lo + hi) / 2)))])
        bands[:, i] = mag[:, idx].mean(axis=1)
    db = 20.0 * np.log10(bands + 1e-7)
    ref = float(np.percentile(db, 99.5))
    spec = np.clip((db - (ref - 42.0)) / 42.0, 0.0, 1.0).astype(np.float32)
    lref = float(np.percentile(rms, 99)) or 1.0
    level = np.clip(rms / lref, 0.0, 1.0).astype(np.float32)
    return spec, level


class AudioEngine:
    def __init__(self) -> None:
        self.available = True
        self.error = ""
        try:
            pygame.mixer.pre_init(44100, -16, 2, 2048)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(64)
        except Exception as exc:  # pragma: no cover - depends on host audio
            self.available = False
            self.error = str(exc)
        self.tracks: dict[str, Track] = {}
        self.master = 0.8
        self.muted = False
        self.playing = False
        self._clock = 0.0
        self._last = time.monotonic()
        self._lock = threading.RLock()
        self._decode_lock = threading.Lock()

    # ------------------------------------------------------------------ clock
    def clock(self) -> float:
        now = time.monotonic()
        if self.playing:
            self._clock += now - self._last
        self._last = now
        return self._clock

    # ---------------------------------------------------------------- loading
    def is_loaded(self, sid: str) -> bool:
        return sid in self.tracks

    def load(self, sid: str, path: Path) -> Track:
        """Decode + analyse a file. Safe to call from a worker thread."""
        if not self.available:
            raise RuntimeError(self.error or "audio unavailable")
        if sid in self.tracks:
            return self.tracks[sid]
        with self._decode_lock:
            if sid in self.tracks:
                return self.tracks[sid]
            snd = pygame.mixer.Sound(str(path))
            track = Track(sound=snd, duration=max(snd.get_length(), 0.1))
            try:
                res = analyze(snd)
                if res is not None:
                    track.spectrum, track.level = res
            except Exception:
                pass
        with self._lock:
            self.tracks[sid] = track
        return track

    # --------------------------------------------------------------- playback
    def _effective(self, vol: float) -> float:
        return 0.0 if self.muted else max(0.0, min(1.0, vol * self.master))

    def is_active(self, sid: str) -> bool:
        t = self.tracks.get(sid)
        if not t or t.channel is None:
            return False
        try:
            return bool(t.channel.get_busy()) and t.channel.get_sound() is t.sound
        except Exception:
            return False

    def play(self, sid: str, volume: float, fade_ms: int = 900) -> None:
        with self._lock:
            t = self.tracks.get(sid)
            if not t or not self.available:
                return
            t.volume = volume
            t.sound.set_volume(self._effective(volume))
            if self.is_active(sid):
                return
            ch = t.sound.play(loops=-1, fade_ms=fade_ms)
            t.channel = ch
            t.start_clock = self.clock()

    def stop(self, sid: str, fade_ms: int = 450) -> None:
        with self._lock:
            t = self.tracks.get(sid)
            if not t or t.channel is None:
                return
            ch, t.channel = t.channel, None
            try:
                if ch.get_sound() is t.sound:
                    if self.playing and fade_ms:
                        ch.fadeout(fade_ms)
                    else:
                        ch.stop()
            except Exception:
                pass

    def set_volume(self, sid: str, volume: float) -> None:
        t = self.tracks.get(sid)
        if t:
            t.volume = volume
            t.sound.set_volume(self._effective(volume))

    def set_master(self, master: float, muted: bool | None = None) -> None:
        self.master = max(0.0, min(1.0, master))
        if muted is not None:
            self.muted = muted
        for t in self.tracks.values():
            t.sound.set_volume(self._effective(t.volume))

    def pause(self) -> None:
        self.clock()
        self.playing = False
        if self.available:
            pygame.mixer.pause()

    def resume(self) -> None:
        self.clock()
        self.playing = True
        if self.available:
            pygame.mixer.unpause()

    def fade_out_all(self, ms: int = 4000) -> None:
        """Gracefully fade everything to silence (sleep timer)."""
        self.clock()
        for t in self.tracks.values():
            if t.channel is not None:
                try:
                    t.channel.fadeout(ms)
                except Exception:
                    pass
                t.channel = None
        self.playing = False

    def stop_all(self) -> None:
        for sid in list(self.tracks):
            self.stop(sid, fade_ms=0)

    def shutdown(self) -> None:
        if self.available:
            try:
                pygame.mixer.quit()
            except Exception:
                pass

    # ---------------------------------------------------------- visualisation
    def snapshot(self) -> tuple[np.ndarray, dict[str, float]]:
        """Return combined spectrum (BANDS,) and per-track live levels."""
        clock = self.clock()
        out = np.ones(BANDS, dtype=np.float32)
        levels: dict[str, float] = {}
        any_live = False
        if not self.playing:
            return np.zeros(BANDS, dtype=np.float32), levels
        for sid, t in list(self.tracks.items()):
            if t.channel is None:
                continue
            v = self._effective(t.volume)
            pos = (clock - t.start_clock) % t.duration
            ramp = min(1.0, (clock - t.start_clock) / 0.9)  # follow the fade-in
            if t.spectrum is not None and len(t.spectrum):
                f = int(pos * FPS) % len(t.spectrum)
                out *= 1.0 - np.clip(t.spectrum[f] * (v ** 0.6) * ramp, 0.0, 1.0)
                levels[sid] = float(t.level[f]) * ramp if t.level is not None else v
            else:
                jitter = np.random.default_rng().random(BANDS).astype(np.float32) * 0.5 + 0.25
                out *= 1.0 - jitter * v * ramp
                levels[sid] = v * ramp
            any_live = True
        if not any_live:
            return np.zeros(BANDS, dtype=np.float32), levels
        return 1.0 - out, levels
