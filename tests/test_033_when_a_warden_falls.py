"""033 — when a Warden falls: the treeline shot works once per Warden,
the kill pays in the card, and the fall is a reel, not a boar card."""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state

reel = pytest.mark.reel          # these tests drive the reel themselves


def playing(name="Sosa", clazz="warrior", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":                # 016: through the movie
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def warden_world(floor=1, hp=None, hp_max=None, strikers=None, **extra):
    hp_max = hp_max or economy.world_warden_hp(floor)
    return {"social": True, "frontier": floor,
            "warden": {"floor": floor, "hp": hp if hp is not None
                       else hp_max, "hp_max": hp_max,
                       "strikers": strikers or []},
            **extra}


def enter_floor(p, floor=1):
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, f"floor_{floor}")
    while p.get("movie_floor"):          # 030: first entry plays a reel
        s = core.apply_choice(p, "1")
    return s


def join_keep(p, floor=1):
    enter_floor(p, floor)
    core.apply_choice(p, "keep")
    return core.apply_choice(p, "strike")


def flee(p):
    for _ in range(60):
        p["hp"] = 999                    # never die in this test
        core.apply_choice(p, "run")
        if p["encounter"] is None:
            return
    raise AssertionError("the getaway must eventually work")


# ── §1: the Warden remembers you ─────────────────────────────────────────

def test_treeline_shot_is_once_per_shared_warden():
    p = playing(clazz="archer", world=warden_world(1))
    s = join_keep(p)
    assert any(o.id == "treeline_shot" for o in s.options)
    core.apply_choice(p, "treeline_shot")
    assert p["treeline_wardens"] == [1]
    flee(p)
    # the wounds persist — and so does the Warden's memory of you
    s = join_keep(p)
    assert p["encounter"]["shot_used"] is True
    assert not any(o.id == "treeline_shot" for o in s.options)
    # 027 law: the missing button is said out loud
    assert any("treeline" in ln for ln in s.body_lines)


def test_treeline_rearms_in_ordinary_fights():
    """The rule bites exactly where damage persists — a wilds monster
    heals to full when you run, so the opener stays per-fight."""
    p = playing(clazz="archer", world=warden_world(1))
    p["treeline_wardens"] = [1]
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    s = core.apply_choice(p, "hunt")
    assert p["encounter"]["kind"] != "warden"
    assert p["encounter"]["shot_used"] is False
    assert any(o.id == "treeline_shot" for o in s.options)


def test_fallen_wardens_are_pruned_from_the_memory():
    p = playing(clazz="archer", world=warden_world(2))
    p["unlocked_floor"] = 2
    p["treeline_wardens"] = [1, 2]      # floor 1's Warden already fell
    join_keep(p, floor=2)
    assert p["treeline_wardens"] == [2]


# ── §2 + §3: the kill pays in the card, and the fall is a reel ──────────

def kill_current_warden(p):
    e = p["encounter"]
    e["hp"] = 1
    if e.get("shared"):
        e["hp_join"] = 1                # keep the cut under the 026 unit
    for _ in range(4):                  # steel crosses first, then swings
        p["hp"] = 999
        s = core.apply_choice(p, "attack")
        if p["encounter"] is None:
            return s
    raise AssertionError("the killing blow must land")


@reel
def test_shared_kill_card_is_the_fall_reel():
    p = playing(world=warden_world(1))
    join_keep(p)
    s = kill_current_warden(p)
    fl = schema.get_floor(1)
    assert s.headline == f"{fl.warden_name} falls"
    assert s.fx == "warden_slain"
    assert s.event_kind == "boss"
    assert {o.id for o in s.options} == {"next", "skip"}
    # the engine's half of the receipt; worldd lands xp/gold/loot on it
    assert p["kill_receipt"]["dealt"] > 0
    assert p["kill_receipt"]["shared"] is True
    assert p["movie_floor"] == 2 and p["movie_beat"] == -1
    # the settled receipt (as worldd writes it) reads back on a refresh
    p["kill_receipt"].update({"xp": 120, "gold": 300, "names": "Sosa"})
    s = core.current_scene(p)
    assert s.support == "Struck down by Sosa."
    assert any("your share of the kill" in ln for ln in s.body_lines)
    assert s.body_lines[-1].startswith("FLOOR 2")
    assert {t["kind"] for t in s.tally} == {"gold", "aether"}


