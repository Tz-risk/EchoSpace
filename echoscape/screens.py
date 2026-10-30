"""Modal screens: help, mixes/presets, sleep timer, pomodoro, breathing, notepad, todos."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Digits, Input, OptionList, SelectionList, Static, TextArea
from textual.widgets.option_list import Option
from textual.widgets.selection_list import Selection

from .data import SOUNDS, STARTER_MIXES
from .widgets import ACCENT, DIM, GOLD, GRADIENT, GREEN, MUTED, PRIMARY, SECONDARY, TEXT, gradient_text, lerp_color

if TYPE_CHECKING:
    from .app import MoodistApp


def fmt_time(seconds: float) -> str:
    seconds = max(0, int(math.ceil(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class Modal(ModalScreen):
    """Base modal with a titled panel and escape-to-close."""

    BINDINGS = [Binding("escape", "close", "Close")]
    TITLE_TEXT = ""
    SUBTITLE_TEXT = ""

    @property
    def mapp(self) -> "MoodistApp":
        return self.app  # type: ignore[return-value]

    def panel_title(self) -> Static:
        t = gradient_text(self.TITLE_TEXT)
        if self.SUBTITLE_TEXT:
            t.append("\n" + self.SUBTITLE_TEXT, style=f"not bold {MUTED}")
        return Static(t, classes="modal-title")

    def action_close(self) -> None:
        self.dismiss(None)

    def on_click(self, event) -> None:
        # click outside the panel closes the modal
        if event.widget is self:
            self.dismiss(None)


# =================================================================== help
HELP_ROWS = [
    ("Playback", [
        ("space", "Play / pause the mix"),
        ("enter / click", "Toggle the focused sound"),
        ("+ / −  (ctrl+scroll)", "Focused sound volume"),
        (", / .", "Master volume down / up"),
        ("m", "Mute / unmute"),
        ("s", "Shuffle a random mix"),
        ("u", "Unselect all  (again to undo)"),
    ]),
    ("Navigation", [
        ("← ↑ ↓ →  /  h j k l", "Move between sounds"),
        ("tab / shift+tab", "Switch panels"),
        ("1 – 9", "Jump to a category"),
        ("/", "Search sounds"),
        ("f", "Favorite the focused sound"),
    ]),
    ("Tools", [
        ("p", "Mixes & presets"),
        ("ctrl+s", "Save current mix as preset"),
        ("t", "Sleep timer"),
        ("o", "Pomodoro timer"),
        ("b", "Breathing exercise"),
        ("n", "Notepad"),
        ("d", "Todo list"),
        ("?", "This help"),
        ("q", "Quit"),
    ]),
]


class HelpScreen(Modal):
    TITLE_TEXT = "Keyboard shortcuts"
    BINDINGS = [Binding("escape,question_mark,q", "close", "Close")]

    def compose(self) -> ComposeResult:
        body = Text()
        for i, (section, rows) in enumerate(HELP_ROWS):
            if i:
                body.append("\n")
            body.append(f"{section}\n", style=f"bold {SECONDARY}")
            for key, desc in rows:
                body.append(f"  {key:<24}", style=f"bold {PRIMARY}")
                body.append(f"{desc}\n", style=TEXT)
        body.append("\nEchoScape — sounds stream on first play and are cached locally.", style=MUTED)
        with Vertical(classes="modal-panel", id="help-panel"):
            yield self.panel_title()
            yield Static(body)


# ================================================================= mixes
class MixesScreen(Modal):
    TITLE_TEXT = "Mixes & presets"
    SUBTITLE_TEXT = "⏎ play · del remove preset · type a name below and ⏎ to save the current mix"
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("delete,backspace", "delete", "Delete preset", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-panel", id="mixes-panel"):
            yield self.panel_title()
            yield OptionList(id="mix-options")
            yield Input(placeholder="💾  Save current mix as…", id="preset-name")

    def on_mount(self) -> None:
        self.rebuild()
        self.query_one(OptionList).focus()

    def _describe(self, sounds: dict[str, float]) -> str:
        names = [SOUNDS[s].label for s in sounds if s in SOUNDS]
        return " · ".join(names[:4]) + (f" +{len(names) - 4}" if len(names) > 4 else "")

    def rebuild(self) -> None:
        ol = self.query_one(OptionList)
        ol.clear_options()
        ol.add_option(Option(Text("STARTER MIXES", style=f"bold {MUTED}"), disabled=True))
        for i, mix in enumerate(STARTER_MIXES):
            t = Text.assemble(("▶ ", PRIMARY), (mix["name"], f"bold {TEXT}"), ("\n   " + mix["description"], MUTED))
            ol.add_option(Option(t, id=f"starter:{i}"))
        presets = self.mapp.store["presets"]
        ol.add_option(Option(Text("\nYOUR MIXES", style=f"bold {MUTED}"), disabled=True))
        if not presets:
            ol.add_option(Option(Text("   nothing saved yet — build a mix and save it below", style=DIM), disabled=True))
        for i, p in enumerate(presets):
            t = Text.assemble(("★ ", GOLD), (p["name"], f"bold {TEXT}"), ("\n   " + self._describe(p["sounds"]), MUTED))
            ol.add_option(Option(t, id=f"preset:{i}"))
        if ol.highlighted is None:
            ol.highlighted = 1

    @on(OptionList.OptionSelected, "#mix-options")
    def load_mix(self, event: OptionList.OptionSelected) -> None:
        kind, _, idx = (event.option.id or "").partition(":")
        if kind == "starter":
            mix = STARTER_MIXES[int(idx)]
            self.mapp.load_mix(mix["sounds"], mix["name"])
        elif kind == "preset":
            p = self.mapp.store["presets"][int(idx)]
            self.mapp.load_mix(p["sounds"], p["name"])
        else:
            return
        self.dismiss(None)

    def action_delete(self) -> None:
        if isinstance(self.focused, Input):
            return
        ol = self.query_one(OptionList)
        if ol.highlighted is None:
            return
        opt = ol.get_option_at_index(ol.highlighted)
        kind, _, idx = (opt.id or "").partition(":")
        if kind == "preset":
            presets = self.mapp.store["presets"]
            removed = presets.pop(int(idx))
            self.mapp.store.save()
            self.mapp.notify(f"Deleted preset “{removed['name']}”", timeout=2)
            self.rebuild()

    @on(Input.Submitted, "#preset-name")
    def save_preset(self, event: Input.Submitted) -> None:
        if self.mapp.save_preset(event.value.strip()):
            event.input.value = ""
            self.rebuild()
            self.query_one(OptionList).focus()


# ============================================================ sleep timer
class SleepTimerScreen(Modal):
    TITLE_TEXT = "Sleep timer"
    SUBTITLE_TEXT = "Sounds gently fade out when the timer ends"
    CHOICES = [5, 10, 15, 20, 30, 45, 60, 90, 120, 180]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-panel", id="sleep-panel"):
            yield self.panel_title()
            yield Static(id="sleep-status")
            yield OptionList(id="sleep-options")
            yield Input(placeholder="⌨  Custom minutes (e.g. 25) then ⏎", id="sleep-custom", type="integer")

    def on_mount(self) -> None:
        ol = self.query_one(OptionList)
        if self.mapp.sleep_deadline is not None:
            ol.add_option(Option(Text("✕  Cancel the running timer", style=f"bold {ACCENT}"), id="cancel"))
        for m in self.CHOICES:
            label = f"{m} minutes" if m < 60 else (f"{m // 60} hour" + ("s" if m >= 120 else "") + (f" {m % 60} min" if m % 60 else ""))
            ol.add_option(Option(Text.assemble(("🌙 ", ""), (label, TEXT)), id=str(m)))
        ol.highlighted = 0
        ol.focus()
        self.update_status()
        self.set_interval(0.5, self.update_status)

    def update_status(self) -> None:
        remaining = self.mapp.sleep_remaining()
        if remaining is None:
            t = Text("No timer running", style=MUTED)
        else:
            t = Text.assemble(("⏳ Fading out in ", MUTED), (fmt_time(remaining), f"bold {PRIMARY}"))
        self.query_one("#sleep-status", Static).update(t)

    @on(OptionList.OptionSelected, "#sleep-options")
    def chosen(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == "cancel":
            self.mapp.set_sleep_timer(None)
        else:
            self.mapp.set_sleep_timer(int(event.option.id or 0))
        self.dismiss(None)

    @on(Input.Submitted, "#sleep-custom")
    def custom(self, event: Input.Submitted) -> None:
        try:
            minutes = int(event.value)
        except ValueError:
            return
        if minutes > 0:
            self.mapp.set_sleep_timer(minutes)
            self.dismiss(None)


# =============================================================== pomodoro
MODE_LABELS = {"pomodoro": "Focus", "short": "Short break", "long": "Long break"}


class PomodoroScreen(Modal):
    TITLE_TEXT = "Pomodoro"
    SUBTITLE_TEXT = "space start/pause · r reset · n next · 1 2 3 mode · + − adjust length"
    BINDINGS = [
        Binding("escape,q", "close", "Close"),
        Binding("space", "toggle", "Start/Pause"),
        Binding("r", "reset", "Reset"),
        Binding("n", "next", "Next"),
        Binding("1", "mode('pomodoro')", show=False),
        Binding("2", "mode('short')", show=False),
        Binding("3", "mode('long')", show=False),
        Binding("plus,equals_sign", "adjust(1)", show=False),
        Binding("minus", "adjust(-1)", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-panel", id="pomo-panel"):
            yield self.panel_title()
            with Horizontal(id="pomo-tabs"):
                for key, label in MODE_LABELS.items():
                    yield Button(label, id=f"tab-{key}", classes="tab", compact=True)
            yield Digits("25:00", id="pomo-digits")
            yield Static(id="pomo-progress")
            yield Static(id="pomo-info")
            with Horizontal(id="pomo-buttons"):
                yield Button("▶ Start", id="pomo-start", variant="primary")
                yield Button("↺ Reset", id="pomo-reset")
                yield Button("⏭ Next", id="pomo-next")

    def on_mount(self) -> None:
        self.refresh_view()
        self.set_interval(0.25, self.refresh_view)

    def refresh_view(self) -> None:
        p = self.mapp.pomodoro
        total = p.durations[p.mode] * 60
        self.query_one("#pomo-digits", Digits).update(fmt_time(p.remaining))
        for key in MODE_LABELS:
            self.query_one(f"#tab-{key}", Button).set_class(key == p.mode, "-active")
        w = 44
        frac = 1 - p.remaining / total if total else 0
        bar = Text()
        filled = round(frac * w)
        for i in range(w):
            bar.append("█" if i < filled else "░", style=lerp_color(GRADIENT, i / (w - 1)) if i < filled else DIM)
        self.query_one("#pomo-progress", Static).update(bar)
        dots = "".join("●" if i < p.completed % 4 else "○" for i in range(4))
        info = Text.assemble(
            (f"{MODE_LABELS[p.mode]}", f"bold {SECONDARY}"), ("  ·  ", MUTED),
            (f"{p.durations[p.mode]} min", TEXT), ("  ·  ", MUTED),
            ("round ", MUTED), (dots, PRIMARY), ("  ·  ", MUTED),
            (f"{p.completed} done", GREEN),
        )
        self.query_one("#pomo-info", Static).update(info)
        self.query_one("#pomo-start", Button).label = "⏸ Pause" if p.running else "▶ Start"

    def action_toggle(self) -> None:
        self.mapp.pomodoro.toggle()
        self.refresh_view()

    def action_reset(self) -> None:
        self.mapp.pomodoro.reset()
        self.refresh_view()

    def action_next(self) -> None:
        self.mapp.pomodoro.advance(manual=True)
        self.refresh_view()

    def action_mode(self, mode: str) -> None:
        self.mapp.pomodoro.set_mode(mode)
        self.refresh_view()

    def action_adjust(self, delta: int) -> None:
        p = self.mapp.pomodoro
        p.durations[p.mode] = max(1, min(180, p.durations[p.mode] + delta))
        if not p.running:
            p.reset()
        self.mapp.store["pomodoro"] = dict(p.durations)
        self.mapp.store.save()
        self.refresh_view()

    @on(Button.Pressed)
    def pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("tab-"):
            self.action_mode(bid[4:])
        elif bid == "pomo-start":
            self.action_toggle()
        elif bid == "pomo-reset":
            self.action_reset()
        elif bid == "pomo-next":
            self.action_next()


# ============================================================== breathing
EXERCISES: dict[str, list[tuple[str, float]]] = {
    "4-7-8 Breathing": [("inhale", 4), ("holdInhale", 7), ("exhale", 8)],
    "Box Breathing": [("inhale", 4), ("holdInhale", 4), ("exhale", 4), ("holdExhale", 4)],
    "Resonant Breathing": [("inhale", 5), ("exhale", 5)],
}
PHASE_LABELS = {"inhale": "Inhale", "exhale": "Exhale", "holdInhale": "Hold", "holdExhale": "Hold"}


class BreathCircle(Widget):
    """A smooth, half-block rendered orb that grows and shrinks with your breath."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.scale = 0.0  # 0 = small, 1 = big

    def render(self) -> Text:
        w, h = self.content_size.width, self.content_size.height
        ph = h * 2
        cx, cy = (w - 1) / 2, (ph - 1) / 2
        max_r = min(w / 2, ph / 2) - 1
        r = max_r * (0.42 + 0.58 * self.scale)
        guide = max_r
        out = Text()

        def px(x: int, y: int) -> str | None:
            d = math.hypot(x - cx, (y - cy))
            if d <= r:
                t = d / max(r, 1)
                return lerp_color([ACCENT, SECONDARY, PRIMARY], t ** 0.8)
            if abs(d - guide) < 0.55:
                return "#24243a"
            return None

        for row in range(h):
            for x in range(w):
                top, bot = px(x, row * 2), px(x, row * 2 + 1)
                if top and bot:
                    out.append("▀", style=f"{top} on {bot}")
                elif top:
                    out.append("▀", style=top)
                elif bot:
                    out.append("▄", style=bot)
                else:
                    out.append(" ")
            if row < h - 1:
                out.append("\n")
        return out


