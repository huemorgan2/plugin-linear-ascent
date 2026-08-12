"""017 phase 007 — armory (engine side), matchup moment, town readability.

The armory's EV law lives in worldd tests; here we prove the engine
half: donate options for members only, the desk's rack section, the
one-take cooldown honored from the injection, and the effects emitted.
Plus: the matchup moment fires once per hard-counter TYPE, the town
list leads with the gate and locks its doors out loud, worn rungs
leave the rack, and long relic shelves fold.
"""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state, tips


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Rook"):
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


def _start(p, floor_no, enc_id):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    return combat.start_encounter(p, fl, enc)


def _member_world(rack=None, took=False):
    """The slice worldd injects for a faction member."""
    return {
        "social": True, "frontier": 5,
        "faction": {"name": "Oakhearts", "store": 0, "dues": 5,
                    "join_fee": 0, "role": "member", "members": [],
                    "week": {}},
        "armory": rack if rack is not None else [],
        "armory_cap": 50,
        "armory_took_today": took,
    }


def _rack_row(item_id=7, slug="pigsticker", frac=1.0, donor="Giver"):
    g = economy.FORGE[slug]
    return {"id": item_id, "slug": slug, "name": g.name, "slot": g.slot,
            "bonus": g.bonus, "frac": frac, "donor": donor}


# ── matchup moment (§5) ──────────────────────────────────────────────────

def test_matchup_fires_once_per_hard_counter_type():
    p = create_character(fresh("ma-1"))          # warrior: flying = wall
    s = _start(p, 4, "glare_moth")
    assert s.event_kind == "matchup"
    assert "glare_moth" in p["matchup_seen"]
    # the same TYPE again: silence
    s = _start(p, 4, "glare_moth")
    assert s.event_kind == ""


def test_matchup_ignores_soft_counters_and_wrong_class():
    p = create_character(fresh("ma-2"))          # warrior
    s = _start(p, 1, "feral_boar")               # plain monster
    assert s.event_kind == ""
    assert not p.get("matchup_seen")
    # an archer facing the same flyer: wings are no wall for arrows
    a = create_character(fresh("ma-3"), clazz="archer")
    s = _start(a, 4, "glare_moth")
    assert s.event_kind == ""


def test_hard_counter_map_by_damage_type():
    p = create_character(fresh("ma-4"))
    assert combat._hard_counter(p, {"type": "fly"})
    assert not combat._hard_counter(p, {"type": "armoured"})
    a = create_character(fresh("ma-5"), clazz="archer")
    assert combat._hard_counter(a, {"type": "armoured"})
    assert not combat._hard_counter(a, {"type": "fly"})
    m = create_character(fresh("ma-6"), clazz="sorcerer")
    assert combat._hard_counter(m, {"type": "magic_resist"})
    assert not combat._hard_counter(m, {"type": "armoured"})


# ── town readability (§4) ────────────────────────────────────────────────

def test_the_gate_leads_the_square():
    p = create_character(fresh("tw-1"))
    s = core.current_scene(p)
    assert s.options[0].id == "gate"
    assert "climb" in s.options[0].hint


def test_locked_doors_read_their_level_from_the_square():
    p = create_character(fresh("tw-2"))
    p["_world"] = _member_world()
    s = core._town_scene(p)
    by_id = {o.id: o for o in s.options}
    assert f"level {economy.RELAY_LEVEL}" in by_id["relay"].hint
    assert f"level {economy.FIELDS_LEVEL}" in by_id["fields"].hint
    # the doors refuse below the level, with a reason
    s = choose(p, "relay")
    assert p["location"] == "town" and "level" in s.shard_note
    s = choose(p, "fields")
    assert p["location"] == "town" and "level" in s.shard_note
    # at level, the locks come off
    p["level"] = max(economy.RELAY_LEVEL, economy.FIELDS_LEVEL)
    s = core._town_scene(p)
    by_id = {o.id: o for o in s.options}
    assert "🔒" not in by_id["relay"].hint
    assert "🔒" not in by_id["fields"].hint


# ── shop owned-state (004 dojo carryover) ────────────────────────────────

def test_the_worn_rung_stays_on_the_rack_as_a_spare():
    # 019: owning a piece never hides it — spares feed the armory
    p = create_character(fresh("sh-1"))
    p["gold"] = 10_000
    choose(p, "forge")
    choose(p, "buy_pigsticker")
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_pigsticker")
    assert "worn — spare" in row.hint


