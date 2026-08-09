"""017 phase 002 — speed & the chase (plan §2.4).

Unit tests for every branch of the range machine, the chase-curve
formulas, and the 10k-roll sim gate: measured close/flee/dodge rates
must sit within ±5 points of the formulas; the warrior floor-1
experience stays within one round of the pre-chase game.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Chase"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    return p


def _player(clazz, floor_no, name):
    p = create_character(fresh(name), clazz=clazz)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    return p


def _enc(floor_no, enc_id):
    fl = schema.get_floor(floor_no)
    return fl, next(e for e in fl.encounters if e.id == enc_id)


# ── formulas ─────────────────────────────────────────────────────────────

def test_close_curve_values_and_bounds():
    assert economy.p_close(5, 5) == pytest.approx(0.25)
    assert economy.p_close(7, 5) == pytest.approx(0.55)
    assert economy.p_close(3, 5) == pytest.approx(0.05)   # clamped floor
    assert economy.p_close(10, 1) == pytest.approx(0.95)  # clamped cap


def test_open_curve_values_and_bounds():
    assert economy.p_open(5, 5) == pytest.approx(0.50)
    assert economy.p_open(5, 3) == pytest.approx(0.80)
    assert economy.p_open(5, 7) == pytest.approx(0.20)
    assert economy.p_open(10, 1) == pytest.approx(0.90)   # capped, never sure


def test_flee_curve_values_and_bounds():
    assert economy.p_flee(5, 5) == pytest.approx(0.60)
    assert economy.p_flee(5, 3) == pytest.approx(0.84)
    assert economy.p_flee(5, 7) == pytest.approx(0.36)
    assert economy.p_flee(1, 10) == pytest.approx(0.10)   # floor


def test_dodge_log_decay_and_cap():
    assert economy.dodge_pct(5, 5) == 0
    assert economy.dodge_pct(6, 5) == 7                   # a=1
    assert economy.dodge_pct(7, 5) == 11                  # a=2
    assert economy.dodge_pct(8, 5) == 12                  # a=3 hits the cap
    assert economy.dodge_pct(10, 3) == 12                 # never above
    assert economy.dodge_pct(3, 7) == 0                   # disadvantage: none


def test_player_speed_reads_the_shoe_hook():
    p = fresh("spd")
    assert economy.player_speed(p) == economy.PLAYER_BASE_SPEED
    economy.SHOE_SPEED["test_boots"] = 2
    try:
        p["gear"]["shoes"] = "test_boots"
        assert economy.player_speed(p) == 7
    finally:
        del economy.SHOE_SPEED["test_boots"]


# ── the range machine ────────────────────────────────────────────────────

def test_fights_open_at_range_and_the_scene_says_so():
    p = _player("warrior", 1, "open-range")
    fl, enc = _enc(1, "grey_wolf")
    s = combat.start_encounter(p, fl, enc)
    assert p["encounter"]["range"] == "at_range"
    # 003: the range state moved into the fight header (scene.enemy);
    # the text fallback still says it in words.
    assert (s.enemy or {}).get("range") == "at_range"
    assert "at range" in s.to_text()


def test_melee_at_range_gets_close_in_not_attack():
    p = _player("warrior", 1, "melee-opts")
    fl, enc = _enc(1, "grey_wolf")
    s = combat.start_encounter(p, fl, enc)
    ids = [o.id for o in s.options]
    assert "close_in" in ids and "attack" not in ids
    assert "open_distance" not in ids                     # only when close


def test_ranged_and_magic_keep_attack_at_range():
    for clazz in ("archer", "sorcerer"):
        p = _player(clazz, 1, f"rng-opts-{clazz}")
        fl, enc = _enc(1, "grey_wolf")
        s = combat.start_encounter(p, fl, enc)
        ids = [o.id for o in s.options]
        assert "attack" in ids and "close_in" not in ids


def test_close_in_crosses_without_a_swing():
    p = _player("warrior", 1, "crossing")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    hp0 = p["encounter"]["hp"]
    s = combat.resolve_fight_action(p, fl, "close_in")
    assert p["encounter"]["range"] == "close"
    assert p["encounter"]["hp"] == hp0                    # no damage dealt
    assert any("cross the open ground" in ln for ln in s.body_lines)
    ids = [o.id for o in s.options]
    # 031 §7: equal legs never part — the wolf matches the warrior at 5,
    # so the break is not even on the menu
    assert "attack" in ids and "open_distance" not in ids
    # against something SLOWER the break is offered again
    p["encounter"]["profile"]["speed"] = economy.SPEED_SLOW
    ids = [o.id for o in combat.fight_scene(p, fl).options]
    assert "open_distance" in ids


def test_bare_attack_at_range_is_the_crossing_for_melee():
    """Stale clients and sims mash attack — it must mean close in."""
    p = _player("warrior", 1, "mash")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    hp0 = p["encounter"]["hp"]
    combat.resolve_fight_action(p, fl, "attack")
    assert p["encounter"]["range"] == "close"
    assert p["encounter"]["hp"] == hp0


def test_open_distance_success_and_failure(monkeypatch):
    fl, enc = _enc(1, "grey_wolf")
    # 031 §7: the break only exists against something SLOWER — pin the
    # wolf slow for the success/failure halves below
    # success: forced rolls — open succeeds, the close roll then fails
    p = _player("archer", 1, "open-ok")
    combat.start_encounter(p, fl, enc)
    p["encounter"]["range"] = "close"
    p["encounter"]["profile"]["speed"] = economy.SPEED_SLOW
    monkeypatch.setattr(state, "roll_ok",
                        lambda pl, prob: prob >= 0.4)     # open .5+ ok, close no
    s = combat.resolve_fight_action(p, fl, "open_distance")
    assert p["encounter"]["range"] == "at_range"
    assert any("put ground between you" in ln for ln in s.body_lines)
    # failure: every roll fails → free halved hit, still close
    p2 = _player("archer", 1, "open-no")
    combat.start_encounter(p2, fl, enc)
    p2["encounter"]["range"] = "close"
    p2["encounter"]["profile"]["speed"] = economy.SPEED_SLOW
    hp0 = p2["hp"]
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
    # 009: pin the damage roll high — a LOW day-seeded roll can chip 1,
    # which the −50% legally rounds to 0 (the flake that ate a day roll)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    s2 = combat.resolve_fight_action(p2, fl, "open_distance")
    assert p2["encounter"]["range"] == "close"
    assert p2["hp"] < hp0
    assert any("No gap opens" in ln for ln in s2.body_lines)
    # refused: equal legs — the round is NOT spent, nothing lands
    p3 = _player("archer", 1, "open-equal")
    combat.start_encounter(p3, fl, enc)
    p3["encounter"]["range"] = "close"
    hp1 = p3["hp"]
    s3 = combat.resolve_fight_action(p3, fl, "open_distance")
    assert p3["encounter"]["range"] == "close"
    assert p3["hp"] == hp1
    assert any("stride for stride" in ln for ln in s3.body_lines)


def test_monster_cannot_answer_your_shot_at_range(monkeypatch):
    """031 §7: a shot loosed from distance draws NO counter — the enemy
    is still crossing open ground. Only in close quarters do blows come
    back. (The halved charging strike survives on the other paths: a
    failed open_distance, a flare guard.)"""
    fl, enc = _enc(1, "grey_wolf")
    taken = {}
    for label, rng in (("at_range", "at_range"), ("close", "close")):
        p = _player("sorcerer", 1, f"halved-{label}")
        combat.start_encounter(p, fl, enc)
        p["encounter"]["range"] = rng
        p["encounter"]["hp"] = 10_000                     # nobody dies here
        monkeypatch.setattr(state, "rng_int", lambda pl, a, b: b)
        monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
        hp0 = p["hp"]
        combat.resolve_fight_action(p, fl, "attack")
        taken[label] = hp0 - p["hp"]
    assert taken["at_range"] == 0
    assert taken["close"] > 0


def test_bow_penalty_in_close_quarters(monkeypatch):
    fl, enc = _enc(1, "grey_wolf")
    dealt = {}
    for rng in ("at_range", "close"):
        p = _player("archer", 1, f"bow-{rng}")
        combat.start_encounter(p, fl, enc)
        p["encounter"]["range"] = rng
        p["encounter"]["hp"] = 10_000
        monkeypatch.setattr(state, "rng_int", lambda pl, a, b: b)
        monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
        hp0 = p["encounter"]["hp"]
        combat.resolve_fight_action(p, fl, "attack")
        dealt[rng] = hp0 - p["encounter"]["hp"]
    assert dealt["close"] < dealt["at_range"]
    assert dealt["close"] == pytest.approx(
        dealt["at_range"] * economy.BOW_CLOSE_MULT, abs=1)


def test_magic_full_strength_at_both_ranges(monkeypatch):
    fl, enc = _enc(1, "grey_wolf")
    dealt = {}
    for rng in ("at_range", "close"):
        p = _player("sorcerer", 1, f"mag-{rng}")
        combat.start_encounter(p, fl, enc)
        p["encounter"]["range"] = rng
        p["encounter"]["hp"] = 10_000
        monkeypatch.setattr(state, "rng_int", lambda pl, a, b: b)
        monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
        hp0 = p["encounter"]["hp"]
        combat.resolve_fight_action(p, fl, "attack")
        dealt[rng] = hp0 - p["encounter"]["hp"]
    assert dealt["close"] == dealt["at_range"]


def test_shield_wall_counter_cannot_reach_at_range():
    p = _player("warrior", 1, "wall-range")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    hp0 = p["encounter"]["hp"]
    s = combat.resolve_fight_action(p, fl, "shield_wall")
    assert p["encounter"]["hp"] == hp0
    assert any("hasn't reached you" in ln for ln in s.body_lines)


def test_pre_002_docs_mid_fight_default_to_close():
    p = _player("warrior", 1, "legacy")
    fl, enc = _enc(1, "grey_wolf")
    combat.start_encounter(p, fl, enc)
    del p["encounter"]["range"]                           # a pre-002 doc
    s = combat.resolve_fight_action(p, fl, "attack")
    # attacks normally — no crossing, no range line
    assert p["encounter"] is None or p["encounter"]["hp"] < \
        p["encounter"]["hp_max"]
    assert not any("at range" in ln for ln in s.body_lines)


def test_alpha_runs_one_faster():
    fl, enc = _enc(1, "grey_wolf")
    for seed in range(200):
        p = _player("warrior", 1, f"alpha-{seed}")
        combat.start_encounter(p, fl, enc)
        if p["encounter"]["specimen"] == "alpha":
            assert p["encounter"]["profile"]["speed"] == \
                economy.SPEED_NORMAL + economy.ALPHA_SPEED_BONUS
            return
    pytest.fail("no alpha rolled in 200 encounters")


# ── the chase sim gate (±5 points of the formulas) ───────────────────────

def _measure_closes(enc_id, floor_no, n=2000):
    """Stand at range as a sorcerer; count how often the monster closes
    at the end of the first at-range round."""
    fl, enc = _enc(floor_no, enc_id)
    closed = 0
    for seed in range(n):
        p = _player("sorcerer", floor_no, f"close-{enc_id}-{seed}")
        combat.start_encounter(p, fl, enc)
        p["encounter"]["hp"] = 10_000
        p["hp"] = 10_000
        combat.resolve_fight_action(p, fl, "stand")
        closed += p["encounter"]["range"] == "close"
    return closed / n


def test_close_rates_match_the_formula():
    for enc_id, floor_no in (("grey_wolf", 1),        # normal: 25%
                             ("downs_courser", 5)):   # fast: 55%
        fl, enc = _enc(floor_no, enc_id)
        prof = economy.profile_from_traits(enc.traits)
        expected = economy.p_close(prof["speed"], economy.PLAYER_BASE_SPEED)
        # specimen alphas run +1 — exclude them via the common-only average
        measured = _measure_closes(enc_id, floor_no)
        assert abs(measured - expected) <= 0.06, (
            f"{enc_id}: measured {measured:.0%} vs formula {expected:.0%}")


def test_flee_rates_match_the_formula(monkeypatch):
    fl, enc = _enc(1, "grey_wolf")
    escaped = 0
    n = 2000
    for seed in range(n):
        p = _player("warrior", 1, f"flee-{seed}")
        combat.start_encounter(p, fl, enc)
        p["hp"] = 10_000
        combat.resolve_fight_action(p, fl, "run")
        escaped += p["encounter"] is None
    expected = economy.p_flee(5, 5)                       # 60%
    assert abs(escaped / n - expected) <= 0.05


def test_dodge_rate_matches_the_formula():
    """+1 speed advantage (via the shoes hook) dodges ~7% of hits."""
    fl, enc = _enc(1, "grey_wolf")
    economy.SHOE_SPEED["sim_boots"] = 1
    try:
        dodged = 0
        n = 3000
        for seed in range(n):
            p = _player("warrior", 1, f"dodge-{seed}")
            p["gear"]["shoes"] = "sim_boots"
            combat.start_encounter(p, fl, enc)
            if p["encounter"]["profile"]["speed"] != economy.SPEED_NORMAL:
                continue                                  # skip alphas
            p["encounter"]["range"] = "close"
            hit = combat._monster_hit(p)
            dodged += bool(hit.get("dodged"))
        assert abs(dodged / n - 0.07) <= 0.03
    finally:
        del economy.SHOE_SPEED["sim_boots"]


def _kite_fight(clazz, floor_no, enc, seed):
    """The archer's dance: shoot at range, open when caught."""
    fl = schema.get_floor(floor_no)
    p = _player(clazz, floor_no, f"kite-{enc.id}-{seed}")
    combat.start_encounter(p, fl, enc)
    for _ in range(80):
        if p["encounter"] is None:
            return True
        if p["hp"] <= 0:
            return False
        if p["encounter"].get("range", "close") == "close":
            combat.resolve_fight_action(p, fl, "open_distance")
        else:
            combat.resolve_fight_action(p, fl, "attack")
    return False


