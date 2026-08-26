"""022 phase 001 — one list of bosses.

ALL 100 wardens are shared; the keep fight is a real fight whose damage
persists to the world pool; the personal unlock is deleted in the shared
world (local dev play is a world of one). 034 §3 retired this plan's
echo bout: a fallen Warden is dead, and its keep is a memorial.
"""

from __future__ import annotations

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def playing(name="Bosses", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "", name)
    # 048: the class question is gone — restore the old warrior FEEL
    # (blade rank 6, sword in hand) the class pick used to grant.
    p["training"]["blade"] = 6
    p["gear"]["weapon"] = "rusted_sword"
    p["held"] = ["rusted_sword"]
    if world is not None:
        p["_world"] = world
    return p


def warden_world(floor=1, hp=None, **extra):
    hp_max = economy.world_warden_hp(floor)
    return {"social": True, "frontier": floor,
            "warden": {"floor": floor,
                       "hp": hp if hp is not None else hp_max,
                       "hp_max": hp_max, "strikers": []},
            **extra}


def join_fight(p):
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    return core.apply_choice(p, "strike")


# ── the solo band (curve law — constants live in 022/002) ────────────────

def test_solo_band_is_one_blade_deep_floors_take_a_rally():
    for f in (1, 12, 30):
        assert economy.required_strikers(f) == 1
        # a lone sustained blade beats the regen inside the solo band
        out = economy.SUSTAINED_FIGHTS_PER_HOUR \
            * economy.strike_fight_damage(f)
        regen = economy.world_warden_regen_hourly(f) \
            * economy.world_warden_hp(f)
        assert out > regen
    for f in (31, 55, 99):
        assert economy.required_strikers(f) >= 2


def _solo_sim(floor):
    """Coarse mirror of the fight math: the at-level player fights the
    world pool until one round from death, flees, repeats on energy."""
    import math
    p_atk, p_def = economy._at_level_loadout(floor)
    w_atk, w_def, _ = economy.warden_stats(floor)
    p_dmg = max(1, round(0.75 * p_atk) - w_def // 2)
    if floor >= economy.WARDEN_PROFILE_FLOOR:
        p_dmg = max(1, round(p_dmg * economy.WARDEN_REF_CUT))
    w_dmg = max(1, round(0.75 * w_atk) - p_def // 2)
    rounds = max(1, (economy.reference_player_hp(floor) - 1) // w_dmg)
    per_fight = rounds * p_dmg
    pool = economy.world_warden_hp(floor)
    # 022/002: the cap rides the gear band, not the level
    bar = economy.energy_cap(economy.gear_tier_for_floor(floor)) \
        // economy.COST_WARDEN_ATTEMPT
    bars_to_finish = math.ceil(pool / per_fight) / bar
    out_hourly = (60 / economy.ENERGY_REGEN_MIN) \
        / economy.COST_WARDEN_ATTEMPT * per_fight
    regen_hourly = economy.world_warden_regen_hourly(floor) * pool
    return bars_to_finish, out_hourly, regen_hourly


def test_solo_gate_warden_12_falls_inside_two_bars():
    bars, out, regen = _solo_sim(12)
    assert bars <= 2.0, f"warden 12 must be soloable, took {bars:.2f} bars"
    assert out > regen, "the solo band must not out-heal one blade"


def test_solo_gate_warden_45_out_heals_a_lone_grinder():
    _, out, regen = _solo_sim(45)
    assert regen > out, (
        f"a lone blade must make no net progress on floor 45 "
        f"({out:.0f}/hr dealt vs {regen:.0f}/hr healed)")


# ── the shared fight ─────────────────────────────────────────────────────

def test_two_players_wounds_stack_on_one_body():
    w = warden_world(1)
    p1 = playing("Kettle", world=w)
    join_fight(p1)
    p1["encounter"]["hp"] -= 25
    _flee(p1)
    # the second blade picks the fight up where the first left it
    p2 = playing("Brakka", world=w)
    join_fight(p2)
    assert p2["encounter"]["hp"] == economy.world_warden_hp(1) - 25


def _flee(p):
    for _ in range(40):
        p["hp"] = 999
        core.apply_choice(p, "run")
        if p["encounter"] is None:
            return
    raise AssertionError("could not flee")


def test_death_still_persists_the_wounds():
    p = playing(world=warden_world(1))
    join_fight(p)
    p["encounter"]["hp"] -= 19
    p["daily"]["death_save"] = True     # burn the free save
    fl = schema.get_floor(1)
    p["hp"] = 1
    p["encounter"]["atk"] = 10_000      # the next blow kills
    combat._death(p, fl)
    fx = [x for x in p["_effects"] if x["kind"] == "warden_strike"]
    assert fx and fx[0]["damage"] == 19


def test_finishing_the_pool_pays_nothing_locally():
    """The server splits the pool by damage — the engine pays no coins
    of its own (033: worldd lands the settled numbers on the card)."""
    p = playing(world=warden_world(1, hp=1))
    p["training"]["blade"] = 10           # 084: no miss-roll flake
    join_fight(p)
    p["encounter"]["range"] = "close"
    xp0, gold0 = p["xp"], p["gold"]
    core.apply_choice(p, "attack")
    assert p["encounter"] is None
    assert p["xp"] == xp0 and p["gold"] == gold0
    fx = [x for x in p["_effects"] if x["kind"] == "warden_strike"]
    assert len(fx) == 1 and fx[0]["damage"] >= 1


def test_shared_warden_cannot_be_slept_past():
    p = playing("Magic", world=warden_world(1))
    # 048: sleep follows the staff in hand at rank 6, not a class
    p["training"]["staff"] = 6
    p["gear"]["weapon"] = "worn_staff"
    p["held"] = ["worn_staff"]
    p["xp"] = 10_000
    join_fight(p)
    s = core.apply_choice(p, "sleep_spell")
    assert p["encounter"] is not None, "the fight must continue"
    assert "does not sleep" in (s.body_lines[0] if s.body_lines else "")


# ── the fallen keep and the deleted personal unlock ──────────────────────

def test_below_frontier_the_keep_pays_nothing_because_nothing_lives_there():
    """034 §3 replaced 022/001's echo bout. The keep of a Warden that has
    already died is a memorial: no fight, no purse, no world effect."""
    w = warden_world(3)
    p = playing(world=w)
    p["unlocked_floor"] = 3
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    xp0 = p["xp"]
    s = core.apply_choice(p, "keep")
    assert p.get("encounter") is None
    assert p["location"] == "memorial"
    assert p["xp"] == xp0
    assert not any(x["kind"] == "warden_strike"
                   for x in p.get("_effects", []))
    assert p["unlocked_floor"] == 3, "a monument never moves the frontier"
    assert "fell here" in s.headline


def test_local_dev_play_is_a_world_of_one():
    p = playing()                       # no world attached
    p["training"]["blade"] = 10         # 084: no miss-roll flake
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    e = p["encounter"]
    assert not e.get("shared")
    e["hp"] = 1
    e["range"] = "close"
    core.apply_choice(p, "attack")
    assert p["unlocked_floor"] == 2, "the world of one still climbs"


# ── the strings tell the truth now ───────────────────────────────────────

def test_the_stone_line_is_true_and_the_keep_tip_speaks_fight():
    from plugin_linear_ascent.engine import tips
    assert "full fight".lower() in tips.option_tip("strike").lower() \
        or "FULL fight".lower() in tips.option_tip("strike").lower()
    assert "shared" in tips.option_tip("keep")
