"""Custom widgets: sound cards, live spectrum visualiser, mixer rows."""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING

import numpy as np
from rich.text import Text
from textual import events
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget

from .data import ASCII_ICONS, Sound

if TYPE_CHECKING:
    from .app import MoodistApp

# ----------------------------------------------------------------- palette
BG = "#0b0b10"
MUTED = "#5b5b6b"
DIM = "#2e2e3a"
TEXT = "#e4e4ec"
PRIMARY = "#818cf8"
SECONDARY = "#c084fc"
ACCENT = "#f472b6"
GOLD = "#fbbf24"
GREEN = "#4ade80"
RED = "#f87171"

SPARK = " ▁▂▃▄▅▆▇█"
BLOCKS = " ▁▂▃▄▅▆▇█"
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def lerp_color(stops: list[str], t: float) -> str:
    t = max(0.0, min(1.0, t))
    if len(stops) == 1:
        return stops[0]
    seg = t * (len(stops) - 1)
    i = min(int(seg), len(stops) - 2)
    f = seg - i
    a, b = _hex(stops[i]), _hex(stops[i + 1])
    r, g, bl = (round(a[k] + (b[k] - a[k]) * f) for k in range(3))
    return f"#{r:02x}{g:02x}{bl:02x}"


GRADIENT = [PRIMARY, SECONDARY, ACCENT]


def gradient_text(text: str, stops: list[str] = GRADIENT, bold: bool = True) -> Text:
    out = Text()
    n = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        out.append(ch, style=f"{'bold ' if bold else ''}{lerp_color(stops, i / n)}")
    return out


def slider(width: int, value: float, active: bool = True, knob: bool = True) -> Text:
    """A horizontal gradient slider like ━━━━━━━●──────."""
    width = max(width, 3)
    filled = round(value * (width - 1))
    out = Text()
    for i in range(width):
        if i < filled:
            out.append("━", style=lerp_color(GRADIENT, i / max(width - 1, 1)) if active else MUTED)
        elif i == filled and knob:
            out.append("●", style=f"bold {TEXT}" if active else MUTED)
        else:
            out.append("─", style=DIM)
    return out


def truncate(s: str, width: int) -> str:
    if width <= 0:
        return ""
    return s if len(s) <= width else s[: max(width - 1, 0)] + "…"


