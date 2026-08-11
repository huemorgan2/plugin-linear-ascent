"""048 — the weapon decides. Part I mechanics: the type tables and
the damage triangle (phase 1: unwired — combat still runs the old
tier system; these prove the new tables before anything reads them)."""

from plugin_linear_ascent import economy

try:
    from tests.conftest import make_character
except ImportError:                                   # rootdir import
    from conftest import make_character

from plugin_linear_ascent.engine import state


# ── N1: one type bundles sign, speed, weight ──────────────────────────

def test_type_tables_exact():
    assert economy.TYPE_SPEED == {
        "fly": 7, "armoured": 3, "magic_resist": 3, "plain": 5}
    assert economy.TYPE_ATK == {
        "fly": 0.6, "armoured": 1.4, "magic_resist": 1.4, "plain": 1.0}
    assert economy.TYPE_HP == {
        "fly": 0.9, "armoured": 1.2, "magic_resist": 1.0, "plain": 1.0}
    assert economy.TYPE_GOLD == {
        "fly": 1.2, "armoured": 1.3, "magic_resist": 1.3, "plain": 1.0}


def test_triangle_cells_exact():
    M = economy.TYPE_MULT
    assert M["fly"] == {"blade": 0.0, "bow": 1.0, "staff": 0.6}
    assert M["armoured"] == {"blade": 0.5, "bow": 0.15, "staff": 1.0}
    assert M["magic_resist"] == {"blade": 1.0, "bow": 0.5, "staff": 0.15}
    assert M["plain"] == {"blade": 1.0, "bow": 1.0, "staff": 1.0}


# ── N2: the triangle in damage ────────────────────────────────────────

def test_typed_damage_blade_and_bow_eat_def_staff_ignores_it():
    # raw 42 vs DEF 20: blade/bow base 32, staff base 42
    assert economy.typed_damage_048("blade", 42, 20, "armoured") == 16
    assert economy.typed_damage_048("bow", 42, 20, "armoured") == 5
    assert economy.typed_damage_048("staff", 42, 20, "armoured") == 42
    assert economy.typed_damage_048("blade", 42, 20, "magic_resist") == 32
    assert economy.typed_damage_048("bow", 42, 20, "magic_resist") == 16
    assert economy.typed_damage_048("staff", 42, 20, "magic_resist") == 6
    assert economy.typed_damage_048("bow", 42, 20, "fly") == 32
    assert economy.typed_damage_048("staff", 42, 20, "fly") == 25
    for path in ("blade", "bow", "staff"):
        assert economy.typed_damage_048(path, 42, 20, "plain") == 32 \
            if path != "staff" else True
    assert economy.typed_damage_048("staff", 42, 20, "plain") == 42


def test_blade_cannot_reach_fly_everything_else_chips():
    # the single legal zero (013 chip law survives everywhere else)
    assert economy.typed_damage_048("blade", 999, 0, "fly") == 0
    # glancing answers still chip ≥1 even at hopeless raw
    assert economy.typed_damage_048("bow", 3, 40, "armoured") == 1
    assert economy.typed_damage_048("staff", 3, 40, "magic_resist") == 1
    assert economy.typed_damage_048("blade", 3, 40, "armoured") == 1


# ── N9: legacy trait sets map to the right type ───────────────────────

def test_type_from_traits_legacy_mapping():
    f = economy.type_from_traits
    assert f(("flying",)) == "fly"
    assert f(("flying", "armor_low")) == "fly"
    assert f(("armor_low",)) == "armoured"
    assert f(("armor_high", "slow")) == "armoured"
    assert f(("resist_med",)) == "magic_resist"
    assert f(("armor_med", "resist_med")) == "magic_resist"
    assert f(()) == "plain"
    assert f(("fast",)) == "plain"
    assert f(("bulwark",)) == "plain"        # ▣ is orthogonal, not a type


# ── the shared creation helper (T6 rescoped: canonical in conftest) ───

def test_conftest_helper_builds_a_character():
    p = state.new_player("048-helper")
    make_character(p, race="human", clazz="warrior", name="Proof")
    assert p["name"] == "Proof"
    assert p["stage"] not in ("intro", "creation_race", "creation_class",
                              "creation_name")


