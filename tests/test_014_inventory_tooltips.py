"""014 — the pack strip (inventory under the meters, 1-bit 32×32 icons)
and the whisper glyphs ([i] with an instant tooltip on every option).
Plus the gap the strip exposed: medgel/trauma kit are finally usable
(at gate camps; the tonic stays the only mid-fight heal)."""

from plugin_linear_ascent import economy, icons, render
from plugin_linear_ascent.engine import core, state, tips
from plugin_linear_ascent.engine.scene import Option, Scene


def fresh():
    return state.new_player("test-user-014")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, name="Packa"):
    core.current_scene(p)
    while p["stage"] == "intro":                # 016: through the movie
        choose(p, "1")
    choose(p, "human")
    choose(p, text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}["warrior"]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}["warrior"]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def at_gate_town(p):
    choose(p, "gate")
    choose(p, "floor_1")
    return p


# ── icons ────────────────────────────────────────────────────────────────

def test_every_grid_is_16x16_one_bit():
    for key in icons.ICON_KEYS:
        grid = icons._GRIDS[key]
        assert len(grid) == 16, key
        for row in grid:
            assert len(row) == 16, key
            assert set(row) <= {".", "#"}, key


def test_icon_urls_render_and_cache():
    for key in icons.ICON_KEYS:
        url = icons.icon_data_url(key)
        assert url.startswith("data:image/svg+xml")
        assert "rect" in url or "%3Crect" in url
    assert icons.icon_data_url("no_such_icon") == icons.icon_data_url("pack")


# ── 018: the shading is a dither, and it is derived, so nothing below
# authors it. Two properties hold the style up.

def test_shading_never_paints_outside_the_silhouette():
    """A dither may only turn ink off, never invent it — otherwise the
    tint bleeds outside the shape it is masking."""
    for key in icons.ICON_KEYS:
        grid = icons._GRIDS[key]
        for y, row in enumerate(icons._painted(grid)):
            for x, lit in enumerate(row):
                assert not lit or grid[y][x] == "#", (key, x, y)


def test_a_hole_keeps_its_rim_and_a_thin_glyph_is_untouched():
    """The rim is what makes a two-pixel detail survive the dither: a
    ring of solid ink around every hole. Its corollary is that a glyph
    with no interior — all of the line art — comes out exactly as it
    did before 018."""
    solid = ["#" * 16] * 16
    assert sum(sum(r) for r in icons._painted(solid)) < 16 * 16

    # a solid block with a two-pixel hole punched in the middle
    holed = ["#" * 7 + ".." + "#" * 7 if y in (8, 9) else "#" * 16
             for y in range(16)]
    painted = icons._painted(holed)
    for x, y in ((6, 8), (9, 8), (6, 9), (9, 9),
                 (7, 7), (8, 7), (7, 10), (8, 10)):
        assert painted[y][x], (x, y)
    # (9, 8) is in the dithered band on the parity the checker drops,
    # so the rim above is doing real work — and away from the hole the
    # checker still bites.
    assert not painted[12][13]

    for key in ("focus", "entangling_net", "curse_scroll"):
        grid = icons._GRIDS[key]
        painted = icons._painted(grid)
        assert all(painted[y][x] == (c == "#")
                   for y, row in enumerate(grid)
                   for x, c in enumerate(row)), key


def test_icon_key_resolution():
    assert icons.icon_key("medgel") == "medgel"
    assert icons.icon_key("scrap_dagger", "weapon") == "weapon"
    assert icons.icon_key("padded_jerkin", "armor") == "armor"
    assert icons.icon_key("mystery_thing", "item") == "pack"


# ── tips: the whole game answers ─────────────────────────────────────────

STATIC_IDS = [
    # navigation + creation
    "town", "back", "begin", "human", "elf", "giant",
    # town buildings
    "forge", "medlab", "lodge", "vault", "pawn", "relay", "fields",
    "guildhall", "stone", "gate",
    # gate town + lodge + vault
    "hunt", "heal", "stew", "keep",
    "deposit_all", "deposit_half", "withdraw_all", "grants",
    # fight
    "attack", "stand", "run", "drink_tonic",
    "shield_wall", "sleep_spell", "treeline_shot",
    # keeps
    "strike", "boss_commit",
    # guildhall / factions
    "guild_train", "found_guild", "donate", "enter_week", "kick",
    "guild_leave", "cancel_found", "cancel_donate", "cancel_kick",
    # relay
    "collect",
]


