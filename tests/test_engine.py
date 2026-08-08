"""Engine flows: creation gates, combat, death, vault, regen."""

import datetime as dt

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state


def fresh():
    return state.new_player("test-user")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def watch_movie(p):
    """016: step through the intro movie to the title card's gate."""
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")                       # next … next, then begin
    return p


def create_character(p, race="human", clazz="warrior", name="Testa"):
    watch_movie(p)
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def test_intro_movie_precedes_creation():
    p = fresh()
    s = core.current_scene(p)
    assert p["stage"] == "intro"
    # 016: the movie opens on Aldervale, one Next, no skip
    assert s.fx == "intro_aldervale"
    assert [o.id for o in s.options] == ["next"]
    assert any("aether" in line for line in s.body_lines)
    # begin is refused mid-movie — Next is the only way forward
    s = choose(p, "begin")
    assert p["stage"] == "intro" and s.shard_note
    for expected in ("intro_theft", "intro_tower", "intro_warden",
                     "intro_refugee", "intro_roothollow", "intro_stone",
                     "intro_shard", "intro_muster"):
        s = choose(p, "next")
        assert s.fx == expected
        assert [o.id for o in s.options] == ["next"]
    # after the last beat: the title card, and the gate
    s = choose(p, "next")
    assert s.banner == "title" and s.fx == "ascent_title"
    assert "Demon King" in s.headline
    assert [o.id for o in s.options] == ["begin"]
    choose(p, "begin")
    assert p["stage"] == "creation_race"


def test_creation_flow_and_gates():
    p = fresh()
    watch_movie(p)
    s = core.current_scene(p)
    assert "shard" in s.headline.lower() or s.options
    # skipping ahead is refused with a steering hint
    s = choose(p, "gate")
    assert p["stage"] == "creation_race"
    assert s.shard_note                      # steering hint present
    choose(p, "elf")
    assert p["stage"] == "creation_class"
    choose(p, "sorcerer")
    assert p["stage"] == "creation_name"
    s = choose(p, text="x")                  # too short
    assert p["stage"] == "creation_name"
    # 004: the name IS the username — one word, so the words are joined
    s = choose(p, text="Nyx of the Vale")
    assert p["stage"] == "playing"
    assert p["name"] == "NyxoftheVale"
    assert "NyxoftheVale" in s.headline


def test_numbered_fallback_resolves_positionally():
    p = fresh()
    watch_movie(p)                           # "1" advances every movie step
    s = choose(p, "1")                       # first race option
    assert p["stage"] == "creation_class"


def test_wilds_fight_costs_energy_and_resolves():
    p = create_character(fresh())
    choose(p, "gate")
    choose(p, "floor_1")
    e_before = state.energy_now(p)
    s = choose(p, "hunt")
    assert p["encounter"] is not None
    assert state.energy_now(p) == e_before - 1
    # fight until it ends, attacking every round
    for _ in range(60):
        if p["encounter"] is None:
            break
        s = choose(p, "attack")
    assert p["encounter"] is None            # somebody won


def test_death_consequences_and_death_save():
    p = create_character(fresh())
    p["daily"]["death_save"] = True          # spend the save first
    p["level"] = 4                           # past beginner mercy
    p["gold"] = 500
    p["gear"]["armor"] = "padded_jerkin"
    p["gear"]["shield"] = "scrapwood_buckler"
    p["gear"]["weapon"] = "pigsticker"
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["hp"] = 1
    p["encounter"]["atk"] = 999              # guaranteed lethal
    s = choose(p, "stand")
    # 006 §3.6: a random 40–60% bite of gold; guard slots take wear
    # instead of destruction; each paid weapon rolls 20% gone.
    assert 500 * 0.40 <= 500 - p["gold"] <= 500 * 0.60
    assert p["gear"]["armor"] == "padded_jerkin"       # worn, not gone
    assert p["gear"]["shield"] == "scrapwood_buckler"
    assert p["gear"]["weapon"] in ("pigsticker", "rusted_sword")
    assert p["location"] == "town"
    assert s.event_kind == "death"


def test_beginner_death_mercy_keeps_gear_and_half_gold():
    # 004 §A.2: levels 1–3 keep armor/shield and lose only half gold
    p = create_character(fresh())
    p["daily"]["death_save"] = True
    p["gold"] = 500
    p["gear"]["armor"] = "padded_jerkin"
    p["gear"]["shield"] = "scrapwood_buckler"
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["hp"] = 1
    p["encounter"]["atk"] = 999
    s = choose(p, "stand")
    assert p["gold"] == 250                  # half kept
    assert p["gear"]["armor"] == "padded_jerkin"      # gear survives
    assert p["gear"]["shield"] == "scrapwood_buckler"
    assert s.event_kind == "death"