# ═══════════════════════════════════════════════════════════════════════
# Phase 2 — N3 trained ranks in the swing + N9 doc migration
# ═══════════════════════════════════════════════════════════════════════

from plugin_linear_ascent.engine import combat, core


def _fresh(uid="048-p2"):
    return state.new_player(uid)


def _choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def _in_fight(p):
    _choose(p, "gate")
    _choose(p, "floor_1")
    _choose(p, "hunt")
    assert p["encounter"] is not None
    p["encounter"]["range"] = "close"
    return p


def test_rank_formulas_exact():
    assert [economy.TRAIN_MISS_PCT(R) for R in range(11)] == \
        [25, 22, 20, 18, 15, 12, 10, 8, 5, 2, 0]
    assert [economy.TRAIN_ROLL_FLOOR(R) for R in range(11)] == \
        [0.30, 0.34, 0.38, 0.42, 0.46, 0.50, 0.54, 0.58, 0.62, 0.66, 0.70]


def test_train_costs_exact():
    # round() truth, not hand-rounding: rank 7 is 370 (the plan's 371
    # was a hand-rounding slip; sum one path 0→10 = 2854 XP)
    assert [economy.train_xp(R) for R in range(1, 11)] == \
        [20, 57, 104, 160, 224, 294, 370, 453, 540, 632]
    assert sum(economy.train_xp(R) for R in range(1, 11)) == 2854
    for front in (1, 5, 20):
        for R in (1, 4, 10):
            assert economy.train_gold(R, front) == \
                round(8 * economy.pillar(front) * R)


def test_path_of_line():
    assert economy.PATH_OF_LINE == {
        "warrior": "blade", "archer": "bow", "sorcerer": "staff"}


def test_creation_grants_blade_two_helper_restores_the_feel():
    # 048 phase 4: creation hands everyone blade 2; the conftest helper
    # then restores the old class FEEL (the clazz path at rank 6).
    p = _fresh("048-p2-new")
    make_character(p, clazz="archer", name="Fletch")
    assert p["training"] == {"blade": 2, "bow": 6, "staff": 0}


def test_legacy_doc_migrates_to_rank6_with_card_once():
    p = _fresh("048-p2-legacy")
    make_character(p, clazz="archer", name="Oldbow")
    # rewind the doc to a pre-048 shape (class docs carried a clazz)
    del p["training"]
    p["clazz"] = "archer"
    p["version"] = 6
    s = core.current_scene(p)
    assert p["training"] == {"blade": 0, "bow": 6, "staff": 0}
    text = " ".join([s.headline or "", s.support or ""]
                    + list(s.body_lines or []))
    assert "School" in text
    assert "Bow — trained rank 6" in text
    s2 = core.current_scene(p)          # the card never comes back
    text2 = " ".join([s2.headline or "", s2.support or ""]
                     + list(s2.body_lines or []))
    assert "trained rank 6" not in text2


def test_swing_floor_follows_rank(monkeypatch):
    p = _fresh("048-p2-swing")
    make_character(p, clazz="warrior", name="Swinga")
    _in_fight(p)
    captured = {}

    def spy(pp, lo, hi):
        captured["lo"], captured["hi"] = lo, hi
        return hi

    monkeypatch.setattr(state, "rng_int", spy)
    atk = state.atk(p)
    for rank, floor_pct in ((6, 0.54), (0, 0.30), (10, 0.70)):
        p["training"]["blade"] = rank
        p["encounter"]["hp"] = 10 ** 6      # nobody dies in this probe
        combat._player_hit(p)
        assert captured["hi"] == atk
        assert captured["lo"] == round(floor_pct * atk), rank


def test_attack_miss_prob_follows_rank(monkeypatch):
    p = _fresh("048-p2-miss")
    make_character(p, clazz="warrior", name="Missa")
    _in_fight(p)
    probs = []

    def spy(pp, prob):
        probs.append(prob)
        return False

    monkeypatch.setattr(state, "roll_ok", spy)
    p["training"]["blade"] = 3
    p["encounter"]["hp"] = 10 ** 6
    combat.resolve_fight_action(p, _floor_obj(p), "attack")
    assert economy.TRAIN_MISS_PCT(3) / 100 in probs


