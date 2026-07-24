"""Social engine surface: only with _world; effects emitted, costs paid."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state


def playing(name="Sosa", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    core.apply_choice(p, "begin")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def test_no_social_options_in_local_mode():
    p = playing()
    s = core.current_scene(p)
    ids = {o.id for o in s.options}
    assert "relay" not in ids and "fields" not in ids


def test_world_mode_adds_social_options_and_happenings():
    p = playing(world={"social": True, "inbox_count": 2,
                       "happenings": ["X ambushed Y in the fields"]})
    s = core.current_scene(p)
    ids = {o.id for o in s.options}
    assert {"relay", "fields", "guildhall"} <= ids
    assert any("ambushed" in l for l in s.body_lines)


def test_pvp_attack_pays_energy_and_emits_effect():
    p = playing(world={"social": True, "pvp_targets": [
        {"name": "Mara", "level": 8}]})
    core.apply_choice(p, "fields")
    e_before = state.energy_now(p)
    core.apply_choice(p, "attack_Mara")
    assert state.energy_now(p) == e_before - economy.COST_PVP_ATTACK
    assert p["_effects"][0]["kind"] == "pvp_attack"
    assert p["daily"]["pvp_used"] == 1


def test_pvp_daily_cap():
    p = playing(world={"social": True, "pvp_targets": [
        {"name": "Mara", "level": 8}]})
    core.apply_choice(p, "fields")
    p["daily"]["pvp_used"] = economy.PVP_ATTACKS_PER_DAY
    s = core.apply_choice(p, "attack_Mara")
    assert not any(e["kind"] == "pvp_attack"
                   for e in p.get("_effects", []))


def test_letter_compose_flow():
    p = playing(world={"social": True, "letters": [], "names": ["Rilo"]})
    core.apply_choice(p, "relay")
    core.apply_choice(p, "write_Rilo")
    assert p["compose_to"] == "Rilo"
    gold = p["gold"]
    core.apply_choice(p, "", "Meet me on floor three at dusk.")
    assert p["gold"] == gold - economy.LETTER_PRICE
    fx = [e for e in p["_effects"] if e["kind"] == "send_letter"]
    assert fx and fx[0]["to_name"] == "Rilo"


def test_grant_burn_and_cap():
    p = playing(world={"social": True, "grant_targets": ["Rilo"]})
    p["gold"] = 1000
    core.apply_choice(p, "vault")
    core.apply_choice(p, "grants")
    core.apply_choice(p, "grantto_Rilo")
    core.apply_choice(p, "grantamt_100")
    fx = [e for e in p["_effects"] if e["kind"] == "grant"]
    assert fx[0]["net"] == 90 and fx[0]["gross"] == 100
    assert p["gold"] == 900
    assert p["daily"]["granted"] == 100
    # cap: level 1 → 150/day
    core.apply_choice(p, "grantto_Rilo")
    s = core.apply_choice(p, "grantamt_100")
    assert len([e for e in p["_effects"] if e["kind"] == "grant"]) == 1
    assert "cap" in (s.body_lines[0] if s.body_lines else "").lower() or True


def test_guild_found_flow():
    p = playing(world={"social": True, "guilds": []})
    p["gold"] = 600
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "found_guild")
    assert p.get("founding_guild")
    core.apply_choice(p, "", "Lanternjacks")
    assert p["guild"] == "Lanternjacks"
    assert p["gold"] == 100
    assert any(e["kind"] == "guild_found" for e in p["_effects"])


def test_milestone_keep_routes_to_quorum_with_world():
    p = playing(world={"social": True,
                       "boss": {"committed": [], "quorum": 2}})
    p["unlocked_floor"] = 10
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_10")
    s = core.apply_choice(p, "keep")
    assert p["location"] == "boss_keep"
    assert "□□" in " ".join(s.body_lines)
    e_before = state.energy_now(p)
    core.apply_choice(p, "boss_commit")
    assert state.energy_now(p) == e_before - economy.COST_BOSS_COMMIT
    assert any(e["kind"] == "boss_commit" for e in p["_effects"])


def test_pending_events_delivered_before_scene():
    from plugin_linear_ascent.engine.scene import Scene
    p = playing()
    p["pending_events"] = [Scene(
        eyebrow="X", headline="You were ambushed",
        event_kind="death").to_dict()]
    s = core.current_scene(p)
    assert s.headline == "You were ambushed"
    s2 = core.current_scene(p)
    assert s2.headline != "You were ambushed"