def test_every_static_id_has_a_tip():
    for oid in STATIC_IDS:
        assert tips.option_tip(oid), f"no tip for {oid}"


def test_prefix_tips_carry_the_numbers():
    g = next(x for x in economy.FORGE.values() if x.tier == 1
             and x.slot == "weapon")
    t = tips.option_tip(f"buy_{g.slug}")
    assert f"+{g.bonus}" in t and g.name in t
    assert "25–55%" in tips.option_tip(f"sell_{g.slug}")   # 006: daily rate
    assert "◈ 10" in tips.option_tip("grantamt_100")     # the 10% burn
    assert "floor 7" in tips.option_tip("floor_7")
    for oid in ("hone_weapon", "hone_shield", "hone_armor",
                "use_medgel", "use_trauma_kit", "write_Bo",
                "grantto_Bo", "join_Ember Pact", "sig_wolf_howl",
                "kick_Bo", "attack_Bo", "buy_medgel"):
        assert tips.option_tip(oid), f"no tip for {oid}"


def test_unknown_id_gets_no_glyph():
    assert tips.option_tip("zz_mystery") == ""
    assert tips.option_tip("grantamt_soup") == ""


def test_item_tips_cover_the_shelf_and_the_pack():
    for slug in economy.APOTHECARY:
        assert tips.item_tip(slug), slug
    worn = tips.item_tip("rusted_shiv", equipped=True)
    packed = tips.item_tip("rusted_shiv")
    assert "worn" in worn and "pack" in packed and worn != packed
    assert tips.item_tip("mystery_thing")                # never empty


def test_every_option_in_a_full_walk_has_a_tip():
    """The coverage guard: creation → town → every building → the gate
    → a camp → a fight. Any new option without a tip fails here."""
    p = fresh()
    missing: set[str] = set()

    def check(s):
        for o in s.options:
            if not tips.option_tip(o.id):
                missing.add(o.id)

    check(core.current_scene(p))                 # intro movie, scene I
    while p["stage"] == "intro":                 # 016: every movie step
        check(choose(p, "1"))
    check(core.current_scene(p))                 # races
    check(choose(p, "human"))                    # the registrar
    choose(p, text="Packa")
    p["inventory"]["medgel"] = 1                 # exercise use_/sell_ rows
    p["inventory"]["padded_jerkin"] = 1
    check(core.current_scene(p))                 # the square
    for menu in ("forge", "medlab", "lodge", "vault", "pawn", "stone",
                 "guildhall"):
        check(choose(p, menu))
        choose(p, "town" if menu == "guildhall" else "back")
    check(choose(p, "gate"))                     # floor_ picks
    p["hp"] = 10
    check(choose(p, "floor_1"))                  # camp incl. use_medgel
    check(choose(p, "hunt"))                     # the fight card
    choose(p, "run")
    assert not missing, f"options without tips: {sorted(missing)}"


def test_every_veteran_option_has_a_tip_too():
    """0.29.5 regression: the level-1 walk never renders the doors that
    open later — the night slot, the long fire, the strongbox picks,
    the contract claims, the interest stubs, the token mend. Walk them
    as a veteran so a new late-game option can't ship tipless."""
    from plugin_linear_ascent.engine import contracts, weekly

    p = create_character(fresh())
    missing: set[str] = set()

    def check(s):
        for o in s.options:
            if not tips.option_tip(o.id):
                missing.add(o.id)

    p["level"] = economy.STRONGBOX_LEVEL
    p["gold"] = 5000
    # a worn paid piece + a token → repair_ and token_ rows at the forge
    g = economy.FORGE["scrap_dagger"]
    p["gear"]["weapon"] = g.slug
    p.setdefault("durability", {})["weapon"] = 1
    p["inventory"]["repair_token"] = 1
    check(choose(p, "forge"))
    choose(p, "back")
    # stubs + an open strongbox → collect_interest and pick_ rows
    p["bank"] = 1000
    p["bank_day"] = state.world_day() - 3
    p["strongbox"] = {"week": weekly.week_no(), "kills": 0, "wardens": 0,
                      "floor0": 1,
                      "pending": {"week": weekly.week_no() - 1, "slots": 3}}
    check(choose(p, "back"))                     # town (badged doors)
    check(choose(p, "vault"))
    choose(p, "back")
    # the night slot and the long fire (fire needs a world blob)
    p["_world"] = {"fire": []}
    check(choose(p, "lodge"))
    choose(p, "back")
    p.pop("_world", None)
    # a finished job → the claim_ row on the board
    job = contracts.board_for(p)[0]
    contracts.sync(p)["got"][job["id"]] = job["need"]
    check(choose(p, "board"))
    assert not missing, f"veteran options without tips: {sorted(missing)}"


