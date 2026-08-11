"""017 phase 004 — shops & gear: rungs, lines, shoes, Arcanum (plan §3.1–3.4).

Catalog invariants (the 60-row table is GENERATED — these pin the
generator), the level gates, the shoes→speed feed, both shop scenes,
and the economy sim gates: days-to-afford stays on the 6→24 line with
mid rungs included. 048: the off-class system is dead — every rack
sells every line at list price; the School rank decides the bite.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Shopper"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
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


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text=text)


# ── the generated catalog (§3.1) ─────────────────────────────────────────

# 025 §4: band 1 sells a rung per level (1.0 … 1.9), then the pre-025
# ladder resumes — whole tiers with one mid between them.
LADDER = [1 + i / 10 for i in range(10)] + [2 + 0.5 * i for i in range(17)]


def test_every_weapon_line_climbs_the_whole_ladder():
    for line in ("warrior", "archer", "sorcerer"):
        rungs = [g.rung for g in economy.weapon_line(line)]
        assert [round(r, 1) for r in rungs] == [round(r, 1) for r in LADDER], \
            line


def test_lines_mirror_the_warrior_numbers_rung_for_rung():
    war = {g.rung: g for g in economy.weapon_line("warrior")}
    for line in ("archer", "sorcerer"):
        for g in economy.weapon_line(line):
            ref = war[g.rung]
            assert (g.bonus, g.price) == (ref.bonus, ref.price), g.slug


def test_mid_rungs_are_midpoint_bonus_and_geometric_price():
    war = {round(g.rung, 1): g for g in economy.weapon_line("warrior")}
    for t in range(1, 10):
        lo, mid, hi = war[float(t)], war[t + 0.5], war[float(t + 1)]
        # 046: the band is exponential, so the honest midpoint is
        # geometric — arithmetic would overshoot the curve
        assert mid.bonus == economy._gmean_bonus(lo.bonus, hi.bonus), \
            mid.slug
        # 047: tier 1's weapon sticker is discounted; the ladder is
        # priced off the full anchor, so the law reads through it
        lo_price = (round(lo.price / economy._EARLY_WEAPON_DISCOUNT)
                    if t == 1 else lo.price)
        assert mid.price == round((lo_price * hi.price) ** 0.5 / 10) * 10
        assert lo.price < mid.price < hi.price, mid.slug


def test_band_ones_new_rungs_did_not_move_the_old_ones():
    """025 §4 re-spaced band 1 by INTERPOLATING between the tier-1 and
    tier-2 rows — the old mid was defined as exactly that midpoint and
    that geometric mean, so every pre-025 piece keeps its numbers and the
    new rungs climb strictly between them."""
    for slot, line in (("weapon", "warrior"), ("shield", ""),
                       ("armor", "")):
        band = [g for g in economy.gear_rungs(slot, line) if g.rung < 2]
        assert len(band) == 10
        assert [g.bonus for g in band] == sorted({g.bonus for g in band})
        assert [g.price for g in band] == sorted({g.price for g in band})
        lo, hi = band[0], economy.gear_rungs(slot, line)[10]
        # 046: sub-rungs step geometrically (the 025 ladder, re-spaced)
        # 047: weapons read the law through the discounted tier-1 sticker
        lo_price = (round(lo.price / economy._EARLY_WEAPON_DISCOUNT)
                    if slot == "weapon" else lo.price)
        assert band[5].bonus == economy._step_bonus(lo.bonus, hi.bonus, 5)
        assert band[5].price == round((lo_price * hi.price) ** 0.5 / 10) * 10


def test_every_level_of_the_first_ten_sells_something():
    """The complaint, as a gate: 'I worked 3 days to advance a level only
    to find I have no more things to buy at level 4.'"""
    for clazz in ("warrior", "archer", "sorcerer"):
        for lvl in range(1, 11):
            new = [g for g in economy.FORGE.values()
                   if g.rung >= 1 and not g.style
                   and economy.rung_player_level_req(g) == lvl
                   and economy.rung_floor_req(g) == 0
                   and (not g.line or g.line == clazz)]
            assert new, f"{clazz} level {lvl} unlocks nothing"
            slots = {g.slot for g in new}
            assert {"weapon", "shield", "armor"} <= slots | {"shoes"}, \
                f"{clazz} level {lvl}: only {slots}"


