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


def test_creation_grants_class_path_rank6():
    # transitional (phases 2–3, classes still exist): the class pick
    # trains its path to 6 ≈ the old on-class feel. Phase 4 replaces
    # this with the classless blade-2 start.
    p = _fresh("048-p2-new")
    make_character(p, clazz="archer", name="Fletch")
    assert p["training"] == {"blade": 0, "bow": 6, "staff": 0}


def test_legacy_doc_migrates_to_rank6_with_card_once():
    p = _fresh("048-p2-legacy")
    make_character(p, clazz="archer", name="Oldbow")
    # rewind the doc to a pre-048 shape
    del p["training"]
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
