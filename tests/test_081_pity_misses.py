"""081 phase-2 — beginner pity: at level L <= 3, after L straight
misses the next swing must land; level 4 keeps honest dice."""

from plugin_linear_ascent import economy

try:
    from tests.conftest import make_character
except ImportError:                                   # rootdir import
    from conftest import make_character

from plugin_linear_ascent.engine import combat, core, state


def _floor_obj(p):
    from plugin_linear_ascent.content import schema
    return schema.get_floor(p["floor"] or 1)


def _fighter(uid, level=1, rank=0):
    p = state.new_player(uid)
    make_character(p, clazz="warrior", name=f"P{uid[-4:]}")
    p["level"] = level
    p["training"]["blade"] = rank
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "hunt")
    assert p["encounter"] is not None
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 10 ** 6      # nobody dies in these probes
    p["hp"] = 10 ** 6                   # and neither do we
    return p


def _attack(p):
    s = combat.resolve_fight_action(p, _floor_obj(p), "attack")
    return " ".join([s.shard_note or ""] + list(s.body_lines or [])).lower()


def test_constants():
    assert economy.PITY_MISS_MAX_LEVEL == 3
    assert [economy.pity_miss_run(l) for l in (1, 2, 3)] == [1, 2, 3]


def test_level1_never_misses_twice(monkeypatch):
    p = _fighter("081-l1", level=1)
    monkeypatch.setattr(state, "roll_ok", lambda pp, prob: True)  # all dice say miss
    text = _attack(p)
    assert "wide" in text
    assert p["encounter"]["miss_run"] == 1
    text = _attack(p)                       # pity: the dice are not consulted
    assert "wide" not in text
    assert p["encounter"]["miss_run"] == 0
    text = _attack(p)                       # run restarts: a miss is allowed again
    assert "wide" in text
    assert p["encounter"]["miss_run"] == 1


def test_level3_allows_exactly_three(monkeypatch):
    p = _fighter("081-l3", level=3)
    monkeypatch.setattr(state, "roll_ok", lambda pp, prob: True)
    for i in (1, 2, 3):
        text = _attack(p)
        assert "wide" in text, i
        assert p["encounter"]["miss_run"] == i
    text = _attack(p)                       # the 4th must land
    assert "wide" not in text
    assert p["encounter"]["miss_run"] == 0


def test_level4_keeps_honest_dice(monkeypatch):
    p = _fighter("081-l4", level=4)
    monkeypatch.setattr(state, "roll_ok", lambda pp, prob: True)
    for i in range(1, 7):                # misses stack without mercy
        text = _attack(p)
        assert "wide" in text, i
        assert p["encounter"]["miss_run"] == i


def test_forced_hit_consumes_no_rng_draw(monkeypatch):
    p = _fighter("081-rng", level=1)
    calls = []

    def spy(pp, prob):
        calls.append(prob)
        return True                      # every consulted roll misses
    monkeypatch.setattr(state, "roll_ok", spy)
    _attack(p)                           # miss — the dice were consulted
    n = len(calls)
    monkeypatch.setattr(state, "rng_int", lambda pp, lo, hi: hi)
    _attack(p)                           # forced hit — roll_ok not consulted
    assert len(calls) == n


def test_hit_resets_run(monkeypatch):
    p = _fighter("081-reset", level=2)
    monkeypatch.setattr(state, "roll_ok", lambda pp, prob: False)  # never miss
    _attack(p)
    assert p["encounter"]["miss_run"] == 0