def test_a_rung_is_a_choice_of_three_temperaments():
    plain = economy.FORGE["iron_sword"]
    keen, warded = economy.gear_styles(plain)
    assert (keen.style, warded.style) == ("keen", "warded")
    # keen buys power with upkeep; warded buys upkeep with gold
    assert keen.bonus > plain.bonus and keen.price > plain.price
    assert economy.item_pool(keen) < economy.item_pool(plain)
    assert warded.bonus == plain.bonus
    assert economy.item_pool(warded) > economy.item_pool(plain)
    # same rung, same gate — a style is never a queue
    for v in (keen, warded):
        assert v.rung == plain.rung and v.slot == plain.slot
        assert economy.rung_player_level_req(v) == \
            economy.rung_player_level_req(plain)
    # and the deep ladder is still plain steel only (025 stops at band 1)
    assert economy.gear_styles(economy.FORGE["dawnbreaker"]) == []


def test_plan_table_spot_checks():
    # the §3.1 example rows — bonuses re-anchored by the 022/002 retune
    # (weapon whole rungs 30T−22, mids the midpoint; prices unchanged)
    # 046: whole rungs ride the pillar (anchor × 1.3^(gate−1)), mids sit
    # at the geometric mean. 047: the first five floors' weapons open
    # 20% cheaper, the discount fading to nothing by rung 1.5.
    for slug, bonus, price in (("pigsticker", 8, 200),
                               ("iron_sword", 30, 930),
                               ("wolfbite", 110, 3_450),
                               ("bloodgroove_falchion", 409, 12_800),
                               ("ashwood_bow", 8, 200),
                               ("sinew_backed_bow", 30, 930),
                               ("tallowwood_staff", 8, 200),
                               ("coalglass_staff", 30, 930)):
        g = economy.FORGE[slug]
        assert (g.bonus, g.price) == (bonus, price), slug


def test_shields_and_armor_carry_the_mid_rungs_too():
    for slot in ("shield", "armor"):
        rungs = [g.rung for g in economy.gear_rungs(slot)]
        assert [round(r, 1) for r in rungs] == \
            [round(r, 1) for r in LADDER], slot


def test_focuses_mirror_shields_rung_for_rung():
    focuses = economy.gear_rungs("shield", "sorcerer")
    # 025 §4: band 1 sells the caster a guard per level too — above it
    # the Arcanum still stocks whole tiers only
    assert [round(g.rung, 1) for g in focuses] == \
        [round(1 + i / 10, 1) for i in range(10)] + \
        [float(t) for t in range(2, 11)]
    shields = {round(g.rung, 1): g for g in economy.gear_rungs("shield")}
    for f in focuses:
        ref = shields[round(f.rung, 1)]
        assert (f.bonus, f.price) == (ref.bonus, ref.price), f.slug


def test_shoes_ladder_matches_the_plan_table():
    # 022/002: gates past the cap become FLOOR gates — the last two
    # pairs ask for level 30 plus a frontier the tower has to earn
    rows = [(g.name, g.speed, g.price, economy.rung_player_level_req(g),
             economy.rung_floor_req(g))
            for g in economy.gear_rungs("shoes")]
    # 046: shoe prices ride the pillar from the Cobbled anchor
    assert rows == [
        ("Cobbled Boots", 1, 500, 3, 0),
        ("Wayfarer's Treads", 2, 4_080, 11, 0),
        ("Chasewind Boots", 3, 56_200, 21, 0),
        ("Skyline Striders", 4, 10_700_000, 30, 41),
        ("Stormstep Greaves", 5, 2_030_000_000, 30, 61),
    ]


def test_level_gates_whole_at_band_start_mids_five_later():
    # 022/002: the raw gate (band start / band start + 5) is a LEVEL up
    # to the cap and a FLOOR past it — one law, split across two axes
    war = {round(g.rung, 1): g for g in economy.weapon_line("warrior")}
    for t in range(1, 11):
        raw = economy.band_start(t)
        assert economy.rung_player_level_req(war[float(t)]) == \
            min(raw, economy.LEVEL_CAP)
        assert economy.rung_floor_req(war[float(t)]) == \
            (raw if raw > economy.LEVEL_CAP else 0)
        if t < 10:
            raw_mid = economy.band_start(t) + 5
            assert economy.rung_player_level_req(war[t + 0.5]) == \
                min(raw_mid, economy.LEVEL_CAP)
            assert economy.rung_floor_req(war[t + 0.5]) == \
                (raw_mid if raw_mid > economy.LEVEL_CAP else 0)


