"""Doc v5 — the pre-017 Forge purchase, re-forged into its owner's line.

Every weapon the Forge had sold before 017 became warrior-line when the
three lines landed, so archers and sorcerers who had bought one were left
off-class on gear they paid full price for. v5 trades each such piece —
worn and packed — for the same rung of the holder's own line.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import combat, core, state


def fresh(user="test-user-offclass"):
    return state.new_player(user)


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def _v4_doc(clazz, weapon, race="human"):
    """A doc that already took every migration up to the halfling one."""
    p = create_character(fresh(f"v4-{clazz}-{weapon}"), race=race,
                         clazz=clazz)
    p["gear"]["weapon"] = weapon
    p["version"] = 4
    p.pop("pending_events", None)
    return p


# ── the twin lookup ──────────────────────────────────────────────────────

@pytest.mark.parametrize("slug,line,want", [
    ("pigsticker", "archer", "ashwood_bow"),
    ("pigsticker", "sorcerer", "tallowwood_staff"),
    ("ashwood_bow", "warrior", "pigsticker"),
    ("iron_sword", "archer", "sinew_backed_bow"),        # a mid rung
    ("dawnbreaker", "sorcerer", "dawncaller_staff"),     # the top rung
])
def test_line_twin_matches_rung(slug, line, want):
    g = economy.FORGE[slug]
    twin = economy.line_twin(g, line)
    assert twin.slug == want
    assert (twin.rung, twin.bonus, twin.price) == (g.rung, g.bonus, g.price)


def test_line_twin_declines_own_line_and_free_gear():
    assert economy.line_twin(economy.FORGE["pigsticker"], "warrior") is None
    assert economy.line_twin(economy.CLASS_STARTERS["archer"],
                             "warrior") is None
    assert economy.line_twin(economy.FORGE["padded_jerkin"],
                             "archer") is None


# ── the worn weapon ──────────────────────────────────────────────────────

@pytest.mark.parametrize("clazz,want", [
    ("archer", "ashwood_bow"),
    ("sorcerer", "tallowwood_staff"),
])
def test_bought_warrior_steel_is_reforged_with_a_letter(clazz, want):
    p = _v4_doc(clazz, "pigsticker")
    state.ensure_current(p)
    assert p["version"] >= 5
    assert p["gear"]["weapon"] == want
    ev = p["pending_events"][0]
    assert "forge" in ev["eyebrow"].lower()
    assert "Pigsticker" in " ".join(ev["body_lines"])
    # idempotent: a second pass neither re-forges nor re-letters
    state.ensure_current(p)
    assert len(p["pending_events"]) == 1


def test_a_warrior_keeps_the_steel_and_hears_nothing():
    p = _v4_doc("warrior", "pigsticker")
    state.ensure_current(p)
    assert p["gear"]["weapon"] == "pigsticker"
    assert not p.get("pending_events")


def test_reforged_weapon_is_no_longer_off_class():
    p = _v4_doc("archer", "pigsticker")
    assert combat._off_class(p)
    state.ensure_current(p)
    assert not combat._off_class(p)
    assert combat._damage_type(p) == "ranged"


def test_wear_and_honing_come_across():
    p = _v4_doc("archer", "pigsticker")
    p["durability"]["weapon"] = 300
    p["hone"]["weapon"] = 2
    state.ensure_current(p)
    assert p["gear"]["weapon"] == "ashwood_bow"
    assert p["durability"]["weapon"] == 300
    assert p["hone"]["weapon"] == 2


def test_deliberate_off_class_buys_are_left_alone_after_v5():
    """v5 is a one-time amnesty, not a rule change: a climber who buys
    off-class on purpose today still carries the penalty."""
    p = create_character(fresh("buys-off-class"), clazz="archer")
    p["level"], p["gold"] = 3, 10_000
    core.apply_choice(p, "forge")
    blade = economy.off_class_offer("warrior", p["level"]).slug
    core.apply_choice(p, f"buy_{blade}")
    assert p["gear"]["weapon"] == blade
    state.ensure_current(p)
    assert p["gear"]["weapon"] == blade


# ── the pack ─────────────────────────────────────────────────────────────

def test_packed_off_class_weapon_is_reforged_too():
    p = _v4_doc("sorcerer", "worn_staff")
    p["inventory"]["wolfbite"] = 1
    p["durability_pack"]["wolfbite"] = 120
    state.ensure_current(p)
    assert "wolfbite" not in p["inventory"]
    assert p["inventory"]["stormtwig_staff"] == 1
    assert p["durability_pack"]["stormtwig_staff"] == 120
    assert "Wolfbite" in " ".join(p["pending_events"][0]["body_lines"])


def test_pack_merge_keeps_the_better_pool():
    p = _v4_doc("archer", "basic_bow")
    p["inventory"].update({"pigsticker": 1, "ashwood_bow": 1})
    p["durability_pack"].update({"pigsticker": 400, "ashwood_bow": 90})
    state.ensure_current(p)
    assert "pigsticker" not in p["inventory"]
    assert p["inventory"]["ashwood_bow"] == 2
    assert p["durability_pack"]["ashwood_bow"] == 400


def test_non_weapon_pack_items_are_untouched():
    p = _v4_doc("archer", "basic_bow")
    p["inventory"].update({"luck_charm": 2, "padded_jerkin": 1})
    state.ensure_current(p)
    assert p["inventory"] == {"luck_charm": 2, "padded_jerkin": 1}


# ── the basic weapon, including docs v2 skipped ──────────────────────────

@pytest.mark.parametrize("clazz,want", [
    ("warrior", "rusted_sword"),
    ("archer", "basic_bow"),
    ("sorcerer", "worn_staff"),
])
def test_mid_creation_docs_finally_get_their_class_weapon(clazz, want):
    """v2 only healed docs already 'playing'; someone who picked a class
    and walked away kept the generic shiv forever."""
    p = fresh(f"mid-creation-{clazz}")
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, "human")
    choose(p, clazz)
    p["gear"]["weapon"] = economy.STARTER_WEAPON.slug   # pre-017 doc
    p["version"] = 1
    state.ensure_current(p)
    assert p["gear"]["weapon"] == want
    assert not p.get("pending_events")


def test_wrong_class_starter_is_swapped_silently():
    p = _v4_doc("archer", "rusted_sword")
    state.ensure_current(p)
    assert p["gear"]["weapon"] == "basic_bow"
    assert not p.get("pending_events")


def test_classless_docs_are_not_touched():
    p = fresh("no-class-yet")
    core.current_scene(p)
    p["version"] = 1
    state.ensure_current(p)
    assert p["clazz"] is None
    assert p["version"] >= 5
