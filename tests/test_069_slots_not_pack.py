"""069 — slots, not pack. Phase 1: the slot map, hone per weapon, held
as slot order with a lead pointer, oil per weapon, v11 migration."""
import copy

try:
    from tests.conftest import make_character
except ImportError:  # pragma: no cover
    from conftest import make_character

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import combat, core, state


def _fresh(uid="069"):
    return state.new_player(uid)


def _choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def _warrior(uid="069-w", slots=3):
    p = _fresh(uid)
    make_character(p, clazz="warrior")
    p["slots"] = slots
    return p


# ── phase 1: doc shape ──────────────────────────────────────────────────

def test_new_doc_has_the_seven_slots_and_v11_keys():
    p = _fresh()
    assert p["version"] == 11
    assert p["gear"]["charm"] is None
    assert p["charm_slot"] is False
    assert p["quiver"] == {} and p["oil"] == {} and p["charm_dur"] == 0
    assert "weapon" not in p["hone"]
    assert [s.key for s in economy.SLOTS] == [
        "charm", "armor", "shoes", "shield", "weapon", "weapon2", "weapon3"]
    assert [s.key for s in economy.SLOTS if s.side == "left"] == \
        ["charm", "armor", "shoes"]


def test_v10_doc_migrates_hone_and_oil_onto_the_lead_weapon():
    p = _warrior("069-mig")
    lead = p["gear"]["weapon"]
    p["version"] = 10
    p["hone"] = {"weapon": 3, "shield": 1, "armor": 0}
    p["oil"] = 7
    del p["gear"]["charm"]
    del p["charm_slot"]
    state.ensure_current(p)
    assert p["version"] == 11
    assert state.hone_level(p, "weapon") == 3
    assert p["hone"].get(f"weapon:{lead}") == 3 and "weapon" not in p["hone"]
    assert p["hone"]["shield"] == 1
    assert state.oil_left(p) == 7 and p["oil"] == {lead: 7}
    assert p["gear"]["charm"] is None and p["charm_slot"] is False


def test_hone_rides_the_weapon_not_the_hand():
    p = _warrior("069-hone")
    sword = p["gear"]["weapon"]
    state.set_hone(p, "weapon", 3)
    honed = state.gear_bonus(p, "weapon")
    assert honed > economy.FORGE[sword].bonus
    p["inventory"]["basic_bow"] = 1
    _choose(p, "wear_basic_bow")
    assert p["gear"]["weapon"] == "basic_bow"
    # the bow leads unhoned — the sword's three steps stayed on the sword
    assert state.hone_level(p, "weapon") == 0
    assert state.gear_bonus(p, "weapon") == economy.FORGE["basic_bow"].bonus
    assert state.hone_level(p, "weapon", sword) == 3
    combat._promote_held(p, sword)
    assert state.hone_level(p, "weapon") == 3


def test_held_is_slot_order_and_the_lead_is_a_pointer():
    p = _warrior("069-order")
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    p["inventory"]["worn_staff"] = 1
    _choose(p, "wear_basic_bow")
    _choose(p, "wear_worn_staff")
    assert p["held"] == [sword, "basic_bow", "worn_staff"]
    assert p["gear"]["weapon"] == "worn_staff"
    combat._promote_held(p, sword)
    assert p["held"] == [sword, "basic_bow", "worn_staff"]   # unchanged
    assert p["gear"]["weapon"] == sword
    combat._promote_held(p, "basic_bow")
    assert p["held"] == [sword, "basic_bow", "worn_staff"]
    assert p["gear"]["weapon"] == "basic_bow"
    state.ensure_current(p)
    assert p["held"] == [sword, "basic_bow", "worn_staff"]
    assert p["gear"]["weapon"] == "basic_bow"
    assert economy.slot_item(p, "weapon") == sword
    assert economy.slot_item(p, "weapon2") == "basic_bow"
    assert economy.slot_item(p, "weapon3") == "worn_staff"


def test_wear_with_a_full_hand_swaps_the_lead_slot_in_place():
    p = _warrior("069-full", slots=2)
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    p["inventory"]["worn_staff"] = 1
    _choose(p, "wear_basic_bow")             # slot 2, leads
    assert p["held"] == [sword, "basic_bow"]
    _choose(p, "wear_worn_staff")            # hand full: replaces the lead
    assert p["held"] == [sword, "worn_staff"]
    assert p["gear"]["weapon"] == "worn_staff"
    assert p["inventory"].get("basic_bow") == 1


