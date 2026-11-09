<div align="center">

# ◐ EchoScape

**Ambient Sounds for Focus, Calm, and Deep Work in Your Terminal**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-818cf8?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Textual TUI](https://img.shields.io/badge/UI-Textual-c084fc?style=for-the-badge)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-4ade80?style=for-the-badge)](LICENSE)
[![Creator](https://img.shields.io/badge/Created%20by-Om%20Patel-f472b6?style=for-the-badge)](#author)

*Layer rain on a window, a crackling campfire, brown noise, and a quiet midnight library without ever leaving your terminal.*

</div>

## ✨ Overview

**EchoScape** is a terminal-based ambient sound mixer and productivity tool created by **Om Patel**. It targets developers, writers, and students who spend their days in the command line. The app features a **multi-track looping audio engine**, **real-time FFT spectrum visualization**, **89 curated ambient sounds**, and a built-in **Focus & Calm Toolbox** loaded with a Pomodoro timer, guided breathing orb, sleep timer, scratchpad, and todo list.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ◐ E c h o S c a p e  ambient sounds for focus and calm      ▶ playing · 3 sounds · 80%  │
├─────────────────┬──────────────────────────────────────────────┬─────────────────────────┤
│ CATEGORIES      │ ★ Favorites   your starred sounds            │ ╭─ NOW PLAYING ───────╮ │
│                 │ ╭──────────────────────────────────────────╮ │ │ ▄▄▆▇█▇▆▅▄▃▄▅▄▃▂▁  │ │
│ 1 🌲 Nature  ●● │ │ 💧 Light Rain                          ★ │ │ │ ● LIVE  Deep focus  │ │
│ 2 ☔ Rain    ●  │ │ ▃▄▅▆▄▃▄▅▆▇▆▅▄▃▄▅▆▅▄▃▄▅▆▅▄  │ │ │ [⏸ Pause] [⤨ Shuf]  │ │
│ 3 🐾 Animals    │ │ ━━━━━━━━━━━━━━━━━━●───────────────── 50% │ │ │ 🔊 Master ▮▮▮▮▯▯ 80%│ │
│ 4 🌆 Urban      │ ╰──────────────────────────────────────────╯ │ ╰─────────────────────╯ │
│ 5 📍 Places     │                                              │ ╭─ YOUR MIX ──────────╮ │
│ 6 🚆 Transport  │ 🌲 Nature   12 sounds                        │ │ 💧 Light Rain   50% │ │
│ 7 🧸 Things     │ ╭────────────────────╮ ╭───────────────────╮ │ │ 🔥 Campfire     35% │ │
│ 8 🔊 Noise      │ │ 🛶 River           │ │ 🔥 Campfire       │ │ │ 🟤 Brown Noise  40% │ │
│ 9 🎧 Binaural   │ │                    │ │ ▁▂▃▅▃▂▁▂▄▆▄▂▁▂▃▄ │ │ ╰─────────────────────╯ │
│                 │ │ ⏎ add to mix       │ │ ━━━━━━━━●──── 35% │ │ ╭─ TOOLBOX ───────────╮ │
│ ? all shortcuts │ ╰────────────────────╯ ╰───────────────────╯ │ │ 🌙 Sleep timer  off │ │
│ ◐ EchoScape     │                                              │ │ 🍅 Pomodoro   25:00 │ │
└─────────────────┴──────────────────────────────────────────────┴─────────────────────────┘
```

## 🌟 Key Features

- **🎶 89 Ambient Sounds Across 9 Categories**
  Mix and match everything from *Light Rain*, *Campfire*, and *Wind in Trees* to *Rainy Café*, *Inside a Train*, *Vinyl Effect*, *Brown Noise*, and *Binaural Beats*.
- **⚡ On-Demand Streaming & Offline Cache**
  Tracks stream on first selection with an inline download progress bar. The app caches them locally so subsequent plays are instant and work entirely offline.
- **📊 Real-Time FFT Audio Visualizer & Sparklines**
  Every loaded track is analyzed with NumPy (`rfft` log-frequency bands + RMS envelope). The 32-band spectrum analyzer, per-card sparkline history, and mixer VU meters react to the actual audio in real time.
- **🎛️ Multi-Channel Looping Audio Engine**
  Simultaneously layer up to 64 stereo channels with smooth fade-ins and fade-outs, individual per-sound volume sliders, master volume control, and instant mute.
- **💾 Starter Mixes & Custom Presets (`p` / `Ctrl+S`)**
  Start immediately with 7 curated soundscapes (*Deep focus*, *Rainy café*, *Slow evening*, *Cabin in the storm*, *Midnight library*, *Summer night*, *Night train*). You can also save and manage your own custom mixes.
- **🧘 Built-in Focus & Calm Toolbox**
  - **🌙 Sleep Timer (`t`):** Choose a preset duration from 5 minutes to 3 hours, or enter custom minutes to gently fade all audio to silence.
  - **🍅 Pomodoro Timer (`o`):** A Focus, Short Break, and Long Break timer with a large digital display, round tracking, and customizable session lengths.
  - **🧘 Breathing Exercise (`b`):** A smooth 30 FPS half-block rendered gradient orb. It guides you through *4-7-8 Breathing*, *Box Breathing*, or *Resonant Breathing*.
  - **📝 Notepad (`n`):** A persistent markdown and text scratchpad with live character and word counts.
  - **✅ Todo List (`d`):** A persistent task manager with completion tracking built right inside your soundboard.
- **⌨️ First-Class Keyboard & Mouse Ergonomics**
  Navigate with arrow keys or Vim keys (`h`/`j`/`k`/`l`). Jump categories with `1` through `9`, fuzzy-filter with `/`, or click directly on cards and volume sliders with your mouse.

## 🗂️ Sound Library

| # | Category | Count | Included Sounds |
| :-: | :--- | :-: | :--- |
| `1` | **🌲 Nature** | 12 | River, Waves, Campfire, Wind, Howling Wind, Wind in Trees, Waterfall, Walk in Snow, Walk on Leaves, Walk on Gravel, Droplets, Jungle |
| `2` | **☔ Rain** | 8 | Light Rain, Heavy Rain, Thunder, Rain on Window, Rain on Car Roof, Rain on Umbrella, Rain on Tent, Rain on Leaves |
| `3` | **🐾 Animals** | 16 | Birds, Seagulls, Crickets, Wolf, Owl, Frog, Dog Barking, Horse Gallop, Cat Purring, Crows, Whale, Beehive, Woodpecker, Chickens, Cows, Sheep |
| `4` | **🌆 Urban** | 7 | Highway, Road, Ambulance Siren, Busy Street, Crowd, Traffic, Fireworks |
| `5` | **📍 Places** | 16 | Cafe, Airport, Church, Temple, Construction Site, Underwater, Crowded Bar, Night Village, Subway Station, Office, Supermarket, Carousel, Laboratory, Laundry Room, Restaurant, Library |
| `6` | **🚆 Transport** | 6 | Train, Inside a Train, Airplane, Submarine, Sailboat, Rowing Boat |
| `7` | **🧸 Things** | 16 | Keyboard, Typewriter, Paper, Clock, Wind Chimes, Singing Bowl, Ceiling Fan, Dryer, Slide Projector, Boiling Water, Bubbles, Tuning Radio, Morse Code, Washing Machine, Vinyl Effect, Windshield Wipers |
| `8` | **🔊 Noise** | 3 | White Noise, Pink Noise, Brown Noise |
| `9` | **🎧 Binaural** | 5 | Delta (Sleep), Theta (Meditate), Alpha (Relax), Beta (Focus), Gamma (Insight) |

## 🚀 Installation & Quick Start

### Prerequisites

- **Python 3.10+**
- A modern terminal emulator (Windows Terminal, WezTerm, Alacritty, iTerm2, Ghostty, kitty, etc.)

### 1. Clone the Repository

```bash
git clone https://github.com/Tz-risk/EchoSpace.git
cd EchoSpace
```

### 2. Run EchoScape

#### Windows (One-Step Launcher)

```powershell
.\echoscape.bat
# or
.\soundboard.bat
```

*(Automatically creates `.venv` and installs dependencies on first launch.)*

#### Cross-Platform (macOS / Linux / Windows via `pip`)

```bash
python -m venv .venv
# Activate virtual environment:
#   Windows: .venv\Scripts\activate
#   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python -m echoscape
```

### Command-Line Flags

```text
usage: echoscape [-h] [--ascii] [--download-all]

EchoScape: ambient sound mixer for your terminal.

options:
  -h, --help      show this help message and exit
  --ascii         use plain symbols instead of emoji icons
  --download-all  pre-download every sound for offline use and exit
```

## ⌨️ Keyboard Shortcuts

### Playback & Mixing

| Shortcut | Action |
| :--- | :--- |
| `Space` | Play / pause the active mix |
| `Enter` / Click | Toggle the focused sound on or off |
| `+` / `-` (or `Ctrl+Scroll`) | Increase / decrease focused sound volume |
| `,` / `.` | Decrease / increase master volume |
| `m` | Mute / unmute master audio |
| `s` | Shuffle a balanced random mix (2 to 4 ambient sounds) |
| `u` | Clear all active sounds (press `u` again to undo) |
| `f` | Star / unstar the focused sound as a Favorite |

### Navigation & Search

| Shortcut | Action |
| :--- | :--- |
| `←` `↑` `↓` `→` or `h` `j` `k` `l` | Move focus across the sound grid or mixer strips |
| `Tab` / `Shift+Tab` | Cycle focus between panels |
| `1` to `9` | Jump directly to category 1 through 9 |
| `/` | Open live sound search (`Esc` to clear) |

### Toolbox & Presets

| Shortcut | Action |
| :--- | :--- |
| `p` | Open Starter Mixes & Saved Presets |
| `Ctrl+S` | Save current mix as a named preset |
| `t` | Open Sleep Timer |
| `o` | Open Pomodoro Timer |
| `b` | Open Guided Breathing Exercise |
| `n` | Open Notepad |
| `d` | Open Todo List |
| `?` | Show keyboard shortcuts help modal |
| `q` | Quit EchoScape (automatically saves your session) |

## 🏗️ Project Structure

```text
EchoSpace/
├── echoscape/
│   ├── __init__.py      # Package metadata & version
│   ├── __main__.py      # CLI entry point (--ascii, --download-all)
│   ├── app.py           # Main EchoScapeApp Textual application & Pomodoro state
│   ├── app.tcss         # Custom dark theme stylesheet (indigo/violet/pink palette)
│   ├── audio.py         # Multi-track pygame mixer & NumPy FFT spectrum analyzer
│   ├── data.py          # Catalogue of 89 sounds, 9 categories & 7 starter mixes
│   ├── downloader.py    # On-demand HTTP streaming & atomic local file caching
│   ├── screens.py       # Modal screens (Mixes, Sleep, Pomodoro, Breathing, Notes, Todos, Help)
│   ├── storage.py       # Persistent JSON store for state, presets, favorites & notes
│   └── widgets.py       # Custom SoundCard, 32-band Visualizer, and MixerRow widgets
├── echoscape.bat        # Windows launcher script
├── soundboard.bat       # Alias launcher script
├── pyproject.toml       # Python package configuration
├── requirements.txt     # Runtime dependencies (textual, pygame, numpy)
├── LICENSE              # MIT License
└── README.md            # Project documentation
```

## 💾 Data & Cache Locations

EchoScape persists your active mix, favorites, saved presets, notepad contents, and todo items automatically:

- **Configuration & State:**
  - **Windows:** `%APPDATA%\echoscape\state.json`
  - **macOS / Linux:** `~/.config/echoscape/state.json`
- **Cached Audio Files:**
  - **Windows:** `%LOCALAPPDATA%\echoscape\sounds\`
  - **macOS / Linux:** `~/.cache/echoscape/sounds/`

*(You can override both locations by setting the `ECHOSCAPE_HOME` environment variable.)*

## 👨‍💻 Author
**Om Patel**  
*Cybersecurity (Honours) Undergraduate | Carleton University*
- **LinkedIn:** [www.linkedin.com/in/om-patel-1806-bcyber](https://www.linkedin.com/in/om-patel-1806-bcyber)
- **Email:** [ompatel14@cmail.carleton.ca](mailto:ompatel14@cmail.carleton.ca)
- **Personal Email:** [om1806patel@gmail.com](mailto:om1806patel@gmail.com)

## 📄 License

This project is licensed under the [MIT License](LICENSE). © Om Patel.
