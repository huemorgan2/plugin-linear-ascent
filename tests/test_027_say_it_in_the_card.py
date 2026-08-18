"""027 — say it in the card.

Five things the card knew and never said: a bare "(1)" on a door, a pack
that filled with salves it wouldn't let you eat, a rail that blinked to a
new number instead of counting to it, a name it demanded you type into the
chat, and a banner it drew as a filename.
"""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, contracts, core, notices, state


def playing(name="Sayer", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def hall_world():
    return {"social": True,
            "factions": [{"name": "Ember Pact", "banner": "wolf_howl",
                          "join_fee": 25, "weekly_dues": 5, "members": 3}],
            "faction_banners": ["wolf_howl", "iron_heart", "gear_sword",
                                "watch_owl", "web_star", "mecha_dragon",
                                "chained_sun", "storm_fist"]}


def door(scene, oid):
    return next(o for o in scene.options if o.id == oid)


def kinds(scene, door_name):
    return [n["kind"] for n in scene.notices if n["door"] == door_name]


# ── the notice board ─────────────────────────────────────────────────────

def test_every_count_on_a_door_also_gets_a_sentence():
    """The whole complaint: a number with no words is a riddle."""
    p = playing("sentence")
    p["bank"], p["bank_day"] = 300, state.world_day_f() - 2
    s = core.current_scene(p)
    assert door(s, "vault").badge == 10          # 041: 2 days × 5 slices
    said = [n for n in s.notices if n["door"] == "vault"]
    assert len(said) == 1
    assert "Vault" in said[0]["text"] and "stub" in said[0]["text"]
    assert "◈" in said[0]["text"]          # what it is WORTH, not just how many
    assert said[0]["opt"] == "vault"       # and the row is the shortcut


def test_the_lodge_says_plan_and_never_says_collect():
    """The lodge (1) read like loot behind a door. It is a decision that
    dawn makes for you if you ignore it — a different word entirely."""
    p = playing("planner")
    p["level"] = economy.NIGHT_SLOT_LEVEL
    s = core.current_scene(p)
    assert kinds(s, "lodge") == ["plan"]
    line = next(n for n in s.notices if n["door"] == "lodge")
    assert "unplanned" in line["text"]
    assert "collect" not in line["text"].lower()
    core.apply_choice(p, "lodge")
    core.apply_choice(p, "night_rest")
    s = core.apply_choice(p, "back")
    assert kinds(s, "lodge") == []


def test_the_forge_badges_a_free_mend_and_broken_steel():
    p = playing("smith")
    s = core.current_scene(p)
    assert door(s, "forge").badge == 0          # a forge is not a claim
    p["inventory"]["repair_token"] = 2
    s = core.current_scene(p)
    assert door(s, "forge").badge == 2
    assert "repair token" in " ".join(n["text"] for n in s.notices)
    p["inventory"].pop("repair_token")
    p["gear"]["armor"] = "padded_jerkin"
    p["durability"] = {"armor": 0}
    s = core.current_scene(p)
    assert door(s, "forge").badge == 1
    assert "half strength" in " ".join(n["text"] for n in s.notices)


def test_the_guildhall_badges_a_level_you_can_actually_buy():
    p = playing("trainee")
    p["xp"] = economy.xp_need(p["level"])
    p["gold"] = 0
    s = core.current_scene(p)
    assert door(s, "guildhall").badge == 0      # a full bar with no fee
    p["gold"] = economy.levelup_gold(p["level"])
    s = core.current_scene(p)
    assert door(s, "guildhall").badge == 1
    assert "LEVEL 2" in " ".join(n["text"] for n in s.notices)


def test_a_notice_rides_every_room_in_town_but_never_the_climb():
    p = playing("rider")
    p["bank"], p["bank_day"] = 300, state.world_day() - 1
    assert core.apply_choice(p, "forge").notices        # the Forge says it too
    assert core.apply_choice(p, "back").notices
    s = core.apply_choice(p, "gate")
    assert s.notices == []                             # the climb stays clean


def test_a_notice_row_is_a_shortcut_from_any_room():
    """Clicking the Vault's notice while standing in the Forge walks you
    there — the row is the door, not a label."""
    p = playing("shortcut")
    p["bank"], p["bank_day"] = 300, state.world_day() - 1
    core.apply_choice(p, "forge")
    s = core.apply_choice(p, "vault")
    assert "VAULT" in s.eyebrow.upper()
    assert any(o.id == "collect_interest" for o in s.options)


def test_the_card_draws_the_notice_as_a_notice_not_a_menu_row():
    p = playing("drawn")
    p["bank"], p["bank_day"] = 300, state.world_day() - 1
    html = render.render_scene_fragment(core.current_scene(p))
    assert 'class="notices"' in html
    assert 'class="nrow" data-opt="vault"' in html
    assert 'class="nb"' in html                  # the blue count chip
    assert 'class="badge"' in html               # and the door's own chip
    # the notice board sits ABOVE the location line, not among the options
    assert html.index('class="notices"') < html.index('class="eyebrow')
    assert html.index('class="notices"') < html.index('class="options')


def test_blue_is_the_notification_ink():
    assert render.AETHER in render.SCENE_CSS.split(".nb,")[1][:200]


# ── the pack has a mouth ─────────────────────────────────────────────────

def test_a_salve_can_be_used_from_the_pack_in_any_room():
    p = playing("eater")
    p["inventory"]["medgel"] = 2
    p["hp"] = 10
    acts, why = core.pack_actions(p, "medgel")
    assert [o.id for o in acts] == ["use_medgel"]
    assert "+25 HP" in acts[0].hint and not why
    s = core.apply_choice(p, "use_medgel")           # standing in the square
    assert p["hp"] == 35 and p["inventory"]["medgel"] == 1
    assert "25 HP" in s.body_lines[0]
    assert "SQUARE" in s.eyebrow                     # never teleports you


def test_a_whole_body_refuses_the_salve_and_says_why():
    p = playing("whole")
    p["inventory"]["medgel"] = 1
    acts, why = core.pack_actions(p, "medgel")
    assert acts == [] and "whole" in why
    s = core.apply_choice(p, "use_medgel")
    assert p["inventory"]["medgel"] == 1             # nothing burned
    assert "whole" in s.shard_note


def test_the_tonic_is_still_the_only_heal_in_a_fight():
    p = playing("fighter")
    p["inventory"]["medgel"] = 1
    p["inventory"]["trollblood_tonic"] = 1
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    while not p.get("encounter"):
        core.apply_choice(p, "hunt")
    p["hp"] = 10
    # 069: in a fight the pack is inert — every row is refused with a why
    acts, why = core.pack_actions(p, "medgel")
    assert acts == [] and why
    tonic, why = core.pack_actions(p, "trollblood_tonic")
    assert tonic == [] and "pouch" in why.lower()
    s = core.apply_choice(p, "use_medgel")
    assert p["inventory"]["medgel"] == 1             # the fight refused it
    assert p.get("encounter")                        # and the fight goes on
    # …the pouch is the only thing that acts
    p["gear"]["charm"] = "trollblood_tonic"
    fl = schema.get_floor(1)
    opts = [o.id for o in combat.fight_scene(p, fl).options]
    assert "drink_tonic" in opts and "drink_medgel" not in opts
    p["gear"]["charm"] = "medgel"
    opts = [o.id for o in combat.fight_scene(p, fl).options]
    assert "drink_medgel" in opts and "drink_tonic" not in opts


def test_a_charm_in_the_pack_is_inert_and_says_so():
    """069: a charm is WORN in the pouch — the pack row has no use verb."""
    p = playing("lucky")
    p["inventory"]["luck_charm"] = 1
    acts, why = core.pack_actions(p, "luck_charm")
    assert not any(o.id == "use_luck_charm" for o in acts)
    assert "pouch" in why.lower() or acts
    core.apply_choice(p, "use_luck_charm")
    assert "luck_day" not in p["flags"]
    assert p["inventory"]["luck_charm"] == 1


def test_a_thing_with_nothing_to_do_here_says_where_it_can():
    p = playing("token")
    p["inventory"]["repair_token"] = 1
    acts, why = core.pack_actions(p, "repair_token")
    assert acts == [] and "Forge" in why


def test_the_pack_strip_carries_its_actions_to_the_card():
    p = playing("strip")
    p["inventory"]["medgel"] = 1
    p["hp"] = 10
    s = core.current_scene(p)
    cell = next(c for c in s.inventory if c["slug"] == "medgel")
    assert cell["acts"] == [{"opt": "use_medgel", "label": "Use a Medgel",
                             "hint": "+25 HP · 1 left"}]
    html = render.render_scene_fragment(s)
    assert 'data-acts="' in html and "use_medgel" in html
    # 031 §3: the cell is a slot button in the pack grid now
    assert 'class="slot item act' in html


def test_the_rail_can_be_counted_not_just_read():
    p = playing("counter")
    html = render.render_scene_fragment(core.current_scene(p))
    for key in ("hp", "en", "xp", "gold"):
        assert f'data-m="{key}"' in html
    assert 'data-max=' in html and 'data-bar="hp"' in html
    assert "__laWire" in render.INTERACT_JS       # and the client does count


# ── the card's own input ─────────────────────────────────────────────────

def test_the_registrar_asks_in_the_card_not_in_the_chat():
    p = state.new_player("t:namer")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    s = core.apply_choice(p, "warrior")
    assert s.ask and s.ask["kind"] == "text" and s.ask["max"] == 24
    assert s.awaits_text                       # the chat path still stands
    html = render.render_scene_fragment(s)
    assert 'form class="ask' in html and 'maxlength="24"' in html
    assert 'class="asend"' in html
    # and the box posts the same text the chat would have
    s = core.apply_choice(p, "", "Thorgrim")
    assert p["name"] == "Thorgrim" and p["stage"] == "playing"


def test_a_number_asked_for_is_a_number_field():
    p = playing("donor", world={"social": True, "faction": {
        "name": "Ember Pact", "banner": "wolf_howl", "join_fee": 25,
        "dues": 5, "store": 10, "role": "member", "members": [],
        "week": {"kind": "cull", "target": 10, "entered": False,
                 "progress": 0, "entry_cost": 10}}})
    p["gold"] = 500
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "donate")
    assert s.ask["kind"] == "number" and s.ask["max"] == 500
    html = render.render_scene_fragment(s)
    assert 'type="number"' in html and 'inputmode="numeric"' in html