# =================================================================== cards
class SoundCard(Widget, can_focus=True):
    """A single sound tile. Click / Enter toggles; the bottom row is a volume slider."""

    BINDINGS = [
        Binding("enter", "toggle", "Toggle", show=False),
        Binding("plus,equals_sign,shift+right,ctrl+right", "vol(5)", "Vol +", show=False),
        Binding("minus,underscore,shift+left,ctrl+left", "vol(-5)", "Vol −", show=False),
        Binding("up,k", "nav('up')", show=False),
        Binding("down,j", "nav('down')", show=False),
        Binding("left,h", "nav('left')", show=False),
        Binding("right,l", "nav('right')", show=False),
        Binding("f", "favorite", "Favorite", show=False),
    ]

    selected: reactive[bool] = reactive(False)
    volume: reactive[float] = reactive(0.5)
    favorite: reactive[bool] = reactive(False)
    status: reactive[str] = reactive("")  # "", "download", "decode", "error"
    progress: reactive[float] = reactive(0.0)
    live: reactive[bool] = reactive(False)  # sound is actually audible right now

    def __init__(self, sound: Sound, emoji: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sound = sound
        self.emoji = emoji
        self.history: deque[float] = deque([0.0] * 64, maxlen=64)

    @property
    def mapp(self) -> "MoodistApp":
        return self.app  # type: ignore[return-value]

    # -- state helpers ------------------------------------------------------
    def push_level(self, level: float) -> None:
        self.history.append(level)
        self.refresh()

    def watch_selected(self, value: bool) -> None:
        self.set_class(value, "-selected")
        if not value:
            self.history.extend([0.0] * self.history.maxlen)  # type: ignore[arg-type]

    def watch_status(self, value: str) -> None:
        self.set_class(value == "error", "-error")
        self.set_class(value in ("download", "decode"), "-busy")

    # -- rendering ------------------------------------------------------------
    def render(self) -> Text:
        w = max(self.content_size.width, 8)
        icon = self.sound.icon if self.emoji else f"{ASCII_ICONS.get(self.sound.category, '•')} "
        star = "★" if self.favorite else " "
        label_w = w - 2 - 2 - 2
        label_style = f"bold {TEXT}" if self.selected else ("#b4b4c4" if self.has_focus else "#8a8a9a")
        line1 = Text.assemble(
            (icon, ""), "  ", (truncate(self.sound.label, label_w).ljust(label_w), label_style), " ", (star, GOLD)
        )

        spin = SPINNER[int(time.monotonic() * 12) % len(SPINNER)]
        if self.status == "download":
            line2 = Text.assemble((f"{spin} ", PRIMARY), ("downloading ", MUTED), (f"{self.progress * 100:3.0f}%", TEXT))
            line3 = slider(w, self.progress, knob=False)
        elif self.status == "decode":
            line2 = Text.assemble((f"{spin} ", SECONDARY), ("preparing audio…", MUTED))
            line3 = slider(w, 1.0, knob=False)
        elif self.status == "error":
            line2 = Text("⚠ couldn't load · ⏎ retry", style=RED)
            line3 = Text("─" * w, style=DIM)
        elif self.selected:
            pct = f" {round(self.volume * 100):>3}%"
            if self.live:
                vals = list(self.history)[-w:]
                line2 = Text()
                for v in vals:
                    v = max(0.0, min(1.0, v))
                    line2.append(SPARK[round(v * (len(SPARK) - 1))], style=lerp_color(GRADIENT, v))
            else:
                line2 = Text.assemble(("⏸ ", MUTED), ("paused · space to play", DIM))
            line3 = slider(w - len(pct), self.volume)
            line3.append(pct, style=TEXT)
        else:
            line2 = Text("")
            hint = "⏎ add to mix" if self.has_focus else ""
            line3 = Text(hint, style=MUTED)
        return Text("\n").join([line1, line2, line3])

    def on_focus(self) -> None:
        self.refresh()
        self.mapp.card_focused(self)

    def on_blur(self) -> None:
        self.refresh()

    # -- mouse ------------------------------------------------------------
    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.focus()
        off = event.get_content_offset(self)
        if off is not None and self.selected and off.y == 2 and self.status == "":
            w = self.content_size.width - 5
            self.mapp.set_sound_volume(self.sound.id, max(0.01, min(1.0, off.x / max(w - 1, 1))))
            return
        self.mapp.toggle_sound(self.sound.id)

    def _scroll_volume(self, event: events.MouseEvent, delta: int) -> None:
        if self.selected and (event.ctrl or event.shift):
            event.stop()
            event.prevent_default()
            self.action_vol(delta)

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self._scroll_volume(event, 5)

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self._scroll_volume(event, -5)

    # -- actions ----------------------------------------------------------
    def action_toggle(self) -> None:
        self.mapp.toggle_sound(self.sound.id)

    def action_vol(self, delta: int) -> None:
        if not self.selected:
            self.mapp.toggle_sound(self.sound.id)
            return
        self.mapp.set_sound_volume(self.sound.id, max(0.01, min(1.0, self.volume + delta / 100)))

    def action_nav(self, direction: str) -> None:
        self.mapp.navigate_cards(self, direction)

    def action_favorite(self) -> None:
        self.mapp.toggle_favorite(self.sound.id)


# ============================================================== visualiser
class Visualizer(Widget):
    """Live spectrum analyser driven by the pre-analysed audio of every active track."""

    def __init__(self, bands: int = 32, **kwargs) -> None:
        super().__init__(**kwargs)
        self.values = np.zeros(bands, dtype=np.float32)
        self.peaks = np.zeros(bands, dtype=np.float32)
        self.idle_phase = 0.0

    def feed(self, spectrum: np.ndarray) -> None:
        target = np.clip(spectrum, 0, 1) ** 1.35
        rising = target > self.values
        self.values = np.where(rising, self.values + (target - self.values) * 0.65, self.values * 0.80 + target * 0.20)
        self.peaks = np.maximum(self.peaks - 0.015, self.values)
        self.idle_phase += 0.08
        self.refresh()

    def render(self) -> Text:
        w = max(self.content_size.width, 1)
        h = max(self.content_size.height, 1)
        n = len(self.values)
        xs = np.linspace(0, n - 1, w)
        vals = np.interp(xs, np.arange(n), self.values)
        peaks = np.interp(xs, np.arange(n), self.peaks)
        out = Text()
        silent = float(self.values.max(initial=0)) < 0.01
        if silent:
            # gentle breathing baseline while idle
            for r in range(h):
                if r < h - 1:
                    out.append(" " * w)
                else:
                    for i in range(w):
                        wave = 0.5 + 0.5 * np.sin(self.idle_phase + i * 0.35)
                        out.append("▁", style=lerp_color([DIM, "#3b3b5c"], wave))
                if r < h - 1:
                    out.append("\n")
            return out
        for r in range(h - 1, -1, -1):
            row_color = lerp_color(GRADIENT, r / max(h - 1, 1))
            line = []
            for i in range(w):
                fill = vals[i] * h - r
                peak_row = int(min(peaks[i], 0.999) * h)
                if fill >= 1:
                    line.append(("█", row_color))
                elif fill > 0:
                    line.append((BLOCKS[max(1, int(fill * 8))], row_color))
                elif peak_row == r and peaks[i] > 0.04:
                    line.append(("▔", "#9ca3af"))
                else:
                    line.append((" ", ""))
            for ch, st in line:
                out.append(ch, style=st)
            if r > 0:
                out.append("\n")
        return out


# ============================================================== mixer rows
class MixerRow(Widget, can_focus=True):
    """A focusable volume strip in the Now Playing panel (also used for master volume)."""

    BINDINGS = [
        Binding("right,l,plus,equals_sign", "vol(5)", "Vol +", show=False),
        Binding("left,h,minus", "vol(-5)", "Vol −", show=False),
        Binding("shift+right", "vol(1)", show=False),
        Binding("shift+left", "vol(-1)", show=False),
        Binding("up,k", "move(-1)", show=False),
        Binding("down,j", "move(1)", show=False),
        Binding("enter,delete,backspace,x", "remove", "Remove", show=False),
    ]

    volume: reactive[float] = reactive(0.5)
    level: reactive[float] = reactive(0.0)
    muted: reactive[bool] = reactive(False)

    def __init__(self, key: str, label: str, icon: str, volume: float, master: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.key = key
        self.label = label
        self.icon = icon
        self.master = master
        self.set_reactive(MixerRow.volume, volume)
        if master:
            self.add_class("-master")

    @property
    def mapp(self) -> "MoodistApp":
        return self.app  # type: ignore[return-value]

    def render(self) -> Text:
        w = max(self.content_size.width, 10)
        pct = "mute" if (self.master and self.muted) else f"{round(self.volume * 100)}%"
        meter_w = 6
        right = f" {pct:>4}"
        tail = 2 if not self.master else 0
        label_w = w - 3 - meter_w - len(right) - tail
        name_style = f"bold {TEXT}" if self.has_focus else "#c4c4d4"
        line1 = Text.assemble((self.icon, ""), " ", (truncate(self.label, label_w).ljust(label_w), name_style))
        # live level meter
        lv = max(0.0, min(1.0, self.level))
        lit = round(lv * meter_w)
        for i in range(meter_w):
            line1.append("▮" if i < lit else "▯", style=lerp_color([GREEN, GOLD, RED], i / (meter_w - 1)) if i < lit else DIM)
        line1.append(right, style=TEXT if not self.muted else MUTED)
        if not self.master:
            line1.append(" ✕", style=MUTED if not self.has_focus else RED)
        line2 = slider(w, self.volume, active=not (self.master and self.muted))
        return Text("\n").join([line1, line2])

    def on_focus(self) -> None:
        self.refresh()

    def on_blur(self) -> None:
        self.refresh()

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.focus()
        off = event.get_content_offset(self)
        if off is None:
            return
        w = self.content_size.width
        if off.y == 0 and not self.master and off.x >= w - 2:
            self.action_remove()
        elif off.y == 1:
            self._set(off.x / max(w - 1, 1))

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        event.stop()
        self.action_vol(5)

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        event.stop()
        self.action_vol(-5)

    def _set(self, vol: float) -> None:
        vol = max(0.0 if self.master else 0.01, min(1.0, vol))
        if self.master:
            self.mapp.set_master_volume(vol)
        else:
            self.mapp.set_sound_volume(self.key, vol)

    def action_vol(self, delta: int) -> None:
        self._set(self.volume + delta / 100)

    def action_move(self, delta: int) -> None:
        rows = [r for r in self.parent.query(MixerRow)] if self.parent else []
        if self.master:
            rows = [self] + list(self.screen.query("#mix-list MixerRow"))
        else:
            rows = [self.screen.query_one("#master-row", MixerRow)] + list(self.screen.query("#mix-list MixerRow"))
        try:
            idx = rows.index(self)
        except ValueError:
            return
        nxt = idx + delta
        if 0 <= nxt < len(rows):
            rows[nxt].focus()
            rows[nxt].scroll_visible()

    def action_remove(self) -> None:
        if self.master:
            self.mapp.action_mute()
        else:
            self.mapp.toggle_sound(self.key)