def test_forge_purchase_replaces_the_lead_slot_in_place():
    p = _warrior("069-buy")
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    _choose(p, "wear_basic_bow")             # [sword, bow], bow leads
    p["gold"] = 10 ** 6
    p["unlocked_floor"] = 30
    p["level"] = 30
    _choose(p, "town")
    _choose(p, "forge")
    s = core.current_scene(p)
    buy = next(o for o in s.options
               if o.id.startswith("buy_")
               and economy.FORGE.get(o.id.removeprefix("buy_"))
               and economy.FORGE[o.id.removeprefix("buy_")].slot == "weapon"
               and not o.locked)
    new = buy.id.removeprefix("buy_")
    _choose(p, buy.id)
    assert p["gear"]["weapon"] == new
    assert p["held"] == [sword, new]


def test_oil_is_per_weapon_and_stays_with_its_blade():
    p = _warrior("069-oil", slots=2)
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    p["oil"] = {sword: 4}
    assert state.oil_left(p) == 4
    _choose(p, "wear_basic_bow")
    assert state.oil_left(p) == 0            # the bow is dry
    assert state.oil_left(p, sword) == 4     # the sword keeps its slick
    combat._promote_held(p, sword)
    assert state.oil_left(p) == 4


def test_slot_locks_explain_themselves():
    p = _warrior("069-lock", slots=1)
    assert economy.slot_lock(p, "weapon") is None
    assert "second grip" in economy.slot_lock(p, "weapon2")
    assert f"level {economy.CARRY3_LEVEL}" in economy.slot_lock(p, "weapon3")
    assert f"level {economy.CHARM_SLOT_LEVEL}" in economy.slot_lock(p, "charm")
    p["slots"] = 3
    p["charm_slot"] = True
    assert all(economy.slot_lock(p, s.key) is None for s in economy.SLOTS)


def test_charm_kinds_are_the_pouch_things_only():
    ck = set(economy.CHARM_KINDS)
    assert {"luck_charm", "trollblood_tonic", "golden_apple", "veil_draught",
            "stone_of_undying", "reincarnation_spell", "entangling_net"} <= ck
    assert not (set(economy.QUIVER_SLUGS) & ck)
    assert "weapon_oil" not in ck
    assert economy.slot_for("luck_charm") == "charm"
    assert economy.slot_for("basic_bow") == "weapon"
    assert economy.slot_for("repair_token") is None


# ── phase 2: effects move to the slots ─────────────────────────────────

def _in_fight(uid="069-f", clazz="warrior", floor_no=1, enc_id="feral_boar"):
    from plugin_linear_ascent.content import schema
    p = _fresh(uid)
    make_character(p, clazz=clazz)
    p["level"] = max(floor_no, 1)
    p["hp"] = 999
    p["charm_slot"] = True
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    combat.start_encounter(p, fl, enc)
    p["encounter"]["range"] = "close"
    return p, fl


def _fight_ids(p, fl):
    return [o.id for o in combat.fight_scene(p, fl).options]


def test_a_full_pack_is_the_same_fight_as_an_empty_one():
    a, fl = _in_fight("069-inert-a")
    b, _ = _in_fight("069-inert-b")
    for slug in economy.CHARM_KINDS:
        b["inventory"][slug] = 1
    for slug in economy.QUIVER_SLUGS:
        b["inventory"][slug] = 5
    b["inventory"]["weapon_oil"] = 1
    assert _fight_ids(a, fl) == _fight_ids(b, fl)
    assert combat.alpha_drop_table(a) == combat.alpha_drop_table(b)
    assert combat.warden_drop_table(a) == combat.warden_drop_table(b)
    assert not combat.lucky(b)
    # death: a spell in the pack does not save you
    b["level"] = 5
    b["daily"]["death_save"] = True
    b["gold"] = 1000
    b["hp"] = 0
    combat._death(b, fl)
    assert b["gold"] < 1000
    assert b["inventory"]["reincarnation_spell"] == 1