# ── a banner is a picture ────────────────────────────────────────────────

def test_the_sigil_step_shows_sigils_not_filenames():
    p = playing("founder", world=hall_world())
    p["gold"], p["level"] = 600, 4
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "found_guild")
    s = core.apply_choice(p, "", "Night Ledger")
    assert s.gallery and len(s.gallery) >= 5
    for tile in s.gallery:
        assert tile["opt"] == f"sig_{tile['slug']}"
        assert render._banner_data_url(tile["slug"]), tile["slug"]
    html = render.render_scene_fragment(s)
    assert 'class="gtile"' in html and 'class="gpic"' in html


def test_the_hall_shows_every_banner_it_offers():
    p = playing("shopper", world=hall_world())
    s = core.apply_choice(p, "guildhall")
    tile = next(g for g in s.gallery if g["label"] == "Ember Pact")
    assert tile["slug"] == "wolf_howl"
    assert tile["opt"] == "join_Ember Pact"
    assert "join ◈ 25" in tile["sub"] and "dues ◈ 5" in tile["sub"]


def test_your_own_colors_hang_over_your_own_table():
    p = playing("member", world={"social": True, "faction": {
        "name": "Ember Pact", "banner": "wolf_howl", "join_fee": 25,
        "dues": 5, "store": 10, "role": "member", "members": [],
        "week": {"kind": "cull", "target": 10, "entered": False,
                 "progress": 0, "entry_cost": 10}}})
    s = core.apply_choice(p, "guildhall")
    assert s.banner == "wolf_howl"
    html = render.render_scene_fragment(s)
    assert 'class="banner"' in html