def test_backfill_heals_bare_handed_doc_with_apology():
    # 004 §A.1: docs from before the starter shiv are healed on load
    p = create_character(fresh())
    p["gear"]["weapon"] = None
    del p["hone"]
    gold = p["gold"]
    s = core.current_scene(p)
    assert p["gear"]["weapon"] == economy.STARTER_WEAPON.slug
    assert p["gold"] == gold + economy.VAULT_APOLOGY_GOLD
    assert p["hone"] == {slot: 0 for slot in economy.HONE_SLOTS}
    assert "Vault" in s.eyebrow or "Vault" in s.headline   # apology letter


def test_bare_hands_impossible_via_gear_bonus_floor():
    p = create_character(fresh())
    p["gear"]["weapon"] = None               # even if a doc slips through
    assert state.gear_bonus(p, "weapon") == economy.STARTER_WEAPON.bonus


def test_honing_buy_flow_and_reset_on_purchase():
    p = create_character(fresh())
    p["gold"] = 10_000
    p["xp"] = economy.xp_need(1)             # 006: honing burns ✦ too
    p["unlocked_floor"] = 3                  # cap = 2 this band
    hone_xp = economy.hone_xp(3)
    choose(p, "forge")
    choose(p, "buy_pigsticker")
    s = choose(p, "hone_weapon")
    assert p["hone"]["weapon"] == 1
    assert p["xp"] == economy.xp_need(1) - hone_xp  # ✦ charged alongside gold
    # 022/002: a hone level is worth its slot's weight, not a flat +1
    assert state.gear_bonus(p, "weapon") == 8 + economy.HONE_WEIGHT["weapon"]
    choose(p, "hone_weapon")
    assert p["hone"]["weapon"] == 2
    s = choose(p, "hone_weapon")             # at cap — refused
    assert p["hone"]["weapon"] == 2
    # 007: the worn rung leaves the rack — the hone-lives-on-the-item
    # rule now shows on the NEXT rung's purchase instead of a re-buy
    p["level"] = 6
    choose(p, "buy_iron_sword")
    assert p["gear"]["weapon"] == "iron_sword"
    assert p["hone"]["weapon"] == 0


def test_honing_refused_without_xp():
    p = create_character(fresh())
    p["gold"] = 10_000
    p["xp"] = 0
    p["unlocked_floor"] = 3
    choose(p, "forge")
    gold_before = p["gold"]
    s = choose(p, "hone_weapon")
    assert p["hone"]["weapon"] == 0          # atomic refusal:
    assert p["gold"] == gold_before          # neither currency charged
    assert "XP" in s.shard_note


def test_fade_no_longer_punishes_overleveling_on_frontier():
    p = create_character(fresh())
    p["level"] = 30                          # wildly over-leveled
    p["unlocked_floor"] = 1
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["encounter"]["range"] = "close"        # 002: skip the crossing
    p["encounter"]["hp"] = 1                 # next hit kills
    p["encounter"]["traits"] = []            # 025: pin threat ×1 — the
    # daily draw may be a low-pay archetype, and this test is about fade
    xp_before = p["xp"]
    gold_before = p["gold"]
    choose(p, "attack")
    # full rewards at the frontier despite the level gap
    assert p["xp"] - xp_before >= round(economy.xp_per_kill(1) * 0.75)
    assert p["gold"] > gold_before


def test_death_save_fires_once_per_day():
    p = create_character(fresh())
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["hp"] = 1
    p["encounter"]["atk"] = 999
    s = choose(p, "attack")
    assert p["hp"] == 1                      # saved at 1 HP
    assert p["daily"]["death_save"] is True
    assert s.event_kind == "death"
    assert p["gold"] > 0                     # nothing lost


def test_vault_interest_lands_as_stubs_and_collects_once():
    # 023/041: interest is never a silent credit — two days away leave
    # ten 1% slices; collecting banks the pile
    p = create_character(fresh())
    p["bank"] = 1000
    p["bank_day"] = state.world_day_f() - 2
    s = choose(p, "vault")
    assert p["bank"] == 1000                       # nothing silent
    assert len(p["interest_due"]) == 10            # 10 × ◈ 10
    assert any("collect_interest" == o.id for o in s.options)
    choose(p, "collect_interest")
    assert p["bank"] == 1100
    assert p["interest_due"] == []
    # re-entering the vault the same day materializes nothing more
    choose(p, "back")
    s = choose(p, "vault")
    assert p["bank"] == 1100
    assert not any("collect_interest" == o.id for o in s.options)