def test_the_pouch_offers_itself_and_empties_on_use():
    p, fl = _in_fight("069-pouch")
    p["gear"]["charm"] = "trollblood_tonic"
    assert "drink_tonic" in _fight_ids(p, fl)
    p["hp"] = 5
    combat.resolve_fight_action(p, fl, "drink_tonic")
    assert p["gear"]["charm"] is None
    assert p["hp"] > 5
    assert "drink_tonic" not in _fight_ids(p, fl)


def test_the_medgel_heals_from_the_pouch_only():
    p, fl = _in_fight("069-medgel")
    p["inventory"]["medgel"] = 3
    assert "drink_medgel" not in _fight_ids(p, fl)
    acts, why = core.pack_actions(p, "medgel")
    assert acts == [] and why
    p["gear"]["charm"] = "medgel"
    assert "drink_medgel" in _fight_ids(p, fl)
    p["hp"] = 5
    combat.resolve_fight_action(p, fl, "drink_medgel")
    assert p["gear"]["charm"] is None
    assert p["inventory"]["medgel"] == 3           # the pack untouched
    assert p["hp"] > 5


def test_the_stone_in_the_pack_lets_you_die_the_stone_in_the_pouch_does_not():
    for where in ("pack", "pouch"):
        p, fl = _in_fight(f"069-stone-{where}")
        p["level"] = 5
        p["daily"]["death_save"] = True
        if where == "pack":
            p["inventory"]["stone_of_undying"] = 1
        else:
            p["gear"]["charm"] = "stone_of_undying"
        p["hp"] = 0
        combat._death(p, fl)
        if where == "pack":
            assert p["encounter"] is None
            assert p["inventory"]["stone_of_undying"] == 1
        else:
            assert p["encounter"] is not None
            assert p["gear"]["charm"] is None


def test_arrows_bind_on_the_road_and_the_quiver_spends_them():
    p, fl = _in_fight("069-quiver", clazz="archer")
    p["inventory"]["poison_arrows"] = 5
    acts, why = core.pack_actions(p, "poison_arrows")
    assert acts == [] and "before the fight" in why
    assert "nock_poison_arrows" not in _fight_ids(p, fl)
    s = core.apply_choice(p, "nock_poison_arrows")
    assert p["quiver"] == {} and p["inventory"]["poison_arrows"] == 5
    p["encounter"] = None
    acts, _ = core.pack_actions(p, "poison_arrows")
    assert [o.id for o in acts] == ["nock_poison_arrows"]
    core.apply_choice(p, "nock_poison_arrows")
    assert p["quiver"] == {"poison_arrows": 5}
    assert "poison_arrows" not in p["inventory"]
    from plugin_linear_ascent.content import schema
    enc = next(e for e in fl.encounters if e.id == "feral_boar")
    combat.start_encounter(p, fl, enc)
    p["encounter"]["range"] = "close"
    assert "nock_poison_arrows" in _fight_ids(p, fl)
    combat.resolve_fight_action(p, fl, "nock_poison_arrows")
    combat.resolve_fight_action(p, fl, "attack")
    assert p["quiver"]["poison_arrows"] == 4


def test_oil_is_slicked_from_the_pack_on_the_road_never_in_a_fight():
    p, fl = _in_fight("069-oilroad")
    p["inventory"]["weapon_oil"] = 1
    acts, why = core.pack_actions(p, "weapon_oil")
    assert acts == [] and why
    assert not any(o.startswith("use_") for o in _fight_ids(p, fl)
                   if "oil" in o)
    p["encounter"] = None
    acts, _ = core.pack_actions(p, "weapon_oil")
    assert [o.id for o in acts] == ["use_weapon_oil"]
    core.apply_choice(p, "use_weapon_oil")
    assert state.oil_left(p) == economy.OIL_STRIKES
    assert "weapon_oil" not in p["inventory"]
    acts, why = core.pack_actions(p, "weapon_oil")
    assert acts == []


