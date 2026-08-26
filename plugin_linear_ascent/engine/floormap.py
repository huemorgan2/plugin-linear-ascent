"""082 phase-1: Labs floormap — the camp menu drawn as the floor's map.

Isolation: this module only builds the dict `render._map_html` draws;
the option ids are the SAME ids the plain list posts, so choosing works
identically with the feature on or off. Off (or an unmapped floor) =
None and the card renders the rows it always has. Dropping the feature
deletes this file, the `floormap` key in labs.py and the render block.

A marker exists only for an option id present in the LIVE scene options
— a conditional row that is absent today (deep hunt before floor 4, the
healer at full HP) never paints a dead marker. Options with no marker in
the layout (stew, heal, use_*, answer_flare) stay ordinary rows under
the map: nothing is ever unreachable.

Cost-on-chip rule (roy): a marker whose CLICK has a real cost wears it
on the chip in the cost's own color — the hunt says `1 ⚡` in the energy
teal. The Warden's chip carries no cost: his keep screen prices the
swing before anything is spent.
"""
from __future__ import annotations

from .. import economy
from . import labs

KEY = "floormap"

# Marker layout per floor: option id -> (x%, y%, label, tooltip, cost).
# label "@warden" resolves to the floor's warden name. cost is (text,
# kind) or None; kind names the ink ("en" = energy teal).
LAYOUTS: dict[int, dict[str, tuple]] = {
    1: {
        "gate": (54, 40, "GATE",
                 "The tower — the elevator between floors.", None),
        # phase-1b (roy): Roothollow is NOT on this floor — it is the
        # base town at the elevator bottom. The chip stands at the
        # tower's massive door and says the town's NAME, not "town".
        "town": (58, 64, "ROOTHOLLOW",
                 "Down the tower to Roothollow — shops, forge, bank.",
                 None),
        "talk": (44, 63, "CAMP",
                 "The fire — Hobb Fennick's talk.", None),
        "keep": (90, 31, "@warden",
                 "The Warden's keep — beat him to open the floor above.",
                 None),
        "hunt": (72, 84, "HUNT",
                 "The near fields — hunt for coin and XP.",
                 (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (18, 20, "DEEP-HUNT",
                      "Off the lit paths — stronger monsters, richer pay.",
                      (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
}


def payload(p: dict, fl, options) -> dict | None:
    """The map dict for this scene, or None (feature off / no layout)."""
    layout = LAYOUTS.get(int(fl.floor))
    if layout is None or not labs.enabled(p, KEY, fl.floor):
        return None
    # "Warden Brackjaw" -> the chip says the NAME, one word: BRACKJAW
    warden = ((getattr(fl, "warden_name", "") or "").split() or [""])[-1].upper()
    markers = []
    for o in options:
        m = layout.get(o.id)
        if m is None:
            continue
        x, y, label, tip, cost = m
        mk = {"opt": o.id, "x": x, "y": y,
              "label": warden if label == "@warden" else label,
              "tip": tip}
        if cost:
            mk["cost"], mk["ck"] = cost
        markers.append(mk)
    if not markers:
        return None
    return {"art": f"map_{int(fl.floor):03d}", "markers": markers}