def test_every_sigil_on_disk_resolves_as_card_art():
    slugs = render.sigil_slugs()
    assert len(slugs) >= 20
    for slug in slugs:
        art = render._banner_data_url(slug)
        assert art and art[1] == 320 and art[2] == 112, slug
        assert render._banner_tint(slug) == render.VIOLET_SOFT


def test_the_lore_bubble_never_covers_the_menu_it_opened():
    """Live: clicking a Medgel focused the cell, the [i] bubble fired on
    focusin, and it drew OVER the popup — the player got a paragraph of lore
    where the Use button should have been. Hover to learn, click to act."""
    js = render.INTERACT_JS + render.TIP_JS
    assert "if (document.querySelector('.pmenu')) return hide();" in js
    assert "tb.style.display = 'none'" in js
    assert ".pmenu{position:fixed;z-index:100" in render.SCENE_CSS
    assert "#tipbox{position:fixed;display:none;z-index:99" in render.SCENE_CSS


# ── the wire an older install has to read ────────────────────────────────

def _v032_scene_from_dict(d: dict):
    """0.28-0.32's parser, verbatim in the part that matters: each option
    dict is splatted into that version's Option, which has five fields and
    no badge. This is what every installed copy runs against worldd."""
    from dataclasses import dataclass

    @dataclass
    class OldOption:
        id: str
        label: str
        hint: str = ""
        aether: bool = False
        locked: bool = False

    return [OldOption(**o) for o in d.get("options", [])]