def test_a_worn_luck_charm_fattens_the_rare_drop_and_wears_out():
    p, fl = _in_fight("069-luck")
    base = combat.rare_loot_pct(p, "alpha")
    p["gear"]["charm"] = "luck_charm"
    p["charm_dur"] = 2
    assert combat.lucky(p)
    assert combat.rare_loot_pct(p, "alpha") > base
    assert combat.rare_loot_pct(p, "warden") > combat.rare_loot_pct(
        _fresh("069-plain"), "warden")
    assert combat._wear_charm(p) == ""
    assert p["charm_dur"] == 1
    assert "crumbles" in combat._wear_charm(p)
    assert p["gear"]["charm"] is None and not combat.lucky(p)


def test_a_luck_charm_in_the_pack_is_not_luck():
    p = _fresh("069-luckpack")
    make_character(p, clazz="warrior")
    p["inventory"]["luck_charm"] = 3
    assert not combat.lucky(p)
    assert combat.rare_loot_pct(p, "alpha") == economy.ALPHA_CHARM_PCT


def test_wear_is_refused_mid_fight_with_a_reason():
    p, fl = _in_fight("069-wearfight")
    p["inventory"]["basic_bow"] = 1
    s = core.apply_choice(p, "wear_basic_bow")
    assert p["gear"]["weapon"] != "basic_bow"
    assert "mid-fight" in s.shard_note


# ── phase 3: the School sells the pouch ────────────────────────────────

def _at_school(uid, level, xp=10 ** 5, gold=10 ** 6):
    p = _warrior(uid)
    p["level"] = level
    p["xp"] = xp
    p["gold"] = gold
    p["charm_slot"] = False
    p["location"] = "school"
    return p


def test_the_pouch_row_is_locked_under_level_nine():
    p = _at_school("069-school8", 8)
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_charm_slot")
    assert row.locked and f"level {economy.CHARM_SLOT_LEVEL}" in row.hint
    s = _choose(p, "buy_charm_slot")
    assert p["charm_slot"] is False
    assert f"level {economy.CHARM_SLOT_LEVEL}" in s.shard_note


def test_the_pouch_wants_its_xp_and_its_fee():
    p = _at_school("069-school9-xp", 9, xp=10)
    s = _choose(p, "buy_charm_slot")
    assert p["charm_slot"] is False and "XP" in s.shard_note
    p = _at_school("069-school9-gold", 9, gold=1)
    s = _choose(p, "buy_charm_slot")
    assert p["charm_slot"] is False and "fee" in s.shard_note


def test_the_pouch_is_bought_once_and_ledgered():
    p = _at_school("069-school9", 9)
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_charm_slot")
    assert not row.locked
    xp0, gold0 = p["xp"], p["gold"]
    fee = economy.charm_slot_gold(max(1, p["unlocked_floor"]))
    s = _choose(p, "buy_charm_slot")
    assert p["charm_slot"] is True
    assert p["xp"] == xp0 - economy.CHARM_SLOT_XP
    assert p["gold"] == gold0 - fee
    assert "POUCH" in s.body_lines[0]
    assert any(r.get("note") == "charm pouch" for r in p["_ledger"])
    assert economy.slot_lock(p, "charm") is None
    s = core.current_scene(p)
    assert not any(o.id == "buy_charm_slot" for o in s.options)
    s = core._school_charm(p)                # forced: the deeper guard
    assert "already" in s.shard_note


# ── phase 4: wear into a slot, move to the pack ─────────────────────────

def _fill_pack(p, n=None):
    n = core.pack_cap(p) if n is None else n
    fillers = [s for s in economy.RELICS if s not in economy.CHARM_KINDS
               and s not in economy.QUIVER_SLUGS][:1]
    junk = ["repair_token", "energy_cell", "medgel", "trauma_kit",
            "poison_arrows", "fire_arrows", "slowing_arrows",
            "piercing_arrows"] + fillers
    for slug in junk[:n]:
        p["inventory"][slug] = 1
    assert core.pack_used(p) >= n


def test_unequip_armor_refused_when_the_pack_is_full():
    p = _warrior("069-unarm-full")
    _fill_pack(p)
    before = dict(p["gear"]), dict(p["inventory"])
    acts, why = core.slot_actions(p, "armor")
    assert [o.id for o in acts] == ["unequip_armor"]
    assert "Pack full" in acts[0].hint
    s = _choose(p, "unequip_armor")
    assert "Pack full" in s.shard_note and "forge" in s.shard_note
    assert (dict(p["gear"]), dict(p["inventory"])) == before


