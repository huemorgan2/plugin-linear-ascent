"""049 — gate steel wears, and is still never lost.

The basic weapons (rusted sword, basic bow, worn staff, legacy shiv)
carry a plain tier-1 durability pool now: they wear per swing, the
Forge mends them for a coin, broken means half strength. What does
NOT change: they are never LOST — a replaced basic rides to the pack
instead of the scrap bin, death's tumble passes over them, and the
pawn broker refuses them.
"""

from plugin_linear_ascent import economy, sheet
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text)


def _character(name):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, "human")
    choose(p, "", text=name)
    return p


def test_the_basic_weapon_carries_a_pool_from_birth():
    p = _character("Wearborn")
    assert economy.wears(economy.FORGE["rusted_sword"])
    assert p["durability"]["weapon"] == \
        economy.item_pool(economy.FORGE["rusted_sword"])
    assert state.durability_max(p, "weapon") > 0


def test_the_basic_weapon_wears_and_breaks_to_half_never_helpless():
    p = _character("Halfsteel")
    full = state.gear_bonus(p, "weapon")
    p["durability"]["weapon"] = 1
    assert state.wear_gear(p, "weapon")        # the snapping wear
    assert state.is_broken(p, "weapon")
    assert state.gear_bonus(p, "weapon") == full // 2


def test_a_bought_bow_sends_the_sword_to_the_pack_wear_and_all():
    p = _character("Packward")
    p["gold"] = 10_000
    state.wear_gear(p, "weapon", 5)
    worn = p["durability"]["weapon"]
    choose(p, "forge")
    s = choose(p, "buy_ashwood_bow")
    assert p["gear"]["weapon"] == "ashwood_bow"
    assert p["inventory"].get("rusted_sword") == 1
    assert p["durability_pack"]["rusted_sword"] == worn
    assert any("goes to your pack" in ln for ln in s.body_lines)
    # and it comes back as worn as it left
    choose(p, "wear_rusted_sword")
    assert p["gear"]["weapon"] == "rusted_sword"
    assert p["durability"]["weapon"] == worn


def test_the_forge_mends_gate_steel_for_a_coin():
    p = _character("Coinmend")
    p["gold"], p["xp"] = 1_000, 1_000
    state.wear_gear(p, "weapon", 100)
    choose(p, "forge")
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "repair_weapon")
    assert "pay ◈ 1 ·" in row.hint
    choose(p, "repair_weapon")
    assert p["durability"]["weapon"] == \
        economy.item_pool(economy.FORGE["rusted_sword"])


def test_promoting_a_held_weapon_swaps_the_pools():
    p = _character("Twohands")
    p["slots"] = 2
    p["gold"] = 10_000
    state.wear_gear(p, "weapon", 7)
    sword_worn = p["durability"]["weapon"]
    choose(p, "forge")
    choose(p, "buy_basic_bow")                 # rides the free hand
    assert set(p["held"]) == {"rusted_sword", "basic_bow"}
    combat._promote_held(p, "basic_bow")
    assert p["gear"]["weapon"] == "basic_bow"
    assert p["durability"]["weapon"] == \
        economy.item_pool(economy.FORGE["basic_bow"])
    assert p["durability_pack"]["rusted_sword"] == sword_worn
    combat._promote_held(p, "rusted_sword")
    assert p["durability"]["weapon"] == sword_worn


def test_the_broker_refuses_gate_steel():
    p = _character("Nopawn")
    p["inventory"]["rusted_sword"] = 1
    choose(p, "pawn")
    s = core.current_scene(p)
    assert not any(o.id == "sell_rusted_sword" for o in s.options)


def test_deaths_tumble_passes_over_the_basics():
    p = _character("Keptsword")
    p["level"] = 25                            # far past every mercy
    p["inventory"] = {"rusted_sword": 1}
    p["daily"]["death_save"] = True
    p["gold"] = 1_000
    fl = schema.get_floor(1)
    enc = next(e for e in fl.encounters if e.id == "feral_boar")
    combat.start_encounter(p, fl, enc)
    p["hp"] = 0
    combat._death(p, fl)
    assert p["inventory"].get("rusted_sword") == 1


def test_the_sheet_names_the_basics_wear():
    p = _character("Sheetline")
    state.wear_gear(p, "weapon", 10)
    line = sheet.character_sheet(p)["gear"]["weapon"]
    assert "durability" in line


def test_legacy_docs_get_the_pool_and_one_letter():
    p = _character("Lettered")
    p["version"] = 7
    del p["durability"]["weapon"]
    state.ensure_current(p)
    assert p["version"] >= 8
    assert p["durability"]["weapon"] == \
        economy.item_pool(economy.FORGE["rusted_sword"])
    ev = p.get("pending_events") or []
    assert any("Gate steel wears now" in (e.get("headline") or "")
               for e in ev)