def test_a_scene_from_this_engine_still_parses_on_an_older_install():
    """worldd runs the engine; the installed plugin renders what it sends,
    and the two are routinely different versions. 0.33.0 shipped `badge`
    INSIDE each option dict, so every copy older than it raised TypeError on
    every scene and read the whole world as "the signal is gone"."""
    p = playing("wire")
    p["bank"], p["bank_day"] = 300, state.world_day_f() - 2
    d = core.current_scene(p).to_dict()
    assert d["option_badges"]["vault"] == 10     # the count still crosses
    assert all("badge" not in o for o in d["options"])
    old = _v032_scene_from_dict(d)               # must not raise
    assert any(o.id == "vault" for o in old)


def test_the_count_survives_the_round_trip_for_a_current_install():
    from plugin_linear_ascent.engine.scene import Scene
    p = playing("trip")
    p["bank"], p["bank_day"] = 300, state.world_day_f() - 2
    back = Scene.from_dict(core.current_scene(p).to_dict())
    assert door(back, "vault").badge == 10       # 041: 2 days × 5 slices
    assert back.notices and back.inventory


def test_a_field_from_a_newer_engine_is_ignored_not_fatal():
    """The next new field must cost an old client nothing."""
    from plugin_linear_ascent.engine.scene import Scene
    d = core.current_scene(playing("future")).to_dict()
    d["options"][0]["sparkle"] = True
    d["meters"]["moonstones"] = 7
    d["a_slot_from_2027"] = {"n": 1}
    s = Scene.from_dict(d)
    assert s.options and s.meters


def test_a_drawn_haul_crosses_the_wire():
    """025 draws coins instead of stating them, but `tally` never made it
    into to_dict — so the one surface players actually play on (worldd)
    printed a number where the coins should be."""
    from plugin_linear_ascent.engine.scene import Scene
    p = playing("haul")
    s = core.current_scene(p)
    s.tally = [{"kind": "gold", "n": 7}, {"kind": "aether", "n": 3}]
    assert Scene.from_dict(s.to_dict()).tally == s.tally


# ── the badge law still holds ────────────────────────────────────────────

def test_a_badge_is_never_mere_availability():
    """The 023 law: a badge that is always on is a badge nobody reads."""
    p = playing("law")
    p["level"] = 10
    p["gold"] = 5_000
    s = core.current_scene(p)
    for oid in ("gate", "forge", "arcanum", "medlab", "pawn", "stone",
                "guildhall", "board", "vault"):
        assert door(s, oid).badge == 0, oid
    assert notices.pending(p) == [] or all(
        n["door"] == "lodge" for n in notices.pending(p))


def test_a_finished_job_badges_and_a_claimed_one_does_not():
    p = playing("worker")
    p["level"] = economy.BOARD_LEVEL
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.sync(p)["got"][job["id"]] = job["need"]
    s = core.current_scene(p)
    assert door(s, "board").badge == 1
    assert "unpaid" in " ".join(n["text"] for n in s.notices)
    core.apply_choice(p, "board")
    core.apply_choice(p, f"claim_{job['id']}")
    s = core.apply_choice(p, "back")
    assert door(s, "board").badge == 0