def test_unequip_armor_moves_it_and_the_def_drops():
    p = _warrior("069-unarm")
    _fill_pack(p, core.pack_cap(p) - 1)
    armor = p["gear"]["armor"]
    dfs0 = state.dfs(p)
    s = _choose(p, "unequip_armor")
    assert p["gear"]["armor"] is None
    assert p["inventory"][armor] == 1
    assert state.dfs(p) < dfs0
    assert "does nothing there" in s.body_lines[0]
    # and back on again from the pack
    acts, _ = core.pack_actions(p, armor)
    assert [o.id for o in acts] == [f"wear_{armor}"] and acts[0].label == "Wear"
    _choose(p, f"wear_{armor}")
    assert p["gear"]["armor"] == armor and state.dfs(p) == dfs0


def test_shoes_above_your_level_are_refused_with_the_lock():
    p = _warrior("069-shoes")
    p["level"] = 9
    p["inventory"]["wayfarers_treads"] = 1
    acts, why = core.pack_actions(p, "wayfarers_treads")
    assert acts == [] and "🔒 level 11" in why
    s = _choose(p, "wear_wayfarers_treads")
    assert p["gear"]["shoes"] != "wayfarers_treads"
    p["level"] = 11
    _choose(p, "wear_wayfarers_treads")
    assert p["gear"]["shoes"] == "wayfarers_treads"


def test_a_bow_into_the_open_second_slot_and_back_to_the_pack():
    p = _warrior("069-bow2", slots=2)
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    acts, _ = core.pack_actions(p, "basic_bow")
    assert acts[0].id == "wear_basic_bow" and acts[0].label == "Hold"
    _choose(p, "wear_basic_bow")
    assert economy.slot_item(p, "weapon2") == "basic_bow"
    assert economy.slot_item(p, "weapon") == sword
    # a quiver bound to it comes back with it
    p["quiver"] = {"poison_arrows": 4}
    p["oil"] = {"basic_bow": 3}
    s = _choose(p, "unequip_weapon2")
    assert p["held"] == [sword] and p["gear"]["weapon"] == sword
    assert p["inventory"]["basic_bow"] == 1
    assert p["inventory"]["poison_arrows"] == 4 and p["quiver"] == {}
    assert p["oil"] == {}
    assert "oil dries" in s.body_lines[0]


def test_the_lead_can_go_to_the_pack_and_the_next_blade_leads():
    p = _warrior("069-unlead", slots=2)
    sword = p["gear"]["weapon"]
    p["inventory"]["basic_bow"] = 1
    _choose(p, "wear_basic_bow")                 # bow leads, slot 2
    assert p["gear"]["weapon"] == "basic_bow"
    _choose(p, "unequip_weapon2")                # the lead leaves
    assert p["held"] == [sword] and p["gear"]["weapon"] == sword
    assert p["durability"].get("weapon") is not None


def test_the_last_blade_stays_in_hand():
    p = _warrior("069-last")
    acts, why = core.slot_actions(p, "weapon")
    assert acts == [] and why == core.LAST_BLADE
    s = _choose(p, "unequip_weapon")
    assert s.shard_note == core.LAST_BLADE
    assert p["held"] == [p["gear"]["weapon"]]


def test_slot_actions_read_locked_and_empty_and_fight():
    p = _warrior("069-slotacts", slots=1)
    acts, why = core.slot_actions(p, "weapon2")
    assert acts == [] and "second grip" in why
    p["slots"] = 2
    assert core.slot_actions(p, "weapon2") == ([], "")
    p["charm_slot"] = True
    p["gear"]["charm"] = "luck_charm"
    acts, _ = core.slot_actions(p, "charm")
    assert [o.id for o in acts] == ["unequip_charm"]
    from plugin_linear_ascent.content import schema
    fl = schema.get_floor(1)
    enc = next(e for e in fl.encounters if e.id == "feral_boar")
    combat.start_encounter(p, fl, enc)
    acts, why = core.slot_actions(p, "charm")
    assert acts == [] and why == core.NOT_IN_A_FIGHT
    s = _choose(p, "unequip_charm")
    assert s.shard_note == core.NOT_IN_A_FIGHT
    assert p["gear"]["charm"] == "luck_charm"