def test_shoe_speed_hook_is_filled():
    assert economy.SHOE_SPEED["cobbled_boots"] == 1
    assert economy.SHOE_SPEED["stormstep_greaves"] == 5
    p = fresh("hook")
    p["gear"]["shoes"] = "wayfarers_treads"
    assert economy.player_speed(p) == economy.PLAYER_BASE_SPEED + 2


# ── the Forge scene (048: one rack for every hand) ───────────────────────

def test_forge_racks_blades_and_bows_at_list_price():
    p = create_character(fresh("w-forge"), clazz="warrior")
    s = choose(p, "forge")
    ids = {o.id for o in s.options}
    assert "buy_pigsticker" in ids
    assert "buy_tallowwood_staff" not in ids   # staves live at the Arcanum
    assert "buy_ashwood_bow" in ids            # every line, list price
    bow = next(o for o in s.options if o.id == "buy_ashwood_bow")
    assert "off-class" not in bow.hint and "200" in bow.hint
    assert "buy_arrow_pack" not in ids         # the quiver died with 048


def test_next_locked_rung_is_always_visible():
    # 019: the rung you're saving for is a LOCKED ROW, not prose
    p = create_character(fresh("locked"), clazz="warrior")
    s = choose(p, "forge")
    # 025: the next rung is one LEVEL away in band 1, not five
    sword = next(o for o in s.options if o.id == "buy_notched_cleaver")
    assert sword.locked and "level 2" in sword.hint and "280" in sword.hint
    boots = next(o for o in s.options if o.id == "buy_cobbled_boots")
    assert boots.locked and "level 3" in boots.hint
    # at level 3 the boots unlock and the NEXT pair takes the lock
    p["level"] = 3
    s = core.current_scene(p)
    boots = next(o for o in s.options if o.id == "buy_cobbled_boots")
    assert not boots.locked
    treads = next(o for o in s.options if o.id == "buy_wayfarers_treads")
    assert treads.locked and "level 11" in treads.hint


def test_archer_sees_the_same_rack():
    p = create_character(fresh("a-forge"), clazz="archer")
    s = choose(p, "forge")
    ids = {o.id for o in s.options}
    assert "buy_ashwood_bow" in ids
    assert "buy_pigsticker" in ids            # every line, one rack
    assert "buy_arrow_pack" not in ids
    blade = next(o for o in s.options if o.id == "buy_pigsticker")
    assert "off-class" not in blade.hint and "200" in blade.hint


def test_sorcerer_forge_points_at_the_arcanum():
    p = create_character(fresh("s-forge"), clazz="sorcerer")
    p["level"] = 3                             # boots on the rack too
    s = choose(p, "forge")
    ids = {o.id for o in s.options}
    assert not any(i.startswith("buy_") and "staff" in i for i in ids)
    assert "buy_scrapwood_buckler" not in ids  # shields serve war+archer
    assert "buy_quilted_rags" in ids           # armor is shared (rung 1.2)
    assert "buy_cobbled_boots" in ids          # so are shoes
    # 031 §14: the card-wall Forge keeps its one pointer as a notice
    assert "Arcanum" in (s.shard_note or "")
    # a forced staff buy at the Forge is turned away, not sold
    p["gold"] = 10_000
    s = choose(p, "buy_tallowwood_staff")
    assert p["gear"]["weapon"] == "worn_staff"


def test_buying_shoes_fills_the_slot_and_the_speed():
    p = create_character(fresh("boots"), clazz="warrior")
    p["level"], p["gold"] = 3, 1_000
    choose(p, "forge")
    s = choose(p, "buy_cobbled_boots")
    assert p["gear"]["shoes"] == "cobbled_boots"
    assert p["gold"] == 500
    assert economy.player_speed(p) == economy.PLAYER_BASE_SPEED + 1
    assert any("laced on" in ln for ln in s.body_lines)


def test_weapons_sell_at_list_price_to_any_hand():
    p = create_character(fresh("triple"), clazz="warrior")
    p["gold"] = 1_000
    choose(p, "forge")
    choose(p, "buy_ashwood_bow")
    assert p["gear"]["weapon"] == "ashwood_bow"
    assert p["gold"] == 800                    # 200 list, no surcharge
    assert p["inventory"].get("rusted_sword") is None  # starter is free →
    # free gear goes to the scrap bin, not the pack


