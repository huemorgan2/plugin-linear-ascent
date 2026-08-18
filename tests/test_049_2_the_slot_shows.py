"""049.2 — a bought slot is a visible square, a locked slot says so.

The 049.1 ungating traded one confusion for another: a level-2 player
saw a buyable-looking 3rd-slot row they could never pay, and a bought
2nd slot changed nothing on the sheet (the side-arm landed in the pack
grid, the empty slot drew nowhere). Now the hand row draws one square
per owned carry slot — lead, held side-arms, open squares — and the
3rd-slot row is back behind level 8, dimmed and named.
"""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, state


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text)


def _character(name):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, "human")
    choose(p, "", text=name)
    return p


# ── the hand row: one square per owned slot ──────────────────────────────

def test_a_bought_empty_slot_draws_an_open_square():
    p = _character("Openhand")
    p["slots"] = 2                      # bought, nothing riding it yet
    # 069: the open grip is an EMPTY weapon slot on the gear map
    marks = [c for c in core._slot_map(p)
             if c["kind"] == "weapon" and c["state"] == "empty"]
    assert len(marks) == 1 and marks[0]["key"] == "weapon2"


def test_one_slot_owned_means_no_open_square():
    p = _character("Onehand")
    assert int(p.get("slots", 1)) == 1
    weapons = [c for c in core._slot_map(p) if c["kind"] == "weapon"]
    assert [c["state"] for c in weapons] == ["filled", "locked", "locked"]


def test_the_hand_row_draws_lead_held_and_open_slots():
    p = _character("Fullhand")
    p["training"]["bow"] = 6
    p["gear"]["weapon"] = "basic_bow"
    p["held"] = ["basic_bow", "scrap_dagger"]
    p["slots"] = 3                      # third bought, still open
    scene = core.current_scene(p)
    html = render.render_scene_fragment(scene)
    hand = html.split('class="gearmap"')[1].split('class="pcol"')[0]
    assert 'data-slug="basic_bow"' in hand
    assert 'data-slug="scrap_dagger"' in hand
    assert 'data-key="weapon3"' in hand and 'slot gm empty' in hand
    assert "weapon 3 — an open grip" in hand
    # the side-arm left the pack grid
    grid = html.split('class="slotgrid"')[1]
    assert 'data-slug="scrap_dagger"' not in grid


# ── the 3rd slot: locked is visible and says its level ───────────────────

def test_below_level_8_the_row_is_locked_and_named():
    p = _character("Gated")
    p["slots"] = 2
    p["location"] = "school"
    s = core._school_scene(p)
    row = next(o for o in s.options if o.id == "buy_carry3")
    assert row.locked
    assert f"level {economy.CARRY3_LEVEL}" in row.hint
    assert "you: 1" in row.hint
    # buying anyway refuses on the level, spends nothing
    xp, gold = p["xp"], p["gold"]
    s = core._school_action(p, "buy_carry3")
    assert p["slots"] == 2
    assert (p["xp"], p["gold"]) == (xp, gold)
    assert f"level {economy.CARRY3_LEVEL}" in (s.shard_note or "")


def test_at_level_8_the_row_unlocks_with_its_price():
    p = _character("Earned")
    p["slots"] = 2
    p["level"] = economy.CARRY3_LEVEL
    p["location"] = "school"
    s = core._school_scene(p)
    row = next(o for o in s.options if o.id == "buy_carry3")
    assert not row.locked
    assert f"{economy.CARRY3_XP} XP" in row.hint


def test_the_slot_rows_say_unlock():
    p = _character("Named")
    p["location"] = "school"
    s = core._school_scene(p)
    row = next(o for o in s.options if o.id == "buy_carry2")
    assert "2nd weapon slot" in row.label
    p["slots"] = 2
    s = core._school_scene(p)
    row = next(o for o in s.options if o.id == "buy_carry3")
    assert "3rd weapon slot" in row.label
