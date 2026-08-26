"""067: Labs — experimental features a player switches on and off.

The contract that keeps a Labs feature ISOLATED:
- the flag lives on the player doc, `p["labs"][key]` (bool, absent = off);
- this module is the only place that names the keys, the floors a
  feature is gated to, and the card that flips them;
- a feature module reads `labs.enabled(p, key, floor)` at its seams and
  does nothing when it is off. Promoting a feature = flip the default,
  delete the old branch, delete the key here. Dropping one = delete the
  key here and the feature module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .scene import Option, Scene


@dataclass(frozen=True)
class Feature:
    key: str
    name: str
    blurb: str
    floors: frozenset = field(default_factory=frozenset)   # empty = all


FEATURES: dict[str, Feature] = {
    # "arena" graduated 2026-08-24 (plans/100floors-attack3dscene): the
    # turn-based 3D fight is on for everyone, gated only by
    # arena.READY_FLOORS while the floor assets roll out.
    "figure3d": Feature(
        "figure3d", "Figure — 3D climber in the profile",
        "Your portrait becomes the 3D climber, breathing still, wearing "
        "what sits in the slots: sword on the hip, bow on the back, "
        "staff in the hand, charm on the neck, boots on the feet. "
        "Hover a slot to light that piece. Off = the drawn portrait.",
        frozenset()),
    # 082 phase-1: the camp menu becomes the floor's map — every choice
    # a marker chip standing on the terrain. Floor 1 only while the art
    # rolls out; quests come in a later phase.
    "floormap": Feature(
        "floormap", "Floor maps",
        "The camp menu becomes a map of the floor. Every place is a "
        "marker on the land — the gate pylon, the town, the fire, the "
        "Warden's keep, the hunting fields. Hover a marker for what it "
        "holds; a click that costs energy says so on the marker. "
        "Off = the plain list.",
        frozenset({1})),
}

OPEN = "labs"
BACK = "labs_back"
TOGGLE = "labs_toggle_"


def flags(p: dict) -> dict:
    lb = p.get("labs")
    if not isinstance(lb, dict):
        lb = {}
        p["labs"] = lb
    return lb


def enabled(p: dict, key: str, floor: int | None = None) -> bool:
    """On for this player — and, when a floor is given, on THIS floor."""
    f = FEATURES.get(key)
    if f is None or not flags(p).get(key):
        return False
    if floor is not None and f.floors and int(floor) not in f.floors:
        return False
    return True


def set_flag(p: dict, key: str, on: bool) -> None:
    if key in FEATURES:
        flags(p)[key] = bool(on)


def enabled_keys(p: dict) -> list[str]:
    return [k for k in FEATURES if flags(p).get(k)]


def is_labs_option(oid: str) -> bool:
    return oid == OPEN or oid == BACK or oid.startswith(TOGGLE)


def labs_scene(p: dict) -> Scene:
    body = ["Experiments. Each one is off until you switch it on, and "
            "off again the moment you switch it off — nothing here "
            "changes what the game does for anyone else."]
    opts: list[Option] = []
    for f in FEATURES.values():
        on = enabled(p, f.key)
        floors = (" · floors " + ", ".join(str(x) for x in sorted(f.floors))
                  if f.floors else "")
        opts.append(Option(TOGGLE + f.key,
                           f"{f.name} — {'ON' if on else 'off'}",
                           f"{'switch off' if on else 'switch on'}{floors}",
                           aether=on))
        body.append(f"▪ {f.name}: {f.blurb}")
    opts.append(Option(BACK, "Back"))
    return Scene(
        eyebrow="LABS",
        headline="The Labs",
        support="Things being tried. Turn one on to test it.",
        body_lines=body,
        options=opts,
        event_kind="",
    )


def handle(p: dict, oid: str, build_scene) -> Scene:
    """Route a Labs option. `build_scene(p)` is the caller's way back to
    wherever the player stands (core._build_scene)."""
    if oid.startswith(TOGGLE):
        key = oid[len(TOGGLE):]
        if key in FEATURES:
            set_flag(p, key, not enabled(p, key))
        return labs_scene(p)
    if oid == BACK:
        return build_scene(p)
    return labs_scene(p)
