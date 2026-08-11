"""020 — the unlock registry: one declarative table behind every gate.

The coverage guard is the test that keeps 020 true a year from now:
adding a *_LEVEL constant without registering the gate fails here.
"""

from __future__ import annotations

import re

from plugin_linear_ascent import economy, unlocks
from plugin_linear_ascent.engine import social


def player(level=1, floor=1):
    return {"level": level, "unlocked_floor": floor}


# ── the coverage guard ───────────────────────────────────────────────────

def test_every_level_gate_constant_has_a_registry_entry():
    level_ats = {u.at for u in unlocks.registry() if u.gate == "level"}
    gates = {
        "ARCANUM_LEVEL": economy.ARCANUM_LEVEL,
        "RELAY_LEVEL": economy.RELAY_LEVEL,
        "FIELDS_LEVEL": economy.FIELDS_LEVEL,
        "BOARD_LEVEL": economy.BOARD_LEVEL,
        "NIGHT_SLOT_LEVEL": economy.NIGHT_SLOT_LEVEL,
        "STRONGBOX_LEVEL": economy.STRONGBOX_LEVEL,
        "FOUND_MIN_LEVEL": social.FOUND_MIN_LEVEL,
        # protections register at the level they EXPIRE
        "BEGINNER_MERCY_MAX_LEVEL": economy.BEGINNER_MERCY_MAX_LEVEL + 1,
        "BEGINNER_PROTECTION_MAX_LEVEL":
            economy.BEGINNER_PROTECTION_MAX_LEVEL + 1,
        "DEATH_NO_PARDON_LEVEL": economy.DEATH_NO_PARDON_LEVEL,
    }
    missing = {n: v for n, v in gates.items() if v not in level_ats}
    assert not missing, f"gates with no registry entry: {missing}"


def test_no_gate_constant_was_forgotten_by_this_test():
    """The guard above lists constants by hand — this one makes sure the
    hand-list can't rot: any NEW *_LEVEL constant in economy.py must be
    either in the guard or explicitly exempted here."""
    known = {"ARCANUM_LEVEL", "RELAY_LEVEL", "FIELDS_LEVEL", "BOARD_LEVEL",
             "NIGHT_SLOT_LEVEL", "STRONGBOX_LEVEL", "CARRY3_LEVEL",
             "BEGINNER_MERCY_MAX_LEVEL",
             "BEGINNER_PROTECTION_MAX_LEVEL", "DEATH_NO_PARDON_LEVEL"}
    # DEATH_FREE_MAX_LEVEL is not a gate — it's the 043.2 free-death
    # window inside the mercy band, invisible in the unlock registry.
    exempt = {"LODGE_PRICE_PER_LEVEL", "GRANT_DAILY_CAP_PER_LEVEL",
              "DEATH_FREE_MAX_LEVEL"}
    found = {n for n in dir(economy)
             if re.search(r"_LEVEL$", n) and n.isupper()}
    unknown = found - known - exempt
    assert not unknown, (
        f"new *_LEVEL constants {unknown} — register them in unlocks.py "
        "and add them to the coverage guard (or exempt them here)")


def test_registry_reads_the_live_constants_no_drift_copies():
    by_id = {u.id: u for u in unlocks.registry()}
    assert by_id["found_guild"].at == social.FOUND_MIN_LEVEL
    assert str(social.GUILD_FOUND_FEE) in by_id["found_guild"].cost
    assert by_id["arcanum"].at == economy.ARCANUM_LEVEL
    assert by_id["mercy_ends"].at == economy.BEGINNER_MERCY_MAX_LEVEL + 1
    assert by_id["gear_tier_2"].at == economy.gear_player_level_req(2)
    assert by_id["milestone_10"].at == 10
    assert str(economy.MILESTONES[10].quorum) in by_id["milestone_10"].why


# ── ahead() ──────────────────────────────────────────────────────────────

def test_ahead_is_unmet_only_sorted_by_distance():
    p = player(level=3, floor=5)
    rows = unlocks.ahead(p)
    assert all(not unlocks.met(p, u) for u in rows)
    dists = [(u.at - (3 if u.gate == "level" else 5)) for u in rows]
    assert dists == sorted(dists)
    assert all(d > 0 for d in dists)


def test_ahead_level_1_and_level_95_both_sane():
    fresh = unlocks.ahead(player(level=1, floor=1), limit=8)
    assert fresh and fresh[0].at <= 4
    done = unlocks.ahead(player(level=95, floor=100))
    assert done == []
    lines = unlocks.climb_ahead_lines(player(level=95, floor=100))
    assert any("ladder is yours" in ln for ln in lines)


def test_ahead_never_leaks_the_whole_tower_to_a_fresh_player():
    lines = unlocks.climb_ahead_lines(player(level=1, floor=1), limit=8)
    assert not any("91" in ln for ln in lines)
    assert any("…and the tower keeps the rest" in ln for ln in lines)


# ── just_reached() ───────────────────────────────────────────────────────

def test_level_1_to_2_wakes_the_town():
    # 0.29.1 re-gate: the daily-texture doors (relay, board, night slot)
    # all open in one "the town wakes up for you" beat
    p = player(level=2, floor=1)
    got = unlocks.just_reached(p, old_level=1, old_floor=1)
    assert {"relay", "board", "night_slot"} <= {u.id for u in got}


def test_level_3_to_4_is_exactly_founding_plus_mercy_ends():
    p = player(level=4, floor=1)
    got = unlocks.just_reached(p, old_level=3, old_floor=1)
    # 025 §4: and a rung of steel — every level in band 1 sells something
    assert {u.id for u in got} == {"found_guild", "mercy_ends",
                                   "band1_rung_4"}
    # opens sort before closes — the gifts are read before the bill
    assert got[-1].id == "mercy_ends"


def test_floor_open_announces_the_band():
    p = player(level=11, floor=11)
    got = unlocks.just_reached(p, old_level=11, old_floor=10)
    ids = {u.id for u in got}
    assert "relics_floor_11" in ids and "hone_reset_2" in ids


# ── the square's footer ──────────────────────────────────────────────────

def test_next_line_carries_the_threshold_and_the_closing_half():
    p = player(level=3, floor=1)
    line = unlocks.next_line(p)
    assert line.startswith("NEXT — LEVEL 4")
    assert "banner" in line and "mercy" in line


def test_protections_active_names_both_shields_then_none():
    both = unlocks.protections_active(player(level=2))
    assert len(both) == 2
    assert unlocks.protections_active(player(level=7)) == []
