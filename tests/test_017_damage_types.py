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
    choose(p, text=name)
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
    p["clazz"] = clazz                    # pre-048 docs carried a class
    p["gear"]["weapon"] = economy.STARTER_WEAPON.slug   # pre-017 shiv
    p["held"] = [economy.STARTER_WEAPON.slug]
    p.pop("pending_events", None)
    return p


def test_v1_archer_gets_bow_and_letter():
    p = _v1_playing_doc("archer")
    state.ensure_current(p)
    assert p["version"] >= 2      # 005 pushed docs to v3
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


def test_v1_doc_with_bought_weapon_is_never_demoted_to_the_starter():
    """Earned gear stays earned: v2 must not hand a paid weapon back for
    the free staff. (v5 later trades it rung-for-rung into the sorcerer
    line — see test_017_offclass_migration.)"""
    p = _v1_playing_doc("sorcerer")
    p["gear"]["weapon"] = "pigsticker"
    state.ensure_current(p)
    held = economy.FORGE[p["gear"]["weapon"]]
    assert held.rung == economy.FORGE["pigsticker"].rung
    assert held.price == economy.FORGE["pigsticker"].price


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


# ── the matchup sim gate ─────────────────────────────────────────────────

def reference_player(clazz, floor, rank=8):
    """The design's at-level player (economy._at_level_loadout) as a real
    doc: level = floor, current-tier set, honing 2 floors behind."""
    p = fresh(f"ref-{clazz}-{floor}")
    p.update(stage="playing", race="human", clazz=clazz, name="Ref",
             level=economy.reference_level(floor), unlocked_floor=floor)
    # 004: three weapon lines mirror each other's numbers — equip the
    # CLASS line's rung so the damage type stays in-class. 025: the rung
    # is the one the ladder sells at this floor (band 1 sells one per
    # level), not the whole tier — the sim player has to BE the player
    # every monster and warden number is derived from.
    rung = economy.reference_rung(floor)

    def _at(items):
        return next(g for g in items if abs(g.rung - rung) < 1e-9).slug

    p["gear"]["weapon"] = _at(economy.weapon_line(clazz))
    p["gear"]["shield"] = _at(economy.gear_rungs("shield"))
    p["gear"]["armor"] = _at(economy.gear_rungs("armor"))
    # 048 phase-2 transitional: the reference climber swings near OLD
    # power. The legacy mean (0.75 of ATK, no miss) has no exact rung
    # on the trained ladder — rank 7 gives 0.73, rank 8 gives 0.77 —
    # so each sim pins the side its law needs. The phase-6 bake
    # re-anchors every band at the rank-6 reference climber.
    p["training"] = {"blade": 0, "bow": 0, "staff": 0}
    p["training"][economy.PATH_OF_LINE[clazz]] = rank
    # 031 §7: the reference ARCHER wears the boots the rack sells —
    # with the kite now gated on strictly faster legs, a bootless bow
    # is nobody's real build past the first band, and speed is
    # orthogonal to the ATK/DEF the tuning derives from. The other
    # classes stay bootless so their danger gates keep their teeth.
    # The shoe ladder has its own sparse rungs: newest at/below ref.
    if economy.DAMAGE_TYPE[clazz] == "ranged":
        shoes = [g for g in economy.gear_rungs("shoes") if g.rung <= rung]
        p["gear"]["shoes"] = shoes[-1].slug if shoes else None
    hone = economy.reference_hone(floor)
    p["hone"] = {s: hone for s in economy.HONE_SLOTS}
    # 022/002: armor feeds max HP — read the live pool, never a bare
    # player_max_hp(floor) (that reads a floor as a level)
    p["hp"] = state.max_hp(p)
    return p


# 009: the sims are pinned to one world day. Every roll is keyed by
# (user, world_day, counter), so an unpinned gate re-rolls every UTC
# morning — and a matchup sitting at the 1.6× drag bar flips green/red
# with the date (floor 15 rod_wisp did exactly that). The gates measure
# DESIGN, not today's dice.
_SIM_DAY = 137


