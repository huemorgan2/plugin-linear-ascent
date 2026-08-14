"""057 — every weapon wears its own face.

Per-slug 1-bit art ships at two sizes (30x48 icon, 100x160 portrait);
the shop cards trade the shared line glyph for the weapon's own face
and carry the portrait in their hover tip; keen/warded variants reuse
the base art; the Arcanum becomes the Forge's twin card wall.
"""

import os

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, state

ART = os.path.join(os.path.dirname(os.path.abspath(render.__file__)),
                   "content", "art", "weapons")


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Smith"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def _design_slugs():
    """The 85 unique faces: 81 shop-line weapons + the four basics.
    keen/warded variants are NOT here — they reuse base art."""
    slugs = ["rusted_shiv", "rusted_sword", "basic_bow", "worn_staff"]
    for line in ("warrior", "archer", "sorcerer"):
        slugs += [g.slug for g in economy.weapon_line(line)]
    return slugs


# ── the shipped assets ───────────────────────────────────────────────────

def test_every_weapon_ships_both_faces():
    missing = [s for s in _design_slugs()
               if not (os.path.exists(os.path.join(
                   ART, "icons", f"{s}_30x48.png"))
                   and os.path.exists(os.path.join(
                       ART, "large", f"{s}_100x160.png")))]
    assert not missing, f"weapons without art: {missing}"


def test_the_count_is_eighty_five():
    assert len(_design_slugs()) == 85


def test_weak_and_mythic_steel_look_different():
    for kind, size in (("icons", "30x48"), ("large", "100x160")):
        poor = open(os.path.join(ART, kind, f"scrap_dagger_{size}.png"),
                    "rb").read()
        mythic = open(os.path.join(ART, kind, f"dawnbreaker_{size}.png"),
                      "rb").read()
        assert poor != mythic


# ── resolution: every weapon draws its own face ──────────────────────────

def test_variants_reuse_the_base_weapons_face():
    assert render._gear_art_slug("keen_iron_sword") == "iron_sword"
    assert render._gear_art_slug("warded_iron_sword") == "iron_sword"
    assert render._gear_art_slug("iron_sword") == "iron_sword"
    # not an item at all → no art
    assert render._gear_art_slug("not_a_thing") == ""


def test_every_line_slug_resolves_a_data_url():
    for slug in _design_slugs():
        assert render._gear_art_url(slug, "icons"), slug
        assert render._gear_art_url(slug, "large"), slug


def test_the_shop_row_icon_is_the_weapons_own():
    html = render._opt_gear_icon("buy_iron_sword")
    assert "gicon gw" in html
    assert render._gear_art_url("iron_sword", "icons") in html
    # 058: armor wears its own face now too
    plate = render._opt_gear_icon("buy_padded_jerkin")
    assert "gicon gw" in plate
    assert render._gear_art_url("padded_jerkin", "icons") in plate


def test_keen_steel_keeps_its_ember_ink_over_the_base_face():
    html = render._opt_gear_icon("wear_keen_iron_sword")
    assert "gicon gw" in html
    assert render._STYLE_TINT["keen"] in html
    assert render._gear_art_url("iron_sword", "icons") in html


# ── the preview: a bigger card, not a popup ──────────────────────────────

def test_forge_card_grows_a_preview_not_a_popup():
    p = create_character(fresh("Tipsy"))
    p["location"] = "forge"
    s = core.current_scene(p)
    html = render.render_scene(s)
    # the fresh rack sells rung 1.0 — its cell carries the preview card
    lurl = render._gear_art_url("scrap_dagger", "large")
    assert lurl in html                     # the portrait, full scale
    assert 'class="wprev"' in html
    assert 'data-wprev="1"' in html         # the tap-intercept flag
    assert 'class="wpx"' in html            # ✕ for touch
    # the buy button at the foot carries the option and the price
    prev = render._gear_card_preview(
        "buy_scrap_dagger", "pay ◈ 370 · +14 ⚔ · durability 1,365")
    assert 'class="opt wpbuy" data-opt="buy_scrap_dagger"' in prev
    assert "buy" in prev and "370" in prev
    assert "data-tiph" not in prev          # the popup is gone


# ── the Arcanum is the Forge's twin ──────────────────────────────────────

def test_arcanum_is_a_card_wall_with_one_line_and_a_legend():
    p = create_character(fresh("Star"), clazz="sorcerer")
    p["level"] = economy.ARCANUM_LEVEL
    p["location"] = "arcanum"
    s = core.current_scene(p)
    assert s.grid is True
    assert "Forge" in s.shard_note            # the one line of explanation
    assert any("what the cards say" in ln for ln in s.body_lines)
    assert not getattr(s, "support", "")      # prose is gone
    html = render.render_scene(s)
    assert 'class="opt gcard' in html         # staves render as cards
    # at ARCANUM_LEVEL the rack has moved past rung 1.0 — kindling_rod
    # (rung 1.1) is on the wall, wearing its own face
    assert render._gear_art_url("kindling_rod", "icons") in html