def test_wear_from_pack_swaps_for_free():
    p = create_character(fresh("swap"), clazz="warrior")
    p["gold"] = 10_000
    choose(p, "forge")
    choose(p, "buy_pigsticker")
    choose(p, "buy_ashwood_bow")               # sticker → pack
    assert p["inventory"]["pigsticker"] == 1
    gold = p["gold"]
    s = choose(p, "wear_pigsticker")
    assert p["gear"]["weapon"] == "pigsticker"
    assert p["inventory"].get("ashwood_bow") == 1
    assert p["gold"] == gold                   # free
    assert any("back on" in ln for ln in s.body_lines)


def test_any_weapon_hones():
    # 048: no off-class exclusion — the smith hones whatever you carry
    p = create_character(fresh("nohone"), clazz="warrior")
    p["gold"], p["unlocked_floor"] = 10_000, 3
    choose(p, "forge")
    choose(p, "buy_ashwood_bow")
    s = core.current_scene(p)
    assert any(o.id == "hone_weapon" for o in s.options)


# ── the Arcanum (§3.4) ───────────────────────────────────────────────────

def test_town_shows_the_locked_arcanum_row():
    p = create_character(fresh("town-row"))
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "arcanum")
    assert "🔒" in row.hint and str(economy.ARCANUM_LEVEL) in row.hint
    s = choose(p, "arcanum")
    assert p["location"] == "town"             # the door held
    assert f"level {economy.ARCANUM_LEVEL}" in s.shard_note


def test_arcanum_opens_at_level_six():
    p = create_character(fresh("door"), clazz="sorcerer")
    p["level"] = 6
    s = choose(p, "arcanum")
    assert p["location"] == "arcanum"
    ids = {o.id for o in s.options}
    # 025: level 6 racks band 1's rungs 1.4 and 1.5 — the ladder moved
    # under this door, the door itself did not
    assert "buy_gatewatch_baton" in ids
    assert "buy_coalglass_staff" in ids
    assert "buy_sootglass_bead" in ids          # the caster's guard


def test_sorcerer_buys_staff_and_focus_at_the_arcanum():
    p = create_character(fresh("caster"), clazz="sorcerer")
    p["level"], p["gold"] = economy.ARCANUM_LEVEL, 1_000
    choose(p, "arcanum")
    staff = economy.FORGE["ratbone_wand"]        # rung 1.2, level 3
    focus = economy.FORGE["ratbone_charm"]
    choose(p, f"buy_{staff.slug}")
    assert p["gear"]["weapon"] == staff.slug
    choose(p, f"buy_{focus.slug}")
    assert p["gear"]["shield"] == focus.slug
    assert p["gold"] == 1_000 - staff.price - focus.price


def test_focus_sold_to_any_hand():
    # 048: the class gate on focuses died with the classes
    p = create_character(fresh("no-focus"), clazz="warrior")
    p["level"], p["gold"] = 6, 10_000
    s = choose(p, "arcanum")
    ids = {o.id for o in s.options}
    assert "buy_sootglass_bead" in ids
    choose(p, "buy_sootglass_bead")
    assert p["gear"]["shield"] == "sootglass_bead"


# ── any weapon in any hand (048) ─────────────────────────────────────────

def _armed(clazz, weapon, floor_no=4, enc_id="glare_moth", arrows=0):
    if enc_id == "feral_boar":
        floor_no = 1                           # the plain reference target
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    p = create_character(fresh(f"oc-{clazz}-{weapon}-{arrows}"),
                         clazz=clazz)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    p["gear"]["weapon"] = weapon
    p["held"] = [weapon]
    if arrows:
        p["inventory"]["arrows"] = arrows
    combat.start_encounter(p, fl, enc)
    return p, fl


def test_a_bow_lets_the_warrior_reach_the_flyer():
    p, fl = _armed("warrior", "ashwood_bow", arrows=30)
    hp0 = p["encounter"]["hp"]
    for _ in range(6):
        if not p["encounter"]:
            break
        combat.resolve_fight_action(p, fl, "attack")
    assert p["encounter"] is None or p["encounter"]["hp"] < hp0


def test_bow_shots_never_burn_arrows():
    # 048: arrows died with the off-class system
    p, fl = _armed("archer", "ashwood_bow", enc_id="feral_boar")
    combat.resolve_fight_action(p, fl, "attack")
    assert "arrows" not in p["inventory"]


def test_treeline_shot_needs_a_bow_in_hand():
    p, fl = _armed("archer", "pigsticker", enc_id="feral_boar")
    s = combat.fight_scene(p, fl)
    assert not any(o.id == "treeline_shot" for o in s.options)


