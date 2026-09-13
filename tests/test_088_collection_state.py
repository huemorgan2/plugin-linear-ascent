"""Candidate ownership, migration and action laws; legacy fixtures stay legacy."""
from copy import deepcopy
import json

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import collection, core, social, state

pytestmark = pytest.mark.reel  # exercise the real action signature, without the legacy auto-stepper


def legacy(slots=1):
    p = state.new_player("collection-contract")
    p.update(stage="playing", name="Contract", race="human", slots=slots)
    p["gear"]["weapon"] = "rusted_sword"
    p["held"] = ["rusted_sword"]
    state.ensure_current(p)
    return p


def candidate():
    p = legacy()
    collection.migrate(p)
    return p


def test_preview_is_read_only_and_migration_preserves_distinct_owned_copies():
    p = legacy(3)
    p["inventory"]["rusted_sword"] = 2
    p["materials"] = {"Wood": 7}
    p["durability"]["weapon"] = 71
    p["hone"]["weapon:rusted_sword"] = 4
    p["oil"]["rusted_sword"] = 3
    before = deepcopy(p)
    report = collection.preview(p)
    assert p == before
    q = report["document"]
    assert report["reconciliation"] == dict(ok=True, errors=[], owned=3, selected=1)
    item = collection.active(q)
    assert item["durability"] == 71
    assert item["legacy"]["hone"] == 4 and item["legacy"]["oil"] == 3
    assert collection.stats(item)["attack"] == economy.honed_bonus(5, 4)
    assert q["materials"] == {"Wood": 7}
    assert q["slots"] == 3 and len(q["deck"]) == 3
    assert q["gold"] == before["gold"] + 230
    assert state.xp_total(q) == state.xp_total(before) + 560
    assert json.loads(json.dumps(q)) == q
    stable = deepcopy(q)
    collection.migrate(q)
    assert q == stable


def test_exact_refunds_are_once_per_slot_and_do_not_erase_school():
    p = legacy(3)
    receipts = [dict(kind="train", note="carry 2", gold=-30, xp=-60),
                dict(kind="train", note="carry 3", gold=-1234, xp=-500)]
    p["training"] = dict(blade=9, bow=3, staff=1)
    p["mastery"] = {"bow": True}
    report = collection.migrate(p, receipts + receipts)
    assert report["refund"]["gold"] == 1264
    assert report["refund"]["xp"] == 560
    assert p["training"] == dict(blade=9, bow=3, staff=1)
    assert p["mastery"] == {"bow": True}
    p["location"] = "school"
    s = core.current_scene(p)
    ids = {o.id for o in s.options}
    assert "train_blade" in ids
    assert not {"buy_carry2", "buy_carry3"} & ids


def test_active_legacy_fight_defers_conversion(monkeypatch):
    p = legacy(1)
    p["encounter"] = {"kind": "wilds", "hp": 11}
    before = deepcopy(p)
    monkeypatch.setenv("ASCENT_RULESET", collection.RULESET)
    assert collection.migrate(p)["status"] == "deferred"
    assert p == before
    p["encounter"] = None
    state.ensure_current(p)
    assert collection.enabled(p)
    monkeypatch.delenv("ASCENT_RULESET")
    state.ensure_current(p)
    assert p["slots"] == 3 and collection.enabled(p)


def test_deck_allows_duplicate_families_not_duplicate_instances():
    p = candidate()
    a = collection.mint(p, "viper")
    b = collection.mint(p, "viper")
    collection.set_slot(p, 1, a["id"])
    collection.set_slot(p, 2, b["id"])
    assert len({x for x in p["deck"] if x}) == 3
    for cell, iid in [(3, a["id"]), (0, a["id"]), (1, "someone-elses")]:
        before = deepcopy(p)
        with pytest.raises(ValueError): collection.set_slot(p, cell, iid)
        assert p == before
    p["group"] = {"committed": True}
    with pytest.raises(ValueError): collection.set_slot(p, 1, None)
    p["group"] = None
    p["expedition"] = {"site": "copse"}
    with pytest.raises(ValueError): collection.set_slot(p, 1, None)


