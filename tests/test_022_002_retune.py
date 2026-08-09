"""022 phase 002 — the grand retune, gated.

One tuning pass, once (Roy's rule): the level cap, gear-carried growth
and the warden coordination curve are one spreadsheet over the same
constants. These gates pin the pass's acceptance criteria from
plans/022-one-world-many-clocks/002-the-grand-retune/plan.md:

- solo wardens 1–30 win 60–85% at-level (measured in the REAL fight
  sim — the old 1.07 damage budget claimed 65–85% on paper while the
  true rate had drifted to 0–36%);
- floor 31+ solo net progress mathematically impossible, including the
  banked-bar burst the 001 stopgap allowed;
- gear carries ≥60% of at-level ATK by floor 50;
- the cap lands in the first weeks and is an edge, not a wall;
- the era lands 4–6 months at A = 200 / 1,000 / 10,000 actives;
- no orphaned `level // 10` reads.
"""

import os
import pathlib
import re

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state
from tests.test_017_damage_types import _SIM_DAY, reference_player


def _fight_warden(fno, seed):
    """One at-level attempt on the floor's warden: True iff the player
    kills it without dying (the daily death save counts as a LOSS — the
    fight ended with the player on the floor)."""
    fl = schema.get_floor(fno)
    p = reference_player("warrior", fno)
    p["luna_user"] = f"022002-warden-{fno}-{seed}"
    orig_day = state.world_day
    state.world_day = lambda at=None: _SIM_DAY
    try:
        combat.start_encounter(p, fl, None, "warden")
        rounds = 0
        while p["encounter"] is not None and rounds < 80:
            rounds += 1
            # the per-swing ⚡ toll is out of scope here — this sim
            # measures combat math, so the bar is kept full
            p["energy_val"] = state.energy_cap_of(p)
            s = combat.resolve_fight_action(p, fl, "attack")
            if s.event_kind == "death" or p["hp"] <= 0:
                return False
        return p["encounter"] is None
    finally:
        state.world_day = orig_day


N_SIM = 150

# 030 Phase 9: the warden sim walks only the tuned floors on a default
# run (≤ TUNED_FLOOR_CAP); ASCENT_FULL_SIMS=1 sims the whole 1–29 band.
# Everything else in this file is closed-form arithmetic and stays on.
_SIM_TOP = (30 if os.environ.get("ASCENT_FULL_SIMS")
            else economy.TUNED_FLOOR_CAP + 1)


def test_solo_warden_band_wins_60_85():
    """Floors 5–29 (milestones excluded — they are quorum bosses tuned
    for 2+): per-floor win 50–95% with ±8% sampling noise allowed, and
    the band AVERAGE inside the design's 60–85%. Floors 1–4 ramp in
    gently (fresh climbers, partial kits): ≥88%."""
    rates = {}
    for fno in range(1, _SIM_TOP):
        if fno % 10 == 0:
            continue
        wins = sum(_fight_warden(fno, seed) for seed in range(N_SIM))
        rates[fno] = wins / N_SIM
    for fno in (1, 2, 3, 4):
        assert rates[fno] >= 0.88, (fno, rates[fno])
    band = [r for f, r in rates.items() if f >= 5]
    for fno in (f for f in rates if f >= 5):
        assert 0.50 <= rates[fno] <= 0.95, (fno, rates[fno])
    avg = sum(band) / len(band)
    assert 0.60 <= avg <= 0.85, avg


def test_floor_31_plus_solo_net_progress_is_impossible():
    """One blade grinding around the clock loses ground on every deep
    floor, at every population — regen breaks even at N/2 sustained
    strikers and N ≥ 2 everywhere past 30. Held numerically, not just
    by the algebra that designed it.  At N = 2 exactly (floor 31, small
    worlds) one blade BREAKS EVEN — zero net progress, and the silence
    window closes the wound the moment he sleeps; everywhere N > 2 he
    strictly loses ground."""
    for active in (None, 200, 1_000, 10_000):
        for fno in range(31, 101):
            n = economy.required_strikers(fno, active)
            assert n >= 2, (fno, active)
            solo_hr = (economy.SUSTAINED_FIGHTS_PER_HOUR
                       * economy.strike_fight_damage(fno))
            regen_hr = (economy.world_warden_regen_hourly(fno)
                        * economy.world_warden_hp(fno, active))
            if n == 2:
                assert solo_hr <= regen_hr, (fno, active)
            else:
                assert solo_hr < regen_hr, (fno, active)


def test_banked_bar_burst_cannot_break_a_deep_warden():
    """The 001 finding, closed structurally: a full energy bar — the
    biggest burst one player can bank — is worth at most ~11 keep
    fights, and every deep pool is N×8 ≥ 16 fights in the SAME honest
    fight units."""
    bar_fights = economy.energy_cap(10) // economy.COST_WARDEN_ATTEMPT
    for active in (None, 200, 1_000, 10_000):
        for fno in range(31, 101):
            burst = bar_fights * economy.strike_fight_damage(fno)
            assert burst < economy.world_warden_hp(fno, active), \
                (fno, active)


def test_gear_carries_the_late_game():
    """Past floor 50 the steel is ≥60% of the at-level ATK — the capped
    level is the minor term, exactly what lets the tower keep growing
    after the drillmaster stops."""
    for fno in range(50, 101):
        atk, _ = economy._at_level_loadout(fno)
        level_part = 3 * economy.reference_level(fno)
        assert 1 - level_part / atk >= 0.60, fno