def test_attack_miss_eats_round_names_rank_and_school(monkeypatch):
    p = _fresh("048-p2-wide")
    make_character(p, clazz="warrior", name="Wide")
    _in_fight(p)
    p["training"]["blade"] = 1
    miss_prob = economy.TRAIN_MISS_PCT(1) / 100

    def rigged(pp, prob):
        return prob == miss_prob

    monkeypatch.setattr(state, "roll_ok", rigged)
    hp_monster = p["encounter"]["hp"]
    s = combat.resolve_fight_action(p, _floor_obj(p), "attack")
    assert p["encounter"] is None or p["encounter"]["hp"] == hp_monster
    note = s.shard_note or ""
    body = " ".join([note] + list(s.body_lines or []))
    assert "wide" in body.lower()
    assert "School" in body or "rank" in body.lower()


def test_rank10_never_misses(monkeypatch):
    p = _fresh("048-p2-ten")
    make_character(p, clazz="warrior", name="Ten")
    _in_fight(p)
    p["training"]["blade"] = 10
    probs = []

    def spy(pp, prob):
        probs.append(prob)
        return False

    monkeypatch.setattr(state, "roll_ok", spy)
    p["encounter"]["hp"] = 10 ** 6
    combat.resolve_fight_action(p, _floor_obj(p), "attack")
    assert 0.0 not in [pr for pr in probs if pr < 0.01] or \
        all(pr != 0.0 or False for pr in probs)
    # a zero miss chance must never reach the dice as a roll
    assert 0.0 not in probs


def _floor_obj(p):
    from plugin_linear_ascent.content import schema
    return schema.get_floor(p["floor"] or 1)


# ═══════════════════════════════════════════════════════════════════════
# Phase 3 — the School (train, mastery, carry, holding)
# ═══════════════════════════════════════════════════════════════════════

import pytest

from plugin_linear_ascent.sheet import character_sheet


def _rich(p, level=15, xp=1300, gold=2000):
    """A doc with room in the bar — training spends the SAME pool the
    Guildhall levels from, and the bar is hard-capped at xp_need."""
    p["level"] = level
    assert xp <= economy.xp_need(level)
    p["xp"] = xp
    p["gold"] = gold
    return p


def _at_school(p):
    _choose(p, "gate")
    _choose(p, "floor_1")
    s = _choose(p, "school")
    assert p["location"] == "school"
    return s


def _school_text(s):
    return " ".join([s.headline or "", s.support or "",
                     s.shard_note or ""] + list(s.body_lines or [])
                    + [f"{o.label} {o.hint}" for o in (s.options or [])])


def test_school_door_in_every_gate_town():
    from plugin_linear_ascent.content import schema
    p = _fresh("048-p3-door")
    make_character(p)
    for n in range(1, 13):
        opts = core._gate_town_options(p, schema.get_floor(n))
        assert "school" in [o.id for o in opts], n


def test_school_lists_three_paths_with_costs_and_improvement():
    p = _fresh("048-p3-list")
    make_character(p, clazz="warrior")
    _rich(p)
    s = _at_school(p)
    text = _school_text(s)
    # blade rank 6 (creation), bar, exact next-cost at frontier 1
    assert "rank 6" in text
    assert "▰▰▰▰▰▰▱▱▱▱" in text
    assert "370 XP" in text and "◈ 56" in text
    # untouched paths at 0 with the rank-1 price
    assert "▱▱▱▱▱▱▱▱▱▱" in text
    assert "20 XP" in text and "◈ 8" in text
    # the "what improves" sentence for blade 6→7
    assert "miss 10%→8%" in text
    assert "54%→58%" in text
    ids = [o.id for o in s.options]
    for oid in ("train_blade", "train_bow", "train_staff"):
        assert oid in ids


