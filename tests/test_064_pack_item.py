"""064 — the pack is a thing.

The Forge's pack row is a card with the next tier's face; buying it
leaves the OLD pack in the inventory as an item that the broker buys
and the faction chest takes.
"""

import os

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, tips
from tests.test_032_banner_hall import (enter_hall, fx, member)
from tests.test_057_weapon_art import create_character, fresh

ART = os.path.join(os.path.dirname(os.path.abspath(render.__file__)),
                   "content", "art", "gear")


def _smith(level=3, gold=1000):
    p = create_character(fresh("Packer"))
    p["level"] = level
    p["gold"] = gold
    p["location"] = "forge"
    return p


def test_every_pack_tier_ships_both_faces():
    for slug in economy.PACKS:
        assert os.path.exists(os.path.join(ART, "icons", f"{slug}_30x48.png")), slug
        assert os.path.exists(os.path.join(ART, "large", f"{slug}_100x160.png")), slug
    assert economy.pack_slug(economy.PACK_BASE_SLOTS) in economy.PACKS
    for _, slots, _ in economy.PACK_TIERS:
        assert economy.pack_slug(slots) in economy.PACKS


def test_the_forge_pack_row_is_a_card_with_the_next_tiers_face():
    p = _smith()
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_pack")
    assert s.option_art["buy_pack"] == "pack_9"
    assert "9 slots" in row.label
    html = render.render_scene(s)
    assert 'data-opt="buy_pack" data-wprev="1"' in html
    assert render._gear_art_url("pack_9", "icons") in html
    assert render._gear_art_url("pack_9", "large") in html
    assert "Climber" in html


def test_a_locked_pack_row_is_still_a_card_without_a_preview():
    p = _smith(level=1)
    html = render.render_scene(core.current_scene(p))
    assert 'class="opt gcard locked" data-opt="buy_pack"' in html
    assert render._gear_art_url("pack_9", "icons") in html
    assert render._gear_art_url("pack_9", "large") not in html


def test_buying_a_pack_keeps_the_old_one_as_an_item():
    p = _smith()
    s = core.apply_choice(p, "buy_pack")
    assert p["pack_slots"] == 9
    assert p["inventory"].get("pack_6") == 1
    assert "Traveler's pack" in " ".join(s.body_lines)
    cell = next(c for c in s.inventory if c["slug"] == "pack_6")
    assert cell["kind"] == "pack" and cell["name"] == "Traveler's pack"
    # a second step keeps the 9 too
    p["level"], p["gold"] = 6, 1000
    core.apply_choice(p, "buy_pack")
    assert p["pack_slots"] == 12
    assert p["inventory"].get("pack_9") == 1
    assert p["inventory"].get("pack_6") == 1


def test_the_broker_buys_an_old_pack():
    p = _smith()
    core.apply_choice(p, "buy_pack")
    p["location"] = "pawn"
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "sell_pack_6")
    assert "Traveler's pack" in row.label
    gold = p["gold"]
    s = core.apply_choice(p, "sell_pack_6")
    assert p["gold"] > gold
    assert "pack_6" not in p["inventory"]
    assert "Traveler's pack" in " ".join(s.body_lines)


def test_the_chest_takes_an_old_pack():
    p = member()
    p["inventory"]["pack_6"] = 1
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    assert any(o.id == "chest_put" for o in s.options)
    s = core.apply_choice(p, "chest_put")
    row = next(o for o in s.options if o.id == "put_pack_6")
    assert "6 slots" in row.hint and "no coin" in row.hint
    assert s.option_art["put_pack_6"] == "pack_6"
    s = core.apply_choice(p, "put_pack_6")
    assert fx(p, "armory_deposit")[0]["slug"] == "pack_6"
    assert p["inventory"].get("pack_6") is None
    assert "Traveler's pack" in " ".join(s.body_lines)


def test_the_pack_tip_says_the_old_one_stays():
    assert "old pack" in tips.option_tip("buy_pack")


def test_the_pack_cell_wears_its_face():
    cell = render._slot_cell({"slug": "pack_6", "kind": "pack",
                              "name": "Traveler's pack", "count": 1})
    assert render._gear_art_url("pack_6", "icons") in cell