def test_set_in_pouch_needs_the_pouch_and_swaps_the_old_one_out():
    p = _warrior("069-pouchset")
    p["inventory"]["luck_charm"] = 1
    acts, why = core.pack_actions(p, "luck_charm")
    assert acts == [] and f"level {economy.CHARM_SLOT_LEVEL}" in why
    s = _choose(p, "wear_luck_charm")
    assert p["gear"]["charm"] is None
    p["charm_slot"] = True
    acts, _ = core.pack_actions(p, "luck_charm")
    assert [(o.id, o.label) for o in acts] == [("wear_luck_charm", "Set in pouch")]
    _choose(p, "wear_luck_charm")
    assert p["gear"]["charm"] == "luck_charm"
    assert p["charm_dur"] == economy.CHARM_POOL
    assert "luck_charm" not in p["inventory"]
    p["inventory"]["trollblood_tonic"] = 1
    acts, _ = core.pack_actions(p, "trollblood_tonic")
    assert "swap out" in acts[0].hint
    _choose(p, "wear_trollblood_tonic")
    assert p["gear"]["charm"] == "trollblood_tonic"
    assert p["inventory"]["luck_charm"] == 1
    # a salve keeps its road use next to the pouch row
    p["hp"] = 1
    p["inventory"]["medgel"] = 2
    acts, _ = core.pack_actions(p, "medgel")
    assert [o.id for o in acts] == ["use_medgel", "wear_medgel"]
    # the pouch empties back to the pack
    _choose(p, "unequip_charm")
    assert p["gear"]["charm"] is None
    assert p["inventory"]["trollblood_tonic"] == 1


def test_wear_refuses_when_the_old_piece_has_no_room():
    p = _warrior("069-wearfull", slots=1)
    sword = p["gear"]["weapon"]
    _fill_pack(p, core.pack_cap(p) - 1)
    p["inventory"]["basic_bow"] = 2               # full now; the swap frees no slot
    assert core.pack_used(p) == core.pack_cap(p)
    s = _choose(p, "wear_basic_bow")
    assert p["gear"]["weapon"] == sword
    assert "Pack full" in s.shard_note
    p["inventory"]["basic_bow"] = 1               # the stack frees a slot
    _choose(p, "wear_basic_bow")
    assert p["gear"]["weapon"] == "basic_bow"
    assert p["inventory"][sword] == 1


# ── phase 5: the gear map on the card ───────────────────────────────────

def _frag(p):
    from plugin_linear_ascent import render
    return render.render_scene_fragment(core.current_scene(p))


def test_the_scene_carries_all_seven_slots_and_they_round_trip():
    from plugin_linear_ascent.engine.scene import Scene
    p = _warrior("069-r-seven", slots=1)
    s = core.current_scene(p)
    keys = [d["key"] for d in s.slots]
    assert keys == ["charm", "armor", "shoes",
                    "shield", "weapon", "weapon2", "weapon3"]
    assert [d["side"] for d in s.slots] == ["left"] * 3 + ["right"] * 4
    by = {d["key"]: d for d in s.slots}
    assert by["charm"]["state"] == "locked" and "level 9" in by["charm"]["lock_text"]
    assert by["weapon2"]["state"] == "locked" and by["weapon3"]["state"] == "locked"
    assert by["weapon"]["state"] == "filled" and by["weapon"]["lead"] is True
    assert by["shoes"]["state"] == "empty"
    back = Scene.from_dict(s.to_dict())
    assert back.slots == s.slots
    # nothing worn rides the pack strip
    assert not [c for c in s.inventory if c.get("equipped")]