def test_forge_buy_equips_and_pawns_old():
    p = create_character(fresh())
    p["gold"] = 1500
    choose(p, "forge")
    choose(p, "buy_pigsticker")
    assert p["gear"]["weapon"] == "pigsticker"
    assert p["gold"] == 1250
    # 019: the worn rung stays on the rack as a spare; outgrowing it
    # (the next rung up) still sends the old paid one back to the pack
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_pigsticker")
    assert "spare" in row.hint
    p["level"] = 6
    choose(p, "buy_iron_sword")
    assert p["inventory"].get("pigsticker") == 1
    choose(p, "back")
    choose(p, "pawn")
    s = choose(p, "sell_pigsticker")
    # 006: the broker pays the day's rate (25–55%), not a flat 40%
    offer = int(250 * economy.pawn_rate(state.world_day()))
    assert p["gold"] == 1250 - 450 + offer
    assert "pigsticker" not in p["inventory"]


def test_energy_regen_is_lazy_and_timestamped():
    p = create_character(fresh())
    p["energy_val"] = 0.0
    p["energy_ts"] = (state.now() - dt.timedelta(minutes=90)).isoformat()
    assert state.energy_now(p) == 2          # 90min / 45min per point


def test_lodge_and_medlab_daily_caps():
    p = create_character(fresh())
    p["gold"] = 1000
    choose(p, "lodge")
    choose(p, "lie_down")               # 041: turning in pays the bunk
    assert p["lodged_until_day"] == state.world_day() + 1
    choose(p, "wake")
    choose(p, "back")
    choose(p, "medlab")
    choose(p, "buy_energy_cell")
    assert p["daily"]["energy_cell"] is True
    gold_after = p["gold"]
    s = choose(p, "buy_energy_cell")         # second cell refused
    assert p["gold"] == gold_after
    assert s.shard_note


def test_scene_is_idempotent():
    p = create_character(fresh())
    a = core.current_scene(p).to_dict()
    b = core.current_scene(p).to_dict()
    assert a["options"] == b["options"]
    assert p["encounter"] is None


def test_encounter_carries_id_for_creature_art():
    # regression: _opener_banner keys creature art off encounter id.
    # The pick is seeded off the world day, so pin to the floor's own
    # roster instead of a hand-typed set that drifts.
    from plugin_linear_ascent.content import schema
    p = create_character(fresh())
    choose(p, "gate")
    choose(p, "floor_1")
    s = choose(p, "hunt")
    assert p["encounter"]["id"] in {e.id for e in
                                    schema.get_floor(1).encounters}
    assert s.banner == p["encounter"]["id"]      # floor-1 art is shipped


# ── 006: the XP pool replaces mana ───────────────────────────────────────

def test_spend_xp_floors_at_zero_and_never_touches_level():
    p = create_character(fresh())
    p["level"], p["xp"] = 5, 10
    assert state.spend_xp(p, 11) is False
    assert (p["level"], p["xp"]) == (5, 10)      # refusal changes nothing
    assert state.spend_xp(p, 10) is True
    assert (p["level"], p["xp"]) == (5, 0)


def test_sleep_spell_burns_kill_xp_and_awards_nothing():
    p = create_character(fresh(), clazz="sorcerer")
    cost = economy.sleep_xp_cost(1)
    p["xp"] = cost + 5
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    s = choose(p, "sleep_spell")
    assert p["encounter"] is None                # fight skipped
    assert p["xp"] == 5                          # cost burned, nothing awarded
    assert p["level"] == 1
    # broke sorcerer: refusal keeps the fight alive and the pool intact
    p["xp"] = cost - 1
    choose(p, "hunt")
    s = choose(p, "sleep_spell")
    assert p["encounter"] is not None
    assert p["xp"] == cost - 1
    assert "XP" in "\n".join(s.body_lines)


def test_scan_prefers_charges_then_falls_back_to_xp():
    p = create_character(fresh())
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    scan_cost = economy.scan_xp_cost(1)
    p["sidekick"]["scout_charges"] = 1
    p["xp"] = scan_cost
    s = choose(p, "scout")
    assert p["sidekick"]["scout_charges"] == 0
    assert p["xp"] == scan_cost                  # charge used, ✦ untouched
    s = choose(p, "scout")                       # falls back to the pool
    assert p["xp"] == 0
    assert "scan" in "\n".join(s.body_lines)
    s = choose(p, "scout")                       # broke: refused, fight lives
    assert p["encounter"] is not None
    assert "XP" in "\n".join(s.body_lines)


