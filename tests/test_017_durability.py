"""017 phase 005 — durability & repair (plan §3.5).

Power becomes a running cost: paid gear carries a use pool that shrinks
with tier, wear hooks fire once per event, broken means half strength
(never helpless), and the Forge mends for a fraction of price × the
missing fraction plus a few XP. Staged onboarding: a slot only starts
wearing after its first PAID purchase. The economy gate proves repairs
stay a tax, not a wall.
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


def _armed(clazz="warrior", weapon="scrap_dagger", floor_no=1,
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

def test_pools_grow_with_tier_and_survive_a_hunting_day():
    """Tuned in-phase: pools grow with tier while the GOLD per use still
    climbs — the running cost lives in the repair bill, not the pool
    curve. 035: the guard slots spend three uses on an evenly-met blow,
    so the mid-day-break gate has to be measured in THEIR events, not in
    rounds — a fresh jerkin still has to see the player home."""
    assert economy.durability_pool(1) == 1300
    assert economy.durability_pool(5) == 2600
    assert economy.durability_pool(10) == 4225
    pools = [economy.durability_pool(t) for t in range(1, 11)]
    assert pools == sorted(pools)
    day = 30 * 6                                    # fights × rounds
    # The shield left this guarantee on purpose: the 50×-block law caps
    # it at ~100 even blows (~16 fights), a mid-day break by design.
    guard_day = day * economy.ARMOR_WEAR_RATE
    assert all(pool > guard_day for pool in pools)  # never mid-day break


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


def test_repair_price_tracks_the_missing_fraction():
    """035: the rate came down 20% → 13% to pay for the plate joining the
    shield on damage-priced wear — same gold a day, a cheaper bench visit
    far more often."""
    g = economy.FORGE["scrap_dagger"]          # ◈ 200 (047 early discount)
    assert economy.REPAIR_PRICE_PCT == 0.13
    assert economy.repair_price(g, 1.0) == 26
    assert economy.repair_price(g, 0.5) == 13
    assert economy.repair_price(g, 0.0) == 1  # floor, never free


# ── staged onboarding ────────────────────────────────────────────────────

def test_fresh_docs_carry_only_the_basic_weapons_pool():
    # 049: the basic weapon wears from birth; the gate guard kit never
    p = create_character(fresh("bare"))
    assert p["durability"] == {
        "weapon": economy.item_pool(economy.CLASS_STARTERS["warrior"])}
    assert not state.is_broken(p, "weapon")
    assert state.durability_max(p, "shield") == 0
    assert state.durability_max(p, "armor") == 0


def test_first_paid_purchase_arms_the_slot_and_teaches_once():
    p = create_character(fresh("learner"))
    p["gold"] = 1000
    p["location"] = "forge"
    s = choose(p, "buy_scrap_dagger")
    assert p["durability"]["weapon"] == economy.durability_pool(1)
    assert any("wears with use" in ln for ln in s.body_lines)
    p["gold"] = 1000
    s = choose(p, "buy_scrapwood_buckler")   # second slot teaches again
    assert any("wears with use" in ln for ln in s.body_lines)
    p["gold"] = 1000
    p["gear"]["weapon"] = economy.CLASS_STARTERS["warrior"].slug
    del p["durability"]["weapon"]
    s = choose(p, "buy_scrap_dagger")          # same slot: taught already
    assert not any("wears with use" in ln for ln in s.body_lines)


def test_the_basic_weapon_wears_but_the_gate_kit_never_does():
    # 049: gate steel wears — a swing on the basic sword ticks its pool;
    # the gate-issue buckler and jerkin stay wear-free.
    p, fl = _armed(weapon=economy.CLASS_STARTERS["warrior"].slug)
    p["encounter"]["range"] = "close"
    before = p["durability"]["weapon"]
    combat.resolve_fight_action(p, fl, "attack")
    assert p["durability"]["weapon"] == before - 1
    assert not state.is_broken(p, "weapon")
    assert "shield" not in p["durability"]
    assert "armor" not in p["durability"]


# ── wear hooks: once per event ───────────────────────────────────────────

def test_a_swing_costs_one_use():
    p, fl = _armed()
    p["encounter"]["range"] = "close"
    before = p["durability"]["weapon"]
    combat.resolve_fight_action(p, fl, "attack")
    assert p["durability"]["weapon"] == before - 1


def test_a_blow_taken_wears_shield_and_armor_not_weapon():
    """035: both guard pieces meet the blow and both are billed by the
    damage they turned — the blade, which swung at nothing, is not."""
    p, fl = _armed(shield="scrapwood_buckler", armor="padded_jerkin")
    p["encounter"]["range"] = "close"
    w0, s0, a0 = (p["durability"]["weapon"], p["durability"]["shield"],
                  p["durability"]["armor"])
    combat.resolve_fight_action(p, fl, "stand")    # no swing, one blow
    assert p["durability"]["weapon"] == w0
    assert p["durability"]["shield"] < s0
    assert p["durability"]["armor"] < a0


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
    p["gear"]["weapon"] = "scrap_dagger"
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
    assert p["gear"]["weapon"] == "scrap_dagger"      # still in hand
    assert state.gear_bonus(p, "weapon") >= 0


# ── the Forge mends ──────────────────────────────────────────────────────

def _worn_smith(gold=10_000, xp=None):
    p = create_character(fresh("smithy"))
    # The bar is hard now (022): XP over the level's need is clamped on load,
    # so fill it exactly rather than piling on a number the model won't hold.
    p["gold"] = gold
    p["xp"] = economy.xp_need(1) if xp is None else xp
    p["gear"]["weapon"] = "scrap_dagger"
    p["held"] = ["scrap_dagger"]            # 069: held is the slot order
    p["durability"]["weapon"] = economy.durability_pool(1) // 2
    p["location"] = "forge"
    return p


def test_repair_row_quotes_price_and_xp():
    p = _worn_smith()
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "repair_weapon")
    g = economy.FORGE["scrap_dagger"]
    want = economy.repair_price(g, 0.5)
    assert f"◈ {want:,}" in row.hint and "XP" in row.hint


def test_repair_restores_the_full_pool():
    p = _worn_smith()
    gold0, xp0 = p["gold"], p["xp"]
    s = choose(p, "repair_weapon")
    assert p["durability"]["weapon"] == economy.durability_pool(1)
    assert p["gold"] == gold0 - economy.repair_price(
        economy.FORGE["scrap_dagger"], 0.5)
    assert p["xp"] == xp0 - economy.hone_xp(p["unlocked_floor"])
    assert any("made whole" in ln for ln in s.body_lines)


def test_repair_refused_without_the_xp():
    p = _worn_smith(xp=0)
    s = choose(p, "repair_weapon")
    assert p["durability"]["weapon"] == economy.durability_pool(1) // 2
    assert "XP" in s.shard_note and "Hunt first" in s.shard_note


def test_fresh_gear_offers_no_repair_row():
    p = create_character(fresh("mint"))
    p["gear"]["weapon"] = "scrap_dagger"
    p["durability"]["weapon"] = economy.durability_pool(1)
    p["location"] = "forge"
    s = core.current_scene(p)
    assert not any(o.id.startswith("repair_") for o in s.options)


# ── wear travels with the item ───────────────────────────────────────────

def test_swapping_gear_stashes_and_restores_the_wear():
    p = create_character(fresh("swapper"))
    p["gold"] = 10_000
    # 025: band 1 racks a rung per level, so the two rungs on the bench
    # at level 6 are 1.4 and 1.5 — the older steel is off the rack
    p["level"] = 6
    p["location"] = "forge"
    choose(p, "buy_gatewatch_gladius")
    p["durability"]["weapon"] = 7                   # grind it down
    choose(p, "buy_iron_sword")                     # the old one to the pack
    assert p["durability_pack"]["gatewatch_gladius"] == 7
    assert p["durability"]["weapon"] == economy.durability_pool(1.5)
    choose(p, "wear_gatewatch_gladius")             # back out of the pack
    assert p["durability"]["weapon"] == 7           # as worn as it left


def test_pawn_pays_by_the_wear():
    p = create_character(fresh("broker"))
    g = economy.FORGE["scrap_dagger"]
    p["inventory"]["scrap_dagger"] = 1
    p["durability_pack"]["scrap_dagger"] = economy.durability_pool(1) // 2
    p["location"] = "pawn"
    s = core.current_scene(p)
    # 006: the broker's rate moves day to day (25–55%) — wear still
    # halves whatever today's rate pays.
    rate = economy.pawn_rate(state.world_day())
    offer = int(g.price * rate * 0.5)
    full = int(g.price * rate)
    assert offer < full
    row = next(o for o in s.options if o.id == "sell_scrap_dagger")
    assert f"◈ {offer:,}" in row.hint
    gold0 = p["gold"]
    choose(p, "sell_scrap_dagger")
    assert p["gold"] == gold0 + offer
    assert "scrap_dagger" not in p["durability_pack"]


# ── migration ────────────────────────────────────────────────────────────

def test_old_docs_arrive_with_full_pools_on_paid_gear():
    p = create_character(fresh("veteran"))
    p["gear"]["weapon"] = "scrap_dagger"
    p["gear"]["shield"] = "scrapwood_buckler"
    del p["durability"]
    del p["durability_pack"]
    p["version"] = 2
    state.ensure_current(p)
    assert p["version"] >= 3
    assert p["durability"]["weapon"] == economy.durability_pool(1)
    assert p["durability"]["shield"] == economy.durability_pool(1)
    assert "shoes" not in p["durability"]           # nothing worn there


def test_migration_arms_only_the_basic_weapon_never_the_gate_kit():
    p = create_character(fresh("frugal"))
    del p["durability"]
    p["version"] = 2
    state.ensure_current(p)
    # 049: the basic weapon's pool comes back; the gate kit stays bare
    assert p["durability"] == {
        "weapon": economy.item_pool(economy.CLASS_STARTERS["warrior"])}


# ── the pack strip and the sheet say it out loud ─────────────────────────

def test_pack_strip_carries_the_fraction():
    p = create_character(fresh("stripy"))
    p["gear"]["weapon"] = "scrap_dagger"
    p["held"] = ["scrap_dagger"]            # 069: held is the slot order
    pool = economy.durability_pool(1)
    p["durability"]["weapon"] = pool // 4
    strip = core._slot_map(p)                 # 069: worn steel sits here
    cell = next(c for c in strip if c["slug"] == "scrap_dagger")
    assert abs(cell["dur"] - 0.25) < 0.01


def test_sheet_names_worn_and_broken():
    from plugin_linear_ascent.sheet import character_sheet
    p = create_character(fresh("sheeted"))
    p["gear"]["weapon"] = "scrap_dagger"
    p["durability"]["weapon"] = economy.durability_pool(1) // 2
    # 045 §3: the sheet says the wear in the unit the forge sells;
    # 048: the word is "durability", spelled out
    half = economy.durability_pool(1) // 2
    g = economy.FORGE["scrap_dagger"]
    want = (f"durability {economy.endurance(g, half):,}"
            f"/{economy.endurance(g):,}")
    assert want in character_sheet(p)["gear"]["weapon"]
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
        # 035: both guard pieces spend their rate on an evenly-met blow
        # where the blade still spends one per swing. The shield's rate
        # rides its own pool now (50×-block law) — a full day caps its
        # missing fraction at 1.0, one whole pool through the bench.
        for g, events in ((weapon, fights * rounds),
                          (shield, fights * rounds
                           * economy.shield_wear_rate(shield.rung)),
                          (armor, fights * rounds
                           * economy.ARMOR_WEAR_RATE)):
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
    for clazz, weapon in (("warrior", "scrap_dagger"),
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


# ── the shortcut home: mend rows wear icons, the pack walks you there ────
# Roy's ask: the Forge's mend rows carry the piece's own icon on the
# left, and the worn piece's pack popup offers "Go to the Forge and fix
# ◈ X + Y XP" — one tap walks you home to the anvil. Just the trip;
# never offered mid-fight.

def test_mend_rows_wear_their_gear_icon():
    from plugin_linear_ascent import render
    p = _worn_smith()
    p["inventory"]["repair_token"] = 1
    s = core.current_scene(p)
    assert s.option_art.get("repair_weapon") == "scrap_dagger"
    assert s.option_art.get("token_weapon") == "scrap_dagger"
    html = render.render_scene_fragment(s)
    row = html.split('data-opt="repair_weapon"', 1)[1].split("</button>")[0]
    # 057: a weapon's mend row wears the weapon's OWN face (gicon gw);
    # non-weapon gear keeps the plain shared glyph
    assert 'class="gicon' in row, "the mend row carries the gear icon"
    # the icon dresses the row where it stands — never promotes it to
    # a shop card up on the wall
    card = html.split('data-opt="repair_weapon"', 1)[0].rsplit("<button", 1)[1]
    assert "gcard" not in card


def test_pack_popup_offers_the_forge_trip():
    p = _worn_smith()
    p["location"] = "town"
    acts, why = core.pack_actions(p, "scrap_dagger")
    assert [o.id for o in acts] == ["forge_fix_weapon"]
    assert acts[0].label == "Go to the Forge and fix"
    g = economy.FORGE["scrap_dagger"]
    want = economy.repair_price(g, 0.5)
    assert f"◈ {want:,}" in acts[0].hint and "XP" in acts[0].hint


def test_forge_fix_walks_home_from_anywhere():
    p = _worn_smith()
    p["location"] = "gate_town"
    p["floor"] = 1
    s = choose(p, "forge_fix_weapon")
    assert p["location"] == "forge"
    assert "FORGE" in s.eyebrow
    assert any(o.id == "repair_weapon" for o in s.options)
    # the trip itself is free — the repair row takes the coin
    assert p["durability"]["weapon"] == economy.durability_pool(1) // 2


def test_forge_trip_never_offered_mid_fight():
    p, fl = _armed()
    p["durability"]["weapon"] = economy.durability_pool(1) // 2
    acts, why = core.pack_actions(p, "scrap_dagger")
    assert not any(o.id.startswith("forge_fix_") for o in acts)


def test_whole_gear_keeps_the_old_answer():
    p = _worn_smith()
    p["location"] = "town"
    p["durability"]["weapon"] = economy.durability_pool(1)
    acts, why = core.pack_actions(p, "scrap_dagger")
    assert acts == [] and "Already in your hand." == why


def test_forge_trip_refused_mid_fight():
    p, fl = _armed()
    p["durability"]["weapon"] = economy.durability_pool(1) // 2
    s = core.apply_choice(p, "forge_fix_weapon")
    assert p.get("encounter") is not None       # still in the fight
    assert p["location"] != "forge"
    assert "Not mid-fight" in s.shard_note


# ── Roy's ask: the weapon's tip leads with ATK and DURABILITY in color,
# and the ATK is the HONED number — a sharpened sword must read sharper.

def _weapon_cell_html(p):
    from plugin_linear_ascent import render
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    return html.split('data-slug="scrap_dagger"', 1)[0].rsplit("<button", 1)[1]


def test_honing_sharpens_the_tooltip_atk():
    p = _worn_smith()
    g = economy.FORGE["scrap_dagger"]
    base_cell = next(c for c in core._slot_map(p)
                     if c["slug"] == "scrap_dagger")
    assert base_cell["stat_val"] == g.bonus
    state.set_hone(p, "weapon", 3)
    honed = next(c for c in core._slot_map(p)
                 if c["slug"] == "scrap_dagger")
    want = economy.honed_bonus(g.bonus, 3)
    assert honed["stat_val"] == want and want > g.bonus
    cell = _weapon_cell_html(p)
    assert f"ATK {want}" in cell
    assert f"+{g.bonus}:" not in cell, "the tip still quotes fresh-forge base"


def test_weapon_tip_leads_with_the_two_colored_params():
    from plugin_linear_ascent import render
    p = _worn_smith()
    cell = _weapon_cell_html(p)
    assert "data-tiph=" in cell
    from html import unescape
    tiph = unescape(cell.split('data-tiph="', 1)[1].split('"', 1)[0])
    g = economy.FORGE["scrap_dagger"]
    left = economy.endurance(g, p["durability"]["weapon"])
    total = economy.endurance(g)
    # params first — ATK gold, DURABILITY green — then the prose
    assert tiph.index("ATK") < tiph.index("DURABILITY") < tiph.index("<br>")
    assert render.GOLD in tiph and render.OK in tiph
    assert f"DURABILITY {left:,}/{total:,}" in tiph
    # the shared tipbox knows how to draw it, on the card and the pane
    assert "data-tiph" in render.TIP_JS
    from plugin_linear_ascent import pane
    assert "data-tiph" in pane.render_pane()


def test_broken_weapon_tip_bleeds_red():
    from plugin_linear_ascent import render
    p = _worn_smith()
    p["durability"]["weapon"] = 0
    cell = _weapon_cell_html(p)
    from html import unescape
    tiph = unescape(cell.split('data-tiph="', 1)[1].split('"', 1)[0])
    assert f'color:{render.RED}">DURABILITY' in tiph


def test_armor_tip_leads_with_the_honed_def():
    from plugin_linear_ascent import render
    p = _worn_smith()
    p["gear"]["armor"] = "padded_jerkin"
    p["hone"]["armor"] = 2
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    cell = html.split('data-slug="padded_jerkin"', 1)[0].rsplit("<button", 1)[1]
    g = economy.FORGE["padded_jerkin"]
    want = economy.honed_bonus(g.bonus, 2)
    assert f"DEF {want}" in cell and "data-tiph=" in cell


def test_stacked_items_tip_leads_with_amount():
    from plugin_linear_ascent import render
    p = _worn_smith()
    p["inventory"]["medgel"] = 7
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    cell = html.split('data-slug="medgel"', 1)[0].rsplit("<button", 1)[1]
    assert "AMOUNT 7" in cell and "data-tiph=" in cell
    assert render.VIOLET in cell


def test_the_game_font_is_never_bold():
    from plugin_linear_ascent import render
    assert "b,strong{font-weight:normal;}" in render.SCENE_CSS
    p = _worn_smith()
    p["inventory"]["medgel"] = 2
    html = render.render_scene_fragment(core.current_scene(p))
    assert "<b>" not in html and "<b " not in html
