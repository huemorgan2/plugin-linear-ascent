"""012 — Guild training and the scarce-XP economy.

Levels are bought at the Guildhall (full XP bar + gold fee), never
granted in the field. XP is scarcer than gold from every source.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.render import render_scene_fragment


def fresh(pid: str = "trainee") -> dict:
    return state.new_player(pid)


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Trainee"):
    core.current_scene(p)
    while p["stage"] == "intro":                # 016: through the movie
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def _kill_one(p: dict) -> object:
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["encounter"]["range"] = "close"        # 002: skip the crossing
    p["encounter"]["hp"] = 1
    return choose(p, "attack")


# ── the fee curve ────────────────────────────────────────────────────────

def test_first_levelup_costs_200():
    assert economy.levelup_gold(1) == 200


def test_fee_grows_with_the_games_income_curve():
    fees = [economy.levelup_gold(lv) for lv in (1, 2, 10, 20, 50)]
    assert fees == sorted(fees)                  # monotone
    assert economy.levelup_gold(11) > economy.levelup_gold(10)  # band jump
    assert economy.levelup_gold(50) > 20_000     # exponential across bands


# ── XP scarcer than gold, in all places ──────────────────────────────────

def test_xp_below_gold_everywhere():
    # 046: gold rides the income pillar (exponential), kill XP rides
    # bar^1.5/wedge (polynomial) — the curves cross once on floors ~4–9
    # where XP may run up to ~1.3× gold, and gold wins everywhere after
    # (046 issues.md)
    for floor in (1, 11, 25, 50, 95):
        assert economy.xp_per_kill(floor) < economy.gold_per_kill(floor)
    for floor in range(4, 10):
        assert economy.xp_per_kill(floor) < \
            1.3 * economy.gold_per_kill(floor)
        assert economy.warden_xp(floor) < economy.warden_gold(floor)
    for m in economy.MILESTONES.values():
        assert m.xp < m.gold


# ── no auto-level ────────────────────────────────────────────────────────

def test_full_bar_never_levels_in_the_field():
    p = create_character(fresh())
    need = economy.xp_need(1)
    p["xp"] = need                               # bar already full
    hp_before_max = state.max_hp(p)
    p["hp"] = hp_before_max - 5
    s = _kill_one(p)
    assert p["level"] == 1                       # no level granted
    assert p["xp"] == need                       # surplus goes nowhere
    assert p["hp"] < state.max_hp(p)             # no free level-up heal
    assert not any(ln.startswith("+ ") and "XP" in ln for ln in s.body_lines)
    assert any(ln.startswith("+ ◈") for ln in s.body_lines)


# ── training at the Guildhall ────────────────────────────────────────────

def test_train_refused_without_full_bar():
    p = create_character(fresh())
    p["gold"] = 10_000
    p["xp"] = economy.xp_need(1) - 1
    choose(p, "guildhall")
    s = choose(p, "guild_train")
    assert p["level"] == 1
    assert p["gold"] == 10_000                   # nothing charged
    assert "XP" in "\n".join(s.body_lines)


def test_train_refused_without_the_fee():
    p = create_character(fresh())
    p["xp"] = economy.xp_need(1)
    p["gold"] = economy.levelup_gold(1) - 1
    choose(p, "guildhall")
    s = choose(p, "guild_train")
    assert p["level"] == 1
    assert p["xp"] == economy.xp_need(1)         # bar untouched
    assert "◈" in "\n".join(s.body_lines)


def test_train_buys_the_level_and_heals():
    p = create_character(fresh())
    need, fee = economy.xp_need(1), economy.levelup_gold(1)
    p["xp"] = need                               # hard bar — no overflow
    p["gold"] = fee + 50
    p["hp"] = 1
    choose(p, "guildhall")
    s = choose(p, "guild_train")
    assert p["level"] == 2
    assert p["xp"] == 0                          # next bar starts empty
    assert p["gold"] == 50
    assert p["hp"] == state.max_hp(p)            # wounds close on the level
    assert any(e["kind"] == "levelup" for e in p["_ledger"])
    assert "LEVEL 2" in "\n".join(s.body_lines)


def test_gain_xp_stops_at_the_bar():
    p = create_character(fresh())
    need = economy.xp_need(1)
    p["xp"] = need - 3
    assert state.gain_xp(p, 100) == 3
    assert p["xp"] == need
    assert state.gain_xp(p, 50) == 0
    assert p["xp"] == need


def test_gain_xp_uncapped_at_level_cap():
    p = create_character(fresh())
    p["level"] = economy.LEVEL_CAP
    p["xp"] = 10_000
    assert state.gain_xp(p, 500) == 500
    assert p["xp"] == 10_500


def test_ensure_current_clamps_overfilled_bar():
    p = create_character(fresh())
    p["xp"] = economy.xp_need(1) + 99
    state.ensure_current(p)
    assert p["xp"] == economy.xp_need(1)


def test_full_bar_kill_does_not_burn_rested():
    p = create_character(fresh())
    need = economy.xp_need(1)
    p["xp"] = need
    p["rested"] = 40
    _kill_one(p)
    assert p["xp"] == need
    assert p["rested"] == 40                 # nothing drawn off a 0-land kill


def test_guildhall_always_offers_training():
    p = create_character(fresh())
    scene = choose(p, "guildhall")
    assert any(o.id == "guild_train" for o in scene.options)
    fee = economy.levelup_gold(p["level"])
    train = next(o for o in scene.options if o.id == "guild_train")
    assert f"{fee:,}" in train.hint


# ── meters ───────────────────────────────────────────────────────────────

def test_meters_carry_level_and_render_says_xp_and_lv():
    p = create_character(fresh())
    p["level"] = 3
    scene = choose(p, "town")
    assert scene.meters.level == 3
    html = render_scene_fragment(scene)
    assert "XP " in html
    # 031 §4: the level left the rail for the ident header, spelled out
    assert "LEVEL 3" in html
    assert "✦" not in html
    text = scene.to_text()
    assert "XP" in text and "LV 3" in text
