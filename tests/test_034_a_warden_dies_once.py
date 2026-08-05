"""034 §3 — a Warden dies once.

Below the frontier the keep used to re-arm as an ECHO bout: a full
Warden fight at half pay, repeatable forever, on a card that said in as
many words that the real one died long ago. Now the keep is a memorial
that names who killed it and when.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import contracts, core, state


def _climber(name, level=12, unlocked=5):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", text=name)
    p["level"] = level
    p["unlocked_floor"] = unlocked
    p["hp"] = economy.player_max_hp(level)
    return p


def _at_floor(p, n, world=None):
    p["floor"] = n
    p["location"] = "gate_town"
    if world is not None:
        p["_world"] = world
    return schema.get_floor(n)


def _world(frontier=5, fallen=None):
    return {"frontier": frontier, "fallen": fallen or {}}


# ── the keep of a dead Warden is a memorial ─────────────────────────────

def test_a_cleared_keep_starts_no_fight_and_spends_no_energy():
    p = _climber("mourner")
    _at_floor(p, 3, _world(frontier=5))
    before = state.energy_now(p)
    s = core.apply_choice(p, "keep")
    assert p.get("encounter") is None
    assert p["location"] == "memorial"
    assert state.energy_now(p) == before
    assert "fell here" in s.headline


def test_the_row_says_monument_before_the_click():
    p = _climber("reader")
    fl = _at_floor(p, 3, _world(frontier=5))
    s = core.current_scene(p)
    keep = next(o for o in s.options if o.id == "keep")
    assert "fell" in keep.label
    assert "⚡" not in keep.hint
    # the live front still charges for its swings
    _at_floor(p, 5, _world(frontier=5))
    live = next(o for o in core.current_scene(p).options if o.id == "keep")
    assert f"{economy.COST_WARDEN_STRIKE} ⚡" in live.hint


def test_the_memorial_names_the_slayers_and_the_day():
    p = _climber("historian")
    day = state.world_day()
    _at_floor(p, 3, _world(frontier=5, fallen={"3": {
        "names": "MASTER-CHIEF, bob", "day": day - 4,
        "top": "MASTER-CHIEF", "top_dmg": 559}}))
    s = core.apply_choice(p, "keep")
    body = " ".join(s.body_lines)
    assert "MASTER-CHIEF, bob" in body
    assert f"day {day - 4:,}" in body and "4 days ago" in body
    assert "559" in body


def test_a_legacy_row_with_no_date_still_reads():
    """`fallen:{floor}` was a bare names string before this plan; the
    memorial says so rather than inventing a date."""
    p = _climber("archivist")
    _at_floor(p, 3, {"frontier": 5,
                     "warden": {"fallen_by": {"3": "MASTER-CHIEF"}}})
    s = core.apply_choice(p, "keep")
    body = " ".join(s.body_lines)
    assert "MASTER-CHIEF" in body
    assert "day" not in body.lower().split("MASTER-CHIEF")[0]


def test_a_keep_the_world_forgot_says_so():
    p = _climber("stranger")
    _at_floor(p, 3, _world(frontier=5))
    s = core.apply_choice(p, "keep")
    assert any("early days" in ln for ln in s.body_lines)


def test_back_leaves_the_memorial_for_the_camp():
    p = _climber("leaver")
    _at_floor(p, 3, _world(frontier=5))
    core.apply_choice(p, "keep")
    s = core.apply_choice(p, "back")
    assert p["location"] == "gate_town"
    assert any(o.id == "hunt" for o in s.options)


# ── the live front is untouched ─────────────────────────────────────────

def test_the_frontier_keep_still_holds_a_warden():
    p = _climber("striker")
    _at_floor(p, 5, {"frontier": 5, "fallen": {},
                     "warden": {"floor": 5, "hp": 900, "hp_max": 900,
                                "strikers": [], "pity": 0}})
    core.apply_choice(p, "keep")
    assert p["location"] == "warden_keep"


def test_local_dev_play_keeps_its_one_real_bout():
    """A world of one: the personal unlock is the record. Floor 5 is
    still the frontier for this doc, so its Warden is alive."""
    p = _climber("solo", unlocked=5)
    _at_floor(p, 5)
    p.pop("_world", None)
    core.apply_choice(p, "keep")
    assert p["encounter"] is not None
    assert p["encounter"]["kind"] == "warden"


def test_local_dev_play_memorialises_what_it_already_killed():
    p = _climber("solo-veteran", unlocked=6)
    _at_floor(p, 5)
    p.pop("_world", None)
    core.apply_choice(p, "keep")
    assert p.get("encounter") is None
    assert p["location"] == "memorial"


def test_a_cleared_milestone_stops_showing_a_quorum_board():
    """The frontier check runs before the milestone branch, or floor 10
    keeps recruiting a war party for a boss that is already dead."""
    p = _climber("late", level=20, unlocked=14)
    _at_floor(p, 10, _world(frontier=14))
    core.apply_choice(p, "keep")
    assert p["location"] == "memorial"


# ── the echo is gone from the economy ───────────────────────────────────

def test_the_echo_multiplier_is_retired():
    assert not hasattr(economy, "WARDEN_ECHO_MULT")


# ── the board stops posting work nobody can do ──────────────────────────

def test_the_horn_job_is_offered_to_hands_that_can_reach_the_front():
    p = _climber("frontliner", level=12, unlocked=5)
    p["_world"] = _world(frontier=5)
    assert any(j["kind"] == "warden" for j in contracts.board_for(p))


def test_the_horn_job_comes_off_the_board_of_a_hand_that_cannot():
    """With the echo retired there is one living Warden in the tower. A
    climber who cannot walk through that floor's gate cannot answer the
    horn, so the board must not post it to them."""
    p = _climber("greenhorn", level=3, unlocked=40)
    p["_world"] = _world(frontier=40)
    assert economy.floor_entry_player_level(40) > 3
    assert not any(j["kind"] == "warden" for j in contracts.board_for(p))
    # and the other two jobs still stand
    assert len(contracts.board_for(p)) == 2
