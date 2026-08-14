"""056 — the Playing feed's engine emits.

The engine stays pure: each event is one _effect(p, "happening", ...)
appended to the doc, guarded by `_world is not None` (solo dev play emits
nothing), and the faction-grain lines (floor step, weapon buy) only fire
for a climber under a banner.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, social, state


def fresh(world=True, guild=None):
    p = state.new_player("test-user-056")
    p["stage"] = "playing"
    p["name"] = "Testa"
    p["location"] = "town"
    if guild:
        p["guild"] = guild
    if world:
        p["_world"] = {"frontier": 100,
                       "census": {"total": 1, "by_floor": {}}}
    return p


def happenings(p):
    return [e for e in p.get("_effects", []) if e["kind"] == "happening"]


# ── level up (world) ─────────────────────────────────────────────────────

def test_levelup_emits_a_world_line():
    p = fresh()
    p["xp"] = economy.xp_need(p["level"])
    p["gold"] = economy.levelup_gold(p["level"]) + 10
    social.guild_train(p)
    hs = happenings(p)
    assert len(hs) == 1
    assert "Testa bought level 2 at the drillmaster" in hs[0]["line"]
    assert hs[0]["meta"] == {"level": 2}
    assert hs[0].get("scope", "world") == "world"


def test_levelup_solo_emits_nothing():
    p = fresh(world=False)
    p["xp"] = economy.xp_need(p["level"])
    p["gold"] = economy.levelup_gold(p["level"]) + 10
    social.guild_train(p)
    assert not happenings(p)


def test_refused_training_emits_nothing():
    p = fresh()
    p["xp"] = 0
    social.guild_train(p)
    assert not happenings(p)


# ── sleeping in the fields (world) ───────────────────────────────────────

def test_sleep_fields_emits_floor_and_line():
    p = fresh()
    p["floor"] = 3
    core._sleep_action(p, "sleep_fields")
    hs = happenings(p)
    assert len(hs) == 1
    assert "lies down in the open fields of floor 3" in hs[0]["line"]
    assert hs[0]["floor"] == 3


def test_sleep_lodge_is_nobodys_business():
    p = fresh()
    p["gold"] = 1000
    core._sleep_action(p, "sleep_lodge")
    assert not happenings(p)


# ── entering a floor (faction grain) ─────────────────────────────────────

def test_floor_step_is_faction_grain_with_a_banner():
    p = fresh(guild="House Ash")
    p["unlocked_floor"] = 5
    p["level"] = 99
    p["flags"]["floor_seen_2"] = True
    core._gate_pick(p, "floor_2")
    hs = happenings(p)
    assert len(hs) == 1
    assert hs[0]["scope"] == "faction"
    assert "Testa steps onto floor 2" in hs[0]["line"]
    assert hs[0]["floor"] == 2


def test_floor_step_without_a_banner_is_silent():
    p = fresh()
    p["unlocked_floor"] = 5
    p["level"] = 99
    p["flags"]["floor_seen_2"] = True
    core._gate_pick(p, "floor_2")
    assert not happenings(p)


# ── buying gear (faction grain) ──────────────────────────────────────────

def _buy(p, slug="iron_sword"):
    g = economy.FORGE[slug]
    p["gold"] = g.price + 1000
    p["level"] = 99
    p["unlocked_floor"] = 100
    return core._gear_purchase(p, g, lambda q: core._build_scene(q))


def test_gear_buy_is_faction_grain_with_a_banner():
    p = fresh(guild="House Ash")
    _buy(p)
    hs = happenings(p)
    assert len(hs) == 1
    assert hs[0]["scope"] == "faction"
    assert "bought" in hs[0]["line"]
    assert hs[0]["meta"]["item"] == "iron_sword"


def test_gear_buy_without_a_banner_is_silent():
    p = fresh()
    _buy(p)
    assert not happenings(p)