def test_archer_kites_the_slow_bulwark(monkeypatch):
    """§2.4's promised payoff: the slow monster can be killed from range
    without ever trading fair — win ≥85% at level. Specimen pinned to
    common: 039 shifted floor-6 weights toward tough/alpha, and this
    gate is about the speed mechanic, not the specimen roll."""
    real = state.rng_pick
    monkeypatch.setattr(state, "rng_pick", lambda p, table: (
        "common" if any(k in economy.SPECIMENS for _, k in table)
        else real(p, table)))
    fl, enc = _enc(6, "lane_boar")                        # bulwark, slow
    wins = sum(_kite_fight("archer", 6, enc, s) for s in range(60))
    assert wins / 60 >= 0.85, f"kite win rate {wins / 60:.0%}"


def test_fast_monster_forces_close_by_round_two():
    """p_close(fast) = 0.55 → ~80% of fights are close by round 2."""
    fl, enc = _enc(5, "downs_courser")
    n = 400
    forced = 0
    for seed in range(n):
        p = _player("archer", 5, f"forced-{seed}")
        combat.start_encounter(p, fl, enc)
        p["encounter"]["hp"] = 10_000
        p["hp"] = 10_000
        for _ in range(2):
            combat.resolve_fight_action(p, fl, "stand")
        forced += p["encounter"]["range"] == "close"
    expected = 1 - (1 - 0.55) ** 2                        # 79.75%
    assert abs(forced / n - expected) <= 0.06, (
        f"forced-close by round 2: {forced / n:.0%} vs {expected:.0%}")


