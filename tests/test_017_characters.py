"""017 phase 009 — races, doc v4 migration, typed kill FX.

The canon cast is three races (human, elf, dwarf); existing halfling
docs are re-registered human with an in-world letter, and the racial
luck bonus retires while luck DAYS and CHARMS keep working. Victory
scenes pick a kill GIF by the landing damage type.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import combat, core, state


def fresh(user="test-user-009"):
    return state.new_player(user)


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, race)
    choose(p, text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


# ── creation: exactly three races ────────────────────────────────────────

def test_creation_menu_has_exactly_three_races():
    assert list(economy.RACES) == ["human", "elf", "dwarf"]
    p = fresh("three-races")
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    scene = core.current_scene(p)
    assert [o.id for o in scene.options] == ["human", "elf", "dwarf"]


def test_halfling_is_not_choosable_at_the_gate():
    p = fresh("no-halfling")
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, "halfling")          # invalid option: scene re-renders
    assert p["race"] != "halfling"
    assert p["stage"] == "creation_race"


def test_new_docs_are_current():
    assert fresh()["version"] == 8        # 049: gate steel wears


# ── doc v4 migration: halfling → human ───────────────────────────────────

def _halfling_playing_doc(clazz):
    p = create_character(fresh(f"v3-halfling-{clazz}"), clazz=clazz)
    p["race"] = "halfling"         # pre-009 doc
    p["version"] = 3
    p.pop("pending_events", None)
    return p


@pytest.mark.parametrize("clazz", ["warrior", "archer", "sorcerer"])
def test_halfling_docs_wake_human_with_a_letter(clazz):
    p = _halfling_playing_doc(clazz)
    state.ensure_current(p)
    assert p["version"] >= 4
    assert p["race"] == "human"
    ev = p["pending_events"][0]
    assert "registrar" in ev["eyebrow"].lower()
    assert "HUMAN" in " ".join(ev["body_lines"])
    # idempotent: running again neither re-registers nor re-letters
    # (049's one-time gate-steel note rides along; it doesn't count)
    state.ensure_current(p)
    letters = [e for e in p["pending_events"]
               if "Gate steel" not in (e.get("headline") or "")]
    assert len(letters) == 1


def test_other_races_migrate_without_a_letter():
    for race in ("human", "elf", "dwarf"):
        p = create_character(fresh(f"v3-{race}"), race=race)
        p["version"] = 3
        p.pop("pending_events", None)
        state.ensure_current(p)
        assert p["race"] == race
        assert p["version"] >= 4
        # only 049's one-time gate-steel note may appear
        assert all("Gate steel" in (e.get("headline") or "")
                   for e in p.get("pending_events") or [])


def test_mid_creation_halfling_migrates_quietly():
    p = fresh("mid-creation")
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    p["race"] = "halfling"         # picked pre-009, never finished
    p["stage"] = "creation_class"
    p["version"] = 3
    state.ensure_current(p)
    assert p["race"] == "human"
    assert not p.get("pending_events")


def test_migrated_halfling_gets_the_human_energy_cap():
    p = _halfling_playing_doc("warrior")
    state.ensure_current(p)
    assert economy.energy_cap(p["level"], p["race"]) == \
        economy.energy_cap(p["level"], "") + 1


def test_luck_day_and_charm_survive_the_retirement():
    p = create_character(fresh("lucky-human"))
    p["gold"] = economy.APOTHECARY["luck_charm"].price
    p["location"] = "medlab"
    choose(p, "buy_luck_charm")
    assert p["flags"].get("luck_day") == state.world_day()


# ── kill FX: family × landing damage type ────────────────────────────────

def _fx(enc_id, name, dtype, shipped, first_clear=False):
    """Run _kill_fx against a fake shipped-art set."""
    real = combat._event_art
    combat._event_art = lambda slug: slug in shipped
    try:
        return combat._kill_fx({"id": enc_id}, name, first_clear, dtype)
    finally:
        combat._event_art = real


def test_kill_fx_picks_the_landing_damage_type():
    shipped = {"wolf_kill", "wolf_kill_melee", "wolf_kill_arrow",
               "wolf_kill_magic"}
    assert _fx("grey_wolf", "Grey wolf", "melee", shipped) == "wolf_kill_melee"
    assert _fx("grey_wolf", "Grey wolf", "ranged", shipped) == "wolf_kill_arrow"
    assert _fx("grey_wolf", "Grey wolf", "magic", shipped) == "wolf_kill_magic"


def test_kill_fx_falls_back_to_the_untyped_family_gif():
    shipped = {"brackjaw_kill"}
    assert _fx("", "Warden Brackjaw", "melee", shipped) == "brackjaw_kill"
    assert _fx("", "Warden Brackjaw", "magic", shipped) == "brackjaw_kill"


def test_kill_fx_family_match_is_per_token():
    shipped = {"rat_kill", "rat_kill_melee", "wolf_kill_melee"}
    # "curator" contains "rat" but is not the rat family
    assert _fx("alpha_curator", "Alpha curator", "melee", shipped) == ""
    # "wolfpack" starts with "wolf" — it IS the wolf family
    assert _fx("orchard_wolfpack", "Orchard wolf", "melee",
               shipped) == "wolf_kill_melee"
    assert _fx("hedge_rat", "Hedgerow rat", "melee",
               shipped) == "rat_kill_melee"


def test_kill_fx_first_clear_still_opens_the_gate():
    assert _fx("grey_wolf", "Grey wolf", "melee", set(),
               first_clear=True) == "ascent_open"
    assert _fx("grey_wolf", "Grey wolf", "melee", set()) == ""


# ── 009 icon audit: both icon surfaces, no pack crates ──────────────────
# The pack strip resolves through icons.icon_key; shop option rows
# resolve independently through render._opt_gear_icon. Every shipped
# item must land on a real glyph through BOTH paths.

def _pack_url():
    from plugin_linear_ascent import icons
    return icons.icon_data_url("pack")


def test_every_forge_item_has_a_real_glyph():
    from plugin_linear_ascent import icons
    for slug, g in economy.FORGE.items():
        key = icons.icon_key(slug, g.slot)
        assert key != "pack", (slug, g.slot)
        assert icons.icon_data_url(key) != _pack_url(), (slug, key)


def test_every_relic_has_a_real_glyph_on_both_surfaces():
    from plugin_linear_ascent import icons, render
    for slug in economy.RELICS:
        key = icons.icon_key(slug, "relic")
        assert key != "pack", slug
        assert icons.icon_data_url(key) != _pack_url(), (slug, key)
        html = render._opt_gear_icon(f"buy_{slug}")
        assert html and _pack_url() not in html, slug


def test_every_apothecary_item_has_a_real_glyph():
    from plugin_linear_ascent import icons
    for slug in economy.APOTHECARY:
        key = icons.icon_key(slug)
        assert key != "pack", slug
        assert icons.icon_data_url(key) != _pack_url(), (slug, key)


def test_shop_rows_draw_forge_and_arrow_icons():
    from plugin_linear_ascent import render
    assert _pack_url() not in render._opt_gear_icon("buy_arrow_pack")
    some_weapon = next(s for s, g in economy.FORGE.items()
                       if g.slot == "weapon" and g.price > 0)
    assert render._opt_gear_icon(f"buy_{some_weapon}")
    assert render._opt_gear_icon("hunt") == ""    # text rows stay text


def test_all_icon_grids_are_16x16_and_drawn():
    from plugin_linear_ascent import icons
    for key, grid in icons._GRIDS.items():
        assert len(grid) == 16, key
        assert all(len(row) == 16 for row in grid), key
        assert any("#" in row for row in grid), f"{key} is blank"
        assert all(set(row) <= {"#", "."} for row in grid), key


def test_every_floor_1_to_3_family_ships_all_three_types():
    """The 009 staging promise: every wilds family on floors 1-3 has
    melee/arrow/magic kill art on disk."""
    from plugin_linear_ascent.content import schema
    families = set()
    for n in (1, 2, 3):
        for enc in schema.get_floor(n).encounters:
            tokens = enc.id.replace("_", " ").split()
            fam = next((f for f in combat._KILL_FAMILIES
                        if any(t.startswith(f) for t in tokens)), None)
            if fam is None:
                # 038: kinded creatures play per-kind reels (freed/fall/
                # evicted), never the family kill art — only legacy
                # wilds without a kind still need a family here.
                assert enc.kind, \
                    f"floor {n} encounter {enc.id} has no kill family"
                continue
            families.add(fam)
    for fam in families:
        for suffix in ("melee", "arrow", "magic"):
            assert combat._event_art(f"{fam}_kill_{suffix}"), \
                f"missing kill art {fam}_kill_{suffix}"