def test_sources_have_explicit_starting_levels_and_condition():
    p = candidate()
    bought = collection.mint(p, "viper", "Legendary", "shop", receipt="shop:1")
    dropped = collection.mint(p, "viper", "Legendary", "drop")
    assert bought["level"] == 6 and bought["durability"] == bought["maximum"]
    assert dropped["level"] == 0
    assert dropped["durability"] == __import__('math').ceil(dropped["maximum"] * .1)
    assert collection.mint(p, "viper", "Legendary", "shop", receipt="shop:1") is bought
    with pytest.raises(ValueError): collection.set_slot(p, 1, bought["id"])
    p["unlocked_floor"] = 76
    collection.set_slot(p, 1, bought["id"])


def test_overflow_is_spendable_and_level_purchase_keeps_the_rest():
    p = candidate()
    p["gold"] = 100000
    awarded = economy.xp_need(1) * 10
    assert state.gain_xp(p, awarded) == awarded
    assert p["xp_reserve"] > 0 and state.xp_total(p) == awarded
    state.ensure_current(p)
    assert state.xp_total(p) == awarded
    before = state.xp_total(p)
    cost = economy.xp_need(p["level"])
    social.guild_train(p)
    assert p["level"] == 2 and state.xp_total(p) == before - cost
    assert state.spend_xp(p, state.xp_total(p) - 3)
    assert p["xp"] == 3 and p["xp_reserve"] == 0
    assert not state.spend_xp(p, -3)
    p["level"] = 30
    state.gain_xp(p, 10**18)
    assert p["xp"] == 10**18 + 3 and p["xp_reserve"] == 0


def test_stale_action_does_not_advance_clock_rng_or_any_owned_value():
    p = candidate()
    p.update(location="vault", gold=1000)
    s = core.current_scene(p)
    core.apply_choice(p, "deposit_half", expected_scene=s.scene_id)
    before = deepcopy(p)
    refused = core.apply_choice(p, "deposit_half", expected_scene=s.scene_id)
    assert refused.refusal and p == before
    assert p["gold"] == 500 and p["bank"] == 500


def test_collection_scene_serializes_and_numbered_actions_select_exact_instance():
    from plugin_linear_ascent.engine.scene import Scene
    from plugin_linear_ascent.render import render_scene_fragment, SCENE_CSS
    p = candidate()
    item = collection.mint(p, "thunder", "Common")
    core.apply_choice(p, "collection")
    s = core.apply_choice(p, "inspect:" + item["id"])
    s.group = {"id": "g1", "hp": 10**18, "paid": [True, False]}
    s.combat_events = [{"kind": "resist", "channel": "magic", "defender": "m1"}]
    encoded = json.loads(json.dumps(s.to_dict()))
    assert Scene.from_dict(encoded).to_dict() == encoded
    html = render_scene_fragment(s)
    assert 'data-opt="inspect:' + item["id"] in html
    assert 'Three battle weapons' in html
    assert 'font-size:16px' in SCENE_CSS
    chosen = core.apply_choice(p, "2")
    assert not chosen.refusal and p["deck"][1] == item["id"]


def test_public_profile_has_three_cells_and_no_ownership_actions():
    from plugin_linear_ascent.engine.profile import public_sheet
    p = candidate()
    blade = collection.mint(p, "viper")
    collection.set_slot(p, 1, blade["id"])
    before = deepcopy(p)
    sheet = public_sheet(p)
    cells = [s for s in sheet["slots"] if s["kind"] == "weapon"]
    assert len(cells) == 3 and cells[1]["instance_id"] == blade["id"]
    assert not any(c.get("acts") for c in cells)
    assert "bank" not in sheet and p == before


def test_candidate_has_no_slot_unlock_advertisement_and_no_free_journey_heal(monkeypatch):
    import datetime as dt
    from plugin_linear_ascent import unlocks
    p = candidate()
    assert not any(u.id == "carry3" for u in unlocks.ahead(p))
    p.update(hp=7, group={"committed": True}, sleeping={"where": "fields", "since": state.now().isoformat()})
    tomorrow = state.now() + dt.timedelta(days=1)
    monkeypatch.setattr(state, "now", lambda: tomorrow)
    state.touch_daily(p)
    assert state.apply_sleep_healing(p) == 0 and p["hp"] == 7
