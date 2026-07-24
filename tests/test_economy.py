"""Economy formulas vs the sample tables in vision/economy.md §3–§4."""

from plugin_linear_ascent import economy


def test_monster_stats_match_design_table():
    # 004 retune: ATK slope 3.3 (wilds ≤40% of pool at level, honed)
    assert economy.monster_stats(5) == (18, 15, 85)
    assert economy.monster_stats(25) == (84, 75, 325)
    assert economy.monster_stats(55) == (184, 165, 685)
    assert economy.monster_stats(95) == (316, 285, 1165)


def test_kill_rewards_jump_per_band():
    assert economy.xp_per_kill(5) == 60
    assert economy.gold_per_kill(5) == 40          # tier 1: base 8×floor
    assert economy.xp_per_kill(95) == 1140
    # 004 §4.5: ×1.2 per band — same work pays visibly better each band
    assert economy.gold_per_kill(95) == round(8 * 95 * 1.2 ** 9)
    assert economy.gold_per_kill(11) == round(8 * 11 * 1.2)


def test_xp_need_curve():
    assert economy.xp_need(1) == 60
    assert economy.xp_need(10) == 1897        # table shows ~1,900
    assert economy.xp_need(50) == 21213       # ~21,200


def test_fade_rule_keys_on_floor_progress():
    # 004 §4.2: fade compares the fought floor to the player's own
    # frontier — never to level
    assert economy.fade_multiplier(10, 10) == 1.0
    assert economy.fade_multiplier(10, 5) == 1.0        # exactly 5 below
    assert economy.fade_multiplier(12, 5) == 0.8
    assert economy.fade_multiplier(40, 3) == 0.25       # floor
    # over-leveled on your frontier floor: full rewards, always
    assert economy.fade_multiplier(9, 9) == 1.0


def test_warden_derivation_and_milestones():
    # 004 §4.1: wardens derive from the at-level player model
    atk, dfs, hp = economy.warden_stats(7)
    m_atk, m_def, m_hp = economy.monster_stats(7)
    assert dfs == m_def
    assert hp == round(m_hp * economy.WARDEN_HP_MULT)
    assert atk > m_atk                                 # hits harder than wilds
    # solo odds decay past the soft floor: HP ramps
    assert economy.warden_stats(40)[2] > round(
        economy.monster_stats(40)[2] * economy.WARDEN_HP_MULT)
    g = economy.MILESTONES[10]
    assert (g.atk, g.dfs, g.hp, g.quorum) == (60, 50, 900, 2)
    assert economy.MILESTONES[100].name == "Vharuk, the Demon King"


def test_forge_catalog_shape():
    t1 = economy.forge_tier(1)
    assert {g.slot for g in t1} == {"weapon", "shield", "armor"}
    pig = economy.FORGE["pigsticker"]
    assert (pig.bonus, pig.price) == (8, 250)
    # 004 §4.4: late tiers repriced from exponential to quadratic
    dawn = [g for g in economy.forge_tier(10) if g.slot == "weapon"][0]
    assert (dawn.bonus, dawn.price) == (80, 685_000)


def test_honing_shape():
    # cap: +1 per unlocked floor past the band start
    assert economy.max_hone(1) == 0
    assert economy.max_hone(17) == 6
    assert economy.max_hone(21) == 0          # new band resets the cap
    # priced ~15% of a frontier day's income
    assert economy.hone_price(17) == max(
        5, round(0.15 * economy.daily_income(17)))
    # the design reference hones with a 2-floor lag
    assert economy.reference_hone(17) == 4


def test_caps_and_race_nudges():
    assert economy.energy_cap(1) == 24
    assert economy.energy_cap(30) == 27
    assert economy.energy_cap(1, "human") == 25
    assert economy.mana_cap(1, "elf") == 11
