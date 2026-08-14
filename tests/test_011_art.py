"""011: every monster has art, ids are globally unique, variants retint.

Art is keyed by encounter id — a repeated id across floors would silently
reuse another creature's image, and a missing file falls back to the floor
banner. Both are content bugs this file gates against.
"""

import os

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, state

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "plugin_linear_ascent", "content", "art")


def _creature_slugs() -> set[str]:
    d = os.path.join(ART, "creatures")
    return {f.rsplit("_", 1)[0] for f in os.listdir(d) if f.endswith(".png")}


def test_encounter_ids_globally_unique():
    seen: dict[str, int] = {}
    for f in schema.load_floors(force=True).values():
        for e in f.encounters:
            assert e.id not in seen, (
                f"encounter id {e.id!r} on floors {seen[e.id]} and "
                f"{f.floor} — art is keyed by id, rename one")
            seen[e.id] = f.floor


def test_every_encounter_has_creature_art():
    have = _creature_slugs()
    missing = sorted(
        e.id for f in schema.load_floors().values()
        for e in f.encounters if e.id not in have)
    assert not missing, f"encounters without art: {missing}"


def test_every_warden_has_art():
    have = _creature_slugs()
    banners = {f.rsplit("_", 1)[0]
               for f in os.listdir(os.path.join(ART, "banners"))
               if f.endswith(".png")}
    missing = []
    for f in schema.load_floors().values():
        if f.floor % 10 == 0:
            slug = "gnarl" if f.floor == 10 else f.banner
            if slug not in have and slug not in banners:
                missing.append(slug)
        elif f"warden_{f.floor:03d}" not in have:
            missing.append(f"warden_{f.floor:03d}")
    assert not missing, f"wardens without art: {missing}"


# ── 049/055: floor 1 promises the full reel matrix ───────────────────────
# The first floor is the game's handshake: every creature has its
# closeup banner and a typed kill reel for every race × weapon line.
# A hole here silently falls back to the untyped reel — a content bug.

def test_floor1_has_every_typed_reel():
    events = {f for f in os.listdir(os.path.join(ART, "events"))
              if f.endswith(".gif")}
    closeups = _creature_slugs()
    floor1 = schema.load_floors()[1]
    beats = [(e.id, combat._BREED_FX_VERB[e.kind])
             for e in floor1.encounters] + [("warden_001", "evicted")]
    missing = []
    for slug, verb in beats:
        if slug not in closeups:
            missing.append(f"creatures/{slug}")
        for race in economy.RACES:
            for line in combat._LINE_OF_DTYPE.values():
                g = f"{slug}_{verb}_{race}_{line}_320x112.gif"
                if g not in events:
                    missing.append(f"events/{g}")
    assert not missing, f"floor 1 art holes: {missing}"


# ── specimen variants retint the shared art ──────────────────────────────

def _fight_scene_with_specimen(specimen: str):
    p = state.new_player("t")
    p.update(race="human", clazz="warrior", name="T", status="playing")
    floor = schema.get_floor(1)
    scene = combat.start_encounter(p, floor, floor.encounters[0])
    p["encounter"]["specimen"] = specimen
    return combat.fight_scene(p, floor, opener=True)


def test_creature_art_stays_up_for_every_round():
    # regression: the banner used to be opener-only, so every round after
    # the first showed no creature and monsters read as art-less.
    p = state.new_player("t")
    p.update(race="human", clazz="warrior", name="T", status="playing")
    floor = schema.get_floor(1)
    opener = combat.start_encounter(p, floor, floor.encounters[0])
    later = combat.fight_scene(p, floor, note="you swing again")
    assert opener.banner == p["encounter"]["id"]
    assert later.banner == opener.banner
    assert 'class="banner"' in render.render_scene_fragment(later)


def test_fight_scene_carries_specimen_variant():
    assert _fight_scene_with_specimen("alpha").banner_variant == "alpha"
    assert _fight_scene_with_specimen("common").banner_variant == ""


def test_variant_tint_overrides_default():
    assert render._banner_tint("feral_boar", "alpha") == render.GOLD
    assert render._banner_tint("feral_boar", "tough") == render.VIOLET_SOFT
    assert render._banner_tint("feral_boar", "runt") == render.FAINT
    assert render._banner_tint("feral_boar", "") == render.ART


def test_variant_survives_scene_roundtrip():
    from plugin_linear_ascent.engine.scene import Scene
    s = _fight_scene_with_specimen("tough")
    assert Scene.from_dict(s.to_dict()).banner_variant == "tough"


def test_specimen_keys_match_render_tints():
    assert set(render._VARIANT_TINT) == set(economy.SPECIMENS) - {"common"}