@reel
def test_the_reel_runs_slain_world_keep_then_home():
    p = playing(world=warden_world(1))
    join_keep(p)
    kill_current_warden(p)
    s = core.apply_choice(p, "next")            # floor 2 introduces itself
    assert s.eyebrow.startswith("FLOOR 2") and s.fx == "floor2_world"
    s = core.apply_choice(p, "next")            # its Warden, still standing
    assert s.fx == "floor2_warden"
    s = core.apply_choice(p, "next")            # back to the floor you're on
    assert p.get("movie_floor") is None
    assert p.get("kill_receipt") is None
    assert p["flags"].get("floor_seen_2") is True
    assert p["location"] == "gate_town" and p["floor"] == 1
    assert s.options                            # a live card, not a beat


@reel
def test_skip_cuts_the_reel_and_still_counts_as_seen():
    p = playing(world=warden_world(1))
    join_keep(p)
    kill_current_warden(p)
    core.apply_choice(p, "skip")
    assert p.get("movie_floor") is None
    assert p["flags"].get("floor_seen_2") is True


@reel
def test_watched_from_the_kill_means_not_replayed_at_the_gate():
    p = playing(world=warden_world(1))
    join_keep(p)
    kill_current_warden(p)
    core.apply_choice(p, "skip")
    p["unlocked_floor"] = 2
    p["level"] = 10
    core.apply_choice(p, "town")        # the kill left us at the gate town
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_2")
    assert p.get("movie_floor") is None         # straight to arrival
    assert "safe fire" in s.headline


def test_the_kill_clears_the_treeline_memory():
    p = playing(clazz="archer", world=warden_world(1))
    join_keep(p)
    core.apply_choice(p, "treeline_shot")
    assert p["treeline_wardens"] == [1]
    p["encounter"]["hp"] = 1
    p["hp"] = 999
    core.apply_choice(p, "attack")
    assert 1 not in p.get("treeline_wardens", [])


@reel
def test_solo_first_clear_keeps_its_card_then_plays_the_reel():
    p = playing()                       # no _world — dev/local play
    enter_floor(p)
    core.apply_choice(p, "keep")
    s = kill_current_warden(p)
    # the card keeps the haul (solo numbers are known right here) …
    assert any(ln.startswith("+") for ln in s.body_lines)
    assert {o.id for o in s.options} == {"next", "skip"}
    assert p["movie_beat"] == -2 and p["movie_teaser"]
    assert p["kill_receipt"]["xp"] > 0 and p["kill_receipt"]["loot"]
    # … and the NEXT click is the Warden going down
    s = core.apply_choice(p, "next")
    fl = schema.get_floor(1)
    assert s.headline == f"{fl.warden_name} falls"
    assert any("XP" in ln for ln in s.body_lines)
    s = core.apply_choice(p, "next")
    assert s.fx == "floor2_world"


@reel
def test_a_memorial_earns_no_reel():
    """034 §3: below the frontier there is nothing left to kill, so
    there is no fall to play — the reel belongs to the one real death."""
    p = playing(world=warden_world(3))
    p["unlocked_floor"] = 3
    enter_floor(p)
    core.apply_choice(p, "keep")        # below the frontier: a monument
    assert p.get("encounter") is None
    assert p.get("movie_floor") is None


def test_receipt_lines_wording():
    lines = combat.kill_receipt_lines(
        {"dealt": 37, "xp": 1200, "gold": 4500, "shared": True,
         "loot": "Trollblood tonic"})
    assert lines[0] == "Your blade took the last 37 of it."
    assert lines[1] == "+ 1,200 XP — your share of the kill"
    assert lines[2] == "+ ◈ 4,500 from the Warden's hoard"
    assert "killing blow" in lines[3]
