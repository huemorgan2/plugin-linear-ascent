"""048 phase 6 — the balance bake's T4 gates.

The trained-rank sink changed what a kill's XP must fund: body levels
AND a weapon path. These gates pin the pace laws the bake tunes toward:

- a one-path climber (trains the main path on schedule) still caps in
  the first weeks — the level≈floor pace survives the sink;
- rank 10 lands ≈ body level 10 — mastering the first weapon is a
  level-10-sized achievement, on time;
- spreading over three paths is a real, priced choice: slower by body
  levels, never a brick;
- the young-tower bounty makes floors 1–10 the classroom: exact coin
  multipliers, and the classroom kit (bow + staff + first ranks) is
  affordable at the leash pace without farming.

All closed-form arithmetic over economy constants — no engine, no rng.
"""

from plugin_linear_ascent import economy


KILLS_PER_DAY = (24 * 60 / economy.ENERGY_REGEN_MIN
                 / economy.COST_WILDS_FIGHT)                    # 32


def _next_rank(training, policy):
    """The rank the climber saves for next, or None past the target."""
    if policy == "one_path":
        r = training["blade"]
        return ("blade", r + 1) if r < 10 else None
    # tri_path: raise the lowest path first — the deliberate spreader
    path = min(("blade", "bow", "staff"), key=lambda k: training[k])
    r = training[path]
    return (path, r + 1) if r < 10 else None


def _climb(policy, max_kills=200_000):
    """Kill-granular pace model: XP lands on a hard bar (overflow
    discarded), the School spends the bar before it fills, the
    Guildhall levels on a full bar. Frontier rides level (leash).
    Returns the timeline: kills at each level-up and at each rank."""
    level, xp = 1, 0.0
    training = {"blade": 2, "bow": 0, "staff": 0}
    kills = 0
    level_at = {1: 0}
    rank_at = {}
    while level < economy.LEVEL_CAP and kills < max_kills:
        kills += 1
        floor = min(level, economy.LEVEL_CAP)
        need = economy.xp_need(level)
        xp = min(xp + economy.xp_per_kill(floor), need)
        want = _next_rank(training, policy)
        if want is not None:
            path, nxt = want
            cost = economy.train_xp(nxt)
            # a rank the bar can never hold waits for a taller bar
            if cost <= need and xp >= cost:
                xp -= cost
                training[path] = nxt
                rank_at[(path, nxt)] = (kills, level)
                continue
        if xp >= need:
            xp -= need
            level += 1
            level_at[level] = kills
    return level_at, rank_at, kills


def test_one_path_climber_still_caps_in_the_first_weeks():
    """The 022/002 law re-run WITH the sink: an all-energy one-path
    climber funds every blade rank on the way and still caps in 3–6
    weeks — XP_PER_KILL_SLOPE 3.0 pays for the School."""
    level_at, rank_at, kills = _climb("one_path")
    assert max(level_at) == economy.LEVEL_CAP
    days = kills / KILLS_PER_DAY
    assert 14 <= days <= 42, f"{days:.1f} days to cap"
    assert ("blade", 10) in rank_at, "never mastered the blade"


def test_rank_ten_lands_near_level_ten():
    """N3: one path 0→10 ≈ the XP of body levels 1→10 — so the
    on-schedule specialist masters the blade around body level 10."""
    _, rank_at, _ = _climb("one_path")
    _, level = rank_at[("blade", 10)]
    assert 9 <= level <= 12, f"blade 10 at body level {level}"


def test_tri_path_spread_is_slower_but_never_bricks():
    """The spreader's price is printed in body levels: ≥3 behind the
    specialist at equal kills by mid-tower — and still climbing (the
    cap arrives, just later)."""
    one_levels, _, one_kills = _climb("one_path")
    mid_kills = one_levels[20]
    tri_levels, _, tri_kills = _climb("tri_path")
    tri_at_mid = max(lv for lv, k in tri_levels.items()
                     if k <= mid_kills)
    assert tri_at_mid <= 20 - 3, (
        f"tri-path at the specialist's level-20 mark: level {tri_at_mid}"
        " — spreading must cost body levels")
    assert max(tri_levels) == economy.LEVEL_CAP, "the spreader bricked"
    assert tri_kills <= 3 * one_kills, "the spreader crawls too far behind"


# ── the young-tower bounty (N8) ────────────────────────────────────────

def test_early_coin_mult_is_exact():
    assert economy.early_coin_mult(1) == 2.0
    assert economy.early_coin_mult(5) == 1.6
    assert economy.early_coin_mult(10) == 1.1
    assert economy.early_coin_mult(11) == 1.0
    assert economy.early_coin_mult(100) == 1.0


def test_bounty_rides_gold_per_kill():
    """The bounty is IN the paycheck, not a separate line item."""
    base = economy.GOLD_PER_KILL_ANCHOR * economy.income_pillar(1)
    assert economy.gold_per_kill(1) == max(1, round(base * 2.0))
    deep = economy.GOLD_PER_KILL_ANCHOR * economy.income_pillar(40)
    assert economy.gold_per_kill(40) == max(1, round(deep))


def test_bounty_extra_funds_the_classroom_kit():
    """N8's stated purpose, as arithmetic: the bounty's EXTRA coin
    (income beyond the un-bountied baseline) covers the classroom kit —
    both basic weapons plus the instructor fees for ranks 1–2 of bow
    and staff — at the leash pace, no farming. Level-up fees are the
    standing sink and stay funded by the wider economy (contracts,
    wardens, specimen premiums) exactly as before 048."""
    level_at, _, _ = _climb("one_path")
    extra = 0.0
    for level in range(1, 11):
        start = level_at.get(level)
        end = level_at.get(level + 1)
        if start is None or end is None:
            break
        kills = end - start
        base = economy.GOLD_PER_KILL_ANCHOR * economy.income_pillar(level)
        extra += kills * (economy.gold_per_kill(level) - round(base))
    fees = sum(economy.train_gold(r, 10) for r in (1, 2)) * 2
    kit = 2 * economy.BASIC_WEAPON_PRICE + fees
    assert extra >= kit, (
        f"bounty extra ◈{extra:.0f} < kit ◈{kit} — the young tower "
        "must fund its own classroom")