def _sim_fight(clazz, floor_no, enc, seed):
    """Each class plays its natural game (002): steel closes and trades,
    the bow kites — reopen distance when caught — and magic just casts."""
    fl = schema.get_floor(floor_no)
    p = reference_player(clazz, floor_no)
    p["luna_user"] = f"sim-{clazz}-{floor_no}-{enc.id}-{seed}"
    rounds = 0
    orig_day = state.world_day
    state.world_day = lambda at=None: _SIM_DAY
    try:
        combat.start_encounter(p, fl, enc)
        while p["encounter"] is not None and rounds < 60:
            rounds += 1
            # 031 §7: the kite exists only against slower legs — equal
            # or faster enemies can't be opened on, so the bow presses.
            can_open = economy.player_speed(p) > combat._mspd(p)
            if clazz == "archer" and can_open and \
                    p["encounter"].get("range", "close") == "close":
                s = combat.resolve_fight_action(p, fl, "open_distance")
            else:
                s = combat.resolve_fight_action(p, fl, "attack")
            if s.event_kind == "death" or p["hp"] <= 0:
                return False, rounds
        return p["encounter"] is None, rounds
    finally:
        state.world_day = orig_day


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


_PLAIN = schema.Encounter(id="_plain", name="Plain thing", weight=1,
                          prose="A plain thing steps onto the path.")


def test_matchup_gate_floors_1_to_10():
    """025: a floor is a RANGE of animals, so the gate reads per shape.

    Before 025 this asserted that EVERY full-damage target dies ≥80% of
    the time — which is exactly the flatness the rebalance removes. What
    still has to hold:

    • prey — anything standing BELOW its floor's bar — stays farmable
      at ≥80% for the class it doesn't counter (043: a creature AT the
      bar pays the full fierce-grade fight cost even with no bite trait,
      so at-bar and above-bar shapes are the floor's real fights and are
      measured by the danger law instead);
    • every class keeps ≥2 farmable targets on every floor (the 008 pool
      rule, now measured and not just linted);
    • a hard counter still walls (<30%) or drags (≥1.6× plain rounds);
    • and every floor holds something that can genuinely bury an at-level
      climber — the danger law. Without it we are back where we started.
    """
    for floor_no in range(1, 11):
        fl = schema.get_floor(floor_no)
        danger = 1.0
        for clazz in economy.DAMAGE_TYPE:
            plain_rounds = sum(
                _sim_fight(clazz, floor_no, _PLAIN, s)[1]
                for s in range(N_SIM)) / N_SIM
            farmable = 0
            for enc in fl.encounters:
                profile = economy.profile_from_traits(enc.traits)
                _, bite = economy._archetype(enc.traits)
                wins = rounds_sum = 0
                for seed in range(N_SIM):
                    won, r = _sim_fight(clazz, floor_no, enc, seed)
                    wins += won
                    rounds_sum += r
                winrate, avg_rounds = wins / N_SIM, rounds_sum / N_SIM
                mult = _class_mult(clazz, profile)
                speed_hard = _speed_counters(clazz, profile)
                # 031 §7: FAST is no longer a hard counter to the bow —
                # the range phase is free shooting now, and the payback
                # is the locked close press (no escape, ×0.6). Speed
                # matchups float between full and countered: exempt from
                # both gates, still counted toward farmable/danger.
                countered = mult <= 0.5 or profile["bulwark"]
                full = mult >= 1.0 and not profile["bulwark"] \
                    and not speed_hard
                where = f"floor {floor_no} {clazz} vs {enc.id}"
                at_or_above = economy.bar_offset(enc.traits) >= 0
                if winrate >= 0.80:
                    farmable += 1
                if bite in ("fierce", "savage") or at_or_above:
                    danger = min(danger, winrate)
                elif full:
                    assert winrate >= 0.80, f"{where}: win {winrate:.0%}"
                elif countered:
                    # overkill on the final round compresses the ratio
                    # below the naive 1/mult, so 1.6× already means a
                    # fight that visibly drags on screen
                    dragged = avg_rounds >= 1.6 * plain_rounds
                    assert winrate < 0.30 or dragged, (
                        f"{where}: win {winrate:.0%}, rounds "
                        f"{avg_rounds:.1f} vs plain {plain_rounds:.1f} — "
                        "neither walls nor drags")
            assert farmable >= 2, (
                f"floor {floor_no} {clazz}: {farmable} farmable targets — "
                "a class must always have somewhere to earn (008 pool rule)")
        # 031: the booted reference archer shaves a few points off the
        # wolves (§7), and death itself got dearer — §8 taxes every
        # death, no pardons past level 6 — so a ≥15% chance of dying
        # is still ruinous EV. The bar moves 80→85, not away.
        # 043.2: the tutorial floors are exempt — FLOOR_ATK_SOFT divides
        # their bite on purpose, so nothing there is frightening BY LAW.
        if floor_no not in economy.FLOOR_ATK_SOFT:
            assert danger <= 0.85, (
                f"floor {floor_no}: the worst fight on the floor is won "
                f"{danger:.0%} of the time — nothing here is frightening "
                "(025)")
