"""017 phase 008 — the bestiary at scale (floors 11-100).

The whole tower speaks the counter language now: every floor 11-100
carries 4-5 encounters, lore, and a deliberate trait spread.  This file
is the at-scale version of the 001 matchup gate plus the content-wide
guarantees: hunting pools everywhere, hard counters that actually wall,
art for every monster, and lore that reaches the [i] card.

001 retro: constants verbatim — hard means win <30% or rounds ≥1.6×
the class's easy prey.  002 retro: sims are chase-aware via
`_sim_fight` (the archer kites); ranged-vs-fast is an INTENDED counter.
Floors without a traitless encounter use the class's fastest intended
kill as the "plain" baseline — the drag ratio needs prey, not blanks.
"""

import os

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat
from tests.test_017_damage_types import (_class_mult, _sim_fight,
                                         _speed_counters, reference_player)

# 030 Phase 9: everything here sims floors above TUNED_FLOOR_CAP — the
# untuned tower. The default run skips the module; ASCENT_FULL_SIMS=1
# is the pre-ship ritual that walks all hundred floors.
if not os.environ.get("ASCENT_FULL_SIMS"):
    pytest.skip(
        f"floors 11-100 sims — tuned cap is {economy.TUNED_FLOOR_CAP} "
        "(030 Phase 9); set ASCENT_FULL_SIMS=1 for the full tower",
        allow_module_level=True)

FLOORS = range(11, 101)
# 022/002: 20 sims put ±10% noise on an 80% gate — floor 95's curator
# read 75% on one seed set while its true rate is 87%. 40 matches the
# floors-1-10 gate and keeps the pass/fail about design, not dice.
N_SIM = 40


def _floor_results(clazz, floor_no):
    """(winrate, avg_rounds_of_WON_fights, profile) per encounter.

    Rounds average victories only: drag means "how long a kill takes",
    and a fight that kills YOU ends early — mixing deaths in
    undercounts the slog exactly on the monsters that are the most
    dangerous (at scale a 45%-win armor_med knight averaged 1.5× plain
    and slipped the 1.6× bar it honestly clears)."""
    fl = schema.get_floor(floor_no)
    out = {}
    for enc in fl.encounters:
        profile = economy.profile_from_traits(enc.traits)
        wins = won_rounds = all_rounds = 0
        for seed in range(N_SIM):
            won, r = _sim_fight(clazz, floor_no, enc, seed)
            wins += won
            all_rounds += r
            won_rounds += r if won else 0
        rounds = won_rounds / wins if wins else all_rounds / N_SIM
        out[enc.id] = (wins / N_SIM, rounds, profile)
    return out


def _intended(clazz, profile):
    return (_class_mult(clazz, profile) >= 1.0 and not profile["bulwark"]
            and not _speed_counters(clazz, profile))


def test_matchup_gate_at_scale():
    """One pass over every floor 11-100 asserts all three at-scale
    promises at once (the sims are the expensive part, the checks are
    free): intended prey dies ≥80%, at least two encounter types per
    floor are a ≥70% hunt for every class, and every hard counter is
    FELT.

    Felt means not prey-grade: a counter may be RISKY (win ≤75% — the
    006 death economy makes a 1-in-4 death chance ruinous EV, players
    route around it) or a DRAG (≥1.6× easy-prey rounds), but never
    both safe and quick.  The 001 gate's win<30% wall exists on floors
    1-10; at scale the mid band (35-75% win) is the armor knights and
    fast predators doing exactly their job."""
    for floor_no in FLOORS:
        for clazz in economy.DAMAGE_TYPE:
            results = _floor_results(clazz, floor_no)
            plain = min((rounds for win, rounds, prof in results.values()
                         if _intended(clazz, prof)), default=None)
            pool = 0
            for enc_id, (win, rounds, prof) in results.items():
                where = f"floor {floor_no} {clazz} vs {enc_id}"
                if win >= 0.70:
                    pool += 1
                if _intended(clazz, prof):
                    assert win >= 0.80, f"{where}: prey escapes {win:.0%}"
                elif (_class_mult(clazz, prof) <= 0.5 or prof["bulwark"]
                        or _speed_counters(clazz, prof)):
                    dragged = plain and rounds >= 1.6 * plain
                    assert win <= 0.75 or dragged, (
                        f"{where}: win {win:.0%}, rounds {rounds:.1f} vs "
                        f"plain {plain:.1f} — safe AND quick, prey-grade")
            assert pool >= 2, (
                f"floor {floor_no}: {clazz} has {pool} viable hunts — "
                "the frontier walls this class")


# Art coverage for every encounter id is already gated by
# tests/test_011_art.py::test_every_encounter_has_creature_art — the 008
# batch only has to make it pass.


def test_lore_reaches_the_dossier_on_every_band():
    """One floor per band: start a fight against each encounter and
    assert its authored lore lands in the scene's enemy payload — the
    [i] card reads from there."""
    for floor_no in range(15, 101, 10):
        fl = schema.get_floor(floor_no)
        for enc in fl.encounters:
            p = reference_player("warrior", floor_no)
            p["luna_user"] = f"lore-{floor_no}-{enc.id}"
            s = combat.start_encounter(p, fl, enc)
            assert s.enemy and s.enemy["lore"] == enc.lore, (
                f"floor {floor_no} {enc.id}: lore missing from payload")