# ── the pack strip on the Scene ──────────────────────────────────────────

def test_playing_scenes_carry_the_pack():
    p = create_character(fresh())
    p["inventory"]["medgel"] = 2
    s = core.current_scene(p)
    by_slug = {i["slug"]: i for i in s.inventory}
    sword = by_slug["rusted_sword"]                      # 017 class starter
    assert sword["equipped"] and sword["kind"] == "weapon"
    assert by_slug["medgel"]["count"] == 2
    assert s.inventory[0]["slug"] == "rusted_sword"      # equipped first
    d = Scene.from_dict(s.to_dict())
    assert d.inventory == s.inventory


def test_honed_gear_names_its_level():
    p = create_character(fresh())
    p["hone"]["weapon"] = 2
    s = core.current_scene(p)
    assert s.inventory[0]["name"] == "Rusted Sword +2"


def test_creation_scenes_carry_no_pack():
    p = fresh()
    assert core.current_scene(p).inventory == []
    s = choose(p, "next")
    assert s.inventory == []


# ── the use_ path (the gap the strip exposed) ────────────────────────────

def test_medgel_heals_at_the_camp_and_decrements():
    p = at_gate_town(create_character(fresh()))
    p["inventory"]["medgel"] = 2
    p["hp"] = 10
    s = core.current_scene(p)
    use = next(o for o in s.options if o.id == "use_medgel")
    assert "+25 HP" in use.hint and "2 left" in use.hint
    s = choose(p, "use_medgel")
    assert p["hp"] == 35
    assert p["inventory"]["medgel"] == 1
    assert any("+ 25 HP" in ln for ln in s.body_lines)


def test_heal_caps_at_max_and_full_hp_refuses():
    p = at_gate_town(create_character(fresh()))
    p["inventory"]["trauma_kit"] = 1
    p["hp"] = state.max_hp(p) - 5
    choose(p, "use_trauma_kit")
    assert p["hp"] == state.max_hp(p)
    assert "trauma_kit" not in p["inventory"]
    p["inventory"]["medgel"] = 1
    s = choose(p, "use_medgel")   # full HP → not offered, refused politely
    assert p["inventory"].get("medgel") == 1
    assert p["hp"] == state.max_hp(p)
    assert s.shard_note


# ── render: the card carries the grammar ─────────────────────────────────

def test_fragment_has_glyphs_strip_and_tipbox_data():
    p = create_character(fresh())
    p["inventory"]["medgel"] = 1
    frag = render.render_scene_fragment(core.current_scene(p))
    assert 'class="orow"' in frag
    assert 'class="info"' in frag and "data-tip=" in frag
    assert 'class="inv later"' in frag
    assert 'class="picon"' in frag and "data:image/svg+xml" in frag
    assert "Medgel" in frag
    # meters now use the instant tipbox, not the native title delay
    assert 'class="meter hp' in frag and 'title="' not in frag


def test_option_without_tip_renders_no_glyph():
    s = Scene(eyebrow="X", headline="Y",
              options=[Option("zz_mystery", "???")])
    frag = render.render_scene_fragment(s)
    assert 'class="opt"' in frag and 'class="info"' not in frag


def test_tip_js_ships_in_both_hosts():
    from plugin_linear_ascent import pane
    assert "tipbox" in render.render_scene(
        Scene(eyebrow="X", headline="Y"))
    assert "tipbox" in pane.render_pane()


def test_hone_rows_wear_the_pieces_icon():
    # the honing bench names each piece's gear slug in option_art, so the
    # row draws the same 1-bit icon the shop and repair rows use
    p = create_character(fresh())
    p["gold"] = 5000
    p["unlocked_floor"] = 2                     # cap +1 in the first band
    p["gear"]["weapon"] = "scrap_dagger"
    s = choose(p, "forge")
    hone = [o for o in s.options if o.id == "hone_weapon"]
    assert hone, [o.id for o in s.options]
    assert s.option_art["hone_weapon"] == "scrap_dagger"
    html = render.render_scene_fragment(s)
    row = html.split('data-opt="hone_weapon"', 1)[1].split("</button>", 1)[0]
    assert 'class="gicon' in row