class BreathingScreen(Modal):
    TITLE_TEXT = "Breathing exercise"
    SUBTITLE_TEXT = "← → change exercise · esc close"
    BINDINGS = [
        Binding("escape,q", "close", "Close"),
        Binding("left,h", "cycle(-1)", "Prev"),
        Binding("right,l", "cycle(1)", "Next"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-panel", id="breath-panel"):
            yield self.panel_title()
            yield Static(id="breath-select")
            yield BreathCircle(id="breath-circle")
            yield Static(id="breath-phase")

    def on_mount(self) -> None:
        name = self.mapp.store["breathing"]
        self.exercise = name if name in EXERCISES else "4-7-8 Breathing"
        self.start = time.monotonic()
        self.set_interval(1 / 30, self.tick)
        self.tick()

    def action_cycle(self, delta: int) -> None:
        names = list(EXERCISES)
        self.exercise = names[(names.index(self.exercise) + delta) % len(names)]
        self.mapp.store["breathing"] = self.exercise
        self.mapp.store.save()
        self.start = time.monotonic()

    def tick(self) -> None:
        phases = EXERCISES[self.exercise]
        cycle = sum(d for _, d in phases)
        elapsed = time.monotonic() - self.start
        t = elapsed % cycle
        for phase, dur in phases:
            if t < dur:
                break
            t -= dur
        frac = t / dur
        ease = 0.5 - 0.5 * math.cos(math.pi * frac)
        scale = {"inhale": ease, "exhale": 1 - ease, "holdInhale": 1.0, "holdExhale": 0.0}[phase]
        circle = self.query_one(BreathCircle)
        circle.scale = scale
        circle.refresh()

        sel = Text(justify="center")
        for i, name in enumerate(EXERCISES):
            if i:
                sel.append("   ")
            if name == self.exercise:
                sel.append(f"‹ {name} ›", style=f"bold {TEXT} on #1e1b4b")
            else:
                sel.append(name, style=MUTED)
        self.query_one("#breath-select", Static).update(sel)

        remaining = math.ceil(dur - t)
        ph = Text(justify="center")
        ph.append_text(gradient_text(PHASE_LABELS[phase].upper().replace("", " ").strip()))
        ph.append(f"\n{remaining}", style=f"bold {TEXT}")
        ph.append(f"\nsession {fmt_time(elapsed)}", style=MUTED)
        self.query_one("#breath-phase", Static).update(ph)


# ================================================================ notepad
class NotepadScreen(Modal):
    TITLE_TEXT = "Notepad"
    SUBTITLE_TEXT = "Auto-saved · esc close"

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-panel", id="notes-panel"):
            yield self.panel_title()
            yield TextArea(self.mapp.store["notes"], id="notes", soft_wrap=True, placeholder="Write something…")
            yield Static(id="notes-stats")

    def on_mount(self) -> None:
        ta = self.query_one(TextArea)
        ta.focus()
        ta.move_cursor(ta.document.end)
        self.update_stats()

    def update_stats(self) -> None:
        text = self.query_one(TextArea).text
        words = len(text.split())
        self.query_one("#notes-stats", Static).update(
            Text.assemble((f"{len(text)}", TEXT), (" chars  ·  ", MUTED), (f"{words}", TEXT), (" words", MUTED))
        )

    @on(TextArea.Changed)
    def changed(self) -> None:
        self.mapp.store["notes"] = self.query_one(TextArea).text
        self.update_stats()

    def action_close(self) -> None:
        self.mapp.store.save()
        self.dismiss(None)


# ================================================================== todos
class TodoScreen(Modal):
    TITLE_TEXT = "Todo list"
    SUBTITLE_TEXT = "⏎ add · space toggle · del remove · c clear done"
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("delete,backspace", "delete", "Delete", show=False),
        Binding("c", "clear_done", "Clear done", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-panel", id="todo-panel"):
            yield self.panel_title()
            yield Input(placeholder="＋ What do you need to do?", id="todo-input")
            yield SelectionList[int](id="todo-list")
            yield Static(id="todo-stats")

    def on_mount(self) -> None:
        self.rebuild()
        self.query_one(Input).focus()

    @property
    def todos(self) -> list[dict]:
        return self.mapp.store["todos"]

    def rebuild(self, highlight: int | None = None) -> None:
        sl = self.query_one(SelectionList)
        with self.app.batch_update():
            sl.clear_options()
            for i, todo in enumerate(self.todos):
                prompt = Text(todo["text"], style=f"strike {MUTED}" if todo["done"] else TEXT)
                sl.add_option(Selection(prompt, i, todo["done"]))
            if self.todos:
                sl.highlighted = min(highlight or 0, len(self.todos) - 1)
        done = sum(t["done"] for t in self.todos)
        self.query_one("#todo-stats", Static).update(
            Text.assemble((f"{done}", GREEN), (f"/{len(self.todos)} done", MUTED))
            if self.todos else Text("Nothing to do. Enjoy the calm. 🌿", style=MUTED)
        )

    def save(self) -> None:
        self.mapp.store.save()

    @on(Input.Submitted, "#todo-input")
    def add(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.todos.append({"text": text, "done": False})
            event.input.value = ""
            self.save()
            self.rebuild(len(self.todos) - 1)

    @on(SelectionList.SelectionToggled)
    def toggled(self, event: SelectionList.SelectionToggled) -> None:
        idx = event.selection.value
        if 0 <= idx < len(self.todos):
            self.todos[idx]["done"] = not self.todos[idx]["done"]
            self.save()
            self.rebuild(idx)

    def action_delete(self) -> None:
        if isinstance(self.focused, Input):
            return
        sl = self.query_one(SelectionList)
        if sl.highlighted is not None and self.todos:
            idx = sl.highlighted
            self.todos.pop(idx)
            self.save()
            self.rebuild(max(0, idx - 1) if idx >= len(self.todos) else idx)

    def action_clear_done(self) -> None:
        if isinstance(self.focused, Input):
            return
        self.mapp.store["todos"] = [t for t in self.todos if not t["done"]]
        self.save()
        self.rebuild()
