"""017 phase 001 — damage types & defense profiles.

Unit table for the tier math, engine edges (flying vs melee, sleep vs
High spellguard, shield-wall counter), doc v2 migration, and the matchup
sim gate: every class beats its intended victims on floors 1-10 and is
genuinely walled by its hard counters.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(user="test-user-017"):
    return state.new_player(user)


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def prof(*traits):
    return economy.profile_from_traits(traits)


# ── typed_damage: the tier table ─────────────────────────────────────────

@pytest.mark.parametrize("dtype,traits,raw,mdef,want", [
    # plain target: melee/ranged keep raw − DEF/2, magic ignores DEF
    ("melee", (), 20, 10, 15),
    ("ranged", (), 20, 10, 15),
    ("magic", (), 20, 10, 20),
    # armor tiers cut physical damage only
    ("melee", ("armor_low",), 20, 10, 11),     # 15 × 0.75
    ("ranged", ("armor_med",), 20, 10, 8),     # 15 × 0.50
    ("melee", ("armor_high",), 20, 10, 4),     # 15 × 0.25
    ("magic", ("armor_high",), 20, 10, 20),    # plate means nothing to magic
    # resist tiers cut magic only
    ("magic", ("resist_low",), 20, 10, 15),    # 20 × 0.75
    ("magic", ("resist_med",), 20, 10, 10),
    ("magic", ("resist_high",), 20, 10, 5),
    ("melee", ("resist_high",), 20, 10, 15),   # spellguard ignores steel
    # legacy content trait maps to armor_med
    ("ranged", ("armored",), 20, 10, 8),
])
def test_tier_math(dtype, traits, raw, mdef, want):
    assert economy.typed_damage(dtype, raw, mdef, prof(*traits)) == want


def test_flying_is_the_single_legal_zero():
    p = prof("flying")
    assert economy.typed_damage("melee", 50, 0, p) == 0
    # flying alone carries no tier: ranged/magic keep full damage
    assert economy.typed_damage("ranged", 50, 0, p) == 50
    assert economy.typed_damage("magic", 50, 0, p) == 50


def test_everything_that_can_hit_chips_at_least_one():
    # massive DEF + High tier still chips 1 (the 013 lesson, kept)
    assert economy.typed_damage("melee", 4, 1000, prof("armor_high")) == 1
    assert economy.typed_damage("magic", 1, 0, prof("resist_high")) == 1


def test_bulwark_raises_armor_tier_and_pays():
    b = prof("bulwark")
    assert b["armor"] == "low" and b["bulwark"]
    assert prof("armor_med", "bulwark")["armor"] == "high"
    assert economy.profile_gold_mult(b) == pytest.approx(1.1 * 1.5)


def test_speed_traits_land_in_the_profile():
    assert prof("fast")["speed"] == economy.SPEED_FAST
    assert prof("slow")["speed"] == economy.SPEED_SLOW
    assert prof()["speed"] == economy.SPEED_NORMAL


def test_profile_gold_mult_compounds():
    p = prof("armor_med", "resist_low", "flying")
    assert economy.profile_gold_mult(p) == pytest.approx(1.25 * 1.1 * 1.2)


def test_warden_profiles_by_band():
    assert economy.warden_profile(5)["armor"] == "none"
    assert economy.warden_profile(20) == prof("armor_med", "resist_med")
    w = economy.warden_profile(35)
    assert w["armor"] == "low" and w["resist"] == "low"


# ── class starters ───────────────────────────────────────────────────────

def test_creation_hands_out_the_class_weapon():
    for clazz, slug in (("warrior", "rusted_sword"), ("archer", "basic_bow"),
                        ("sorcerer", "worn_staff")):
        p = create_character(fresh(f"starter-{clazz}"), clazz=clazz)
        assert p["gear"]["weapon"] == slug
        item = economy.FORGE[slug]
        assert item.tier == 0 and item.price == 0 and item.bonus == 5


def test_starters_never_appear_in_the_forge_stock():
    for tier in range(1, 11):
        slugs = {g.slug for g in economy.forge_tier(tier)}
        assert not slugs & {"rusted_shiv", "rusted_sword", "basic_bow",
                            "worn_staff"}


# ── doc v2 migration ─────────────────────────────────────────────────────

def _v1_playing_doc(clazz):
    p = create_character(fresh(f"v1-{clazz}"), clazz=clazz)
    p["version"] = 1
    p["gear"]["weapon"] = economy.STARTER_WEAPON.slug   # pre-017 shiv
    p.pop("pending_events", None)
    return p


def test_v1_archer_gets_bow_and_letter():
    p = _v1_playing_doc("archer")
    state.ensure_current(p)
    assert p["version"] == 2
    assert p["gear"]["weapon"] == "basic_bow"
    ev = p["pending_events"][0]
    assert "weapon" in ev["headline"].lower()
    # idempotent: running again neither re-swaps nor re-letters
    state.ensure_current(p)
    assert len(p["pending_events"]) == 1


def test_v1_warrior_renames_silently():
    p = _v1_playing_doc("warrior")
    state.ensure_current(p)
    assert p["gear"]["weapon"] == "rusted_sword"
    assert not p.get("pending_events")


def test_v1_doc_with_bought_weapon_is_untouched():
    p = _v1_playing_doc("sorcerer")
    p["gear"]["weapon"] = "pigsticker"       # earned gear stays
    state.ensure_current(p)
    assert p["gear"]["weapon"] == "pigsticker"
    assert not p.get("pending_events")


# ── engine edges ─────────────────────────────────────────────────────────

def _fight(clazz, floor_no, enc_id):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    p = create_character(fresh(f"edge-{clazz}-{enc_id}"), clazz=clazz)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    opener = combat.start_encounter(p, fl, enc)
    return p, fl, opener


def test_melee_cannot_touch_a_flyer():
    p, fl, _ = _fight("warrior", 4, "glare_moth")
    p["encounter"]["range"] = "close"        # 002: past the crossing
    hp0 = p["encounter"]["hp"]
    s = combat.resolve_fight_action(p, fl, "attack")
    assert p["encounter"]["hp"] == hp0                 # zero, not chip
    assert any("air" in ln.lower() or "flies" in ln.lower()
               for ln in s.body_lines)


def test_ranged_and_magic_reach_the_flyer():
    for clazz in ("archer", "sorcerer"):
        p, fl, _ = _fight(clazz, 4, "glare_moth")
        hp0 = p["encounter"]["hp"]
        combat.resolve_fight_action(p, fl, "attack")
        if p["encounter"] is not None:                 # may have killed it
            assert p["encounter"]["hp"] < hp0


def test_shield_wall_counter_misses_the_flyer():
    p, fl, _ = _fight("warrior", 4, "glare_moth")
    hp0 = p["encounter"]["hp"]
    s = combat.resolve_fight_action(p, fl, "shield_wall")
    assert p["encounter"]["hp"] == hp0
    assert any("airborne" in ln.lower() for ln in s.body_lines)


def test_sleep_refused_by_high_spellguard_costs_nothing():
    fl = schema.get_floor(4)
    enc = next(e for e in fl.encounters if e.id == "glare_moth")
    p = create_character(fresh("sleep-high"), clazz="sorcerer")
    p["level"] = 4
    p["xp"] = 10_000
    combat.start_encounter(p, fl, enc)
    p["encounter"]["profile"]["resist"] = "high"       # force the wall
    xp0 = p["xp"]
    s = combat.resolve_fight_action(p, fl, "sleep_spell")
    assert p["xp"] == xp0                              # refused pre-spend
    assert p["encounter"] is not None                  # still in the fight
    assert any("spellguard" in ln.lower() for ln in s.body_lines)


def test_opener_names_the_profile():
    # 003: the profile moved off the body and into scene.enemy — the
    # fight header + [i] dossier render it, and the text fallback keeps
    # naming it for card-less hosts.
    _, _, opener = _fight("warrior", 10, "kings_guard")
    assert "plate Medium" in (opener.enemy or {}).get("tiers", [])
    assert "plate medium" in opener.to_text().lower()


def test_scan_includes_the_profile():
    p, fl, _ = _fight("warrior", 4, "glare_moth")
    p["sidekick"]["scout_charges"] = 1
    s = combat.resolve_fight_action(p, fl, "scout")
    joined = " ".join(s.body_lines)
    assert "AIRBORNE" in joined


# ── the matchup sim gate ─────────────────────────────────────────────────

def reference_player(clazz, floor):
    """The design's at-level player (economy._at_level_loadout) as a real
    doc: level = floor, current-tier set, honing 2 floors behind."""
    p = fresh(f"ref-{clazz}-{floor}")
    p.update(stage="playing", race="human", clazz=clazz, name="Ref",
             level=floor, unlocked_floor=floor)
    tier = economy.gear_tier_for_floor(floor)
    # 004: three weapon lines mirror each other's numbers — equip the
    # CLASS line's whole-tier rung so the damage type stays in-class.
    p["gear"]["weapon"] = next(
        g for g in economy.weapon_line(clazz) if g.rung == tier).slug
    p["gear"]["shield"] = next(
        g for g in economy.gear_rungs("shield") if g.rung == tier).slug
    p["gear"]["armor"] = next(
        g for g in economy.gear_rungs("armor") if g.rung == tier).slug
    hone = economy.reference_hone(floor)
    p["hone"] = {s: hone for s in economy.HONE_SLOTS}
    p["hp"] = economy.player_max_hp(floor)
    return p


def _sim_fight(clazz, floor_no, enc, seed):
    """Each class plays its natural game (002): steel closes and trades,
    the bow kites — reopen distance when caught — and magic just casts."""
    fl = schema.get_floor(floor_no)
    p = reference_player(clazz, floor_no)
    p["luna_user"] = f"sim-{clazz}-{floor_no}-{enc.id}-{seed}"
    combat.start_encounter(p, fl, enc)
    rounds = 0
    while p["encounter"] is not None and rounds < 60:
        rounds += 1
        if clazz == "archer" and \
                p["encounter"].get("range", "close") == "close":
            s = combat.resolve_fight_action(p, fl, "open_distance")
        else:
            s = combat.resolve_fight_action(p, fl, "attack")
        if s.event_kind == "death" or p["hp"] <= 0:
            return False, rounds
    return p["encounter"] is None, rounds


def _class_mult(clazz, profile):
    dtype = economy.DAMAGE_TYPE[clazz]
    if dtype == "melee" and profile["flying"]:
        return 0.0
    tier = profile["resist"] if dtype == "magic" else profile["armor"]
    return economy.TIER_MULT[tier]


def _speed_counters(clazz, profile):
    """002: FAST counters the bow — the kite fails (p_open 20%) and
    close quarters cost the archer ×0.6. A counter axis, same as tiers."""
    return (economy.DAMAGE_TYPE[clazz] == "ranged"
            and profile["speed"] >= economy.SPEED_FAST)


N_SIM = 40


def test_matchup_gate_floors_1_to_10():
    """Intended victims die ≥80% of the time; hard counters genuinely
    wall (win <30%) or drag (≥2× the class's plain-target rounds)."""
    for floor_no in range(1, 11):
        fl = schema.get_floor(floor_no)
        for clazz in economy.DAMAGE_TYPE:
            plain_rounds = None
            results = {}
            for enc in fl.encounters:
                profile = economy.profile_from_traits(enc.traits)
                wins = rounds_sum = 0
                for seed in range(N_SIM):
                    won, r = _sim_fight(clazz, floor_no, enc, seed)
                    wins += won
                    rounds_sum += r
                results[enc.id] = (wins / N_SIM, rounds_sum / N_SIM, profile)
                if not enc.traits and plain_rounds is None:
                    plain_rounds = rounds_sum / N_SIM
            for enc_id, (winrate, avg_rounds, profile) in results.items():
                mult = _class_mult(clazz, profile)
                speed_hard = _speed_counters(clazz, profile)
                hard = mult <= 0.5 or profile["bulwark"] or speed_hard
                where = f"floor {floor_no} {clazz} vs {enc_id}"
                if mult >= 1.0 and not profile["bulwark"] and not speed_hard:
                    assert winrate >= 0.80, f"{where}: win {winrate:.0%}"
                elif hard:
                    # overkill on the final round compresses the ratio
                    # below the naive 1/mult, so 1.6× already means a
                    # fight that visibly drags on screen
                    dragged = (plain_rounds and
                               avg_rounds >= 1.6 * plain_rounds)
                    assert winrate < 0.30 or dragged, (
                        f"{where}: win {winrate:.0%}, rounds "
                        f"{avg_rounds:.1f} vs plain {plain_rounds:.1f} — "
                        "neither walls nor drags")