def test_the_card_draws_the_three_slot_states():
    p = _warrior("069-r-states", slots=2)
    frag = _frag(p)
    assert 'class="gearmap later"' in frag
    gm = frag.split('class="gearmap later"')[1].split('class="pcol"')[0]
    # locked: grey box + lock, the hover says the level
    assert 'class="slot gm locked" data-key="charm"' in gm
    assert "School, level 9" in gm
    # empty: dotted, and the tip names what goes there
    assert 'class="slot gm empty" data-key="shoes"' in gm
    assert "boots — none worn" in gm
    assert 'class="slot gm empty" data-key="weapon2"' in gm
    # filled: the item cell with its acts, the lead marked
    assert 'data-key="weapon" class="slot gm item act lead' in gm
    assert "unequip_weapon" not in gm          # last blade — no row
    assert "unequip_armor" in gm and "Move to the pack" in gm
    # columns in order, portrait between them
    left = gm.split('class="slotcol left"')[1].split('class="pwrap"')[0]
    right = gm.split('class="slotcol right"')[1]
    assert [k for k in ("charm", "armor", "shoes")
            if f'data-key="{k}"' in left] == ["charm", "armor", "shoes"]
    assert 'data-key="shield"' in right and 'data-key="weapon3"' in right
    assert 'class="portrait later"' in gm.split('class="pwrap"')[1]


def test_the_pack_grid_is_pack_only_and_sits_under_the_profile():
    p = _warrior("069-r-pack", slots=1)
    p["inventory"]["medgel"] = 2
    frag = _frag(p)
    assert 'class="handrow"' not in frag and 'class="hcell"' not in frag
    grid = frag.split('class="slotgrid"')[1]
    assert 'data-slug="medgel"' in grid
    assert 'data-slug="rusted_sword"' not in grid
    assert frag.index('class="gearmap later"') < frag.index('class="slotgrid"')
    # the pack row is a wear row from here
    assert "wear_" not in grid or "Set in pouch" not in grid


def test_a_worn_luck_charm_draws_in_the_pouch_with_its_pool():
    p = _warrior("069-r-charm", slots=1)
    p["charm_slot"] = True
    p["gear"]["charm"] = "luck_charm"
    p["charm_dur"] = 7
    s = core.current_scene(p)
    d = next(x for x in s.slots if x["key"] == "charm")
    assert d["state"] == "filled" and d["charm_dur"] == 7
    assert d["icon"] == "luck_charm"
    frag = _frag(p)
    assert "7 victories of fortune left" in frag
    assert "unequip_charm" in frag


def test_the_gear_map_css_and_wiring_are_in_the_renderer():
    from plugin_linear_ascent import render
    src = open(render.__file__, encoding="utf-8").read()
    assert ".gearmap{{display:grid;grid-template-columns:auto auto auto" in src
    assert ".slot.gm.locked{{background:#222;border:2px solid #555" in src
    assert ".slot.gm.empty{{border:2px dotted" in src
    assert ".slot.gm.lead{{border-color:" in src
    assert "'.inv .item, .gearmap .item'" in src
    assert "pr.querySelectorAll('.slotcol')" in src


def test_the_arena_payload_carries_the_pouch_and_per_weapon_atk():
    from plugin_linear_ascent.engine import arena
    p = _warrior("069-arena", slots=2)
    p["level"] = 10
    p["training"]["bow"] = 6
    p["held"] = ["rusted_sword", "basic_bow"]
    p["durability_pack"] = {"basic_bow": 100.0}
    p["charm_slot"] = True
    p["gear"]["charm"] = "luck_charm"
    p["charm_dur"] = 9
    me = arena._me(p)
    assert me["charm"] == {"slug": "luck_charm", "name": "Luck charm", "dur": 9}
    atks = {w["slug"]: w["atk"] for w in me["weapons"]}
    assert atks["rusted_sword"] == economy.player_atk(
        10, economy.honed_bonus(economy.FORGE["rusted_sword"].bonus, 0))
    assert atks["basic_bow"] == economy.player_atk(
        10, economy.FORGE["basic_bow"].bonus)
    state.set_hone(p, "weapon", 2, "basic_bow")   # honed → its own number
    atks = {w["slug"]: w["atk"] for w in arena._me(p)["weapons"]}
    assert atks["basic_bow"] == economy.player_atk(
        10, economy.honed_bonus(economy.FORGE["basic_bow"].bonus, 2))
    assert atks["rusted_sword"] != atks["basic_bow"]
    assert arena.tile("attack_basic_bow", p)["atk"] == atks["basic_bow"]
    assert arena.tile("attack", p)["atk"] == atks["rusted_sword"]
    p["gear"]["charm"] = "medgel"
    assert arena._me(p)["charm"] == {"slug": "medgel", "name": "Medgel",
                                     "dur": None}
    p["charm_slot"] = False
    assert arena._me(p)["charm"] is None