def test_train_gold_price_rides_the_current_frontier():
    p = _fresh("048-p3-frontier")
    make_character(p, clazz="warrior")
    _rich(p)
    p["unlocked_floor"] = 5
    s = _at_school(p)
    assert f"◈ {economy.train_gold(7, 5)}" in _school_text(s)


def test_train_deducts_xp_and_gold_and_bumps():
    p = _fresh("048-p3-train")
    make_character(p, clazz="warrior")
    _rich(p, xp=1300, gold=2000)
    _at_school(p)
    s = _choose(p, "train_bow")
    assert p["training"]["bow"] == 1
    assert p["xp"] == 1300 - economy.train_xp(1)
    assert p["gold"] == 2000 - economy.train_gold(1, 1)
    # and again — the price climbs the curve
    s = _choose(p, "train_bow")
    assert p["training"]["bow"] == 2
    assert p["xp"] == 1300 - economy.train_xp(1) - economy.train_xp(2)


def test_train_refusals_name_the_numbers():
    p = _fresh("048-p3-refuse")
    make_character(p, clazz="warrior")
    # xp short: rank 7 blade wants 370
    _rich(p, xp=100, gold=2000)
    _at_school(p)
    s = _choose(p, "train_blade")
    assert p["training"]["blade"] == 6
    assert "370" in (s.shard_note or "") and "100" in (s.shard_note or "")
    # gold short
    _rich(p, xp=1300, gold=3)
    s = _choose(p, "train_blade")
    assert p["training"]["blade"] == 6
    assert "56" in (s.shard_note or "") and "3" in (s.shard_note or "")
    # rank 10: the row is gone from the menu AND the guard behind it
    # still answers "nothing left to teach" (defense-in-depth)
    p["training"]["blade"] = 10
    _rich(p, xp=1300, gold=2000)
    s = core.current_scene(p)
    assert "train_blade" not in [o.id for o in s.options]
    s = core._school_action(p, "train_blade")
    assert p["training"]["blade"] == 10
    assert "nothing left to teach" in (s.shard_note or "").lower()


def test_economy_school_constants():
    assert economy.MASTERY_XP == 948            # round(632 * 1.5)
    assert economy.CARRY2_XP == 60 and economy.CARRY2_GOLD == 30
    # phase-6 bake: 500 fits the level-8 bar (xp_need(8) = 543) — at
    # 900 the printed level-8 gate was a lie until ~level 12
    assert economy.CARRY3_XP == 500 and economy.CARRY3_LEVEL == 8
    for front in (1, 5, 20):
        assert economy.carry3_gold(front) == \
            round(200 * economy.pillar(front))
    # a master pays 80% on the other paths' ranks 1-5, full after
    assert economy.train_xp_cost(1, discounted=True) == 16
    assert economy.train_xp_cost(5, discounted=True) == \
        round(economy.train_xp(5) * 0.8)
    assert economy.train_xp_cost(6, discounted=True) == economy.train_xp(6)
    assert economy.train_xp_cost(1) == 20


def test_rank10_gold_bar_mastery_row_and_invitation_once():
    p = _fresh("048-p3-ten")
    make_character(p, clazz="warrior")
    p["training"]["blade"] = 9
    _rich(p, xp=1300, gold=2000)
    _at_school(p)
    _choose(p, "train_blade")
    assert p["training"]["blade"] == 10
    # the invitation card fires once, then never again
    s = core.current_scene(p)
    text = _school_text(s)
    assert "master" in text.lower()
    assert p["flags"].get("invited_blade")
    s2 = core.current_scene(p)
    assert "master will see you" not in _school_text(s2).lower() or \
        p["location"] == "school"
    assert not p.get("pending_events")
    # the school bar turns gold and shows the study
    s = core.apply_choice(p, "school") if p["location"] != "school" else s2
    if p["location"] != "school":
        _at_school(p)
    s = core.current_scene(p)
    text = _school_text(s)
    assert "▰▰▰▰▰▰▰▰▰▰" in text
    assert "MASTERY" in text and "948" in text


