"""EchoScape — the main Textual application."""

from __future__ import annotations

import random
import time
from functools import partial

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ItemGrid, Vertical, VerticalScroll
from textual.theme import Theme
from textual.widgets import Button, Footer, Input, OptionList, Static
from textual.widgets.option_list import Option

from . import downloader
from .audio import BANDS, AudioEngine
from .data import ASCII_ICONS, CATEGORIES, CATEGORY_BY_ID, SOUNDS
from .screens import (
    BreathingScreen,
    HelpScreen,
    MixesScreen,
    NotepadScreen,
    PomodoroScreen,
    SleepTimerScreen,
    TodoScreen,
    fmt_time,
)
from .storage import Store
from .widgets import (
    ACCENT,
    DIM,
    GOLD,
    GREEN,
    MUTED,
    PRIMARY,
    SECONDARY,
    TEXT,
    MixerRow,
    SoundCard,
    Visualizer,
    gradient_text,
)

CARD_MIN_WIDTH = 26
DEFAULT_VOLUME = 0.5

ECHOSCAPE_THEME = Theme(
    name="echoscape",
    primary=PRIMARY,
    secondary=SECONDARY,
    accent=ACCENT,
    foreground=TEXT,
    background="#09090d",
    surface="#111117",
    panel="#16161e",
    success=GREEN,
    warning=GOLD,
    error="#f87171",
    dark=True,
)


class Pomodoro:
    MODES = ("pomodoro", "short", "long")

    def __init__(self, durations: dict[str, int]) -> None:
        self.durations = {"pomodoro": 25, "short": 5, "long": 15, **durations}
        self.mode = "pomodoro"
        self.remaining = float(self.durations[self.mode] * 60)
        self.running = False
        self.completed = 0
        self._last = time.monotonic()

    @property
    def active(self) -> bool:
        return self.running or self.remaining < self.durations[self.mode] * 60

    def toggle(self) -> None:
        self.running = not self.running
        self._last = time.monotonic()

    def reset(self) -> None:
        self.running = False
        self.remaining = float(self.durations[self.mode] * 60)

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.reset()

    def advance(self, manual: bool = False) -> None:
        if self.mode == "pomodoro":
            if not manual:
                self.completed += 1
            nxt = "long" if self.completed and self.completed % 4 == 0 and not manual else "short"
        else:
            nxt = "pomodoro"
        self.set_mode(nxt)

    def tick(self) -> str | None:
        now = time.monotonic()
        dt, self._last = now - self._last, now
        if not self.running:
            return None
        self.remaining -= dt
        if self.remaining <= 0:
            finished = self.mode
            self.advance()
            return finished
        return None


class EchoScapeApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "EchoScape"

    BINDINGS = [
        Binding("space", "play_pause", "Play/Pause"),
        Binding("slash", "search", "Search"),
        Binding("s", "shuffle", "Shuffle"),
        Binding("p", "mixes", "Mixes"),
        Binding("t", "sleep", "Sleep"),
        Binding("o", "pomodoro", "Pomodoro"),
        Binding("b", "breathe", "Breathe"),
        Binding("n", "notes", "Notes"),
        Binding("d", "todos", "Todos"),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
        Binding("comma", "master(-5)", "Vol −", show=False),
        Binding("full_stop", "master(5)", "Vol +", show=False),
        Binding("m", "mute", "Mute", show=False),
        Binding("u", "unselect", "Unselect all", show=False),
        Binding("ctrl+s", "save_preset", "Save mix", show=False),
        Binding("escape", "escape", show=False),
        *[Binding(str(i + 1), f"jump({i})", show=False) for i in range(min(9, len(CATEGORIES)))],
    ]

    def __init__(self, emoji: bool = True) -> None:
        super().__init__()
        self.emoji = emoji
        self.store = Store()
        self.engine = AudioEngine()
        self.selected: dict[str, float] = {}
        self.last_volumes: dict[str, float] = {}
        self.favorites: list[str] = [f for f in self.store["favorites"] if f in SOUNDS]
        self.master = float(self.store["master_volume"])
        self.muted = False
        self.playing = False
        self.loading: set[str] = set()
        self.cards: dict[str, list[SoundCard]] = {}
        self.undo_selection: dict[str, float] | None = None
        self.mix_name: str | None = None
        self.sleep_deadline: float | None = None
        self.pomodoro = Pomodoro(self.store["pomodoro"])
        self.engine.set_master(self.master, False)

    # ================================================================ layout
    def icon(self, sound_or_cat) -> str:
        if self.emoji:
            return sound_or_cat.icon
        cid = getattr(sound_or_cat, "category", None) or sound_or_cat.id
        return ASCII_ICONS.get(cid, "•")

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static(id="brand")
            yield Static(id="status")
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("CATEGORIES", classes="side-label")
                yield OptionList(*self._nav_options(), id="nav")
                yield Static(id="side-foot")
            with Vertical(id="main"):
                yield Input(placeholder="🔍  Search sounds…  (esc to clear)", id="search")
                with VerticalScroll(id="sounds"):
                    with Vertical(id="sec-favorites", classes="section"):
                        yield Static(self._section_title("★", "Favorites", "your starred sounds"), classes="section-title")
                        yield ItemGrid(id="grid-favorites", min_column_width=CARD_MIN_WIDTH, max_column_width=CARD_MIN_WIDTH + 14)
                    for cat in CATEGORIES:
                        with Vertical(id=f"sec-{cat.id}", classes="section"):
                            yield Static(self._section_title(self.icon(cat), cat.title, f"{len(cat.sounds)} sounds"), classes="section-title")
                            with ItemGrid(id=f"grid-{cat.id}", min_column_width=CARD_MIN_WIDTH):
                                for snd in cat.sounds:
                                    yield SoundCard(snd, emoji=self.emoji)
                    yield Static("No sounds match your search.", id="no-results")
            with Vertical(id="right"):
                with Vertical(id="now-panel"):
                    yield Visualizer(bands=BANDS, id="viz")
                    yield Static(id="play-state")
                    with Horizontal(id="controls"):
                        yield Button("▶ Play", id="btn-play", compact=True, action="app.play_pause")
                        yield Button("⤨ Shuffle", id="btn-shuffle", compact=True, action="app.shuffle")
                    with Horizontal(id="controls2"):
                        yield Button("♫ Mixes", id="btn-mixes", compact=True, action="app.mixes")
                        yield Button("✕ Clear", id="btn-clear", compact=True, action="app.unselect")
                    yield MixerRow("__master__", "Master volume", "🔊" if self.emoji else "♪", self.master, master=True, id="master-row")
                with VerticalScroll(id="mix-list"):
                    yield Static(id="mix-empty")
                with Vertical(id="tools"):
                    yield Button("", id="tool-sleep", compact=True, action="app.sleep")
                    yield Button("", id="tool-pomo", compact=True, action="app.pomodoro")
                    yield Button(f"{'🧘' if self.emoji else '○'} Breathe", id="tool-breathe", compact=True, action="app.breathe")
                    yield Button(f"{'📝' if self.emoji else '≡'} Notepad", id="tool-notes", compact=True, action="app.notes")
                    yield Button("", id="tool-todo", compact=True, action="app.todos")
        yield Footer()

    def _section_title(self, icon: str, title: str, sub: str) -> Text:
        t = Text.assemble((icon, ""), "  ")
        t.append_text(gradient_text(title))
        t.append(f"   {sub}", style=MUTED)
        return t

    def _nav_options(self) -> list[Option]:
        return [Option(self._nav_prompt(i, cat), id=cat.id) for i, cat in enumerate(CATEGORIES)]

    def _nav_prompt(self, i: int, cat) -> Text:
        count = sum(1 for s in cat.sounds if s.id in self.selected)
        t = Text.assemble((f"{i + 1} ", DIM), (self.icon(cat), ""), " ", (cat.title.ljust(10), TEXT))
        t.append(f" {'●' * min(count, 3)}{'+' if count > 3 else ''}".ljust(5), style=ACCENT if count else DIM)
        return t

    # ================================================================ mount
    def on_mount(self) -> None:
        self.register_theme(ECHOSCAPE_THEME)
        self.theme = "echoscape"
        self.query_one("#search").display = False
        self.query_one("#no-results").display = False
        self.query_one("#now-panel").border_title = "NOW PLAYING"
        self.query_one("#mix-list").border_title = "YOUR MIX"
        self.query_one("#tools").border_title = "TOOLBOX"
        self.query_one("#sounds").border_title = "SOUNDS"
        brand = Text.assemble(("◐ ", f"bold {ACCENT}"))
        brand.append_text(gradient_text("E c h o S c a p e"))
        brand.append("   ambient sounds for focus and calm", style=MUTED)
        self.query_one("#brand", Static).update(brand)
        self.query_one("#side-foot", Static).update(
            Text.assemble(("? ", f"bold {PRIMARY}"), ("all shortcuts\n", MUTED), ("◐ ", ACCENT), ("EchoScape", MUTED))
        )
        self._rebuild_favorites()
        self._index_cards()
        if not self.engine.available:
            self.notify(f"Audio device unavailable: {self.engine.error}", severity="error", timeout=8)
        # restore the previous session (paused)
        for sid, vol in (self.store["selected"] or {}).items():
            if sid in SOUNDS:
                self._select(sid, float(vol), autoplay=False)
        self._refresh_all()
        first = self.query(SoundCard).first()
        if first:
            first.focus()
        self.set_interval(1 / 15, self._tick)
        self.set_interval(0.5, self._slow_tick)
        if self.selected:
            self.notify("Restored your last mix — press [b]space[/b] to play.", timeout=4)
        else:
            self.notify("Welcome! Pick a sound with [b]⏎[/b] or a click. Press [b]?[/b] for shortcuts.", timeout=6)

    def _index_cards(self) -> None:
        self.cards = {}
        for card in self.query(SoundCard):
            self.cards.setdefault(card.sound.id, []).append(card)

    def _rebuild_favorites(self) -> None:
        grid = self.query_one("#grid-favorites", ItemGrid)
        grid.remove_children()
        cards = []
        for sid in self.favorites:
            card = SoundCard(SOUNDS[sid], emoji=self.emoji)
            card.favorite = True
            card.selected = sid in self.selected
            card.volume = self.selected.get(sid, DEFAULT_VOLUME)
            cards.append(card)
        if cards:
            grid.mount(*cards)
        self.query_one("#sec-favorites").display = bool(cards)

    # ============================================================== state ops
    def _cards_for(self, sid: str) -> list[SoundCard]:
        return [c for c in self.cards.get(sid, []) if c.is_attached]

    def _sync_card(self, sid: str) -> None:
        for card in self._cards_for(sid):
            card.selected = sid in self.selected
            card.volume = self.selected.get(sid, self.last_volumes.get(sid, DEFAULT_VOLUME))
            card.favorite = sid in self.favorites
            card.refresh()

    def _select(self, sid: str, volume: float, autoplay: bool = True) -> None:
        self.selected[sid] = volume
        self._sync_card(sid)
        self._add_mixer_row(sid)
        self._ensure_ready(sid)
        if autoplay and not self.playing:
            self.action_play()

    def _deselect(self, sid: str) -> None:
        vol = self.selected.pop(sid, None)
        if vol is not None:
            self.last_volumes[sid] = vol
        self.engine.stop(sid)
        self._sync_card(sid)
        for row in self.query(f"#mix-{sid}"):
            row.remove()

    def toggle_sound(self, sid: str) -> None:
        cards = self._cards_for(sid)
        if cards and cards[0].status == "error":
            for c in cards:
                c.status = ""
            self.loading.discard(sid)
            self._ensure_ready(sid)
            return
        if sid in self.selected:
            self._deselect(sid)
        else:
            self.undo_selection = None
            self._select(sid, self.last_volumes.get(sid, DEFAULT_VOLUME))
        self.mix_name = None
        self._refresh_all()

    def set_sound_volume(self, sid: str, volume: float) -> None:
        volume = round(max(0.01, min(1.0, volume)), 2)
        if sid not in self.selected:
            return
        self.selected[sid] = volume
        self.engine.set_volume(sid, volume)
        for card in self._cards_for(sid):
            card.volume = volume
        for row in self.query(f"#mix-{sid}"):
            row.volume = volume  # type: ignore[attr-defined]
        self._save_session()

    def set_master_volume(self, volume: float) -> None:
        self.master = round(max(0.0, min(1.0, volume)), 2)
        self.muted = False
        self.engine.set_master(self.master, self.muted)
        row = self.query_one("#master-row", MixerRow)
        row.volume = self.master
        row.muted = False
        self._refresh_status()
        self._save_session()

    def toggle_favorite(self, sid: str) -> None:
        if sid in self.favorites:
            self.favorites.remove(sid)
            self.notify(f"Removed {SOUNDS[sid].label} from favorites", timeout=2)
        else:
            self.favorites.append(sid)
            self.notify(f"★ Added {SOUNDS[sid].label} to favorites", timeout=2)
        self.store["favorites"] = self.favorites
        self.store.save()
        focused = self.focused
        self._rebuild_favorites()
        self.call_after_refresh(self._after_favorites, sid, focused)

    def _after_favorites(self, sid: str, focused) -> None:
        self._index_cards()
        self._sync_card(sid)
        if focused is not None and not focused.is_attached:
            cards = [c for c in self.cards.get(sid, []) if c.is_attached]
            if cards:
                cards[-1].focus()

    def load_mix(self, sounds: dict[str, float], name: str | None = None) -> None:
        for sid in list(self.selected):
            self._deselect(sid)
        for sid, vol in sounds.items():
            if sid in SOUNDS:
                self._select(sid, float(vol), autoplay=False)
        self.mix_name = name
        self.action_play()
        self._refresh_all()
        if name:
            self.notify(f"♫ Now playing “{name}”", timeout=3)

    def save_preset(self, name: str) -> bool:
        if not self.selected:
            self.notify("Select some sounds first — there's nothing to save.", severity="warning", timeout=3)
            return False
        name = name or f"Mix {len(self.store['presets']) + 1}"
        self.store["presets"].append({"name": name, "sounds": dict(self.selected)})
        self.store.save()
        self.mix_name = name
        self.notify(f"💾 Saved “{name}”", timeout=3)
        self._refresh_status()
        return True

    # ------------------------------------------------------------- loading
    def _ensure_ready(self, sid: str) -> None:
        if self.engine.is_loaded(sid):
            if self.playing and sid in self.selected:
                self.engine.play(sid, self.selected[sid])
            return
        if sid in self.loading:
            return
        self.loading.add(sid)
        self.run_worker(partial(self._load_worker, sid), thread=True, group="load", exit_on_error=False)

    def _load_worker(self, sid: str) -> None:
        snd = SOUNDS[sid]
        last = [-1.0]

        def progress(p: float) -> None:
            if p - last[0] >= 0.02 or p >= 1.0:
                last[0] = p
                self.call_from_thread(self._set_status, sid, "download", p)

        try:
            if not downloader.is_cached(snd):
                self.call_from_thread(self._set_status, sid, "download", 0.0)
                path = downloader.download(snd, progress)
            else:
                path = downloader.cache_path(snd)
            self.call_from_thread(self._set_status, sid, "decode", 1.0)
            self.engine.load(sid, path)
        except Exception as exc:  # network / decode errors
            self.call_from_thread(self._load_failed, sid, str(exc))
            return
        self.call_from_thread(self._load_done, sid)

    def _set_status(self, sid: str, status: str, progress: float) -> None:
        for card in self._cards_for(sid):
            card.status = status
            card.progress = progress

    def _load_done(self, sid: str) -> None:
        self.loading.discard(sid)
        self._set_status(sid, "", 1.0)
        if sid in self.selected and self.playing:
            self.engine.play(sid, self.selected[sid])

    def _load_failed(self, sid: str, error: str) -> None:
        self.loading.discard(sid)
        self._set_status(sid, "error", 0.0)
        self.notify(f"Couldn't load {SOUNDS[sid].label}: {error}", severity="error", timeout=5)

    # ============================================================== mixer UI
    def _add_mixer_row(self, sid: str) -> None:
        if self.query(f"#mix-{sid}"):
            return
        snd = SOUNDS[sid]
        row = MixerRow(sid, snd.label, self.icon(snd), self.selected[sid], id=f"mix-{sid}")
        self.query_one("#mix-list").mount(row)

    # ============================================================== refresh
    def _refresh_all(self) -> None:
        self._refresh_status()
        self._refresh_nav()
        self._save_session()

    def _refresh_nav(self) -> None:
        nav = self.query_one("#nav", OptionList)
        for i, cat in enumerate(CATEGORIES):
            nav.replace_option_prompt_at_index(i, self._nav_prompt(i, cat))

    def _refresh_status(self) -> None:
        n = len(self.selected)
        parts = Text()
        if self.playing:
            parts.append("▶ playing", style=f"bold {GREEN}")
        else:
            parts.append("⏸ paused", style=f"bold {MUTED}")
        parts.append("  ·  ", style=DIM)
        parts.append(f"{n} sound{'s' if n != 1 else ''}", style=TEXT)
        parts.append("  ·  ", style=DIM)
        parts.append("🔇 muted" if self.muted else f"vol {round(self.master * 100)}%", style=TEXT if not self.muted else ACCENT)
        rem = self.sleep_remaining()
        if rem is not None:
            parts.append("  ·  ", style=DIM)
            parts.append(f"🌙 {fmt_time(rem)}", style=PRIMARY)
        if self.pomodoro.active:
            parts.append("  ·  ", style=DIM)
            parts.append(f"🍅 {fmt_time(self.pomodoro.remaining)}", style=ACCENT if self.pomodoro.running else MUTED)
        self.query_one("#status", Static).update(parts)

        # Now playing panel
        state = Text()
        if not n:
            state.append("Nothing selected", style=MUTED)
        elif self.playing:
            state.append("● LIVE  ", style=f"bold {GREEN}")
            state.append(self.mix_name or f"{n} sound mix", style=f"bold {TEXT}")
        else:
            state.append("⏸ PAUSED  ", style=f"bold {MUTED}")
            state.append(self.mix_name or f"{n} sound mix", style=TEXT)
        self.query_one("#play-state", Static).update(state)
        play_btn = self.query_one("#btn-play", Button)
        play_btn.label = "⏸ Pause" if self.playing else "▶ Play"
        play_btn.set_class(self.playing, "-playing")

        empty = self.query_one("#mix-empty", Static)
        empty.display = not n
        empty.update(Text.assemble(("Your mix is empty.\n", f"bold {TEXT}"), ("Pick sounds on the left, or press ", MUTED), ("p", f"bold {PRIMARY}"), (" for a starter mix.", MUTED)))

        # Toolbox labels
        moon = "🌙" if self.emoji else "☾"
        self.query_one("#tool-sleep", Button).label = f"{moon} Sleep timer  {fmt_time(rem) if rem is not None else 'off'}"
        tomato = "🍅" if self.emoji else "◔"
        p = self.pomodoro
        pomo_state = f"{fmt_time(p.remaining)}{' ▶' if p.running else ''}"
        self.query_one("#tool-pomo", Button).label = f"{tomato} Pomodoro  {pomo_state}"
        todos = self.store["todos"]
        open_todos = sum(1 for t in todos if not t["done"])
        check = "✅" if self.emoji else "☑"
        self.query_one("#tool-todo", Button).label = f"{check} Todos  {open_todos} open" if todos else f"{check} Todos"

    def _save_session(self) -> None:
        self.store["selected"] = dict(self.selected)
        self.store["master_volume"] = self.master

    def _tick(self) -> None:
        spectrum, levels = self.engine.snapshot()
        self.query_one(Visualizer).feed(spectrum)
        eff = 0.0 if self.muted else self.master
        for sid, vol in self.selected.items():
            live = self.playing and self.engine.is_active(sid)
            lv = levels.get(sid, 0.0) if live else 0.0
            for card in self._cards_for(sid):
                card.live = live
                card.push_level(lv * (0.35 + 0.65 * vol))
            for row in self.query(f"#mix-{sid}"):
                row.level = lv * (vol * eff) ** 0.5  # type: ignore[attr-defined]
        master_row = self.query_one("#master-row", MixerRow)
        master_row.level = min(1.0, float(spectrum.mean()) * 1.4) if self.playing else 0.0
        for sid in self.loading:
            for card in self._cards_for(sid):
                card.refresh()

    def _slow_tick(self) -> None:
        finished = self.pomodoro.tick()
        if finished:
            self.bell()
            msg = "Focus session complete — take a break! ☕" if finished == "pomodoro" else "Break's over — back to focus. 🎯"
            self.notify(msg, title="Pomodoro", timeout=10)
        if self.sleep_deadline is not None and time.monotonic() >= self.sleep_deadline:
            self.sleep_deadline = None
            if self.playing:
                self.engine.fade_out_all(6000)
                self.playing = False
            self.notify("Sleep timer finished. Sweet dreams 🌙", timeout=8)
        self._refresh_status()

    # ============================================================ navigation
    def card_focused(self, card: SoundCard) -> None:
        nav = self.query_one("#nav", OptionList)
        idx = next((i for i, c in enumerate(CATEGORIES) if c.id == card.sound.category), None)
        if idx is not None and nav.highlighted != idx:
            with nav.prevent(OptionList.OptionHighlighted):
                nav.highlighted = idx

    def _card_rows(self) -> list[list[SoundCard]]:
        rows: list[list[SoundCard]] = []
        for grid in self.query(ItemGrid):
            if not grid.display or not (grid.parent and grid.parent.display):
                continue
            cards = [c for c in grid.children if isinstance(c, SoundCard) and c.display]
            if not cards:
                continue
            gutter = grid.styles.grid_gutter_horizontal
            cols = max(1, (grid.content_size.width + gutter) // (CARD_MIN_WIDTH + gutter))
            cols = min(cols, len(cards))
            rows.extend(cards[i : i + cols] for i in range(0, len(cards), cols))
        return rows

    def navigate_cards(self, card: SoundCard, direction: str) -> None:
        rows = self._card_rows()
        pos = next(((r, row.index(card)) for r, row in enumerate(rows) if card in row), None)
        if pos is None:
            return
        r, c = pos
        target: SoundCard | None = None
        if direction == "left":
            if c > 0:
                target = rows[r][c - 1]
            elif r > 0:
                target = rows[r - 1][-1]
        elif direction == "right":
            if c < len(rows[r]) - 1:
                target = rows[r][c + 1]
            elif r < len(rows) - 1:
                target = rows[r + 1][0]
        elif direction == "up" and r > 0:
            target = rows[r - 1][min(c, len(rows[r - 1]) - 1)]
        elif direction == "down" and r < len(rows) - 1:
            target = rows[r + 1][min(c, len(rows[r + 1]) - 1)]
        if target is not None:
            target.focus()

    @on(OptionList.OptionSelected, "#nav")
    def nav_selected(self, event: OptionList.OptionSelected) -> None:
        idx = next(i for i, c in enumerate(CATEGORIES) if c.id == event.option.id)
        self.action_jump(idx)

    def action_jump(self, idx: int) -> None:
        if idx >= len(CATEGORIES):
            return
        cat = CATEGORIES[idx]
        section = self.query_one(f"#sec-{cat.id}")
        if not section.display:
            return
        first = next((c for c in self.query_one(f"#grid-{cat.id}").children if isinstance(c, SoundCard) and c.display), None)
        if first:
            first.focus(scroll_visible=False)
        self.query_one("#sounds", VerticalScroll).scroll_to_widget(section, top=True, duration=0.25)

    # ================================================================ search
    def action_search(self) -> None:
        search = self.query_one("#search", Input)
        search.display = True
        search.focus()

    @on(Input.Changed, "#search")
    def search_changed(self, event: Input.Changed) -> None:
        q = event.value.strip().lower()
        any_visible = False
        with self.batch_update():
            for cat in CATEGORIES:
                visible = 0
                for card in self.query_one(f"#grid-{cat.id}").children:
                    if isinstance(card, SoundCard):
                        match = not q or q in card.sound.label.lower() or q in cat.title.lower() or q in card.sound.id
                        card.display = match
                        visible += match
                self.query_one(f"#sec-{cat.id}").display = visible > 0
                any_visible |= visible > 0
            self.query_one("#sec-favorites").display = bool(self.favorites) and not q
            self.query_one("#no-results").display = not any_visible
        self.query_one("#sounds", VerticalScroll).scroll_home(animate=False)

    @on(Input.Submitted, "#search")
    def search_submitted(self) -> None:
        first = next((c for c in self.query(SoundCard) if c.display and c.parent and c.parent.display and c.parent.parent.display), None)
        if first:
            first.focus()

    def action_escape(self) -> None:
        search = self.query_one("#search", Input)
        if search.display:
            search.value = ""
            search.display = False
            first = self.query(SoundCard).first()
            if isinstance(self.focused, Input) and first:
                first.focus()

    # =============================================================== actions
    def action_play(self) -> None:
        if not self.selected:
            return
        self.playing = True
        self.engine.resume()
        for sid, vol in self.selected.items():
            if self.engine.is_loaded(sid) and not self.engine.is_active(sid):
                self.engine.play(sid, vol)
        self._refresh_status()

    def action_pause(self) -> None:
        self.playing = False
        self.engine.pause()
        self._refresh_status()

    def action_play_pause(self) -> None:
        if self.playing:
            self.action_pause()
        elif not self.selected:
            self.notify("Your mix is empty — select a sound or press [b]s[/b] to shuffle.", timeout=3)
        else:
            self.action_play()

    def action_master(self, delta: int) -> None:
        self.set_master_volume(self.master + delta / 100)

    def action_mute(self) -> None:
        self.muted = not self.muted
        self.engine.set_master(self.master, self.muted)
        self.query_one("#master-row", MixerRow).muted = self.muted
        self._refresh_status()

    def action_unselect(self) -> None:
        if self.selected:
            self.undo_selection = dict(self.selected)
            for sid in list(self.selected):
                self._deselect(sid)
            self.mix_name = None
            self.action_pause()
            self.notify("Cleared your mix — press [b]u[/b] again to undo.", timeout=3)
        elif self.undo_selection:
            mix, self.undo_selection = self.undo_selection, None
            self.load_mix(mix)
        self._refresh_all()

    def action_shuffle(self) -> None:
        pool = [s.id for c in CATEGORIES if c.id not in ("binaural", "noise") for s in c.sounds]
        picks = random.sample(pool, k=random.randint(2, 4))
        self.load_mix({sid: round(random.uniform(0.25, 0.8), 2) for sid in picks}, None)
        names = ", ".join(SOUNDS[s].label for s in picks)
        self.notify(f"⤨ Shuffled: {names}", timeout=3)

    def action_mixes(self) -> None:
        self.push_screen(MixesScreen())

    def action_save_preset(self) -> None:
        def focus_input() -> None:
            if isinstance(self.screen, MixesScreen):
                self.screen.query_one("#preset-name", Input).focus()

        self.push_screen(MixesScreen())
        self.call_after_refresh(focus_input)

    def action_sleep(self) -> None:
        self.push_screen(SleepTimerScreen())

    def action_pomodoro(self) -> None:
        self.push_screen(PomodoroScreen(), lambda _: self._refresh_status())

    def action_breathe(self) -> None:
        self.push_screen(BreathingScreen())

    def action_notes(self) -> None:
        self.push_screen(NotepadScreen())

    def action_todos(self) -> None:
        self.push_screen(TodoScreen(), lambda _: self._refresh_status())

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def set_sleep_timer(self, minutes: int | None) -> None:
        if minutes is None:
            self.sleep_deadline = None
            self.notify("Sleep timer cancelled", timeout=2)
        else:
            self.sleep_deadline = time.monotonic() + minutes * 60
            self.notify(f"🌙 Sounds will fade out in {fmt_time(minutes * 60)}", timeout=3)
        self._refresh_status()

    def sleep_remaining(self) -> float | None:
        if self.sleep_deadline is None:
            return None
        return max(0.0, self.sleep_deadline - time.monotonic())

    # ================================================================ exit
    def on_unmount(self) -> None:
        self._save_session()
        self.store["favorites"] = self.favorites
        self.store.save()
        self.engine.shutdown()


MoodistApp = EchoScapeApp
