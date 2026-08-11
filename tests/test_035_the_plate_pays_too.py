"""035 — the plate is billed by the damage it turns.

034 put the shield on damage-priced wear and deliberately left armour at a
flat point per blow. The piece that meets EVERY blow was therefore the one
that never visibly moved: a player who turned a Warden's full swing and a
player who took a chip paid the plate the same single use. Now both guard
pieces are billed the same way, and the repair rate came down to keep the
daily tax where it was.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def _character(name, clazz="warrior"):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def _armed(name, floor_no=1, enc_id="feral_boar", clazz="warrior", **slots):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    p = _character(name, clazz=clazz)
    p["level"] = max(floor_no, 1)
    p["hp"] = economy.player_max_hp(p["level"])
    for slot, slug in slots.items():
        p["gear"][slot] = slug
    for slot in economy.DURABILITY_SLOTS:
        g = economy.FORGE.get(p["gear"].get(slot) or "")
        if g and g.price > 0:
            p["durability"][slot] = economy.item_pool(g)
    combat.start_encounter(p, fl, enc)
    return p, fl


# ── the formula ─────────────────────────────────────────────────────────

def test_an_evenly_met_blow_costs_the_plate_its_rate():
    for total_def in (18, 60, 176):
        assert economy.armor_wear(total_def // 2, 24, total_def) \
            == economy.ARMOR_WEAR_RATE


def test_the_plate_bills_by_the_damage_turned():
    """The report, pinned: a massive blow has to cost more than a graze."""
    graze = economy.armor_wear(20, 60, 120)
    heavy = economy.armor_wear(120, 60, 120)
    assert heavy > graze
    assert economy.armor_wear(180, 60, 120) == 3 * economy.ARMOR_WEAR_RATE


def test_a_blow_that_chips_straight_through_still_costs_one():
    """The floor 034 gave the shield holds for the plate — no free hits,
    and a light blow is still exactly the point it always was."""
    assert economy.armor_wear(0, 30, 120) == 1
    assert economy.armor_wear(1, 30, 120) == 1


def test_shield_and_plate_pay_the_same_for_the_same_blow():
    """The bonus cancels out of `guard_wear`, which is the honest reading:
    the two pieces met one blow together and split no bill."""
    for blocked in (10, 60, 120, 300):
        assert economy.shield_wear(blocked, 30, 120) \
            == economy.armor_wear(blocked, 55, 120)


def _even_blow_wear(tier: int) -> int:
    shield = next(g for g in economy.gear_rungs("shield")
                  if g.line != "sorcerer" and g.tier == tier
                  and g.rung == float(tier))
    armor = next(g for g in economy.gear_rungs("armor")
                 if g.tier == tier and g.rung == float(tier))
    level = min(economy.band_start(tier), economy.LEVEL_CAP)
    total_def = economy.player_def(level, shield.bonus, armor.bonus)
    return economy.armor_wear(total_def // 2, armor.bonus, total_def)


def test_an_even_blow_costs_the_plate_the_same_at_every_tier():
    """Same trap the shield formula dodges: `blocked` grows with DEF, so
    naive proportional wear would bill deep plate an order of magnitude
    more per blow than a jerkin."""
    per_blow = [_even_blow_wear(t) for t in range(1, 11)]
    assert per_blow == [economy.ARMOR_WEAR_RATE] * 10, per_blow


def test_better_plate_still_lasts_longer():
    lives = [economy.item_pool(
        next(g for g in economy.gear_rungs("armor")
             if g.tier == t and g.rung == float(t))
    ) / _even_blow_wear(t) for t in range(1, 11)]
    assert lives == sorted(lives)


def test_a_fresh_jerkin_lasts_days_not_a_week():
    shield = economy.FORGE["scrapwood_buckler"]
    armor = economy.FORGE["padded_jerkin"]
    total_def = economy.player_def(3, shield.bonus, armor.bonus)
    per_blow = economy.armor_wear(total_def // 2, armor.bonus, total_def)
    fights = economy.item_pool(armor) / per_blow / 6
    assert 55 <= fights <= 90, f"{fights:.0f} fights per jerkin"


# ── in the fight ────────────────────────────────────────────────────────

def test_taking_a_blow_spends_more_than_one_point_of_plate():
    p, fl = _armed("plated", shield="scrapwood_buckler",
                   armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    before = p["durability"]["armor"]
    combat.resolve_fight_action(p, fl, "stand")
    assert before - p["durability"]["armor"] >= 2


def test_plate_worn_by_the_blow_not_by_the_round():
    """Two blows of very different size against one doc: the bigger one
    costs more plate. Driven through the formula so the assertion does
    not ride the encounter RNG."""
    p, _ = _armed("comparer", shield="scrapwood_buckler",
                  armor="padded_jerkin")
    total_def = state.dfs(p)
    bonus = state.gear_bonus(p, "armor")
    small = economy.armor_wear(max(1, total_def // 8), bonus, total_def)
    large = economy.armor_wear(total_def, bonus, total_def)
    assert large > small


def test_free_starter_gear_still_never_wears():
    p, fl = _armed("bare-plate")
    p["encounter"]["range"] = "close"
    combat.resolve_fight_action(p, fl, "stand")
    assert "armor" not in p["durability"]


def test_a_broken_plate_stops_being_billed():
    p, fl = _armed("cracked", shield="scrapwood_buckler",
                   armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    p["durability"]["armor"] = 0
    combat.resolve_fight_action(p, fl, "stand")
    assert p["durability"]["armor"] == 0


def test_shield_wall_leaves_the_plate_alone():
    """The shield took the whole blow — the plate had nothing to turn."""
    p, fl = _armed("waller-plate", shield="scrapwood_buckler",
                   armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    before = p["durability"]["armor"]
    combat.resolve_fight_action(p, fl, "shield_wall")
    assert p["durability"]["armor"] == before


# ── the bench still bills a tax, not a wall ─────────────────────────────

def test_the_daily_repair_bill_did_not_grow_with_the_wear():
    """035's whole balancing act: tripling the plate's event count and
    cutting the repair rate to 13% leaves the worst band's daily tax on
    the 034 ceiling."""
    fights, rounds = 30, 6
    fracs = []
    for tier in range(1, 11):
        income = economy.daily_income(economy.band_start(tier))
        weapon = next(g for g in economy.weapon_line("warrior")
                      if g.tier == tier and g.rung == float(tier))
        shield = next(g for g in economy.gear_rungs("shield")
                      if g.line != "sorcerer" and g.tier == tier
                      and g.rung == float(tier))
        armor = next(g for g in economy.gear_rungs("armor")
                     if g.tier == tier and g.rung == float(tier))
        spend = sum(
            economy.repair_price(
                g, min(1.0, ev / economy.durability_pool(g.tier)))
            for g, ev in ((weapon, fights * rounds),
                          (shield, fights * rounds
                           * economy.SHIELD_WEAR_RATE),
                          (armor, fights * rounds
                           * economy.ARMOR_WEAR_RATE)))
        fracs.append(spend / income)
    assert max(fracs) <= 0.162, fracs
