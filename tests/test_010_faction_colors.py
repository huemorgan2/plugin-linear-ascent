"""010 faction colors: nine named 1-bit inks. Founding picks one after
the banner; the steward's desk changes it later; meters() carries it to
the strip. worldd owns persistence — the engine only emits effects."""

from plugin_linear_ascent import colors, render
from plugin_linear_ascent.engine import core

from tests.test_faction_hall import fx, hall_world, member_world, playing
from tests.test_032_banner_hall import enter_hall, member

NINE = list(colors.FACTION_COLORS)


# ── The roster itself ────────────────────────────────────────────────────

def test_roster_is_nine_named_inks_from_the_existing_palette():
    assert len(colors.FACTION_COLORS) == 9
    assert colors.DEFAULT_COLOR in colors.FACTION_COLORS
    palette = {render.DIM, render.TEXT, render.BRIGHT, render.GOLD,
               render.AETHER, render.VIOLET, render.RED, render.OK,
               render.BROWN}
    for slug, (nm, ink) in colors.FACTION_COLORS.items():
        assert ink in palette, f"{slug} ink {ink} not a palette color"
        assert nm and nm[0].isupper()


def test_ink_and_name_fall_back_on_unknown_slug():
    assert colors.faction_ink("no-such-ink") == \
        colors.faction_ink(colors.DEFAULT_COLOR)
    assert colors.faction_ink("ember-red") == "#f26541"
    assert colors.faction_color_name("mouse-grey") == "Mouse Grey"


# ── Founding: name → banner → color → fee → dues ─────────────────────────

def founder(**wkw):
    p = playing(world=hall_world(faction_colors=NINE, **wkw))
    p["gold"], p["level"] = 600, 4
    return p


def test_founding_walks_through_the_color_step():
    p = founder()
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "found_guild")
    core.apply_choice(p, "", "Lanternjacks")
    s = core.apply_choice(p, "sig_wolf_howl")
    assert p["founding_guild"]["step"] == "color"
    ids = {o.id for o in s.options}
    assert {f"col_{slug}" for slug in NINE} <= ids
    s = core.apply_choice(p, "col_ember-red")
    assert p["founding_guild"]["step"] == "fee"
    core.apply_choice(p, "", "0")
    core.apply_choice(p, "", "5")
    e = fx(p, "guild_found")[0]
    assert e["guild"] == "Lanternjacks" and e["color"] == "ember-red"


def test_unknown_color_pick_stays_on_the_color_step():
    p = founder()
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "found_guild")
    core.apply_choice(p, "", "Lanternjacks")
    core.apply_choice(p, "sig_wolf_howl")
    core.apply_choice(p, "col_hot-pink")
    assert p["founding_guild"]["step"] == "color"


def test_old_server_without_roster_skips_the_color_step():
    p = playing(world=hall_world())            # no faction_colors key
    p["gold"], p["level"] = 600, 4
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "found_guild")
    core.apply_choice(p, "", "Lanternjacks")
    core.apply_choice(p, "sig_wolf_howl")
    assert p["founding_guild"]["step"] == "fee"
    core.apply_choice(p, "", "0")
    core.apply_choice(p, "", "5")
    assert fx(p, "guild_found")[0]["color"] == ""


# ── The strip reads the color off the world ──────────────────────────────

def test_meters_carry_the_faction_color():
    w = member_world()
    w["faction"]["color"] = "aether-teal"
    p = playing(world=w)
    p["guild"] = "Ember Pact"
    s = core.apply_choice(p, "guildhall")
    assert s.meters.faction_color == "aether-teal"


def test_meters_color_empty_when_the_server_sends_none():
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    s = core.apply_choice(p, "guildhall")
    assert s.meters.faction_color == ""


# ── The steward's desk changes the ink ───────────────────────────────────

def test_desk_recolor_lists_nine_and_marks_the_current():
    p = member(role="steward")
    p["_world"]["faction"]["color"] = "warden-violet"
    enter_hall(p)
    core.apply_choice(p, "hall_desk")
    s = core.apply_choice(p, "recolor_banner")
    ids = [o.id for o in s.options]
    assert [f"hcol_{slug}" for slug in NINE] == ids[:-1]
    cur = next(o for o in s.options if o.id == "hcol_warden-violet")
    assert cur.hint == "flying now"


def test_desk_recolor_emits_the_effect_and_follows_at_once():
    p = member(role="steward")
    enter_hall(p)
    core.apply_choice(p, "hall_desk")
    core.apply_choice(p, "recolor_banner")
    s = core.apply_choice(p, "hcol_orchard-green")
    assert fx(p, "faction_recolor")[0]["color"] == "orchard-green"
    assert p["_world"]["faction"]["color"] == "orchard-green"
    assert any("Orchard Green" in ln for ln in s.body_lines)
    assert s.meters.faction_color == "orchard-green"


# ── The strip wears the ink (phase 3) ────────────────────────────────────

def strip(color):
    w = member_world()
    w["faction"]["color"] = color
    w["faction"]["members_count"] = 2
    p = playing(world=w)
    p["guild"] = "Ember Pact"
    frag = render.render_scene_fragment(core.current_scene(p))
    return frag.split('class="facblk')[1].split("</div>")[0]


def test_strip_door_carries_the_faction_ink_as_a_custom_property():
    assert "--fac:#f26541" in strip("ember-red")
    # legacy factions (no color on the wire) keep today's exact violet
    assert f"--fac:{render.VIOLET_SOFT}" in strip("")


def test_strip_sigil_is_the_half_res_mask_not_an_img():
    blk = strip("ember-red")
    assert "<img" not in blk
    assert 'class="facsig"' in blk and "mask-image:url(" in blk
    # half-res art: the 160x56 file, not the 320x112 one
    half = render._sigil_half_data_url("wolf_howl")
    full = render._banner_data_url("wolf_howl")
    assert half and half[1:] == (160, 56)
    assert half[0] in blk
    assert len(half[0]) < len(full[0])           # ~1/4 the bytes
    # 60px tall at 160:56 keeps the old footprint: ~171px wide
    assert "width:171px" in blk


def test_hall_galleries_keep_full_res():
    # _banner_data_url never resolves the 160x56 file
    assert render._banner_data_url("wolf_howl")[1:] == (320, 112)


def test_strip_css_hover_is_flat_color_no_growth_no_glow():
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    page = render.render_scene(core.current_scene(p))
    css = page.split(".facblk{")[1].split(".piprows")[0]
    assert "scale(" not in css and "drop-shadow" not in css
    assert f"background:var(--fac,{render.VIOLET_SOFT})" in css
    # the ink flips to black for contrast, banner and name both
    assert "color:#000" in css and "background-color:#000" in css
    # the counts' rules stay untouched next door
    assert f".facblk .facsub .dim{{color:{render.DIM};}}" in page


def test_join_door_keeps_the_gold_text_hover():
    p = playing(world={"social": True, "factions": [],
                       "factions_total": 3, "faction_banners": [],
                       "hall_board": {"banners": []}})
    page = render.render_scene(core.current_scene(p))
    assert ".facdoor.join:hover" in page
    assert (f".facblk .facdoor.join:focus-visible .facname{{\n"
            f" color:{render.GOLD};border-bottom-color:{render.GOLD};}}"
            in page)


def test_desk_recolor_never_mind_changes_nothing():
    p = member(role="steward")
    enter_hall(p)
    core.apply_choice(p, "hall_desk")
    core.apply_choice(p, "recolor_banner")
    core.apply_choice(p, "hall_cancel")
    assert not fx(p, "faction_recolor")
    assert "hall_recoloring" not in p
