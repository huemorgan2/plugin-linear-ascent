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
