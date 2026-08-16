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


def test_desk_recolor_never_mind_changes_nothing():
    p = member(role="steward")
    enter_hall(p)
    core.apply_choice(p, "hall_desk")
    core.apply_choice(p, "recolor_banner")
    core.apply_choice(p, "hall_cancel")
    assert not fx(p, "faction_recolor")
    assert "hall_recoloring" not in p
