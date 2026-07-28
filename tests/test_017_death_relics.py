"""017 phase 006 — the death economy & the relic catalog (plan §3.6–3.8).

The law of the catalog: every relic does ONE dramatic thing and carries
ONE hard limitation, both said out loud before the coin moves. Death
gets its decided shape — a random bite of gold, every paid weapon rolls
the void — unless a Weapon Reincarnation Spell burns instead of you.
Faucets tighten so the bought answers matter.

002 retro honored: every fight helper pins `encounter["range"]`.
005 retro honored: the economy gate expresses every drain as a fraction
of daily_income per band, in the test, before anything ships.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Reaper"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    return p


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text=text)


def _fight(clazz="warrior", floor_no=1, enc_id="feral_boar",
           rng="close", user=None, **inv):
    """A leveled fighter mid-encounter, range pinned, pack stocked."""
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    p = create_character(fresh(user or f"r6-{clazz}-{enc_id}"), clazz=clazz)
    p["level"] = max(floor_no, 1)
    p["hp"] = 999                      # relic mechanics, not survival
    for slug, n in inv.items():
        p["inventory"][slug] = n
    combat.start_encounter(p, fl, enc)
    p["encounter"]["range"] = rng
    return p, fl


def act(p, fl, oid):
    return combat.resolve_fight_action(p, fl, oid)


# ── the catalog law (§3.7) ───────────────────────────────────────────────

def test_every_relic_names_its_effect_and_its_catch():
    for r in economy.RELICS.values():
        assert r.effect and r.limit, r.slug
        assert r.shop in ("forge", "arcanum", "apothecary"), r.slug
        assert r.di > 0 and r.floor >= 1 and r.count >= 1, r.slug


def test_prices_anchor_to_the_frontier_and_stay_pretty():
    for r in economy.RELICS.values():
        lo = economy.relic_price(r.slug, r.floor)
        hi = economy.relic_price(r.slug, 91)
        assert 0 < lo < hi, r.slug                # deeper frontier, dearer
        for n in (lo, hi):                        # two leading digits max
            digits = str(n)
            assert set(digits[2:]) <= {"0"} or n < 100, (r.slug, n)


def test_stock_filters_by_shop_floor_and_class():
    # floor 6 forge: quivers and oil, not the floor-11 tools
    slugs = {r.slug for r in economy.relic_stock("forge", 6, "warrior")}
    assert "poison_arrows" in slugs and "weapon_oil" in slugs
    assert "entangling_net" not in slugs
    # floor 11 forge, warrior: nets yes, archer-only piercing no
    slugs = {r.slug for r in economy.relic_stock("forge", 11, "warrior")}
    assert "entangling_net" in slugs and "piercing_arrows" not in slugs
    # the arcanum keeps sorcerer's work from other hands
    assert not any(r.clazz == "sorcerer"
                   for r in economy.relic_stock("arcanum", 31, "warrior"))
    assert any(r.slug == "strip_potion"
               for r in economy.relic_stock("arcanum", 6, "sorcerer"))


# ── shop wiring ──────────────────────────────────────────────────────────

def _shopper(clazz="warrior", floor=21, gold=10 ** 7, user=None):
    p = create_character(fresh(user or f"r6-shop-{clazz}-{floor}"),
                         clazz=clazz)
    p["unlocked_floor"] = floor
    p["level"] = floor
    p["gold"] = gold
    return p


def test_the_forge_shelf_says_the_law_out_loud():
    p = _shopper(floor=11)
    p["location"] = "forge"
    s = core.current_scene(p)
    body = " ".join(s.body_lines)
    assert "the relic shelf" in body
    r = economy.RELICS["weapon_oil"]
    assert r.effect in body and r.limit in body
    assert any(o.id == "buy_weapon_oil" for o in s.options)


def test_quivers_arrive_in_packs_of_five():
    p = _shopper(clazz="archer", floor=11)
    p["location"] = "forge"
    core.current_scene(p)
    choose(p, "buy_poison_arrows")
    assert p["inventory"]["poison_arrows"] == 5


def test_hold1_refuses_a_second_stone():
    p = _shopper(floor=21)
    p["location"] = "medlab"
    core.current_scene(p)
    choose(p, "buy_stone_of_undying")
    assert p["inventory"]["stone_of_undying"] == 1
    s = choose(p, "buy_stone_of_undying")
    assert p["inventory"]["stone_of_undying"] == 1
    assert "One, exactly" in s.shard_note


def test_class_lock_refuses_cross_class_work():
    p = _shopper(clazz="warrior", floor=21)
    p["level"] = 21
    p["location"] = "arcanum"
    s = core.current_scene(p)
    # the shelf never even shows sorcerer's work to a warrior…
    assert not any(o.id == "buy_strip_potion" for o in s.options)
    s = choose(p, "buy_strip_potion")
    assert "strip_potion" not in p["inventory"]
    # …and the deeper guard answers a forced buy in its own words
    s = core._relic_buy(p, "strip_potion", core._arcanum_scene)
    assert "strip_potion" not in p["inventory"]
    assert "not yours" in s.shard_note


# ── the broker's mood (§3.8) ─────────────────────────────────────────────

def test_pawn_rate_walks_25_to_55_by_the_world_day():
    rates = [economy.pawn_rate(d) for d in range(365)]
    assert all(0.25 <= r <= 0.55 for r in rates)
    assert max(rates) - min(rates) > 0.15          # it actually moves
    assert economy.pawn_rate(40) == economy.pawn_rate(40)  # same for all


def test_selling_a_relic_pays_the_days_rate():
    p = _shopper(floor=11, user="r6-broker")
    p["inventory"]["weapon_oil"] = 1
    p["location"] = "pawn"
    s = core.current_scene(p)
    assert any(o.id == "sell_weapon_oil" for o in s.options)
    offer = int(economy.relic_price("weapon_oil", 11)
                * economy.pawn_rate(state.world_day()))
    gold0 = p["gold"]
    choose(p, "sell_weapon_oil")
    assert p["gold"] == gold0 + offer
    assert "weapon_oil" not in p["inventory"]


# ── the quiver (§3.7) ────────────────────────────────────────────────────

def test_nocking_is_free_and_the_shot_spends_one_arrow():
    p, fl = _fight("archer", poison_arrows=5)
    hp0, php0 = p["encounter"]["hp"], p["hp"]
    act(p, fl, "nock_poison_arrows")
    assert p["encounter"]["nocked"] == "poison_arrows"
    assert p["inventory"]["poison_arrows"] == 5    # nocking spends nothing
    assert p["encounter"]["hp"] == hp0 and p["hp"] == php0
    act(p, fl, "attack")
    assert p["inventory"]["poison_arrows"] == 4


def test_poison_ticks_true_damage_and_never_stacks():
    p, fl = _fight("archer", floor_no=2, enc_id="shellback_tortoise",
                   poison_arrows=5)
    act(p, fl, "nock_poison_arrows")
    act(p, fl, "attack")
    e = p["encounter"]
    assert e["poison_left"] == economy.POISON_ROUNDS
    dose = e["poison_dmg"]
    hp1 = e["hp"]
    s = act(p, fl, "attack")                       # tick, then the shot
    assert e["poison_left"] == economy.POISON_ROUNDS - 1
    assert e["hp"] <= hp1 - dose                   # the venom's share
    assert "second dose is wasted" in " ".join(s.body_lines)
    assert e["poison_dmg"] == dose                 # no stacking, ever


def test_wardens_shrug_the_venom_off():
    p, fl = _fight("archer", poison_arrows=5)
    p["encounter"]["kind"] = "warden"
    act(p, fl, "nock_poison_arrows")
    s = act(p, fl, "attack")
    assert "poison_left" not in p["encounter"]
    assert "doesn't poison" in " ".join(s.body_lines)


def test_slowing_arrow_rewrites_the_chase_math():
    p, fl = _fight("archer", floor_no=5, enc_id="downs_courser",
                   rng="at_range", slowing_arrows=5)
    prof = combat._profile(p)
    assert prof["speed"] == economy.SPEED_FAST     # the kiting nightmare
    fast = economy.p_close(economy.SPEED_FAST, economy.SPEED_NORMAL)
    act(p, fl, "nock_slowing_arrows")
    act(p, fl, "attack")
    prof = combat._profile(p)
    assert prof["speed"] == economy.SPEED_FAST - economy.SLOW_ARROW_DELTA
    slowed = economy.p_close(prof["speed"], economy.SPEED_NORMAL)
    assert slowed < fast                           # its close pressure dies


def test_slowing_arrow_wasted_on_the_already_slow():
    p, fl = _fight("archer", slowing_arrows=5)     # boar: normal 5
    act(p, fl, "nock_slowing_arrows")
    act(p, fl, "attack")                           # 5 → 3 (slow floor)
    assert combat._profile(p)["speed"] == economy.SPEED_SLOW
    act(p, fl, "nock_slowing_arrows")
    s = act(p, fl, "attack")
    assert combat._profile(p)["speed"] == economy.SPEED_SLOW
    assert "changes nothing" in " ".join(s.body_lines)


def test_piercing_arrow_ignores_the_plate():
    def _dmg(nock):
        p, fl = _fight("archer", floor_no=10, enc_id="kings_guard",
                       user="r6-pierce", piercing_arrows=5)
        if nock:
            act(p, fl, "nock_piercing_arrows")
        hp0 = p["encounter"]["hp"]
        act(p, fl, "attack")
        return hp0 - p["encounter"]["hp"]
    # same user, same day, same roll counter → same raw roll; the only
    # difference is the plate, and the piercing shaft never meets it.
    assert _dmg(nock=True) > _dmg(nock=False)


def test_fire_arrow_bursts_half_again():
    def _dmg(nock):
        p, fl = _fight("archer", user="r6-fire", fire_arrows=5)
        if nock:
            act(p, fl, "nock_fire_arrows")
        hp0 = p["encounter"]["hp"]
        act(p, fl, "attack")
        return hp0 - p["encounter"]["hp"]
    assert _dmg(nock=True) > _dmg(nock=False)


# ── the tools (§3.7) ─────────────────────────────────────────────────────

def test_oil_buffs_ten_strikes_then_the_flask_is_gone():
    p, fl = _fight("warrior", floor_no=2, enc_id="shellback_tortoise",
                   weapon_oil=1)
    act(p, fl, "use_oil")
    assert p["oil"] == economy.OIL_STRIKES
    assert "weapon_oil" not in p["inventory"]
    act(p, fl, "attack")
    assert p["oil"] == economy.OIL_STRIKES - 1


def test_oil_never_touches_a_caster():
    p, fl = _fight("sorcerer", weapon_oil=1)
    s = combat.fight_scene(p, fl)
    assert not any(o.id == "use_oil" for o in s.options)


def test_the_net_spends_the_monsters_round():
    p, fl = _fight("warrior", entangling_net=3)
    act(p, fl, "throw_net")
    assert p["encounter"]["netted"]
    assert p["inventory"]["entangling_net"] == 2
    hp0 = p["hp"]
    s = act(p, fl, "attack")
    assert p["hp"] == hp0                          # its round went to cord
    assert "net" in " ".join(s.body_lines)
    assert not p["encounter"].get("netted")        # one round, one net


def test_the_net_blocks_the_close_too():
    p, fl = _fight("archer", rng="at_range", entangling_net=3)
    act(p, fl, "throw_net")
    line = combat._advance_chase(p)
    assert "net" in line
    assert p["encounter"]["range"] == "at_range"   # it closed no ground


def test_wardens_tear_through_nets():
    p, fl = _fight("warrior", entangling_net=3)
    p["encounter"]["kind"] = "warden"
    s = combat.fight_scene(p, fl)
    assert not any(o.id == "throw_net" for o in s.options)


def test_sky_hook_grounds_the_flyer_for_the_fight():
    p, fl = _fight("warrior", floor_no=4, enc_id="glare_moth", sky_hook=5)
    assert combat._profile(p)["flying"]
    act(p, fl, "use_hook")
    assert not combat._profile(p)["flying"]
    hp0 = p["encounter"]["hp"]
    act(p, fl, "attack")
    assert p["encounter"]["hp"] < hp0              # steel reaches it now


def test_strip_potion_dissolves_the_spellguard():
    p, fl = _fight("sorcerer", floor_no=3, enc_id="windfall_haunt",
                   strip_potion=1)
    assert combat._profile(p)["resist"] != "none"
    act(p, fl, "use_strip")
    assert combat._profile(p)["resist"] == "none"
    assert "strip_potion" not in p["inventory"]


def test_curse_scroll_halves_the_plate():
    p, fl = _fight("sorcerer", floor_no=10, enc_id="kings_guard",
                   curse_scroll=1)
    assert combat._profile(p)["armor"] == "med"
    act(p, fl, "use_curse")
    assert combat._profile(p)["armor"] == "low"


def test_polymorph_ends_the_fight_with_nothing():
    p, fl = _fight("sorcerer", polymorph_dust=1)
    gold0, xp0 = p["gold"], p["xp"]
    s = act(p, fl, "use_polymorph")
    assert p["encounter"] is None
    assert p["gold"] == gold0 and p["xp"] == xp0   # no loot, no XP
    assert "No loot, no XP" in " ".join(s.body_lines)


# ── the life-guards (§3.7) ───────────────────────────────────────────────

def test_the_veil_holds_until_your_first_strike():
    p, fl = _fight("warrior", veil_draught=1)
    act(p, fl, "use_veil")
    assert p["encounter"]["veiled"]
    hp0 = p["hp"]
    act(p, fl, "stand")                            # it swings at a ghost
    assert p["hp"] == hp0
    act(p, fl, "attack")                           # the strike breaks it
    assert not p["encounter"].get("veiled")


def test_the_apple_overshields_and_rots():
    p, fl = _fight("warrior", golden_apple=1)
    p["hp"] = state.max_hp(p)
    act(p, fl, "use_apple")
    shell = round(state.max_hp(p) * economy.APPLE_SHIELD_MULT)
    e = p["encounter"]
    assert 0 < e["apple_hp"] <= shell              # the counter bit some
    before = e["apple_hp"]
    act(p, fl, "stand")                            # a round passes
    assert e["apple_hp"] < before                  # 20% rots + the soak


def test_one_life_guard_per_fight():
    p, fl = _fight("warrior", veil_draught=1, golden_apple=1)
    act(p, fl, "use_veil")
    s = act(p, fl, "use_apple")
    assert "One life-guard per fight" in " ".join(s.body_lines)
    assert p["inventory"]["golden_apple"] == 1     # nothing was spent


def test_the_stone_cancels_the_death_itself():
    p, fl = _fight("warrior", stone_of_undying=1)
    p["level"] = 5
    p["daily"]["death_save"] = True                # the free save is spent
    p["hp"] = 0
    s = combat._death(p, fl)
    assert p["encounter"] is not None              # the fight goes on
    assert p["hp"] == max(1, round(state.max_hp(p)
                                   * economy.STONE_REVIVE_PCT))
    assert "stone_of_undying" not in p["inventory"]
    assert p["encounter"]["life_used"]
    assert "Stone of Undying" in " ".join(s.body_lines)


def test_the_stone_works_once_per_fight():
    p, fl = _fight("warrior", stone_of_undying=1)
    p["level"] = 5
    p["daily"]["death_save"] = True
    p["encounter"]["life_used"] = True             # a guard already spent
    p["hp"] = 0
    combat._death(p, fl)
    assert p["encounter"] is None                  # this death stood
    assert p["inventory"]["stone_of_undying"] == 1


# ── the severing word ────────────────────────────────────────────────────

def test_the_severing_word_simply_ends_it():
    p, fl = _fight("sorcerer", severing_word=1)
    s = act(p, fl, "use_severing")
    assert p["encounter"] is None
    assert "severing_word" not in p["inventory"]
    assert "simply over" in " ".join(s.body_lines)


def test_the_word_means_nothing_to_a_warden():
    p, fl = _fight("sorcerer", severing_word=1)
    p["encounter"]["kind"] = "warden"
    s = combat.fight_scene(p, fl)
    assert not any(o.id == "use_severing" for o in s.options)


# ── the death matrix (§3.6) ──────────────────────────────────────────────

def _doomed(user, level=5, gold=1000, bank=500, spells=0, **gear):
    """A climber at the moment of death, free save already spent."""
    p, fl = _fight("warrior", user=user)
    p["level"] = level
    p["gold"], p["bank"] = gold, bank
    p["daily"]["death_save"] = True
    if spells:
        p["inventory"]["reincarnation_spell"] = spells
    for slot, slug in gear.items():
        p["gear"][slot] = slug
        g = economy.FORGE[slug]
        if g.price > 0:
            p["durability"][slot] = economy.item_pool(g)
    p["hp"] = 0
    return p, fl


def test_the_free_save_comes_before_bought_things():
    p, fl = _fight("warrior", reincarnation_spell=1)
    p["level"] = 5
    p["hp"] = 0
    combat._death(p, fl)
    assert p["hp"] == 1                            # the shard caught you
    assert p["inventory"]["reincarnation_spell"] == 1


def test_mercy_still_holds_below_level_four():
    p, fl = _doomed("r6-mercy", level=3, weapon="pigsticker")
    combat._death(p, fl)
    assert p["gold"] == 500                        # half, exactly
    assert p["gear"]["weapon"] == "pigsticker"     # everything survives


def test_unprotected_death_bites_gold_wear_and_maybe_steel():
    p, fl = _doomed("r6-bitten", armor="padded_jerkin",
                    shield="scrapwood_buckler", weapon="pigsticker")
    pools = {s: p["durability"][s] for s in ("armor", "shield")}
    s = combat._death(p, fl)
    frac = 1 - p["gold"] / 1000
    assert economy.DEATH_GOLD_MIN <= frac <= economy.DEATH_GOLD_MAX
    assert p["bank"] == 500                        # the Vault keeps its word
    for slot in ("armor", "shield"):
        g = economy.FORGE[p["gear"][slot]]
        hit = round(economy.item_pool(g) * economy.DEATH_DURABILITY_HIT)
        assert p["durability"][slot] == pools[slot] - hit
    assert "Banked gold untouched" in " ".join(s.body_lines)


def test_each_paid_weapon_rolls_one_in_five():
    lost = 0
    trials = 300
    p, fl = _doomed("r6-roller", weapon="pigsticker")
    for _ in range(trials):
        p["gear"]["weapon"] = "pigsticker"
        p["gold"], p["hp"] = 1000, 0
        p["daily"]["death_save"] = True
        fl2 = schema.get_floor(1)
        enc = next(e for e in fl2.encounters if e.id == "feral_boar")
        combat.start_encounter(p, fl2, enc)
        p["encounter"]["range"] = "close"
        combat._death(p, fl)
        if p["gear"]["weapon"] != "pigsticker":
            lost += 1
    assert 0.12 <= lost / trials <= 0.28, lost / trials


def test_protected_death_loses_nothing_and_mends_everything():
    p, fl = _doomed("r6-shielded", spells=1, weapon="pigsticker",
                    armor="padded_jerkin")
    p["durability"]["weapon"] = 3                  # nearly spent
    p["durability"]["armor"] = 3
    p["inventory"]["ashwood_bow"] = 1              # a stashed paid weapon
    p["durability_pack"] = {"ashwood_bow": 2}
    s = combat._death(p, fl)
    assert p["gold"] == 1000                       # death took NOTHING
    assert p["gear"]["weapon"] == "pigsticker"
    assert "reincarnation_spell" not in p["inventory"]
    assert p["durability"]["weapon"] == economy.item_pool(
        economy.FORGE["pigsticker"])
    assert p["durability"]["armor"] == economy.item_pool(
        economy.FORGE["padded_jerkin"])
    assert p["durability_pack"]["ashwood_bow"] == economy.item_pool(
        economy.FORGE["ashwood_bow"])              # the stash mends too
    assert "nothing is lost" in " ".join(s.body_lines)


def test_spare_spells_leak_half_the_time():
    leaked = 0
    trials = 200
    p, fl = _doomed("r6-hoarder", weapon="pigsticker")
    for _ in range(trials):
        p["inventory"]["reincarnation_spell"] = 3
        p["gold"], p["hp"] = 1000, 0
        p["daily"]["death_save"] = True
        fl2 = schema.get_floor(1)
        enc = next(e for e in fl2.encounters if e.id == "feral_boar")
        combat.start_encounter(p, fl2, enc)
        p["encounter"]["range"] = "close"
        combat._death(p, fl)
        leaked += 2 - p["inventory"].get("reincarnation_spell", 0)
    # two spares each rolling 50% → expected one leak per death
    assert 0.35 <= leaked / (2 * trials) <= 0.65, leaked / (2 * trials)


# ── the faucet cuts (§3.8) ───────────────────────────────────────────────

def test_charm_faucets_cut_to_a_third_of_the_old_rate():
    assert economy.ALPHA_CHARM_PCT * 3 <= 30       # alpha was 30%
    assert economy.WARDEN_CHARM_PCT * 3 <= 40      # warden was 40%


# ── the economy gate (005 retro hard rule) ───────────────────────────────

def _kit(tier):
    w = next(g for g in economy.weapon_line("warrior")
             if g.tier == tier and g.rung == float(tier))
    sh = next(g for g in economy.gear_rungs("shield")
              if g.line != "sorcerer" and g.tier == tier
              and g.rung == float(tier))
    ar = next(g for g in economy.gear_rungs("armor")
              if g.tier == tier and g.rung == float(tier))
    return w, sh, ar


def _death_cost(tier):
    """Expected unprotected death at band `tier`, carrying a day's gold:
    E[gold] + E[weapon] + the guards' mending bill, in gold."""
    fl = economy.band_start(tier)
    di = economy.daily_income(fl)
    w, sh, ar = _kit(tier)
    gold = (economy.DEATH_GOLD_MIN + economy.DEATH_GOLD_MAX) / 2 * di
    weapon = economy.DEATH_WEAPON_LOSS * w.price
    guards = sum(economy.repair_price(g, economy.DEATH_DURABILITY_HIT)
                 for g in (sh, ar))
    return gold + weapon + guards, di


