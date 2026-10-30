"""EchoScape sound catalogue — 89 ambient sounds across 9 categories.

Every sound streams on demand and is cached locally on first play.
"""

from __future__ import annotations

from dataclasses import dataclass, field

BASE_URL = "https://moodist.mvze.net"


@dataclass(frozen=True)
class Sound:
    id: str
    label: str
    path: str  # e.g. "/sounds/rain/light-rain.mp3"
    icon: str
    category: str = ""

    @property
    def url(self) -> str:
        return BASE_URL + self.path

    @property
    def filename(self) -> str:
        return self.path.removeprefix("/sounds/").replace("/", "_")


@dataclass(frozen=True)
class Category:
    id: str
    title: str
    icon: str
    sounds: tuple[Sound, ...] = field(default_factory=tuple)


def _cat(cid: str, title: str, icon: str, folder: str, items: list[tuple[str, str, str]], ext: str = "mp3") -> Category:
    sounds = tuple(
        Sound(id=sid, label=label, path=f"/sounds/{folder}/{sid}.{ext}", icon=icon_, category=cid)
        for sid, label, icon_ in items
    )
    return Category(id=cid, title=title, icon=icon, sounds=sounds)


# NOTE: icons only use code points that have default *emoji presentation*, so they are
# reliably two cells wide in modern terminals.
CATEGORIES: tuple[Category, ...] = (
    _cat("nature", "Nature", "🌲", "nature", [
        ("river", "River", "🛶"),
        ("waves", "Waves", "🌊"),
        ("campfire", "Campfire", "🔥"),
        ("wind", "Wind", "💨"),
        ("howling-wind", "Howling Wind", "🌀"),
        ("wind-in-trees", "Wind in Trees", "🌳"),
        ("waterfall", "Waterfall", "💦"),
        ("walk-in-snow", "Walk in Snow", "⛄"),
        ("walk-on-leaves", "Walk on Leaves", "🍂"),
        ("walk-on-gravel", "Walk on Gravel", "👣"),
        ("droplets", "Droplets", "🚰"),
        ("jungle", "Jungle", "🌴"),
    ]),
    _cat("rain", "Rain", "☔", "rain", [
        ("light-rain", "Light Rain", "💧"),
        ("heavy-rain", "Heavy Rain", "☔"),
        ("thunder", "Thunder", "⚡"),
        ("rain-on-window", "Rain on Window", "🏠"),
        ("rain-on-car-roof", "Rain on Car Roof", "🚗"),
        ("rain-on-umbrella", "Rain on Umbrella", "🌂"),
        ("rain-on-tent", "Rain on Tent", "⛺"),
        ("rain-on-leaves", "Rain on Leaves", "🌿"),
    ]),
    _cat("animals", "Animals", "🐾", "animals", [
        ("birds", "Birds", "🐤"),
        ("seagulls", "Seagulls", "🦢"),
        ("crickets", "Crickets", "🦗"),
        ("wolf", "Wolf", "🐺"),
        ("owl", "Owl", "🦉"),
        ("frog", "Frog", "🐸"),
        ("dog-barking", "Dog Barking", "🐕"),
        ("horse-gallop", "Horse Gallop", "🐎"),
        ("cat-purring", "Cat Purring", "🐈"),
        ("crows", "Crows", "🐦"),
        ("whale", "Whale", "🐋"),
        ("beehive", "Beehive", "🐝"),
        ("woodpecker", "Woodpecker", "🌲"),
        ("chickens", "Chickens", "🐔"),
        ("cows", "Cows", "🐄"),
        ("sheep", "Sheep", "🐑"),
    ]),
    _cat("urban", "Urban", "🌆", "urban", [
        ("highway", "Highway", "🚚"),
        ("road", "Road", "🚙"),
        ("ambulance-siren", "Ambulance Siren", "🚑"),
        ("busy-street", "Busy Street", "🚦"),
        ("crowd", "Crowd", "👥"),
        ("traffic", "Traffic", "🚥"),
        ("fireworks", "Fireworks", "🎆"),
    ]),
    _cat("places", "Places", "📍", "places", [
        ("cafe", "Cafe", "☕"),
        ("airport", "Airport", "🛄"),
        ("church", "Church", "⛪"),
        ("temple", "Temple", "🛕"),
        ("construction-site", "Construction Site", "🚧"),
        ("underwater", "Underwater", "🐠"),
        ("crowded-bar", "Crowded Bar", "🍺"),
        ("night-village", "Night Village", "🌃"),
        ("subway-station", "Subway Station", "🚇"),
        ("office", "Office", "🏢"),
        ("supermarket", "Supermarket", "🛒"),
        ("carousel", "Carousel", "🎠"),
        ("laboratory", "Laboratory", "🔬"),
        ("laundry-room", "Laundry Room", "🧺"),
        ("restaurant", "Restaurant", "🍝"),
        ("library", "Library", "📚"),
    ]),
    _cat("transport", "Transport", "🚆", "transport", [
        ("train", "Train", "🚆"),
        ("inside-a-train", "Inside a Train", "🚃"),
        ("airplane", "Airplane", "🛫"),
        ("submarine", "Submarine", "🚢"),
        ("sailboat", "Sailboat", "⛵"),
        ("rowing-boat", "Rowing Boat", "🚣"),
    ]),
    _cat("things", "Things", "🧸", "things", [
        ("keyboard", "Keyboard", "💻"),
        ("typewriter", "Typewriter", "📝"),
        ("paper", "Paper", "📄"),
        ("clock", "Clock", "⏰"),
        ("wind-chimes", "Wind Chimes", "🎐"),
        ("singing-bowl", "Singing Bowl", "🔔"),
        ("ceiling-fan", "Ceiling Fan", "🎡"),
        ("dryer", "Dryer", "👕"),
        ("slide-projector", "Slide Projector", "🎬"),
        ("boiling-water", "Boiling Water", "🍵"),
        ("bubbles", "Bubbles", "🧼"),
        ("tuning-radio", "Tuning Radio", "📻"),
        ("morse-code", "Morse Code", "📡"),
        ("washing-machine", "Washing Machine", "🧦"),
        ("vinyl-effect", "Vinyl Effect", "💿"),
        ("windshield-wipers", "Windshield Wipers", "🚘"),
    ]),
    _cat("noise", "Noise", "🔊", "noise", [
        ("white-noise", "White Noise", "⚪"),
        ("pink-noise", "Pink Noise", "🌸"),
        ("brown-noise", "Brown Noise", "🟤"),
    ], ext="wav"),
    _cat("binaural", "Binaural", "🎧", "binaural", [
        ("binaural-delta", "Delta · Sleep", "🌙"),
        ("binaural-theta", "Theta · Meditate", "🧘"),
        ("binaural-alpha", "Alpha · Relax", "😌"),
        ("binaural-beta", "Beta · Focus", "🎯"),
        ("binaural-gamma", "Gamma · Insight", "💡"),
    ], ext="wav"),
)

