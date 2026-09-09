"""085: standard floor maps — the camp menu drawn on the land.

This module builds the dict `render._map_html` draws. Floors with an
art/layout pair use it for every player; unmapped floors keep menu rows.
The option ids remain the same as the plain list's actions.

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

# Marker layout per floor: option id -> (x%, y%, label, tooltip, cost).
# label "@warden" resolves to the floor's warden name. cost is (text,
# kind) or None; kind names the ink ("en" = energy teal).
LAYOUTS: dict[int, dict[str, tuple]] = {
    1: {
        "gate": (56, 50, "GATE",
                 "The tower — the elevator between floors.", None),
        # phase-1b (roy): Roothollow is NOT on this floor — it is the
        # base town at the elevator bottom. The chip stands on the
        # village at the tower's foot and says the town's NAME, not
        # "town". (phase-1c: coords re-placed on the small-door art.)
        "town": (63, 69, "ROOTHOLLOW",
                 "Down the tower to Roothollow — shops, forge, bank.",
                 None),
        "talk": (45, 59, "CAMP",
                 "The fire — Hobb Fennick's talk.", None),
        "keep": (91, 26, "@warden",
                 "The Warden's keep — beat him to open the floor above.",
                 None),
        "hunt": (72, 84, "HUNT",
                 "The near fields — hunt for coin and XP.",
                 (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (18, 20, "DEEP-HUNT",
                      "Off the lit paths — stronger monsters, richer pay.",
                      (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    2: {
        "gate": (53, 50, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (65, 69, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (42, 60, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (92, 22, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (77, 87, 'HUNT',
                 'The near mine benches — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (19, 22, 'DEEP-HUNT',
                 'The remote rustwater galleries — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    3: {
        "gate": (51, 52, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (65, 68, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (41, 61, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 22, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (75, 88, 'HUNT',
                 'The drowned field paths — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (19, 22, 'DEEP-HUNT',
                 'The far reed marshes — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    4: {
        "gate": (55, 53, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (67, 72, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (43, 63, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 22, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (78, 88, 'HUNT',
                 'The woodland clearings — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (20, 22, 'DEEP-HUNT',
                 'Beyond the last lit path — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    5: {
        "gate": (48, 50, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (64, 72, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (38, 61, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 22, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (77, 88, 'HUNT',
                 'The dry mine terraces — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (18, 25, 'DEEP-HUNT',
                 'The drowned inner galleries — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    6: {
        "gate": (54, 56, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (68, 76, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (41, 66, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 24, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (78, 89, 'HUNT',
                 'The last lit terraces — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (18, 28, 'DEEP-HUNT',
                 'The silk-hung dark beyond — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    7: {
        "gate": (51, 55, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (64, 75, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (35, 65, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 22, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (78, 89, 'HUNT',
                 'The near orchard rows — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (18, 23, 'DEEP-HUNT',
                 'The deep windfall — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    8: {
        "gate": (53, 54, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (65, 70, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (40, 62, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 22, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (78, 89, 'HUNT',
                 'The near ash dunes — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (18, 23, 'DEEP-HUNT',
                 'The remote ash bowls — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    9: {
        "gate": (54, 55, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (66, 71, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (41, 63, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 23, '@warden',
                 '{warden}’s keep — defeat the Warden to open the floor above.', None),
        "hunt": (79, 89, 'HUNT',
                 'The near beacon heath — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (19, 25, 'DEEP-HUNT',
                 'The far moving shadows — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
    10: {
        "gate": (53, 54, 'GATE',
                 'The tower — the elevator between floors.', None),
        "town": (65, 74, 'ROOTHOLLOW',
                 'From {town}, descend to Roothollow — shops, forge, bank.', None),
        "talk": (41, 64, 'CAMP',
                 'The fire at {town} — talk with {npc}.', None),
        "keep": (93, 24, '@warden',
                 'Gnarl’s fortress — gather your war party to face the Goblin King.', None),
        "hunt": (78, 89, 'HUNT',
                 'The muster fields — hunt for coin and XP.', (f"{economy.COST_WILDS_FIGHT} ⚡", "en")),
        "hunt_deep": (19, 24, 'DEEP-HUNT',
                 'The abandoned tent-lines — stronger monsters, richer pay.', (f"{economy.COST_WILDS_DEEP} ⚡", "en")),
    },
}


def payload(p: dict, fl, options) -> dict | None:
    """The map dict for a mapped floor; legacy Labs flags are ignored."""
    layout = LAYOUTS.get(int(fl.floor))
    if layout is None:
        return None
    # "Warden Brackjaw" -> the chip says the NAME, one word: BRACKJAW
    warden = (getattr(fl, "warden_name", "") or "").removeprefix("Warden ").split(",", 1)[0]
    places = {"warden": warden, "town": getattr(fl, "gate_town", "the camp"),
              "npc": getattr(getattr(fl, "npc", None), "name", "the keeper")}
    markers = []
    for o in options:
        m = layout.get(o.id)
        if m is None:
            continue
        x, y, label, tip, cost = m
        mk = {"opt": o.id, "x": x, "y": y,
              "label": warden.upper() if label == "@warden" else label,
              "tip": tip.format(**places)}
        if cost:
            mk["cost"], mk["ck"] = cost
        markers.append(mk)
    if not markers:
        return None
    return {"art": f"map_{int(fl.floor):03d}", "markers": markers}
