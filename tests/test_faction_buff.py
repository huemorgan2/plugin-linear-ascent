"""010: faction weekly blessings — engine-side effect of a won CULL/CLIMB
week. worldd writes doc['faction_buff']; the engine honors it only during
its week."""

from plugin_linear_ascent.engine import state


def _player(buff=None):
    p = state.new_player("t:owner")
    p["stage"] = "playing"
    p["level"] = 5
    if buff:
        p["faction_buff"] = buff
    return p


def _this_week():
    return state.world_day() // 7


def test_no_buff_no_change():
    base = state.max_hp(_player())
    assert base == state.max_hp(_player({"kind": "hp", "pct": 0,
                                         "week": _this_week()}))


def test_hp_buff_applies_during_its_week():
    plain = state.max_hp(_player())
    blessed = state.max_hp(_player({"kind": "hp", "pct": 20,
                                    "week": _this_week()}))
    assert blessed == round(plain * 1.20)


def test_hp_buff_expires_after_its_week():
    stale = state.max_hp(_player({"kind": "hp", "pct": 20,
                                  "week": _this_week() - 1}))
    assert stale == state.max_hp(_player())


def test_xp_buff_does_not_touch_hp():
    xp_week = state.max_hp(_player({"kind": "xp", "pct": 20,
                                    "week": _this_week()}))
    assert xp_week == state.max_hp(_player())


def test_buff_pct_helper():
    p = _player({"kind": "xp", "pct": 26, "week": _this_week()})
    assert state.faction_buff_pct(p, "xp") == 26
    assert state.faction_buff_pct(p, "hp") == 0
    p["faction_buff"]["week"] -= 1
    assert state.faction_buff_pct(p, "xp") == 0


def test_garbage_buff_is_inert():
    assert state.faction_buff_pct(_player({"kind": "hp"}), "hp") == 0
    p = _player()
    p["faction_buff"] = "nonsense"
    assert state.faction_buff_pct(p, "hp") == 0
