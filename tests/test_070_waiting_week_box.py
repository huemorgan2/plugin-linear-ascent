"""070 — last week's reward sits in waiting-for-you, in English."""
from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, notices, state, weekly

try:
    from tests.conftest import make_character
except ImportError:  # pragma: no cover
    from conftest import make_character

_JARGON = ("strongbox", "aether", "relic", "lump", "rested", "vanish",
           "owed you")


def _climber(tag="070"):
    p = state.new_player(tag)
    make_character(p)
    p["level"] = economy.STRONGBOX_LEVEL
    p["unlocked_floor"] = 6
    p["location"] = "town"
    weekly.sync(p)
    return p


def _pending(p, n_slots):
    p["strongbox"]["pending"] = {
        "week": weekly.week_no() - 1, "slots": n_slots}


def test_pending_week_is_a_weekpick_not_a_vault_collect():
    p = _climber()
    _pending(p, 3)
    board = notices.pending(p)
    weeks = [n for n in board if n.get("kind") == "weekpick"]
    assert len(weeks) == 1
    assert weeks[0]["text"] == weekly.HEADER
    assert not any("strongbox" in str(n.get("text", "")).lower()
                   for n in board)
    assert "vault" not in notices.doors(p)


def test_vault_menu_has_no_prize_rows():
    p = _climber()
    _pending(p, 3)
    p["location"] = "vault"
    s = core.current_scene(p)
    assert not any(o.id.startswith("pick_") for o in s.options)
    assert any(o.id == "deposit_all" or o.id == "back" for o in s.options)


def test_two_slots_is_gold_only_then_extra_xp():
    p = _climber()
    _pending(p, 1)
    assert [c["opt"] for c in weekly.choices(p, 1)] == ["pick_gold"]
    _pending(p, 2)
    assert [c["opt"] for c in weekly.choices(p, 2)] == [
        "pick_gold", "pick_aether"]
    _pending(p, 3)
    assert [c["opt"] for c in weekly.choices(p, 3)] == [
        "pick_gold", "pick_aether", "pick_token", "pick_relic"]


def test_pick_gold_from_town_pays_and_clears():
    p = _climber()
    _pending(p, 3)
    gold = p["gold"]
    want = economy.strongbox_gold(p["unlocked_floor"])
    s = core.apply_choice(p, "pick_gold")
    assert p["gold"] == gold + want
    assert weekly.sync(p)["pending"] is None
    assert s.body_lines[0].startswith("You chose the gold.")
    assert "◈" in s.body_lines[0] and str(want) in s.body_lines[0]
    assert not any(n.get("kind") == "weekpick" for n in s.notices)


def test_pick_from_the_forge_too():
    p = _climber()
    _pending(p, 3)
    p["location"] = "forge"
    s = core.apply_choice(p, "pick_relic")
    assert (p.get("inventory") or {}).get("luck_charm") == 1
    assert weekly.sync(p)["pending"] is None
    assert "luck charm" in s.body_lines[0]
    assert "pack" in s.body_lines[0]


def test_copy_has_no_engine_slang():
    p = _climber()
    blob = " ".join(
        [weekly.HEADER]
        + [f"{c['title']} {c['text']} {c['hint']}"
           for c in weekly.choices(p, 3)]
        + [weekly.pick(p, "pick_gold") or ""]
    ).lower()
    for word in _JARGON:
        assert word not in blob, word
    p2 = _climber("070-fb")
    p2["strongbox"]["pending"] = {"week": 0, "slots": 1}
    p2["strongbox"]["week"] = weekly.week_no() - 1
    weekly.sync(p2)
    note = (p2.get("strongbox_note") or "").lower()
    assert "did not choose a reward in time" in note
    for word in _JARGON:
        assert word not in note, word


def test_to_text_lists_the_numbered_choices():
    p = _climber()
    _pending(p, 3)
    s = core.current_scene(p)
    text = s.to_text()
    assert weekly.HEADER in text
    assert "1  Gold —" in text
    assert "2  Extra XP —" in text
    assert "4  Luck charm —" in text


def test_render_draws_one_rail_and_four_buttons():
    p = _climber()
    _pending(p, 3)
    html = render.render_scene_fragment(core.current_scene(p))
    assert html.count('class="weekbox"') == 1
    assert html.count('class="wrail"') == 1
    assert 'data-opt="pick_gold"' in html
    assert 'data-opt="pick_aether"' in html
    assert 'data-opt="pick_token"' in html
    assert 'data-opt="pick_relic"' in html
    assert weekly.HEADER in html
    assert "waiting for you" in html
