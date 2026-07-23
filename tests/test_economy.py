"""Economy formulas vs the sample tables in vision/economy.md §3–§4."""

from plugin_linear_ascent import economy


def test_monster_stats_match_design_table():
    # §4 sample rows: floor → ATK/DEF/HP
    assert economy.monster_stats(5) == (22, 15, 85)
    assert economy.monster_stats(25) == (102, 75, 325)
    assert economy.monster_stats(55) == (222, 165, 685)
    assert economy.monster_stats(95) == (382, 285, 1165)


def test_kill_rewards():
    assert economy.xp_per_kill(5) == 60
    assert economy.gold_per_kill(5) == 40
    assert economy.xp_per_kill(95) == 1140
    assert economy.gold_per_kill(95) == 760


def test_xp_need_curve():
    assert economy.xp_need(1) == 60
    assert economy.xp_need(10) == 1897        # table shows ~1,900
    assert economy.xp_need(50) == 21213       # ~21,200


def test_fade_rule():
    assert economy.fade_multiplier(10, 10) == 1.0
    assert economy.fade_multiplier(10, 5) == 1.0        # exactly 5 below
    assert economy.fade_multiplier(12, 5) == 0.8
    assert economy.fade_multiplier(40, 3) == 0.25       # floor


def test_warden_and_milestones():
    assert economy.warden_stats(7) == (35, 28, 420)
    g = economy.MILESTONES[10]
    assert (g.atk, g.dfs, g.hp, g.quorum) == (60, 50, 900, 2)
    assert economy.MILESTONES[100].name == "Vharuk, the Demon King"


def test_forge_catalog_shape():
    t1 = economy.forge_tier(1)
    assert {g.slot for g in t1} == {"weapon", "shield", "armor"}
    pig = economy.FORGE["pigsticker"]
    assert (pig.bonus, pig.price) == (8, 250)
    dawn = [g for g in economy.forge_tier(10) if g.slot == "weapon"][0]
    assert (dawn.bonus, dawn.price) == (80, 2_800_000)


def test_caps_and_race_nudges():
    assert economy.energy_cap(1) == 24
    assert economy.energy_cap(30) == 27
    assert economy.energy_cap(1, "human") == 25
    assert economy.mana_cap(1, "elf") == 11