# ── folded shelves (006 retro) ───────────────────────────────────────────

def test_fold_markers_still_work_and_the_forge_wall_stays_bare():
    # 031 §14: the Forge card wall retired the only shelf long enough to
    # fold — but the ▣ machinery stays live (THE LONG FIRE still uses
    # it), so the render law is held here on its own
    from plugin_linear_ascent.engine.scene import Scene
    s = Scene(eyebrow="E", headline="H",
              body_lines=["▣ the relic shelf — 3 on the wall",
                          "row one", "row two", "▣."])
    html = render.render_scene_fragment(s)
    assert '<details class="fold">' in html and "▣" not in html
    txt = s.to_text()
    assert "▣" not in txt and "— the relic shelf" in txt
    # 048: the Forge's only prose is the folded plain-words legend —
    # cards and rows carry everything else
    q = create_character(fresh("fo-2"))
    choose(q, "forge")
    fs = core.current_scene(q)
    assert fs.grid and fs.support == ""
    assert fs.body_lines[0].startswith("▣ ") and fs.body_lines[-1] == "▣."


# ── the armory, engine side ──────────────────────────────────────────────

def test_pawn_offers_the_donate_to_members_only():
    p = create_character(fresh("ar-1"))
    p["inventory"]["pigsticker"] = 1
    choose(p, "pawn")
    s = core.current_scene(p)
    assert not any(o.id.startswith("donate_") for o in s.options)
    p["_world"] = _member_world()
    s = core._pawn_scene(p)
    assert any(o.id == "donate_pigsticker" for o in s.options)
    # free starter steel is not donatable
    assert not any(o.id == "donate_rusted_sword" for o in s.options)


def test_donate_lifts_the_piece_and_its_wear_into_the_effect():
    p = create_character(fresh("ar-2"))
    p["_world"] = _member_world()
    p["inventory"]["pigsticker"] = 1
    p.setdefault("durability_pack", {})["pigsticker"] = 42
    p["location"] = "pawn"
    gold0 = p["gold"]
    s = choose(p, "donate_pigsticker")
    assert "goes to the Oakhearts racks" in " ".join(s.body_lines)
    assert "pigsticker" not in p["inventory"]
    assert "pigsticker" not in p["durability_pack"]
    assert p["gold"] == gold0                        # the EV law
    fx = [e for e in p["_effects"] if e["kind"] == "armory_deposit"]
    assert fx == [{"kind": "armory_deposit", "slug": "pigsticker",
                   "uses_left": 42}]


def test_full_racks_refuse_before_the_piece_moves():
    p = create_character(fresh("ar-3"))
    p["_world"] = _member_world(rack=[_rack_row(item_id=i)
                                      for i in range(50)])
    p["inventory"]["pigsticker"] = 1
    p["location"] = "pawn"
    s = choose(p, "donate_pigsticker")
    assert "full" in s.shard_note
    assert p["inventory"]["pigsticker"] == 1
    assert not p.get("_effects")


def test_the_desk_lists_the_rack_and_takes_once():
    p = create_character(fresh("ar-4"))
    p["_world"] = _member_world(rack=[_rack_row(frac=0.33)])
    s = choose(p, "guildhall")
    joined = " ".join(s.body_lines)
    assert "ARMORY 1/50" in joined
    assert "worn to 33%" in joined and "from Giver" in joined
    s = choose(p, "take_arm_7")
    assert "comes off the rack" in " ".join(s.body_lines)
    fx = [e for e in p["_effects"] if e["kind"] == "armory_take"]
    assert fx == [{"kind": "armory_take", "item_id": 7}]
    # optimistic state: row gone, cooldown on — no second take today
    assert p["_world"]["armory"] == []
    assert p["_world"]["armory_took_today"] is True


def test_the_cooldown_hides_the_take_and_refuses_a_forced_one():
    from plugin_linear_ascent.engine import social
    p = create_character(fresh("ar-5"))
    p["_world"] = _member_world(rack=[_rack_row()], took=True)
    s = choose(p, "guildhall")
    assert not any(o.id.startswith("take_arm_") for o in s.options)
    assert "already took" in " ".join(s.body_lines)
    # a forced take (stale card, crafted click) refuses on the guard
    s = social._armory_take(p, "7")
    assert "tomorrow" in " ".join(s.body_lines)
    assert not p.get("_effects")


def test_armory_options_carry_tips():
    assert "no coin" in tips.option_tip("donate_pigsticker")
    assert "One take" in tips.option_tip("take_arm_7")
