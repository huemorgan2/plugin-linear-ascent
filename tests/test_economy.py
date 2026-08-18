"""Economy formulas vs the sample tables in vision/economy.md §3–§4."""

from plugin_linear_ascent import economy


def test_monster_stats_match_design_table():
    # 004 retune: ATK slope 3.3; 008: HP derived from the at-level
    # player's damage × a rounds budget — quick kills early, never a
    # slog.  022/002 retune: the at-level player now carries gear-first
    # power (weapon 30T−22, weighted hone), so wilds HP re-derived.
    # 025 §4: band 1 sells a rung per level, so the at-level player on
    # floor 5 hits harder and the animals there carry the HP to match.
    # 046: ATK/DEF ride the pillar, HP still derives from the rounds
    # budget against the (now pillar-riding) reference player
    assert economy.monster_stats(5) == (11, 9, 90)
    assert economy.monster_stats(25) == (1793, 1628, 16338)
    assert economy.monster_stats(55) == (4693050, 4266407, 20442338)
    assert economy.monster_stats(95) == (169507553878, 154097776251,
                                         737207440620)
    for f in (1, 5, 25, 95):
        atk, dfs, hp = economy.monster_stats(f)
        p_atk, _ = economy._at_level_loadout(f)
        p_dmg = max(1, round(0.75 * p_atk) - dfs // 2)
        assert hp == round(p_dmg * economy.wilds_rounds(f))


def test_kill_rewards_jump_per_band():
    # 046: XP syncs level to floor (slope·bar^1.5 ÷ wedge), gold rides
    # the income pillar from the floor-1 anchor of 8. 048: slope 3.0
    # (the School sink), and the young-tower bounty rides gold ≤ 10
    assert economy.xp_per_kill(5) == 29
    # 065: 20 base × 1.6 bounty = 32, but coin rides ≥ 1.25 × the
    # kill's XP — the floor rule pays 36 here
    assert economy.gold_per_kill(5) == 36
    assert economy.base_gold_per_kill(5) == 20
    assert economy.xp_per_kill(95) == 70
    assert economy.gold_per_kill(95) == max(
        1, round(8 * economy.income_pillar(95)))
    assert economy.gold_per_kill(11) == 92    # 065: 74 xp × 1.25
    assert economy.gold_per_kill(14) == 146   # the pillar is back on top


def test_xp_need_curve():
    # 022/002: base 24 (was 60) — levels are the early game now, the
    # cap (30) lands in ~2-3 weeks and gear carries growth after
    assert economy.xp_need(1) == 24
    assert economy.xp_need(10) == 759
    assert economy.xp_need(economy.LEVEL_CAP) == 3944   # the last climb


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
    # 004 §4.1: wardens derive from the at-level player model.
    # 008: their HP budget stays on the pre-008 curve (12F+25) so the
    # wilds fast-kill retune never shrinks a boss.
    atk, dfs, hp = economy.warden_stats(7)
    m_atk, m_def, _ = economy.monster_stats(7)
    assert dfs == m_def
    assert hp == round(economy._boss_hp_base(7) * economy.WARDEN_HP_MULT)
    assert atk > m_atk                                 # hits harder than wilds
    # 046: the post-30 ramp retired — the warden rise (×1.02^(F−1))
    # lives in _boss_hp_base itself, on top of the pillar
    assert economy.warden_stats(40)[2] == round(
        economy._boss_hp_base(40) * economy.WARDEN_HP_MULT)
    assert economy._boss_hp_base(40) > round(37 * economy.pillar(40))
    g = economy.MILESTONES[10]
    assert (g.atk, g.dfs, g.hp, g.quorum) == (202, 32, 1426, 2)
    assert economy.MILESTONES[100].name == "Vharuk, the Demon King"


def test_forge_catalog_shape():
    # 017/004: tier 1 now spans the three weapon lines, shield + focus,
    # armor and the first shoe rung
    t1 = economy.forge_tier(1)
    assert {g.slot for g in t1} == {"weapon", "shield", "armor", "shoes"}
    pig = economy.FORGE["scrap_dagger"]
    assert (pig.bonus, pig.price) == (8, 200)
    # 004 §4.4: late tiers repriced from exponential to quadratic;
    # 022/002: bonuses rescaled to carry growth past the cap (30T−22)
    # 046: tier 10 rides the pillar all the way up
    dawn = economy.FORGE["dawnbreaker"]
    assert (dawn.bonus, dawn.price) == (143_877_106_312,
                                        4_500_000_000_000)


def test_honing_shape():
    # cap: +1 per unlocked floor past the band start
    assert economy.max_hone(1) == 0
    assert economy.max_hone(17) == 6
    assert economy.max_hone(21) == 0          # new band resets the cap
    # priced ~15% of a frontier day's income, in CAPITAL terms — the
    # hone is bought power, so the fee rides the wedge (046 cost law)
    assert economy.hone_price(17) == max(
        5, round(0.15 * economy.daily_income(17)
                 * economy.pace_wedge(17)))
    # the design reference hones with a 2-floor lag
    assert economy.reference_hone(17) == 4


def test_caps_and_race_nudges():
    # 022/002: the meter grows with GEAR (one point per tier past the
    # first), not with level — steel is the long game
    assert economy.energy_cap(1) == 24
    assert economy.energy_cap(5) == 28
    assert economy.energy_cap(10) == 33
    assert economy.energy_cap(1, "human") == 25
    # 006: the mana meter is gone — elves learn faster instead
    assert not hasattr(economy, "mana_cap")
    assert economy.ELF_XP_BONUS == 0.05


def test_xp_pool_costs_scale_with_floor():
    # 006: XP costs are priced in frontier kills (048: kill = 3.0×bar);
    # 045 dropped the scan, so its cost row is gone.
    assert economy.hone_xp(1) == 2            # half of 3
    assert economy.hone_xp(17) == 56          # half of 112 (046 xp law)
    assert economy.sleep_xp_cost(5) == 29     # exactly the kill skipped


def test_level_gates():
    # tier T answers to the band's first floor — as a LEVEL up to the
    # cap, as a FLOOR gate past it (022/002: the tower vouches for you
    # once the drillmaster can't)
    assert economy.gear_player_level_req(1) == 1
    assert economy.gear_player_level_req(2) == 11
    assert economy.gear_player_level_req(10) == economy.LEVEL_CAP
    assert economy.gear_floor_req(3) == 0            # pre-cap: level only
    assert economy.gear_floor_req(4) == 31
    assert economy.gear_floor_req(10) == 91
    assert economy.floor_entry_player_level(1) == 1
    assert economy.floor_entry_player_level(11) == 1
    assert economy.floor_entry_player_level(40) == 30
    assert economy.floor_entry_player_level(100) == economy.LEVEL_CAP