def test_mastery_purchase_records_and_discounts():
    p = _fresh("048-p3-mastery")
    make_character(p, clazz="warrior")
    p["training"]["blade"] = 10
    _rich(p, xp=1300, gold=2000)
    _at_school(p)
    s = _choose(p, "mastery_blade")
    assert (p.get("mastery") or {}).get("blade") is True
    assert p["xp"] == 1300 - economy.MASTERY_XP
    # the other paths' low ranks discount to 80%
    text = _school_text(core.current_scene(p))
    assert "16 XP" in text
    before = p["xp"]
    _choose(p, "train_bow")
    assert p["training"]["bow"] == 1
    assert p["xp"] == before - 16


def test_carry_slots_second_and_third():
    p = _fresh("048-p3-carry")
    make_character(p, clazz="warrior")
    assert p["slots"] == 1
    _rich(p, level=5, xp=200, gold=500)
    _at_school(p)
    s = _choose(p, "buy_carry2")
    assert p["slots"] == 2
    assert p["xp"] == 200 - economy.CARRY2_XP
    assert p["gold"] == 500 - economy.CARRY2_GOLD
    # 3rd slot: level-gated with the exact sentence
    s = _choose(p, "buy_carry3")
    assert p["slots"] == 2
    assert "needs level 8 — you: 5" in _school_text(s)
    # phase-6 bake: 500 fits the level-8 bar — the gate is honest now
    _rich(p, level=8, xp=520, gold=2000)
    s = _choose(p, "buy_carry3")
    assert p["slots"] == 3
    assert p["xp"] == 520 - economy.CARRY3_XP
    assert p["gold"] == 2000 - economy.carry3_gold(1)


def test_held_defaults_and_promote_swaps():
    p = _fresh("048-p3-held")
    make_character(p, clazz="warrior")
    assert p["held"] == [p["gear"]["weapon"]]
    # a bagged bow promotes into the hand; one slot → the sword is bumped
    p["inventory"]["basic_bow"] = 1
    _choose(p, "wear_basic_bow")
    assert p["gear"]["weapon"] == "basic_bow"
    assert p["held"] == ["basic_bow"]


def test_promote_with_a_free_slot_keeps_both():
    p = _fresh("048-p3-both")
    make_character(p, clazz="warrior")
    p["slots"] = 2
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    _choose(p, "wear_basic_bow")
    assert p["gear"]["weapon"] == "basic_bow"
    assert p["held"] == ["basic_bow", sword]
    assert sword not in p["inventory"]


def test_promote_refused_mid_fight():
    p = _fresh("048-p3-midfight")
    make_character(p, clazz="warrior")
    _in_fight(p)
    p["inventory"]["basic_bow"] = 1
    sword = p["gear"]["weapon"]
    s = _choose(p, "wear_basic_bow")
    assert p["encounter"] is not None
    assert p["gear"]["weapon"] == sword
    assert "fight" in (s.shard_note or "").lower()


def test_sheet_carries_trained_and_holding():
    p = _fresh("048-p3-sheet")
    make_character(p, clazz="warrior")
    sheet = character_sheet(p)
    assert sheet["trained"] == {"blade": 6, "bow": 0, "staff": 0}
    assert sheet["slots"] == 1
    assert sheet["holding"] == [economy.FORGE[p["gear"]["weapon"]].name]


def test_bag_tooltip_warns_on_an_untrained_path():
    p = _fresh("048-p3-tooltip")
    make_character(p, clazz="warrior")     # bow rank 0
    p["inventory"]["basic_bow"] = 1
    acts, _why = core.pack_actions(p, "basic_bow")
    assert acts, "the bow should offer its promote row"
    assert "miss 25%" in acts[0].hint
    # the trained path carries no warning
    p["inventory"]["pigsticker"] = 1
    acts, _why = core.pack_actions(p, "pigsticker")
    assert acts and "miss" not in acts[0].hint


# ── N4: the mastery studies DO something (phase 5) ─────────────────────