SOUNDS: dict[str, Sound] = {s.id: s for c in CATEGORIES for s in c.sounds}
CATEGORY_BY_ID: dict[str, Category] = {c.id: c for c in CATEGORIES}

# Starter mixes taken from the website (src/components/starter-mixes) plus a few extras.
STARTER_MIXES: tuple[dict, ...] = (
    {"name": "Deep focus", "description": "Brown noise · Light rain",
     "sounds": {"brown-noise": 0.5, "light-rain": 0.35}},
    {"name": "Rainy café", "description": "Café · Rain on window",
     "sounds": {"cafe": 0.75, "rain-on-window": 0.15}},
    {"name": "Slow evening", "description": "Waves · Campfire",
     "sounds": {"waves": 0.5, "campfire": 0.35}},
    {"name": "Cabin in the storm", "description": "Heavy rain · Thunder · Campfire",
     "sounds": {"heavy-rain": 0.45, "thunder": 0.3, "campfire": 0.4}},
    {"name": "Midnight library", "description": "Library · Clock · Rain on window",
     "sounds": {"library": 0.55, "clock": 0.2, "rain-on-window": 0.3}},
    {"name": "Summer night", "description": "Crickets · Night village · Wind in trees",
     "sounds": {"crickets": 0.4, "night-village": 0.35, "wind-in-trees": 0.25}},
    {"name": "Night train", "description": "Inside a train · Light rain",
     "sounds": {"inside-a-train": 0.6, "light-rain": 0.25}},
)

ASCII_ICONS = {
    "nature": "♣", "rain": "≈", "animals": "ж", "urban": "▤", "places": "◈",
    "transport": "»", "things": "◇", "noise": "∿", "binaural": "◉",
}
