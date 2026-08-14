"""048 phase 5 — T2: understood, not just fair.

The "can I tell why?" law as assertions on rendered scenes: every
monster shows every number plus its sign; the verdict before a fight
names the player's actual best answer and its rank; every locked row
explains its gate; every miss/shallow line blames the hand by rank;
every defeat names its cause and one lever the player owns.
"""

from types import SimpleNamespace

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state
from plugin_linear_ascent.sheet import character_sheet


# ── helpers (test_048_no_classes patterns) ─────────────────────────────

def _classless(uid):
    p = state.new_player(uid)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1", "")
    core.apply_choice(p, "human", "")
    core.apply_choice(p, "", "Testa")
    return p


def _arm(p, weapons, training, slots=None):
    held = [weapons] if isinstance(weapons, str) else list(weapons)
    p["training"] = dict(training)
    p["slots"] = slots or len(held)
    p["held"] = held
    p["gear"]["weapon"] = held[0]
    return p


def _enc(traits, name="Test Beast"):
    return SimpleNamespace(id="test_beast", name=name,
                           prose="It waits.", weight=1,
                           traits=tuple(traits), kind="", was="")


def _start(p, traits, rng="at_range"):
    """A fight against a monster of OUR choosing — content-independent."""
    fl = schema.get_floor(1)
    s = combat.start_encounter(p, fl, _enc(traits), "wilds")
    e = p["encounter"]
    e["range"] = rng
    e["gap"] = 1 if rng == "at_range" else 0
    return combat.fight_scene(p, fl, opener=True)


def _opt(s, oid):
    for o in s.options or []:
        if o.id == oid:
            return o
    return None


def _scene_text(s):
    return " ".join([s.headline or "", s.support or "",
                     s.shard_note or ""] + list(s.body_lines or [])
                    + [f"{o.label} {o.hint}" for o in (s.options or [])])


# ── every monster shows every number plus its sign ─────────────────────

def test_fight_card_shows_every_number_and_sign():
    cases = [(("fly",), "⚡"), (("armoured",), "⛨"),
             (("magic_resist",), "✧")]
    for i, (traits, sign) in enumerate(cases):
        p = _arm(_classless(f"048-v-card-{i}"), "rusted_sword",
                 {"blade": 6, "bow": 0, "staff": 0})
        s = _start(p, traits)
        e = p["encounter"]
        txt = s.to_text()
        for bit in (f"HP {e['hp']}", f"ATK {e['atk']}",
                    f"DEF {e['def']}", "SPD"):
            assert bit in txt, (traits, bit, txt)
        assert sign in s.headline, (traits, s.headline)


