"""020 — nothing locked is invisible: the square's NEXT line, the Stone's
ladder, locked town doors, locked gate floors, and the moments the rules
change (level-up card, first-clear card, first unprotected death)."""

from __future__ import annotations

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, social, state


def playing(name="Gates", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def town(p):
    p["location"] = "town"
    return core.apply_choice(p, "town")


# ── the square ───────────────────────────────────────────────────────────

def test_square_carries_the_next_line_for_a_fresh_climber():
    s = town(playing())
    nxt = [ln for ln in s.body_lines if ln.startswith("NEXT — ")]
    assert len(nxt) == 1
    assert "LEVEL" in nxt[0]


def test_locked_town_doors_are_locked_rows_and_still_refuse_kindly():
    p = playing(world={"social": True, "factions": [],
                       "factions_total": 0})
    p["level"] = 1
    s = town(p)
    for oid in ("arcanum", "relay", "fields"):
        row = next(o for o in s.options if o.id == oid)
        assert row.locked, oid
        assert "🔒" in row.hint, oid
        refusal = core.apply_choice(p, oid)
        assert refusal.shard_note, oid          # refuses with a reason
        assert p["location"] == "town", oid     # no scene change
        town(p)
    # at rank the same rows are live
    p["level"] = 6
    s = town(p)
    for oid in ("arcanum", "relay", "fields"):
        assert not next(o for o in s.options if o.id == oid).locked, oid


# ── the Stone ────────────────────────────────────────────────────────────

def test_stone_carries_the_climb_ahead_fold():
    p = playing()
    town(p)
    s = core.apply_choice(p, "stone")
    body = "\n".join(s.body_lines)
    assert "THE CLIMB AHEAD" in body
    assert "LEVEL" in body
    # the closing half of level 4 is on the ladder, glyphed −
    assert any(ln.strip().startswith("−") for ln in s.body_lines)


# ── the gate picker ──────────────────────────────────────────────────────

def test_far_floors_are_locked_rows_not_refusals_after_the_click():
    p = playing()
    p["unlocked_floor"] = 15
    p["level"] = 3
    town(p)
    s = core.apply_choice(p, "gate")
    far = next(o for o in s.options if o.id == "floor_15")
    req = economy.floor_entry_player_level(15)
    assert far.locked and f"level {req}" in far.hint
    near = next(o for o in s.options if o.id == "floor_1")
    assert not near.locked


def test_milestone_floor_carries_its_war_party_in_the_hint():
    p = playing()
    p["unlocked_floor"] = 10
    p["level"] = 10
    town(p)
    s = core.apply_choice(p, "gate")
    row = next(o for o in s.options if o.id == "floor_10")
    assert f"war party of {economy.MILESTONES[10].quorum}" in row.hint


def test_floor_below_a_milestone_warns_at_the_gate():
    p = playing()
    p["unlocked_floor"] = 9
    p["level"] = 9
    town(p)
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_9")
    body = "\n".join(s.body_lines)
    m = economy.MILESTONES[10]
    assert m.name in body and f"war party of {m.quorum}" in body


# ── the moments it changes ───────────────────────────────────────────────

def test_training_to_level_4_announces_both_halves():
    p = playing()
    p["level"] = 3
    p["xp"] = economy.xp_need(3)
    p["gold"] = economy.levelup_gold(3) + 10
    town(p)
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "guild_train")
    assert p["level"] == 4
    body = "\n".join(s.body_lines)
    assert "LEVEL 4" in body
    assert "faction" in body          # the gift
    assert "mercy" in body            # the bill


def _stage_death(p):
    p["daily"]["death_save"] = True
    p["hp"] = 1
    p["location"] = "gate_town"
    p["floor"] = 1
    p["encounter"] = {"kind": "wilds", "name": "test wolf", "hp": 99,
                      "hp_max": 99, "atk": 500, "dfs": 0, "spd": 5,
                      "range": "close", "specimen": "common",
                      "profile": {}}


def test_first_unprotected_death_names_the_change_exactly_once():
    from plugin_linear_ascent.content import schema
    from plugin_linear_ascent.engine import combat
    p = playing("Mortal")
    p["level"] = 4
    fl = schema.get_floor(1)
    _stage_death(p)
    s = combat._death(p, fl)
    assert any("no longer gentle" in ln for ln in s.body_lines)
    # a second death is quiet about it
    _stage_death(p)
    s2 = combat._death(p, fl)
    assert not any("no longer gentle" in ln for ln in s2.body_lines)


# ── the sheet hands Luna the ladder ──────────────────────────────────────

def test_sheet_carries_next_unlocks_and_protections():
    from plugin_linear_ascent import sheet
    p = playing()
    d = sheet.character_sheet(p)
    assert d["next_unlocks"], "the ladder must ride the sheet"
    first = d["next_unlocks"][0]
    assert {"at", "effect", "title", "why"} <= set(first)
    # 081: mercy + ambush immunity + steady hands while green
    assert len(d["protections_active"]) == 3
    p["level"] = 8
    assert sheet.character_sheet(p)["protections_active"] == []
