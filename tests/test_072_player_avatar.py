"""072: the reusable other-climber avatar — look, worn slots, parameters."""

from plugin_linear_ascent import render
from plugin_linear_ascent.engine import core, profile
from plugin_linear_ascent.engine.scene import Scene
from tests.test_042_guilds_players_looting import playing, prof, world_with


def test_public_sheet_is_public_and_strips_acts():
    p = playing()
    p["bank"] = 9999
    sheet = profile.public_sheet(p)
    assert "bank" not in sheet
    assert sheet["name"] == p["name"]
    assert sheet["gold"] == p["gold"]
    assert sheet["slots"]
    assert all("acts" not in sl and "why" not in sl for sl in sheet["slots"])
    assert any(sl.get("state") == "filled" for sl in sheet["slots"])


def test_player_avatar_html_is_readonly_sheet():
    html = render.player_avatar_html({
        "name": "Bo", "level": 4, "race": "elf", "clazz": "ranger",
        "faction": "Ember Pact", "gold": 120,
        "energy": 8, "energy_max": 25, "xp": 10, "xp_need": 40,
        "hp": 30, "hp_max": 30, "atk": 6, "dfs": 4, "spd": 5,
        "slots": [
            {"key": "charm", "side": "left", "state": "locked",
             "lock_text": "locked"},
            {"key": "armor", "side": "left", "state": "filled",
             "slug": "leather", "name": "Leather", "kind": "armor"},
            {"key": "shoes", "side": "left", "state": "empty"},
            {"key": "shield", "side": "right", "state": "empty"},
            {"key": "weapon", "side": "right", "state": "filled",
             "slug": "scrap_blade", "name": "Scrap blade", "kind": "weapon"},
        ],
    })
    assert 'class="pavatar' in html
    assert "Bo" in html and "LEVEL 4" in html
    assert "Ember Pact" in html
    assert "HP 30/30" in html and "ATK 6" in html
    assert "data-m=" not in html
    assert "unequip" not in html
    assert "Move to the pack" not in html
    assert "<button" not in html


def test_profile_page_ships_the_avatar_and_says_loot_them():
    pr = prof("Bo", energy_max=25, xp=10, xp_need=40, spd=5,
              slots=[{"key": "armor", "side": "left", "state": "empty",
                      "label": "armour"}])
    p = playing(world=world_with(pr))
    s = core.apply_choice(p, "pv:Bo")
    assert s.avatar["name"] == "Bo"
    assert s.avatar["gold"] == 120
    assert "bank" not in (s.avatar or {})
    row = next(o for o in s.options if o.id == "pf_loot")
    assert row.label == "Loot them"
    html = render.render_scene_fragment(s)
    assert 'class="pavatar' in html
    assert "Loot them" in html
    assert "Loot their camp" not in html
    assert html.find("pavatar") < html.find("Loot them")


def test_scene_wire_keeps_avatar_and_old_dicts_drop_it():
    s = Scene(eyebrow="x", headline="y", avatar={"name": "Bo", "gold": 3})
    back = Scene.from_dict(s.to_dict())
    assert back.avatar == {"name": "Bo", "gold": 3}
    d = s.to_dict()
    d.pop("avatar")
    assert Scene.from_dict(d).avatar is None


def test_empty_sheet_renders_nothing():
    assert render.player_avatar_html({}) == ""
    assert render.player_avatar_html({"level": 2}) == ""