def test_fight_card_carries_the_triangle_line():
    p = _arm(_classless("048-v-tri"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ("armoured",))
    text = _scene_text(s)
    assert "steel: half" in text
    assert "arrows: glance" in text
    assert "magic: full" in text


def test_plain_monster_says_no_sign():
    p = _arm(_classless("048-v-plain"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ())
    assert "no sign — every weapon bites full" in _scene_text(s)


def test_speed_word_rides_the_spd_number():
    p = _arm(_classless("048-v-spd"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    from plugin_linear_ascent import render
    s = _start(p, ("armoured",))          # armoured — SPD 3
    assert "SPD 3" in s.to_text()
    assert "SPEED 3" in render._estat_html(s.enemy)
    p2 = _arm(_classless("048-v-spd2"), "rusted_sword",
              {"blade": 6, "bow": 0, "staff": 0})
    s2 = _start(p2, ("fly",))           # fly — SPD 7; alphas +1
    assert "SPD 7" in s2.to_text()


def test_hunt_menu_carries_no_stat_roster():
    # 048 retro: the per-monster stat dump left the camp — the fight
    # card and the mechanics page carry the numbers.
    p = _classless("048-v-hunt")
    core.apply_choice(p, "gate", "")
    s = core.apply_choice(p, "floor_1", "")
    text = " ".join(s.body_lines or [])
    assert "Out past the wire:" not in text
    assert "HP " not in text and "ATK " not in text


# ── the verdict, before every fight ────────────────────────────────────

def test_verdict_names_the_held_answer_and_rank():
    p = _arm(_classless("048-v-verd1"), "rusted_sword",
             {"blade": 4, "bow": 0, "staff": 0})
    s = _start(p, ("armoured",))
    text = _scene_text(s)
    # the held blade's answer, with the player's actual rank…
    assert "rank 4" in text
    # …and the full answer it does NOT hold, named as the lever
    assert "staff" in text
    assert "rank 0" in text


def test_verdict_on_a_flyer_with_steel_only_says_cant_reach():
    p = _arm(_classless("048-v-verd2"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ("fly",))
    text = _scene_text(s).lower()
    assert "cannot reach" in text or "can't reach" in text
    assert "bow" in text


# ── locked rows explain their gates ────────────────────────────────────

def test_third_slot_row_shows_locked_below_level_8():
    # 049.2: the row is always on the menu — below level 8 it LOOKS
    # locked and names the level; at 8 it prints its price instead.
    p = _arm(_classless("048-v-slot3"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    p["slots"] = 2
    p["floor"] = 1
    p["location"] = "school"
    s = core._school_scene(p)
    row = next(o for o in s.options if o.id == "buy_carry3")
    assert row.locked
    assert f"level {economy.CARRY3_LEVEL}" in row.hint
    assert "locked" in _scene_text(s)
    p["level"] = economy.CARRY3_LEVEL
    s = core._school_scene(p)
    row = next(o for o in s.options if o.id == "buy_carry3")
    assert not row.locked
    assert f"{economy.CARRY3_XP} XP" in row.hint


def test_school_rows_say_what_improves():
    p = _classless("048-v-school")
    p["floor"] = 1
    s = core._school_scene(p)
    text = _scene_text(s)
    assert "miss" in text
    assert "worst swing" in text


# ── per-slot attack labels with predicted damage ───────────────────────

def test_attack_rows_carry_rank_and_predicted_damage():
    p = _arm(_classless("048-v-rows"), ["rusted_sword", "basic_bow"],
             {"blade": 4, "bow": 2, "staff": 0}, slots=2)
    s = _start(p, (), rng="close")
    lead = _opt(s, "attack")
    assert lead is not None
    assert "rank 4" in lead.hint and "~" in lead.hint, lead.hint
    side = _opt(s, "attack_basic_bow")
    assert side is not None
    assert "rank 2" in side.hint and "~" in side.hint, side.hint


# ── the TRAINED block lives on the player, never the weapon ────────────

def test_sheet_carries_trained_block_and_holding_row():
    p = _arm(_classless("048-v-sheet"), ["rusted_sword", "basic_bow"],
             {"blade": 4, "bow": 2, "staff": 0}, slots=2)
    sheet = character_sheet(p)
    assert sheet["trained"] == {"blade": 4, "bow": 2, "staff": 0}
    assert sheet["holding"] == ["Rusted Sword", "Basic Bow"]


# ── miss and shallow lines name the rank ───────────────────────────────

def test_miss_line_names_the_rank(monkeypatch):
    p = _arm(_classless("048-v-miss"), "rusted_sword",
             {"blade": 1, "bow": 0, "staff": 0})
    _start(p, (), rng="close")
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: True)
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    s = core.apply_choice(p, "attack", "")
    text = _scene_text(s)
    # 053: the fumble leads with its name and still points at the lever
    assert "ATTACK MISSED" in text
    assert "rank-1" in text
    assert "School" in text


def test_shallow_hit_names_the_rank(monkeypatch):
    p = _arm(_classless("048-v-shallow"), "rusted_sword",
             {"blade": 4, "bow": 0, "staff": 0})
    _start(p, (), rng="close")
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: lo)
    s = core.apply_choice(p, "attack", "")
    text = _scene_text(s)
    assert "rank-4" in text and "shallow" in text, text


# ── every defeat names the cause and one lever ─────────────────────────

def _dying(uid, traits, weapons, training):
    p = _arm(_classless(uid), weapons, training)
    _start(p, traits)
    p["daily"]["death_save"] = True     # past the daily save
    p["hp"] = 0
    return p


def test_defeat_by_armoured_with_a_bow_names_the_plate():
    p = _dying("048-v-d1", ("armoured",), "basic_bow",
               {"blade": 0, "bow": 6, "staff": 0})
    s = combat._death(p, schema.get_floor(1))
    text = _scene_text(s).lower()
    assert "plate" in text and "arrow" in text
    assert "staff" in text or "steel" in text


def test_defeat_by_a_flyer_with_steel_only_names_the_wings():
    p = _dying("048-v-d2", ("fly",), "rusted_sword",
               {"blade": 6, "bow": 0, "staff": 0})
    s = combat._death(p, schema.get_floor(1))
    text = _scene_text(s).lower()
    assert "flew" in text or "flies" in text
    assert "bow" in text


def test_defeat_at_rank_one_names_the_school():
    p = _dying("048-v-d3", (), "rusted_sword",
               {"blade": 1, "bow": 0, "staff": 0})
    s = combat._death(p, schema.get_floor(1))
    text = _scene_text(s)
    assert "rank-1" in text.lower()
    assert "School" in text


def test_defeat_by_plain_overreach_names_the_trade():
    p = _dying("048-v-d4", (), "rusted_sword",
               {"blade": 6, "bow": 0, "staff": 0})
    s = combat._death(p, schema.get_floor(1))
    text = _scene_text(s).lower()
    assert "harder" in text
    assert "gear" in text or "floor" in text or "run" in text


def test_the_daily_save_also_teaches():
    p = _arm(_classless("048-v-d5"), "basic_bow",
             {"blade": 0, "bow": 6, "staff": 0})
    _start(p, ("armoured",))
    p["hp"] = 0                          # death_save still unspent
    s = combat._death(p, schema.get_floor(1))
    text = _scene_text(s).lower()
    assert "plate" in text and "arrow" in text


# ── phase 6 ships the bounty label ─────────────────────────────────────

def test_early_kills_carry_the_bounty_label(monkeypatch):
    p = _arm(_classless("048-v-bounty"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    _start(p, (), rng="close")
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    p["encounter"]["hp"] = 1
    fl = schema.get_floor(1)
    s = combat.resolve_fight_action(p, fl, "attack")
    assert any("young-tower bounty" in ln for ln in s.body_lines), \
        s.body_lines
