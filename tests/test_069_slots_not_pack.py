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