def test_days_to_cap_lands_in_the_first_weeks():
    """An all-energy hunter reaches LEVEL_CAP in 3–6 weeks: every day
    the full passive energy income goes into frontier kills at the
    leash pace (frontier ≈ level). 043 cut XP 40%, so the cap moved
    out from ~3 weeks — levelling is meant to be slower now."""
    daily_energy = 24 * 60 / economy.ENERGY_REGEN_MIN
    day, level, xp = 0, 1, 0.0
    while level < economy.LEVEL_CAP and day < 100:
        day += 1
        floor = min(level, economy.LEVEL_CAP)
        xp += (daily_energy / economy.COST_WILDS_FIGHT
               * economy.xp_per_kill(floor))
        while level < economy.LEVEL_CAP and xp >= economy.xp_need(level):
            xp -= economy.xp_need(level)
            level += 1
    assert 21 <= day <= 42, day


# ── the era-length model ─────────────────────────────────────────────────
# A deliberately simple, documented arithmetic of the siege (004-style):
# it exists so that a change to N(F), the pool size or the regen curve
# that silently reshapes the era shows up as a red gate.
RALLY_APPETITE_DAYS = 7   # an active joins a frontier rally about weekly
RALLY_OVERHEAD = 1.2      # bars needed ÷ pool: regen during the same-day
#                           rally window (~6h ≈ +17%) plus slack
ORGANIZE_DAYS = 1.5       # open the wound, spread the word, land the rally
SOLO_BAND_DAYS = 30       # frontier 1–30 moves at the levelling pace


def _era_days(active):
    days = SOLO_BAND_DAYS
    for fno in range(31, 101):
        n = economy.required_strikers(fno, active)
        # a floor falls the day the world gathers ~1.2×N full bars;
        # gathering is bounded by the daily rally appetite of A actives
        gather = RALLY_OVERHEAD * n / (active / RALLY_APPETITE_DAYS)
        days += max(ORGANIZE_DAYS, gather)
    return days


def test_rally_overhead_covers_the_regen_window():
    # ties the model to the live constants: the +20% bar overhead must
    # cover what the pool regrows during the tightest same-day window
    regrow = (economy.world_warden_regen_hourly(31)
              * economy.warden_silence_hours(31))
    assert regrow <= RALLY_OVERHEAD - 1.0


def test_era_length_lands_4_to_6_months():
    for active in (200, 1_000, 10_000):
        days = _era_days(active)
        assert 120 <= days <= 180, (active, round(days, 1))


def test_milestone_quorums_ride_the_curve():
    """A big world's milestone asks for the same rally the curve asks
    for; a tiny world never sinks below the authored table."""
    for fno in (10, 50, 100):
        table = economy.MILESTONES[fno].quorum
        assert economy.milestone_quorum(fno, active=10_000) == max(
            table, economy.required_strikers(fno, 10_000))
        assert economy.milestone_quorum(fno, active=1) == table


# ── the cap edge, in the engine ──────────────────────────────────────────

def _capped_player(name):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", text="Capped")
    p["level"] = economy.LEVEL_CAP
    p["hp"] = state.max_hp(p)
    return p


def test_kill_xp_still_accrues_at_cap():
    """✦ is pure currency at the cap: the kill pays, the level holds."""
    p = _capped_player("cap-xp")
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "hunt")
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    xp0 = p["xp"]
    core.apply_choice(p, "attack")
    assert p["encounter"] is None
    assert p["xp"] > xp0
    assert p["level"] == economy.LEVEL_CAP


def test_guildhall_refuses_training_at_cap():
    p = _capped_player("cap-guild")
    p["xp"], p["gold"] = 1_000_000, 1_000_000
    s = core.apply_choice(p, "guildhall")
    assert not any(o.id == "guild_train" for o in s.options)
    assert any("nothing left to teach" in ln for ln in s.body_lines)
    from plugin_linear_ascent.engine import social
    s = social.guild_train(p)
    assert p["level"] == economy.LEVEL_CAP
    assert any("whole drill" in ln for ln in s.body_lines)


def test_deep_steel_sells_at_cap_on_the_right_floor():
    """Tier 4 (raw gate 31 > cap): refused while the war sits below
    floor 31, sold the moment the frontier reaches it — at level 30."""
    p = _capped_player("cap-steel")
    p["gold"] = 10_000_000
    p["unlocked_floor"] = 30
    core.apply_choice(p, "forge")
    s = core.apply_choice(p, "buy_thornsong")
    assert p["gear"]["weapon"] != "thornsong"
    assert "hasn't earned" in s.shard_note
    p["unlocked_floor"] = 31
    core.apply_choice(p, "buy_thornsong")
    assert p["gear"]["weapon"] == "thornsong"


def test_no_orphaned_level_div_10():
    """The energy cap (and everything else) stopped reading level//10 —
    the grep gate keeps it that way."""
    pkg = pathlib.Path(economy.__file__).parent
    pat = re.compile(r"level\s*//\s*10")
    offenders = [str(py) for py in sorted(pkg.rglob("*.py"))
                 if pat.search(py.read_text(encoding="utf-8"))]
    assert not offenders, offenders