# ── shoes in the chase (002 retro: re-run the sims WITH shoes) ───────────

def test_treads_turn_the_fast_race_even_not_free():
    # Wayfarer's Treads (+2) against a fast (7) monster: the race is
    # even — kiting becomes POSSIBLE (p_open .5) but never safe, and the
    # monster still closes one round in four. A purchased answer, not a
    # free one.
    pspd = economy.PLAYER_BASE_SPEED + 2
    assert economy.p_open(pspd, economy.SPEED_FAST) == pytest.approx(0.50)
    assert economy.p_close(economy.SPEED_FAST, pspd) == pytest.approx(0.25)
    assert economy.p_flee(pspd, economy.SPEED_FAST) == pytest.approx(0.60)
    assert economy.dodge_pct(pspd, economy.SPEED_FAST) == 0


def test_boots_walk_away_from_the_slow_bulwark():
    pspd = economy.PLAYER_BASE_SPEED + 1
    assert economy.p_flee(pspd, economy.SPEED_SLOW) > 0.9
    assert economy.p_close(economy.SPEED_SLOW, pspd) == \
        pytest.approx(0.05)


# ── economy sim gates ────────────────────────────────────────────────────

def _set_price(rung: float) -> int:
    """Weapon + shield + armor at one rung (the band's shopping list)."""
    w = {g.rung: g for g in economy.weapon_line("warrior")}
    s = {g.rung: g for g in economy.gear_rungs("shield")}
    a = {g.rung: g for g in economy.gear_rungs("armor")}
    return w[rung].price + s[rung].price + a[rung].price


def test_days_to_afford_curve_is_smooth_and_bounded():
    """The days-in-tier line with mid rungs included: measured curve is
    ~2.4 days (band 2) rising smoothly to ~32 (band 10) for the full
    band spend (mid set + whole set). The gate pins the SHAPE: the mid
    is always the reachable half, the curve only rises, no adjacent
    band more than doubles, and the endpoints stay on the line."""
    prev_total = None
    for t in range(2, 11):
        income = economy.daily_income(economy.band_start(t) - 5)
        days_set = _set_price(float(t)) / income
        days_mid = _set_price(t - 0.5) / income
        assert days_mid < days_set, t          # reachable vs aspirational
        total = days_set + days_mid
        # 046: the climb-time law — a band's spend is a constant number
        # of floor-1-equivalent days; in real days it grows by the wedge
        # (×1.48 per band), which IS the exponential time investment
        norm = total / economy.pace_wedge(economy.band_start(t) - 5)
        assert 12 <= norm <= 16, (t, round(norm, 1))
        if prev_total is not None:
            assert total > prev_total, t       # saving never gets shorter
            assert total < prev_total * 2.2, t  # and never walls
        prev_total = total


def test_no_price_wall_between_adjacent_rungs():
    """Mid rungs exist to absorb the tier walls: with them in the
    ladder, no next-rung purchase costs more than ~3.6× the last."""
    for line in ("warrior", "archer", "sorcerer"):
        rungs = economy.weapon_line(line)
        for lo, hi in zip(rungs, rungs[1:]):
            # 046: tier-to-tier is 1.3^10 — a half-band step is its
            # square root, ~3.71
            assert hi.price / lo.price <= 3.8, (line, hi.slug)


def test_migrated_docs_grow_the_shoes_slot():
    p = fresh("old-doc")
    del p["gear"]["shoes"]
    state.ensure_current(p)
    assert p["gear"]["shoes"] is None


def test_weapon_icons_follow_the_line():
    """Dojo catch: a bow drawn as a sword misreads the whole rack.
    Weapons resolve to their line's silhouette; focuses to the diamond."""
    from plugin_linear_ascent import icons
    assert icons.icon_key("pigsticker", "weapon") == "weapon"
    assert icons.icon_key("ashwood_bow", "weapon") == "bow"
    assert icons.icon_key("basic_bow", "weapon") == "bow"
    assert icons.icon_key("tallowwood_staff", "weapon") == "staff"
    assert icons.icon_key("worn_staff", "weapon") == "staff"
    assert icons.icon_key("scrapwood_buckler", "shield") == "shield"
    focus = economy.gear_rungs("shield", line="sorcerer")[0]
    assert icons.icon_key(focus.slug, "shield") == "focus"
    for key in ("bow", "staff", "focus"):
        assert icons.icon_data_url(key).startswith("data:image/svg+xml")
