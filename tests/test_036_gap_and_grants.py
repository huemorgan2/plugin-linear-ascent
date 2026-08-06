"""036 — the gap ladder and open grants.

The archer's third axis: Create distance always makes ground (gap 1→3),
the parting blow's CHANCE is what speed buys, and every length of gap is
draw-time — bow damage climbs the ladder (×1 / ×1.25 / ×1.5) and pays
for it in close quarters (×0.5). Run is now "Run away". And the Vault's
grants desk serves every level — the receiver gate is gone.
"""

import pytest

from plugin_linear_ascent import economy, unlocks
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="archer", name="Gap"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    return p


def _player(clazz, floor_no, name):
    p = create_character(fresh(name), clazz=clazz, name=name)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    return p


def _enc(floor_no, enc_id):
    fl = schema.get_floor(floor_no)
    return fl, next(e for e in fl.encounters if e.id == enc_id)


# ── the curves ───────────────────────────────────────────────────────────

def test_gap_mult_ladder_and_close_penalty():
    assert economy.bow_gap_mult(0) == economy.BOW_CLOSE_MULT == 0.5
    assert economy.bow_gap_mult(1) == 1.0
    assert economy.bow_gap_mult(2) == 1.25
    assert economy.bow_gap_mult(3) == 1.5
    assert economy.bow_gap_mult(9) == 1.5          # capped at GAP_MAX


def test_parting_blow_chance_falls_with_speed_advantage():
    even = economy.p_gap_hit(5, 5)
    faster = economy.p_gap_hit(7, 5)
    slower = economy.p_gap_hit(5, 7)
    assert even == pytest.approx(0.65)
    assert faster == pytest.approx(0.41)
    assert slower == pytest.approx(0.89)
    assert faster < even < slower
    assert economy.p_gap_hit(15, 1) == pytest.approx(0.05)   # floor
    assert economy.p_gap_hit(1, 15) == pytest.approx(0.95)   # cap


# ── the menu ─────────────────────────────────────────────────────────────

def test_run_reads_run_away():
    p = _player("archer", 1, "run-label")
    fl, enc = _enc(1, "grey_wolf")
    s = combat.start_encounter(p, fl, enc)
    labels = {o.id: o.label for o in s.options}
    assert labels["run"] == "Run away"


def test_archer_sees_create_distance_others_do_not():
    fl, enc = _enc(1, "grey_wolf")
    p = _player("archer", 1, "cd-archer")
    s = combat.start_encounter(p, fl, enc)
    assert "create_distance" in [o.id for o in s.options]
    for clazz in ("warrior", "sorcerer"):
        q = _player(clazz, 1, f"cd-{clazz}")
        s2 = combat.start_encounter(q, fl, enc)
        assert "create_distance" not in [o.id for o in s2.options]


def test_create_distance_row_disappears_at_the_cap(monkeypatch):
    p = _player("archer", 1, "cd-cap")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
    combat.resolve_fight_action(p, fl, "create_distance")   # 1 → 2
    combat.resolve_fight_action(p, fl, "create_distance")   # 2 → 3
    assert p["encounter"]["gap"] == economy.GAP_MAX
    s = combat.fight_scene(p, fl)
    assert "create_distance" not in [o.id for o in s.options]
    # a stale click at the cap is refused without spending anything
    hp0 = p["hp"]
    s2 = combat.resolve_fight_action(p, fl, "create_distance")
    assert p["encounter"]["gap"] == economy.GAP_MAX
    assert p["hp"] == hp0
    assert any("long edge" in ln for ln in s2.body_lines)


# ── the ladder in play ───────────────────────────────────────────────────

def test_clean_break_when_the_roll_says_so(monkeypatch):
    p = _player("archer", 1, "cd-clean")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    hp0 = p["hp"]
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
    s = combat.resolve_fight_action(p, fl, "create_distance")
    assert p["encounter"]["gap"] == 2
    assert p["encounter"]["range"] == "at_range"
    assert p["hp"] == hp0
    assert any("break clean" in ln for ln in s.body_lines)


def test_parting_blow_collects_when_the_roll_lands(monkeypatch):
    p = _player("archer", 1, "cd-toll")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    hp0 = p["hp"]
    # the p_gap_hit roll succeeds; damage pinned high so the halved
    # blow still chips
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    s = combat.resolve_fight_action(p, fl, "create_distance")
    assert p["encounter"]["gap"] == 2          # the ground IS made
    assert p["hp"] < hp0                       # but the toll was paid
    assert any("collects the toll" in ln for ln in s.body_lines)


def test_bow_damage_climbs_the_ladder(monkeypatch):
    fl, enc = _enc(1, "grey_wolf")
    dealt = {}
    for gap in (1, 3):
        p = _player("archer", 1, f"gap-dmg-{gap}")
        combat.start_encounter(p, fl, enc)
        p["encounter"]["gap"] = gap
        p["encounter"]["hp"] = 10_000
        monkeypatch.setattr(state, "rng_int", lambda pl, a, b: b)
        monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
        hp0 = p["encounter"]["hp"]
        combat.resolve_fight_action(p, fl, "attack")
        dealt[gap] = hp0 - p["encounter"]["hp"]
    assert dealt[3] > dealt[1]
    assert dealt[3] == pytest.approx(dealt[1] * 1.5, abs=2)


def test_chase_eats_the_ladder_one_length_at_a_time(monkeypatch):
    p = _player("archer", 1, "chase-ladder")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    p["encounter"]["gap"] = 3
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    note = combat._advance_chase(p)
    assert p["encounter"]["gap"] == 2
    assert p["encounter"]["range"] == "at_range"
    assert "eats a length" in note
    combat._advance_chase(p)
    note = combat._advance_chase(p)
    assert p["encounter"]["gap"] == 0
    assert p["encounter"]["range"] == "close"
    assert "on you now" in note


def test_closing_in_resets_the_gap():
    p = _player("warrior", 1, "close-reset")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    p["encounter"]["gap"] = 3
    combat.resolve_fight_action(p, fl, "close_in")
    assert p["encounter"]["gap"] == 0
    assert p["encounter"]["range"] == "close"


# ── grants for everyone ──────────────────────────────────────────────────

def test_the_receiver_level_gate_is_gone():
    assert not hasattr(economy, "GRANT_MIN_RECEIVER_LEVEL")
    assert "receive_grants" not in {u.id for u in unlocks.registry()}
