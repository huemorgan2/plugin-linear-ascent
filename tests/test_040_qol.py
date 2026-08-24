"""040 — four quality-of-life rules from live play.

1. The Sleep door shows only when the energy bar is dry.
2. One verb for making ground: the archer's gap ladder wears the
   "Open distance" label and the footwork gamble never doubles it;
   the ladder carries its own [i] tip.
3. The treeline shot is the OPENING move — offered from the distance
   only, and any attack burns it for the rest of the fight.
4. Held post opens the Relay door at any level, and the notice board
   says so — a level-1 climber granted gold can actually collect it.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import combat, core, notices, state, tips
from plugin_linear_ascent.content import schema


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Nap"):
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


def _drain(p):
    p["energy_val"] = 0.0
    p["energy_ts"] = state.now().isoformat()


def _enc(floor_no, slug):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == slug)
    return fl, enc


# ── 1. the sleep door ────────────────────────────────────────────────────

def test_sleep_door_always_open():
    # 042: the door is always there — rested or dry, sleep is the
    # player's call.
    p = create_character(fresh("qol-sleep"), name="Rested")
    ids = [o.id for o in core.current_scene(p).options]
    assert "sleep_menu" in ids
    _drain(p)
    ids = [o.id for o in core.current_scene(p).options]
    assert "sleep_menu" in ids


def test_the_lodge_still_offers_turning_in_when_rested():
    p = create_character(fresh("qol-lodge"), name="Planner")
    core.apply_choice(p, "lodge")
    s = core.current_scene(p)
    assert any(o.id == "lie_down" for o in s.options)


# ── 2. one "Open distance" row ───────────────────────────────────────────

def test_archer_sees_exactly_one_open_distance_row():
    fl, enc = _enc(1, "grey_wolf")
    p = create_character(fresh("qol-gap"), clazz="archer", name="Fletch")
    combat.start_encounter(p, fl, enc)
    # drag the fight into close quarters where both rows used to stack
    p["encounter"]["range"] = "close"
    p["encounter"]["gap"] = 0
    p["encounter"]["profile"]["speed"] = economy.SPEED_SLOW
    s = combat.fight_scene(p, fl)
    rows = [o for o in s.options if o.label == "Open distance"]
    assert len(rows) == 1
    assert rows[0].id == "create_distance"      # the ladder won the label
    assert "open_distance" not in [o.id for o in s.options]


def test_the_gap_ladder_carries_its_own_tip():
    # 075 plain-English copy: the ladder explained without multipliers
    tip = tips.option_tip("create_distance")
    assert tip
    assert "2 paces" in tip and "harder from farther away" in tip


def test_non_archers_keep_the_footwork_row():
    fl, enc = _enc(1, "grey_wolf")
    p = create_character(fresh("qol-foot"), name="Boots")
    combat.start_encounter(p, fl, enc)
    p["encounter"]["range"] = "close"
    p["encounter"]["gap"] = 0
    p["encounter"]["profile"]["speed"] = economy.SPEED_SLOW
    ids = [o.id for o in combat.fight_scene(p, fl).options]
    assert "open_distance" in ids and "create_distance" not in ids


# ── 3. the treeline shot is the opener ───────────────────────────────────

def test_treeline_is_offered_at_range_not_in_close():
    fl, enc = _enc(1, "grey_wolf")
    p = create_character(fresh("qol-tree"), clazz="archer", name="Cover")
    s = combat.start_encounter(p, fl, enc)          # fights open at range
    assert "treeline_shot" in [o.id for o in s.options]
    p["encounter"]["range"] = "close"
    p["encounter"]["gap"] = 0
    assert "treeline_shot" not in [
        o.id for o in combat.fight_scene(p, fl).options]


def test_any_attack_burns_the_treeline_for_the_fight():
    fl, enc = _enc(1, "grey_wolf")
    p = create_character(fresh("qol-burn"), clazz="archer", name="Loosed")
    combat.start_encounter(p, fl, enc)
    p["hp"] = 10_000                                # survive the answer
    combat.resolve_fight_action(p, fl, "attack")
    e = p.get("encounter")
    if not e:                                        # the wolf died to it
        return
    assert e["attacked"] is True
    s = combat.fight_scene(p, fl)
    assert "treeline_shot" not in [o.id for o in s.options]
    # even re-opening the distance does not bring the cover back
    combat.resolve_fight_action(p, fl, "create_distance")
    if p.get("encounter"):
        s = combat.fight_scene(p, fl)
        assert "treeline_shot" not in [o.id for o in s.options]


def test_a_stale_treeline_click_after_attacking_is_refused():
    fl, enc = _enc(1, "grey_wolf")
    p = create_character(fresh("qol-stale"), clazz="archer", name="Poke")
    combat.start_encounter(p, fl, enc)
    p["hp"] = 10_000
    combat.resolve_fight_action(p, fl, "attack")
    e = p.get("encounter")
    if not e:
        return
    hp0 = e["hp"]
    combat.resolve_fight_action(p, fl, "treeline_shot")
    e2 = p.get("encounter")
    if e2:
        # the poke fell through to a plain attack — never the ×2 opener
        assert e2["shot_used"] is False


# ── 4. held post opens the Relay at any level ────────────────────────────

def test_a_letter_opens_the_relay_door_for_level_one():
    p = create_character(fresh("qol-post"), name="Green")
    assert p["level"] < economy.RELAY_LEVEL
    p["_world"] = {"inbox_count": 1}
    s = core.current_scene(p)
    relay = next(o for o in s.options if o.id == "relay")
    assert not relay.locked
    assert "letter" in relay.hint
    # and the door actually opens
    core.apply_choice(p, "relay")
    assert p["location"] == "relay"


def test_no_post_keeps_the_relay_locked_below_level():
    p = create_character(fresh("qol-lock"), name="Still")
    assert p["level"] < economy.RELAY_LEVEL
    p["_world"] = {"inbox_count": 0}
    s = core.current_scene(p)
    relay = next(o for o in s.options if o.id == "relay")
    assert relay.locked
    core.apply_choice(p, "relay")
    assert p["location"] == "town"                   # bounced, with a note


def test_the_notice_board_announces_letters_at_any_level():
    p = create_character(fresh("qol-board"), name="Told")
    assert p["level"] < economy.RELAY_LEVEL
    rows = notices.pending(p, {"inbox_count": 2})
    relay_rows = [r for r in rows if r["door"] == "relay"]
    assert relay_rows and relay_rows[0]["n"] == 2
    assert "gold" in relay_rows[0]["text"]
