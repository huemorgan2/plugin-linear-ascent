"""010: the faction color roster — the ONE source of truth.

Nine named inks, every hex already in the game's 1-bit palette
(render.py constants) — no new color enters the world here. Names
signal something in it: the mice in the walls, the coin ◈, the
Rotting Orchard, Roothollow's roots. worldd mirrors the SLUGS ONLY
(app/factions.py COLOR_SLUGS) for validation; keep both lists in step.

A faction founded before this plan has no chosen color and falls back
to warden-violet — the exact ink every sigil wore until now, so
nothing changes color uninvited.
"""

FACTION_COLORS: dict[str, tuple[str, str]] = {
    # slug -> (display name, ink)
    "mouse-grey": ("Mouse Grey", "#5b5952"),      # DIM
    "rag-silver": ("Rag Silver", "#adaba0"),      # TEXT
    "bone-white": ("Bone White", "#fbfbf7"),      # BRIGHT
    "coin-gold": ("Coin Gold", "#f5b825"),        # GOLD
    "aether-teal": ("Aether Teal", "#45d0c0"),    # AETHER
    "warden-violet": ("Warden Violet", "#d967c8"),  # VIOLET
    "ember-red": ("Ember Red", "#f26541"),        # RED
    "orchard-green": ("Orchard Green", "#8ed24a"),  # OK
    "root-brown": ("Root Brown", "#b5722f"),      # BROWN
}

DEFAULT_COLOR = "warden-violet"


def faction_ink(slug: str) -> str:
    """The hex for a roster slug — unknown/empty falls back to the
    default, so a legacy banner keeps its violet."""
    return FACTION_COLORS.get(slug or "", FACTION_COLORS[DEFAULT_COLOR])[1]


def faction_color_name(slug: str) -> str:
    return FACTION_COLORS.get(slug or "",
                              FACTION_COLORS[DEFAULT_COLOR])[0]
