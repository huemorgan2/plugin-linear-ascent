"""031 — the shape of things: the render punch list, held by tests.

§1 no stripe survives.  §4 the ident header (name · who / LEVEL · COINS).
§3 the slot-grid pack with a promoted hand row.  §9 Wick has a face.
§11 the activity band.  §13 art rides the in-floor choice, not the floor
list.  §14 the Forge is a card wall — pictures with a cost, the [i] kept,
and not one line of prose above the racks.  The wire carries all of it
BESIDE the options (option_art / grid / npc / activity are top-level
scene fields old clients drop safely).
"""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, scene as scene_mod, state


def fresh(tag):
    return state.new_player(f"test-user-031-{tag}")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="elf", clazz="archer", name="Testa"):
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


# ── §14: the Forge card wall ─────────────────────────────────────────────

def test_forge_scene_is_a_grid_with_no_prose():
    # 048: one exception — the folded plain-words legend; folded shut,
    # it costs the wall no prose
    p = create_character(fresh("wall"))
    s = choose(p, "forge")
    assert s.grid
    assert s.support == ""
    assert s.body_lines[0].startswith("▣ ") and s.body_lines[-1] == "▣."


def test_forge_renders_cards_for_gear_and_rows_for_the_bench():
    p = create_character(fresh("cards"))
    p["gold"], p["level"] = 10_000, 4
    choose(p, "forge")
    choose(p, "buy_scrap_dagger")
    p["durability"]["weapon"] = 1          # earn a repair row
    s = core.current_scene(p)
    frag = render.render_scene_fragment(s)
    assert 'class="ggrid"' in frag
    assert 'class="opt gcard"' in frag
    # buys are cards; the bench and the door stay rows
    assert 'gcard" data-opt="buy_' in frag or \
           'gcard locked" data-opt="buy_' in frag
    assert 'class="orow"' in frag
    row_ids = [o.id for o in s.options
               if not (o.id.startswith("buy_") or o.id.startswith("wear_"))]
    assert "back" in row_ids
    # every buy card still carries its whisper glyph next door
    cards = frag.count("gcard")
    assert cards >= 3 and frag.count('class="info"') >= cards // 2


def test_forge_hints_carry_the_stat_the_prose_used_to():
    p = create_character(fresh("stat"), clazz="warrior")
    p["gold"] = 10_000
    s = choose(p, "forge")
    # 049: the basics carry a stat + durability hint like any card now
    buy = [o for o in s.options if o.id.startswith("buy_")
           and o.id.removeprefix("buy_") in economy.FORGE]
    assert buy
    for o in buy:
        assert ("ATK" in o.hint or "DEF" in o.hint or "spd" in o.hint), \
            (o.id, o.hint)
        assert "◈" in o.hint


def test_grid_never_leaks_into_row_scenes():
    p = create_character(fresh("rows"))
    s = choose(p, "lodge")
    assert not s.grid
    frag = render.render_scene_fragment(s)
    assert "ggrid" not in frag


# ── §1: the stripe is gone ───────────────────────────────────────────────

def test_no_left_stripe_anywhere_in_the_card_css():
    assert "border-left" not in render.SCENE_CSS


# ── §4: the ident header ─────────────────────────────────────────────────

def test_ident_header_names_you_and_bolds_the_purse():
    p = create_character(fresh("ident"), race="elf", clazz="archer",
                         name="Vael")
    frag = render.render_scene_fragment(core.current_scene(p))
    assert 'class="ident later"' in frag
    assert "Vael" in frag
    # 048: the calling is the weapon path in hand, not a class
    assert "elf" in frag.lower() and "bow" in frag.lower()
    assert "LEVEL" in frag and "COINS" in frag


def test_ident_header_names_your_faction_with_a_tooltip():
    p = create_character(fresh("ident-fac"), race="elf", clazz="archer",
                         name="Vael")
    frag = render.render_scene_fragment(core.current_scene(p))
    assert "faction" not in frag.split('class="ident')[1][:300]  # bannerless
    p["_world"] = {"faction": {"name": "Ironvow"}}
    frag = render.render_scene_fragment(core.current_scene(p))
    assert "of Ironvow" in frag
    assert "home of all the factions" in frag   # the tooltip points home


# ── §3: the slot-grid pack ───────────────────────────────────────────────

def test_pack_is_a_slot_grid_with_a_promoted_hand_row():
    p = create_character(fresh("pack"))
    p["inventory"]["medgel"] = 2
    frag = render.render_scene_fragment(core.current_scene(p))
    assert 'class="slotgrid"' in frag
    # 069: the hand row became the gear map — seven slots round the figure
    assert 'class="handrow"' not in frag
    assert 'class="gearmap later"' in frag
    assert 'class="slot empty"' in frag     # blocked spaces wait for loot


# ── §9 + §11: the lodge ──────────────────────────────────────────────────

def test_wick_rideses_the_wire_and_the_lodge_band_shows_the_evening():
    p = create_character(fresh("lodge"))
    p["level"] = economy.NIGHT_SLOT_LEVEL
    s = choose(p, "lodge")
    assert s.activity.startswith("ACTIVITY IN THE LODGE:")
    ids = {o.id for o in s.options}
    assert "talk" in ids
    labels = {o.id: o.label for o in s.options}
    assert labels["night_work"].startswith("JOB OFFER:")
    assert labels["night_rest"].startswith("ACTIVITY:")
    frag = render.render_scene_fragment(s)
    assert 'class="actband later"' in frag
    s2 = choose(p, "talk")
    assert s2.npc and s2.npc["name"] == "Wick"
    frag2 = render.render_scene_fragment(s2)
    assert 'class="npcbox later"' in frag2 and "Wick" in frag2


# ── §13: art on the in-floor choice ──────────────────────────────────────

def test_option_art_rides_the_gate_town_not_the_floor_list():
    p = create_character(fresh("art"))
    s = choose(p, "gate")
    assert not s.option_art                 # the floor list is plain rows
    s = choose(p, "floor_1")
    assert s.option_art.get("hunt")
    assert s.option_art.get("keep", "").startswith("warden_")
    frag = render.render_scene_fragment(s)
    assert 'class="farts"' in frag


# ── the wire law ─────────────────────────────────────────────────────────

def test_the_new_fields_survive_the_wire_and_die_politely():
    p = create_character(fresh("wire"))
    p["level"] = economy.NIGHT_SLOT_LEVEL
    choose(p, "lodge")
    s = choose(p, "talk")
    d = s.to_dict()
    back = scene_mod.Scene.from_dict(d)
    assert back.npc == s.npc and back.activity == s.activity
    assert back.grid == s.grid and back.option_art == s.option_art
    # an old client that never heard of these keys still round-trips
    for k in ("npc", "activity", "grid", "option_art"):
        d.pop(k, None)
    old = scene_mod.Scene.from_dict(d)
    assert old.npc is None and old.activity == ""
    assert old.grid is False and old.option_art == {}
