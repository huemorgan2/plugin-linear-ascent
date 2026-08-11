"""034 §1 — the shield spends itself on what it stops.

A shield used to tick one use per blow whether it turned 1 damage or 90:
the card narrated the mitigation by name and the bench billed a flat
point. Now wear scales with the damage actually turned, priced against
the shield's own rating so the pace holds at every tier.
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

def test_an_evenly_met_blow_costs_the_rate():
    """`blocked` sits at DEF/2 on an ordinary hit — that is the blow the
    rate is defined against."""
    for total_def in (18, 60, 176):
        assert economy.shield_wear(total_def // 2, 20, total_def) \
            == economy.SHIELD_WEAR_RATE


def test_wear_tracks_the_damage_turned():
    """Twice the block, twice the bill — that is the whole complaint."""
    even = economy.shield_wear(60, 60, 120)      # DEF/2 — the even blow
    assert even == economy.SHIELD_WEAR_RATE
    assert economy.shield_wear(120, 60, 120) == 2 * even
    assert economy.shield_wear(180, 60, 120) == 3 * even


def test_a_blow_that_chips_straight_through_still_costs_one():
    assert economy.shield_wear(0, 30, 120) == 1
    assert economy.shield_wear(1, 30, 120) == 1


def _even_blow_wear(tier: int) -> int:
    shield = next(g for g in economy.gear_rungs("shield")
                  if g.line != "sorcerer" and g.tier == tier
                  and g.rung == float(tier))
    armor = next(g for g in economy.gear_rungs("armor")
                 if g.tier == tier and g.rung == float(tier))
    level = min(economy.band_start(tier), economy.LEVEL_CAP)
    total_def = economy.player_def(level, shield.bonus, armor.bonus)
    return economy.shield_wear(total_def // 2, shield.bonus, total_def)


def test_an_even_blow_costs_the_same_at_every_tier():
    """The trap this formula exists to avoid: `blocked` grows with DEF,
    so naive proportional wear would bill a tier-10 shield 20 uses a
    blow against a tier-1 shield's 2. Pricing the block against the
    shield's own rating flattens it — the pool curve is then free to do
    what 017 tuned it to do (better gear lasts longer)."""
    per_blow = [_even_blow_wear(t) for t in range(1, 11)]
    assert per_blow == [economy.SHIELD_WEAR_RATE] * 10, per_blow


def test_better_shields_still_last_longer():
    """017's pool curve survives: the wear rate is flat, so the 25%
    a tier the pool grows lands straight in the piece's life."""
    lives = [economy.item_pool(
        next(g for g in economy.gear_rungs("shield")
             if g.line != "sorcerer" and g.tier == t and g.rung == float(t))
    ) / _even_blow_wear(t) for t in range(1, 11)]
    assert lives == sorted(lives)


def test_a_fresh_buckler_lasts_days_not_a_week():
    """The user's complaint, pinned: a flat point per blow gave a
    tier-1 buckler ~1300 blows — about 216 fights, a week of play."""
    shield = economy.FORGE["scrapwood_buckler"]
    armor = economy.FORGE["padded_jerkin"]
    total_def = economy.player_def(3, shield.bonus, armor.bonus)
    per_blow = economy.shield_wear(total_def // 2, shield.bonus, total_def)
    fights = economy.item_pool(shield) / per_blow / 6
    assert 55 <= fights <= 90, f"{fights:.0f} fights per shield"


# ── in the fight ────────────────────────────────────────────────────────

def test_taking_a_blow_spends_more_than_one_use():
    # floor 3: the first un-softened floor (043.2 tutorial ATK division
    # leaves floor-1 blows too small to spend real tread)
    p, fl = _armed("blocker", floor_no=3, enc_id="sluice_wolf",
                   shield="scrapwood_buckler", armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    before = p["durability"]["shield"]
    combat.resolve_fight_action(p, fl, "stand")
    assert before - p["durability"]["shield"] >= 2


def test_shield_wall_pays_for_the_whole_blow(monkeypatch):
    """Nothing gets through because the shield stopped all of it — the
    one round that used to be free for the piece doing the work. The
    turned blow is pinned to the top roll: the law is about the wear
    rate, not today's seeded dice."""
    p, fl = _armed("waller", shield="scrapwood_buckler",
                   armor="padded_jerkin")
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    p["encounter"]["range"] = "close"
    before = p["durability"]["shield"]
    hp_before = p["hp"]
    combat.resolve_fight_action(p, fl, "shield_wall")
    assert p["hp"] == hp_before               # still no damage taken
    assert before - p["durability"]["shield"] >= 2


def test_a_monster_still_crossing_lands_nothing_to_stop():
    p, fl = _armed("waller-far", floor_no=2, enc_id="marsh_wolf",
                   shield="scrapwood_buckler", armor="padded_jerkin")
    p["encounter"]["range"] = "at_range"
    before = p["durability"]["shield"]
    combat.resolve_fight_action(p, fl, "shield_wall")
    assert p["durability"]["shield"] == before


def test_free_starter_gear_still_never_wears():
    p, fl = _armed("bare")
    p["encounter"]["range"] = "close"
    combat.resolve_fight_action(p, fl, "stand")
    assert "shield" not in p["durability"]


def test_a_broken_shield_stops_being_billed():
    p, fl = _armed("snapped", shield="scrapwood_buckler",
                   armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    p["durability"]["shield"] = 0
    combat.resolve_fight_action(p, fl, "stand")
    assert p["durability"]["shield"] == 0