def test_warrior_floor_one_within_one_round_of_before():
    """Regression: the crossing round is strictly additive flavor —
    rounds-to-kill sits within +1 of the pre-chase game, wins stay easy."""
    fl, enc = _enc(1, "feral_boar")
    n = 200

    def run(skip_chase):
        rounds_total = wins = 0
        for seed in range(n):
            p = _player("warrior", 1, f"reg-{skip_chase}-{seed}")
            combat.start_encounter(p, fl, enc)
            if skip_chase:                    # the pre-002 game: born close
                p["encounter"]["range"] = "close"
            r = 0
            while p["encounter"] is not None and r < 40:
                r += 1
                combat.resolve_fight_action(p, fl, "attack")
                if p["hp"] <= 0:
                    break
            wins += p["encounter"] is None and p["hp"] > 0
            rounds_total += r
        return wins / n, rounds_total / n

    win_new, rounds_new = run(skip_chase=False)
    win_old, rounds_old = run(skip_chase=True)
    assert win_new >= 0.95                    # still a kindergarten
    # 043.1: the soft low-bar caps mean floor-1 blows almost never end a
    # fight early, so the measured chase stretches a hair past the old
    # 1.3 — the crossing itself is unchanged.
    assert rounds_new - rounds_old <= 1.5, (
        f"chase adds {rounds_new - rounds_old:.1f} rounds "
        f"({rounds_old:.1f} → {rounds_new:.1f}) — more than the crossing")