def test_forge_tier_gated_by_level():
    # 004: the shop only RACKS what your level unlocks — the next rung
    # shows greyed with its level, and a forced buy is refused unpaid.
    p = create_character(fresh())
    p["gold"] = 100_000
    p["unlocked_floor"] = 11                     # tier-2 stock, level 11 req
    s = choose(p, "forge")
    assert not any(o.id == "buy_wolfbite" for o in s.options)
    # 019: the lock is a dimmed ROW with the level, not prose
    nxt = next(o for o in s.options if o.locked and o.id.startswith("buy_"))
    assert "level 2" in nxt.hint                 # 025: a rung per level
    s = choose(p, "buy_wolfbite")
    assert p["gear"]["weapon"] != "wolfbite"     # refused at level 1
    assert p["gold"] == 100_000                  # not charged
    p["level"] = 11                              # the rack re-reads level
    choose(p, "buy_wolfbite")
    assert p["gear"]["weapon"] == "wolfbite"


def test_floor_gated_by_level():
    p = create_character(fresh())
    p["unlocked_floor"] = 40                     # world lift far ahead
    choose(p, "gate")
    s = choose(p, "floor_12")                    # needs level 2, we are 1
    assert p["floor"] == 0
    assert "level" in s.shard_note
    s = choose(p, "floor_11")                    # F−10 = 1: allowed
    assert p["floor"] == 11


def test_elf_learns_faster():
    p = create_character(fresh(), race="elf")
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["encounter"]["range"] = "close"        # 002: skip the crossing
    p["encounter"]["hp"] = 1
    p["encounter"]["traits"] = []            # 025: pin threat ×1 — the
    # daily draw may be a low-pay archetype, and this test is about race
    choose(p, "attack")
    # base 4 ±25% then ×1.05: minimum possible is round(round(4·0.75)·1.05)
    assert p["xp"] >= round(round(4 * 0.75) * 1.05)


# ── 017: encounter traits → defense profiles ─────────────────────────────

def test_floor_one_teaches_shapes_not_counters():
    """017 §2.3 + 025 §1: floor 1 carries no COUNTER — no armor, resist,
    flying or bulwark, because nothing has been bought to answer them
    yet. It does carry archetypes: before 025 the whole floor shared one
    stat line and all four animals were the same monster in costume."""
    from plugin_linear_ascent.content import schema
    from plugin_linear_ascent import economy
    fl = schema.get_floor(1)
    assert len(fl.encounters) >= 4
    counters = {"armored", "flying", "bulwark"}
    shapes = set()
    for e in fl.encounters:
        for t in e.traits:
            assert t not in counters and not t.startswith(("armor_",
                                                          "resist_")), \
                f"{e.id} carries counter trait {t!r} on floor 1"
        shapes.add(economy.creature_stats(1, e.traits))
    assert len(shapes) >= 3, f"floor 1 has only {len(shapes)} stat lines"


def test_profile_derived_and_stored_on_encounter():
    from plugin_linear_ascent.content import schema
    from plugin_linear_ascent.engine import combat
    fl = schema.get_floor(2)
    tortoise = next(e for e in fl.encounters
                    if e.id == "shellback_tortoise")
    p = create_character(fresh())
    combat.start_encounter(p, fl, tortoise)
    prof = p["encounter"]["profile"]
    assert prof["armor"] == "low" and prof["resist"] == "none"
    assert not prof["flying"] and not prof["bulwark"]


def test_med_plate_resists_the_treeline_shot():
    from plugin_linear_ascent.content import schema
    from plugin_linear_ascent.engine import combat
    fl = schema.get_floor(10)
    guard = next(e for e in fl.encounters if e.id == "kings_guard")
    p = create_character(fresh(), clazz="archer")
    combat.start_encounter(p, fl, guard)
    e = p["encounter"]
    e["hp"] = e["hp_max"] = 10_000                   # survive the shot
    s = combat.resolve_fight_action(p, fl, "treeline_shot")
    assert e["shot_used"] is True
    note = " ".join(s.body_lines)
    assert "snaps against its plate" in note         # no double damage
    dealt = 10_000 - e["hp"]
    assert dealt <= state.atk(p)                     # single-mult ceiling


def test_legacy_doc_with_mana_keys_still_loads():
    p = create_character(fresh())
    # a pre-006 doc carries mana keys and a stored scene with mana meters —
    # preserved (never deleted), never read
    p["mana_ts"], p["mana_val"] = state.now().isoformat(), 7.0
    p.setdefault("pending_events", []).append({
        "eyebrow": "X", "headline": "old present",
        "options": [{"id": "town", "label": "ok", "hint": "", "aether": False}],
        "meters": {"hp": 52, "hp_max": 52, "energy": 24, "energy_max": 24,
                   "mana": 7, "mana_max": 10, "gold": 50},
    })
    s = core.current_scene(p)                    # must not raise
    assert s.headline == "old present"
    assert s.meters.xp == 7                      # legacy keys mapped
    assert p["mana_val"] == 7.0                  # data preserved