def test_death_stings_one_to_two_days_where_it_first_bites():
    """Bands 2–4 (the first unprotected deaths): a visible sting, never
    a wipe — and the cost climbs smoothly, no cliff between bands."""
    fracs = []
    for tier in range(2, 11):
        cost, di = _death_cost(tier)
        fracs.append(cost / di)
    for a, b in zip(fracs, fracs[1:]):
        assert 0 <= b - a <= 0.5, fracs            # scarier, gradually
    for frac in fracs[:3]:                         # bands 2–4
        assert 0.5 <= frac <= 2.0, fracs
    assert all(f <= 3.0 for f in fracs), fracs     # never a wipe, anywhere


def test_one_spell_is_the_buy_and_three_is_a_leak():
    for tier in (2, 3, 4, 6, 8, 10):
        cost, di = _death_cost(tier)
        fl = economy.band_start(tier)
        spell = economy.relic_price("reincarnation_spell", fl)
        # one held spell: it saves more than it costs — the intended buy
        assert spell < cost, (tier, spell, cost)
        # hoarding three: two spares × 50% leak ≈ one whole spell burned
        # per protected death, pure waste over banking the gold
        expected_leak = 2 * economy.SPARE_SPELL_LEAK * spell
        assert expected_leak >= 0.4 * di, (tier, expected_leak, di)


def test_the_combined_drain_leaves_room_to_climb():
    """Death + repairs + the insurance relic, summed per band, must stay
    under ~40% of a day's income — the 005 lesson, applied before
    shipping. Death rate modeled at one per four hunting days (the risk
    gate's worst honest read); the rational climber holds one spell, so
    the death line is min(unprotected, spell price)."""
    fights, rounds = 30, 6
    for tier in range(1, 11):
        fl = economy.band_start(tier)
        di = economy.daily_income(fl)
        w, sh, ar = _kit(tier)
        repair = sum(
            economy.repair_price(g, min(1.0, fights * rounds
                                        / economy.item_pool(g)))
            for g in (w, sh, ar))
        cost, _ = _death_cost(tier)
        spell = economy.relic_price("reincarnation_spell", fl)
        death_per_day = min(cost, spell) / 4
        drain = (repair + death_per_day) / di
        assert drain <= 0.40, (tier, drain)
