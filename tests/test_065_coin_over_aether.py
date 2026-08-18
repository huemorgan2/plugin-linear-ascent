"""065 — coin over aether, the wound bill.

1. A kill's gold is never below its XP: the mean paycheck rides ≥ 1.25 ×
   the kill's XP on every floor (the 012 law, restored as a floor after
   048's steeper XP slope crossed it on floors 7–10), specimens scale XP
   as they scale HP, and the rolled numbers on the card obey the law
   after every jitter and multiplier.
2. The tent bills by the wound: a whole bar costs six kills' base gold,
   a scratch a fraction; the gate-town row quotes THIS wound's bill and
   the death card the whole bar.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state
from tests.test_013_combat_feel import (at_gate_town, choose,
                                        create_character, fresh)


def _user(tag):
    return state.new_player(f"test-065-{tag}")


# ── 1. coin over aether ──────────────────────────────────────────────────

def test_mean_gold_rides_a_quarter_over_xp_on_every_floor():
    for f in range(1, 31):
        assert economy.gold_per_kill(f) >= round(
            economy.xp_per_kill(f) * economy.KILL_GOLD_OVER_XP) - 1, f
    # the price anchor is untouched — the extra is pocket coin
    assert economy.base_gold_per_kill(9) == round(
        economy.GOLD_PER_KILL_ANCHOR * economy.income_pillar(9))
    # deep, the pillar is above the floor rule again
    assert economy.gold_per_kill(20) == round(
        economy.GOLD_PER_KILL_ANCHOR * economy.income_pillar(20))


def _wilds_kill(p, floor, specimen, deep=False):
    fl = schema.get_floor(floor)
    enc = schema.Encounter(id="_t", name="Thing", weight=1,
                           prose="A thing arrives.", traits=())
    combat.start_encounter(p, fl, enc, "wilds", deep=deep)
    p["encounter"]["specimen"] = specimen
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    x0, g0 = p["xp"], p["gold"]
    combat.resolve_fight_action(p, fl, "attack")
    return p["xp"] - x0, p["gold"] - g0


def _climber(tag, floor=6):
    p = create_character(_user(tag))
    p["training"]["blade"] = 12
    p["unlocked_floor"], p["level"] = floor, 20   # room in the XP bar
    p["floor"] = floor
    return p


def test_the_card_never_writes_gold_below_xp():
    """100 rolled floor-6 kills across every specimen: gold > xp on
    each — after jitter (gold ±50%), the specimen and the profile."""
    seen = set()
    for i in range(100):
        spec = ("runt", "common", "tough", "alpha")[i % 4]
        p = _climber(f"law-{i}")
        xp, gold = _wilds_kill(p, 6, spec)
        assert xp > 0 and gold > xp, (i, spec, xp, gold)
        seen.add(spec)
    assert len(seen) == 4


def test_the_easy_kill_teaches_less(monkeypatch):
    monkeypatch.setattr(state, "rng_jitter", lambda p, base, pct: base)
    runt_xp, runt_gold = _wilds_kill(_climber("runt"), 6, "runt")
    com_xp, com_gold = _wilds_kill(_climber("common"), 6, "common")
    alpha_xp, alpha_gold = _wilds_kill(_climber("alpha"), 6, "alpha")
    assert runt_xp < com_xp < alpha_xp
    assert runt_gold < com_gold < alpha_gold
    assert runt_xp == round(economy.xp_per_kill(6)
                            * economy.SPECIMENS["runt"]["hp"])
    assert com_gold >= round(com_xp * economy.KILL_GOLD_OVER_XP) - 1


# ── 2. the wound bill ────────────────────────────────────────────────────

def test_the_wound_bill_scales_with_the_wound():
    full = economy.tent_full_price(6)
    assert full == round(economy.TENT_FULL_KILLS
                         * economy.base_gold_per_kill(6))
    assert economy.healer_tent_price(6, 0, 500) == full
    half = economy.healer_tent_price(6, 250, 500)
    assert abs(half - full / 2) <= 1
    scratch = economy.healer_tent_price(6, 450, 500)
    assert 0 < scratch < economy.gold_per_kill(6)
    assert economy.healer_tent_price(6, 500, 500) == 0
    # a 500-HP bar is no longer a half-kill refill
    assert full > 3 * economy.gold_per_kill(6)


def test_the_gate_row_quotes_this_wound_and_charges_it():
    p = at_gate_town(create_character(_user("row")))
    p["gold"] = 1000
    p["hp"] = state.max_hp(p) // 2
    missing = state.max_hp(p) - p["hp"]
    price = economy.healer_tent_price(1, p["hp"], state.max_hp(p))
    s = core.current_scene(p)
    heal = next(o for o in s.options if o.id == "heal")
    assert heal.hint == f"pay ◈ {price} · +{missing} HP"
    gold = p["gold"]
    choose(p, "heal")
    assert p["gold"] == gold - price
    assert p["hp"] == state.max_hp(p)
    # whole: no tent row
    s = core.current_scene(p)
    assert not any(o.id == "heal" for o in s.options)


def test_the_death_card_prices_the_whole_bar():
    p = at_gate_town(create_character(_user("death")))
    fl = schema.get_floor(1)
    enc = schema.Encounter(id="_t", name="Thing", weight=1,
                           prose="A thing arrives.", traits=())
    combat.start_encounter(p, fl, enc, "wilds")
    p["hp"] = 1
    p["encounter"]["atk"] = 999
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 10 ** 6
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.event_kind == "death"
    heal = next(o for o in s.options if o.id == "heal")
    assert f"◈ {economy.tent_full_price(1)}" in heal.hint
