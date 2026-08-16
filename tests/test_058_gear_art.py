"""058 — the rest of the shop wears its own face.

Shields, caster focuses, armor, boots and the fifteen relics ship
per-slug 1-bit art at the same two sizes as 057's weapons (30x48 icon,
100x160 portrait); shop rows, cards, previews and pack cells pick the
faces up through the generalized _gear_art_* helpers. keen/warded
variants reuse their base item's art with the style tint.
"""

import os

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core
from tests.test_057_weapon_art import create_character, fresh

ART = os.path.join(os.path.dirname(os.path.abspath(render.__file__)),
                   "content", "art", "gear")


def _design_slugs():
    """The 95 unique faces: every non-weapon FORGE base design plus
    the relics. keen/warded variants reuse base art and are NOT here."""
    slugs = [g.slug for g in economy.FORGE.values()
             if g.slot != "weapon" and not g.base]
    return slugs + list(economy.RELICS)


# ── the shipped assets ───────────────────────────────────────────────────

def test_every_design_ships_both_faces():
    missing = [s for s in _design_slugs()
               if not (os.path.exists(os.path.join(
                   ART, "icons", f"{s}_30x48.png"))
                   and os.path.exists(os.path.join(
                       ART, "large", f"{s}_100x160.png")))]
    assert not missing, f"gear without art: {missing}"


def test_the_count_is_ninety_five():
    assert len(_design_slugs()) == 95


def test_rag_and_myth_look_different():
    for kind, size in (("icons", "30x48"), ("large", "100x160")):
        poor = open(os.path.join(
            ART, kind, f"padded_jerkin_{size}.png"), "rb").read()
        mythic = open(os.path.join(
            ART, kind, f"aegis_of_the_vale_{size}.png"), "rb").read()
        assert poor != mythic


# ── resolution: every item draws its own face ────────────────────────────

def test_every_design_resolves_a_data_url():
    for slug in _design_slugs():
        assert render._gear_art_url(slug, "icons"), slug
        assert render._gear_art_url(slug, "large"), slug


def test_armored_variants_reuse_the_base_face():
    assert render._gear_art_slug("keen_banded_kite") == "banded_kite"
    assert render._gear_art_slug("warded_studded_jack") == "studded_jack"
    assert render._gear_art_slug("poison_arrows") == "poison_arrows"


def test_the_relic_shelf_row_wears_the_relics_own_face():
    html = render._opt_gear_icon("buy_poison_arrows")
    assert "gicon gw" in html
    assert render._gear_art_url("poison_arrows", "icons") in html


# ── the preview grows on every card, relics included ─────────────────────

def test_a_shield_card_grows_a_preview():
    prev = render._gear_card_preview(
        "buy_scrapwood_buckler", "pay ◈ 300 · +6 🛡 · durability 900")
    assert 'class="wprev"' in prev
    assert render._gear_art_url("scrapwood_buckler", "large") in prev
    assert 'data-opt="buy_scrapwood_buckler"' in prev
    assert "300" in prev


def test_a_relic_card_grows_a_preview_with_its_name():
    prev = render._gear_card_preview("buy_poison_arrows", "pay ◈ 120")
    assert 'class="wprev"' in prev
    assert render._gear_art_url("poison_arrows", "large") in prev
    assert economy.RELICS["poison_arrows"].name in prev
    assert "120" in prev


def test_the_forge_wall_previews_armor_too():
    p = create_character(fresh("Wallflower"))
    p["location"] = "forge"
    s = core.current_scene(p)
    html = render.render_scene(s)
    assert render._gear_art_url("padded_jerkin", "large") in html


# ── the pack cell ────────────────────────────────────────────────────────

def test_the_pack_cell_wears_gear_art():
    cell = render._slot_cell({"slug": "scrapwood_buckler",
                              "kind": "shield",
                              "name": "Scrapwood Buckler"})
    assert "picon gw" in cell
    assert render._gear_art_url("scrapwood_buckler", "icons") in cell


def test_the_pack_tip_carries_the_portrait_on_the_left():
    # 058b: hovering a pack item shows its 100x160 portrait inside the
    # tip — for every item with shipped art, stat line or not
    for slug, kind in (("scrapwood_buckler", "shield"),
                       ("poison_arrows", "relic")):
        cell = render._slot_cell({"slug": slug, "kind": kind,
                                  "name": slug})
        lurl = render._gear_art_url(slug, "large")
        assert "data-tiph" in cell, slug
        assert _e_url(lurl) in cell, slug


def _e_url(url):
    # data URLs survive _e() untouched except quoting — assert on the
    # base64 payload to stay independent of attribute escaping
    return url.split(",", 1)[1][:64]


# ── 062: the Medlab shelf wears faces too ────────────────────────────────

def test_every_apothecary_ware_ships_both_faces():
    missing = [s for s in economy.APOTHECARY
               if not (os.path.exists(os.path.join(
                   ART, "icons", f"{s}_30x48.png"))
                   and os.path.exists(os.path.join(
                       ART, "large", f"{s}_100x160.png")))]
    assert not missing, f"wares without art: {missing}"


def test_the_medlab_row_and_card_wear_the_wares_face():
    html = render._opt_gear_icon("buy_medgel")
    assert "gicon gw" in html
    assert render._gear_art_url("medgel", "icons") in html
    prev = render._gear_card_preview("buy_medgel", "◈ 25 · heals 40")
    assert 'class="wprev"' in prev
    assert render._gear_art_url("medgel", "large") in prev
    assert economy.APOTHECARY["medgel"].name in prev
    assert "25" in prev


def test_the_medlab_scene_previews_every_ware():
    p = create_character(fresh("Nurse"))
    p["location"] = "medlab"
    html = render.render_scene(core.current_scene(p))
    for slug in economy.APOTHECARY:
        assert render._gear_art_url(slug, "large") in html, slug


def test_the_pack_cell_wears_a_wares_face():
    cell = render._slot_cell({"slug": "medgel", "kind": "consumable",
                              "name": "Medgel"})
    assert render._gear_art_url("medgel", "icons") in cell
    assert "data-tiph" in cell


def test_no_shipped_face_has_a_frame_rule():
    """The generator sometimes draws a border; strip_art_frames.py erases
    it. Guard: no outer column of a portrait is a near-solid vertical
    line."""
    from PIL import Image
    bad = []
    for fn in os.listdir(os.path.join(ART, "large")):
        im = Image.open(os.path.join(ART, "large", fn)).convert("RGBA")
        a = im.split()[3].load()
        w, h = im.size
        for x in (0, 1, 2, w - 3, w - 2, w - 1):
            if sum(1 for y in range(h) if a[x, y] > 128) > h * 0.7:
                bad.append(fn)
                break
    assert not bad, bad