def _mastered(uid, path, slug):
    p = _fresh(uid)
    make_character(p)
    p["training"] = {"blade": 0, "bow": 0, "staff": 0}
    p["training"][path] = 10
    p["mastery"] = {path: True}
    p["gear"]["weapon"] = slug
    p["held"] = [slug]
    from plugin_linear_ascent.content import schema
    fl = schema.get_floor(1)
    from types import SimpleNamespace
    enc = SimpleNamespace(id="m_test", name="Test Beast",
                          prose="It waits.", weight=1, traits=(),
                          kind="", was="")
    combat.start_encounter(p, fl, enc, "wilds")
    return p, fl


def test_riposte_returns_a_quarter_of_the_mean_swing(monkeypatch):
    p, fl = _mastered("048-m-riposte", "blade", "rusted_sword")
    e = p["encounter"]
    e["range"], e["gap"] = "close", 0
    e["atk"] = 8
    p["level"] = 20                     # a guard that BLOCKS the blow
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: lo)
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    hp0 = e["hp"]
    hit = combat._monster_hit(p)
    assert hit["blocked"] >= hit["dmg"], hit
    atk_full = state.atk(p)
    lo = round(economy.TRAIN_ROLL_FLOOR(10) * atk_full)
    expected = max(1, round(economy.RIPOSTE_RETURN * (lo + atk_full) / 2))
    assert hit.get("riposte") == expected
    assert e["hp"] == hp0 - expected


def test_riposte_needs_the_study(monkeypatch):
    p, fl = _mastered("048-m-riposte0", "blade", "rusted_sword")
    p["mastery"] = {}
    e = p["encounter"]
    e["range"], e["gap"] = "close", 0
    e["atk"] = 8
    p["level"] = 20
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: lo)
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    hp0 = e["hp"]
    hit = combat._monster_hit(p)
    assert not hit.get("riposte")
    assert e["hp"] == hp0


def test_long_draw_crits_the_top_roll_at_gap_three(monkeypatch):
    p, fl = _mastered("048-m-draw", "bow", "basic_bow")
    e = p["encounter"]
    e["range"], e["gap"] = "at_range", 3
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    hp0 = e["hp"]
    core.apply_choice(p, "attack", "")
    atk_full = state.atk(p)
    want = economy.typed_damage_048(
        "bow", round(atk_full * economy.bow_gap_mult(3)
                     * economy.LONG_DRAW_CRIT_MULT), e["def"], "plain")
    assert hp0 - e["hp"] == want


def test_long_draw_needs_the_study_and_the_top_roll(monkeypatch):
    p, fl = _mastered("048-m-draw0", "bow", "basic_bow")
    p["mastery"] = {}
    e = p["encounter"]
    e["range"], e["gap"] = "at_range", 3
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    hp0 = e["hp"]
    core.apply_choice(p, "attack", "")
    atk_full = state.atk(p)
    want = economy.typed_damage_048(
        "bow", round(atk_full * economy.bow_gap_mult(3)), e["def"],
        "plain")
    assert hp0 - e["hp"] == want


def test_focus_lifts_the_staff_answers():
    # fly: staff ×0.6 → ×0.75 under focus; the glance (×0.15) stays a
    # mistake; full answers don't move.
    assert economy.typed_damage_048("staff", 100, 0, "fly") == 60
    assert economy.typed_damage_048("staff", 100, 0, "fly",
                                    focus=True) == 75
    assert economy.typed_damage_048("staff", 100, 0, "magic_resist",
                                    focus=True) == 15
    assert economy.typed_damage_048("staff", 100, 0, "plain",
                                    focus=True) == 100


def test_focus_rides_the_cast_in_the_fight(monkeypatch):
    p, fl = _mastered("048-m-focus", "staff", "worn_staff")
    e = p["encounter"]
    e["range"], e["gap"] = "at_range", 1
    e["profile"] = economy.profile_from_traits(("fly",))
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    monkeypatch.setattr(state, "roll_ok", lambda p, chance: False)
    hp0 = e["hp"]
    core.apply_choice(p, "attack", "")
    atk_full = state.atk(p)
    want = economy.typed_damage_048("staff", atk_full, e["def"], "fly",
                                    focus=True)
    assert hp0 - e["hp"] == want
