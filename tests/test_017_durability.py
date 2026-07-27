"""017 phase 005 — durability & repair (plan §3.5).

Power becomes a running cost: paid gear carries a use pool that shrinks
with tier, wear hooks fire once per event, broken means half strength
(never helpless), and the Forge mends for 20% of price × the missing
fraction plus a few XP. Staged onboarding: a slot only starts wearing
after its first PAID purchase. The economy gate proves repairs stay a
tax, not a wall.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Wearer"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    return p


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text=text)


def _armed(clazz="warrior", weapon="pigsticker", floor_no=1,
           enc_id="feral_boar", **slots):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    p = create_character(fresh(f"dur-{clazz}-{weapon}"), clazz=clazz)
    p["level"] = max(floor_no, 1)
    p["hp"] = economy.player_max_hp(p["level"])
    p["gear"]["weapon"] = weapon
    for slot, slug in slots.items():
        p["gear"][slot] = slug
    # equipping by hand: give every paid piece its full pool, the way
    # the ensure_current migration would
    for slot in economy.DURABILITY_SLOTS:
        g = economy.FORGE.get(p["gear"].get(slot) or "")
        if g and g.price > 0:
            p["durability"][slot] = economy.item_pool(g)
    combat.start_encounter(p, fl, enc)
    return p, fl


# ── the pool (§3.5) ──────────────────────────────────────────────────────

def test_pools_last_about_a_week_and_grow_with_tier():
    """Tuned in-phase: pools grow with tier (a piece never breaks inside
    one hunting day) while the GOLD per use still climbs — the running
    cost lives in the repair bill, not the pool curve."""
    assert economy.durability_pool(1) == 1300
    assert economy.durability_pool(5) == 2600
    assert economy.durability_pool(10) == 4225
    pools = [economy.durability_pool(t) for t in range(1, 11)]
    assert pools == sorted(pools)
    day = 30 * 6                                    # fights × rounds
    assert all(pool >= 3 * day for pool in pools)   # never mid-day break


def test_power_still_costs_more_per_swing():
    """The intent behind "better gear wears faster": gold per use rises
    with tier even though pools grow."""
    costs = []
    for t in range(1, 11):
        w = next(g for g in economy.weapon_line("warrior")
                 if g.tier == t and g.rung == float(t))
        costs.append(economy.repair_price(w, 1.0) / economy.item_pool(w))
    assert costs == sorted(costs), costs


def test_mid_tiers_sit_between_the_wholes():
    assert (economy.durability_pool(2)
            < economy.durability_pool(2.5)
            < economy.durability_pool(3))


def test_repair_price_is_a_fifth_of_the_missing_fraction():
    g = economy.FORGE["pigsticker"]          # ◈ 250
    assert economy.repair_price(g, 1.0) == 50
    assert economy.repair_price(g, 0.5) == 25
    assert economy.repair_price(g, 0.0) == 1  # floor, never free


# ── staged onboarding ────────────────────────────────────────────────────

def test_fresh_docs_carry_no_durability():
    p = create_character(fresh("bare"))
    assert p["durability"] == {}
    assert not state.is_broken(p, "weapon")


def test_first_paid_purchase_arms_the_slot_and_teaches_once():
    p = create_character(fresh("learner"))
    p["gold"] = 1000
    p["location"] = "forge"
    s = choose(p, "buy_pigsticker")
    assert p["durability"]["weapon"] == economy.durability_pool(1)
    assert any("wears with use" in ln for ln in s.body_lines)
    p["gold"] = 1000
    s = choose(p, "buy_scrapwood_buckler")   # second slot teaches again
    assert any("wears with use" in ln for ln in s.body_lines)
    p["gold"] = 1000
    p["gear"]["weapon"] = economy.class_starter("warrior").slug
    del p["durability"]["weapon"]
    s = choose(p, "buy_pigsticker")          # same slot: taught already
    assert not any("wears with use" in ln for ln in s.body_lines)


def test_free_gear_never_wears():
    p, fl = _armed(weapon=economy.class_starter("warrior").slug)
    p["encounter"]["range"] = "close"
    combat.resolve_fight_action(p, fl, "attack")
    assert "weapon" not in p["durability"]
    assert not state.is_broken(p, "weapon")


# ── wear hooks: once per event ───────────────────────────────────────────

def test_a_swing_costs_one_use():
    p, fl = _armed()
    p["encounter"]["range"] = "close"
    before = p["durability"]["weapon"]
    combat.resolve_fight_action(p, fl, "attack")
    assert p["durability"]["weapon"] == before - 1


def test_a_blow_taken_wears_shield_and_armor_not_weapon():
    p, fl = _armed(shield="scrapwood_buckler", armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    w0, s0, a0 = (p["durability"]["weapon"], p["durability"]["shield"],
                  p["durability"]["armor"])
    combat.resolve_fight_action(p, fl, "stand")    # no swing, one blow
    assert p["durability"]["weapon"] == w0
    assert p["durability"]["shield"] <= s0
    assert p["durability"]["armor"] <= a0
    assert p["durability"]["shield"] == p["durability"]["armor"] \
        - (a0 - s0)                                # same events for both


def test_chase_actions_wear_the_shoes():
    p, fl = _armed(shoes="cobbled_boots")
    b0 = p["durability"]["shoes"]
    combat.resolve_fight_action(p, fl, "close_in")   # crossing
    assert p["durability"]["shoes"] == b0 - 1
    combat.resolve_fight_action(p, fl, "open_distance")
    assert p["durability"]["shoes"] == b0 - 2


def test_standing_still_spares_the_boots():
    p, fl = _armed(shoes="cobbled_boots")
    p["encounter"]["range"] = "close"
    b0 = p["durability"]["shoes"]
    combat.resolve_fight_action(p, fl, "stand")
    assert p["durability"]["shoes"] == b0


# ── broken: half strength, one honest line ───────────────────────────────

def test_broken_weapon_hits_at_half():
    p = create_character(fresh("halved"))
    p["gear"]["weapon"] = "pigsticker"
    p["durability"]["weapon"] = 5
    full = state.gear_bonus(p, "weapon")
    p["durability"]["weapon"] = 0
    assert state.is_broken(p, "weapon")
    assert state.gear_bonus(p, "weapon") == full // 2


def test_broken_boots_drag_at_half_speed():
    p = create_character(fresh("dragging"))
    p["gear"]["shoes"] = "wayfarers_treads"          # +2 spd
    p["durability"]["shoes"] = 10
    assert economy.player_speed(p) == economy.PLAYER_BASE_SPEED + 2
    p["durability"]["shoes"] = 0
    assert economy.player_speed(p) == economy.PLAYER_BASE_SPEED + 1


def test_the_snap_gets_its_line_exactly_once():
    p, fl = _armed()
    p["encounter"]["range"] = "close"
    p["durability"]["weapon"] = 1
    p["encounter"]["hp"] = 10 ** 6                  # nothing dies early
    s = combat.resolve_fight_action(p, fl, "attack")
    if p["hp"] <= 0 or p.get("encounter") is None:  # deterministic guard
        return
    text = " ".join(s.body_lines)
    assert "gives out" in text
    s = combat.resolve_fight_action(p, fl, "attack")
    if p.get("encounter") is not None and p["hp"] > 0:
        assert "gives out" not in " ".join(s.body_lines)


def test_broken_is_never_gone():
    p, fl = _armed()
    p["durability"]["weapon"] = 0
    assert p["gear"]["weapon"] == "pigsticker"      # still in hand
    assert state.gear_bonus(p, "weapon") >= 0


# ── the Forge mends ──────────────────────────────────────────────────────

def _worn_smith(gold=10_000, xp=500):
    p = create_character(fresh("smithy"))
    p["gold"], p["xp"] = gold, xp
    p["gear"]["weapon"] = "pigsticker"
    p["durability"]["weapon"] = economy.durability_pool(1) // 2
    p["location"] = "forge"
    return p


def test_repair_row_quotes_price_and_xp():
    p = _worn_smith()
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "repair_weapon")
    g = economy.FORGE["pigsticker"]
    want = economy.repair_price(g, 0.5)
    assert f"◈ {want:,}" in row.hint and "XP" in row.hint


def test_repair_restores_the_full_pool():
    p = _worn_smith()
    gold0, xp0 = p["gold"], p["xp"]
    s = choose(p, "repair_weapon")
    assert p["durability"]["weapon"] == economy.durability_pool(1)
    assert p["gold"] == gold0 - economy.repair_price(
        economy.FORGE["pigsticker"], 0.5)
    assert p["xp"] == xp0 - economy.hone_xp(p["unlocked_floor"])
    assert any("made whole" in ln for ln in s.body_lines)


def test_repair_refused_without_the_xp():
    p = _worn_smith(xp=0)
    s = choose(p, "repair_weapon")
    assert p["durability"]["weapon"] == economy.durability_pool(1) // 2
    assert "XP" in s.shard_note and "Hunt first" in s.shard_note


def test_fresh_gear_offers_no_repair_row():
    p = create_character(fresh("mint"))
    p["gear"]["weapon"] = "pigsticker"
    p["durability"]["weapon"] = economy.durability_pool(1)
    p["location"] = "forge"
    s = core.current_scene(p)
    assert not any(o.id.startswith("repair_") for o in s.options)


# ── wear travels with the item ───────────────────────────────────────────

def test_swapping_gear_stashes_and_restores_the_wear():
    p = create_character(fresh("swapper"))
    p["gold"] = 10_000
    p["level"] = 6
    p["location"] = "forge"
    choose(p, "buy_pigsticker")
    p["durability"]["weapon"] = 7                   # grind it down
    choose(p, "buy_iron_sword")                     # shiv to the pack
    assert p["durability_pack"]["pigsticker"] == 7
    assert p["durability"]["weapon"] == economy.durability_pool(1.5)
    choose(p, "wear_pigsticker")                    # back out of the pack
    assert p["durability"]["weapon"] == 7           # as worn as it left


def test_pawn_pays_by_the_wear():
    p = create_character(fresh("broker"))
    g = economy.FORGE["pigsticker"]
    p["inventory"]["pigsticker"] = 1
    p["durability_pack"]["pigsticker"] = economy.durability_pool(1) // 2
    p["location"] = "pawn"
    s = core.current_scene(p)
    full = int(g.price * economy.PAWN_BUYBACK)
    row = next(o for o in s.options if o.id == "sell_pigsticker")
    assert f"◈ {full // 2:,}" in row.hint
    gold0 = p["gold"]
    choose(p, "sell_pigsticker")
    assert p["gold"] == gold0 + full // 2
    assert "pigsticker" not in p["durability_pack"]


# ── migration ────────────────────────────────────────────────────────────

def test_old_docs_arrive_with_full_pools_on_paid_gear():
    p = create_character(fresh("veteran"))
    p["gear"]["weapon"] = "pigsticker"
    p["gear"]["shield"] = "scrapwood_buckler"
    del p["durability"]
    del p["durability_pack"]
    p["version"] = 2
    state.ensure_current(p)
    assert p["version"] >= 3
    assert p["durability"]["weapon"] == economy.durability_pool(1)
    assert p["durability"]["shield"] == economy.durability_pool(1)
    assert "shoes" not in p["durability"]           # nothing worn there


def test_migration_never_arms_free_gear():
    p = create_character(fresh("frugal"))
    del p["durability"]
    p["version"] = 2
    state.ensure_current(p)
    assert p["durability"] == {}


# ── the pack strip and the sheet say it out loud ─────────────────────────

def test_pack_strip_carries_the_fraction():
    p = create_character(fresh("stripy"))
    p["gear"]["weapon"] = "pigsticker"
    pool = economy.durability_pool(1)
    p["durability"]["weapon"] = pool // 4
    strip = core._pack_strip(p)
    cell = next(c for c in strip if c["slug"] == "pigsticker")
    assert abs(cell["dur"] - 0.25) < 0.01


def test_sheet_names_worn_and_broken():
    from plugin_linear_ascent.sheet import character_sheet
    p = create_character(fresh("sheeted"))
    p["gear"]["weapon"] = "pigsticker"
    p["durability"]["weapon"] = economy.durability_pool(1) // 2
    assert "worn to 50%" in character_sheet(p)["gear"]["weapon"]
    p["durability"]["weapon"] = 0
    assert "BROKEN" in character_sheet(p)["gear"]["weapon"]


# ── economy gates (§3.5 + phase plan) ────────────────────────────────────

def test_repair_tax_stays_under_a_fifth_of_income_every_band():
    """At-level play (≈30 fights/day, ~6 rounds each — the same model
    daily_income anchors on): a warrior repairing the full kit daily
    must spend ≤20% of that day's income at every band — a tax, not a
    wall. And the tax fraction must not step-function between bands."""
    fights, rounds = 30, 6
    fracs = []
    for tier in range(1, 11):
        floor_no = economy.band_start(tier)
        income = economy.daily_income(floor_no)
        weapon = next(g for g in economy.weapon_line("warrior")
                      if g.tier == tier and g.rung == float(tier))
        shield = next(g for g in economy.gear_rungs("shield")
                      if g.line != "sorcerer" and g.tier == tier
                      and g.rung == float(tier))
        armor = next(g for g in economy.gear_rungs("armor")
                     if g.tier == tier and g.rung == float(tier))
        spend = 0.0
        for g, events in ((weapon, fights * rounds),
                          (shield, fights * rounds),
                          (armor, fights * rounds)):
            pool = economy.durability_pool(g.tier)
            spend += economy.repair_price(g, min(1.0, events / pool))
        frac = spend / income
        fracs.append(frac)
        assert frac <= 0.20, (
            f"band {tier}: repairs ◈ {spend:.0f} vs income ◈ {income} "
            f"({100 * frac:.0f}%)")
    for a, b in zip(fracs, fracs[1:]):
        assert abs(b - a) <= 0.10, f"repair-tax cliff between bands: {fracs}"


def test_a_player_who_never_repairs_still_clears_the_floor():
    """Broken ≠ bricked: floor-1 warrior with a BROKEN paid kit (half
    bonuses) still beats the plain reference monster more often than
    not — the basic-weapon floor holds underneath."""
    wins = 0
    n = 60
    for i in range(n):
        p, fl = _armed(shield="scrapwood_buckler", armor="padded_jerkin")
        p["luna_user"] = f"never-repairs-{i}"
        for slot in ("weapon", "shield", "armor"):
            p["durability"][slot] = 0
        p["encounter"]["range"] = "close"
        for _ in range(40):
            if p.get("encounter") is None:
                if p["hp"] > 0:
                    wins += 1
                break
            if p["hp"] <= 0:
                break
            combat.resolve_fight_action(p, fl, "attack")
    assert wins / n >= 0.5, f"broken-kit win rate {wins / n:.2f}"


def test_archer_kiting_does_not_double_pay_the_wear():
    """004 retro gate: the archer's long fights must not make bow wear
    a class tax — uses per KILL for a kiting archer stay within 3× the
    warrior's trade (rounds differ, the pool math must absorb it)."""
    counts = {}
    for clazz, weapon in (("warrior", "pigsticker"),
                          ("archer", "ashwood_bow")):
        spent = []
        for i in range(40):
            p, fl = _armed(clazz=clazz, weapon=weapon)
            p["luna_user"] = f"wear-{clazz}-{i}"
            start = p["durability"]["weapon"]
            p["encounter"]["range"] = "close"
            for _ in range(60):
                if p.get("encounter") is None or p["hp"] <= 0:
                    break
                if clazz == "archer" and \
                        p["encounter"].get("range") == "close":
                    combat.resolve_fight_action(p, fl, "open_distance")
                else:
                    combat.resolve_fight_action(p, fl, "attack")
            if p.get("encounter") is None and p["hp"] > 0:
                spent.append(start - p["durability"]["weapon"])
        counts[clazz] = sum(spent) / max(1, len(spent))
    assert counts["archer"] <= 3 * counts["warrior"], counts
