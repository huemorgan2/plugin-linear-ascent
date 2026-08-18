"""067 phase 2: the arena recorder — same numbers, ordered script,
floors 6–7 with labs.arena on; nothing anywhere else."""
import json

from plugin_linear_ascent import render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import arena, combat, core, labs, state
from plugin_linear_ascent.engine.scene import Scene

from tests.conftest import make_character


def _climber(name="u-arena", clazz="warrior", floor=6, arena_on=True):
    p = state.new_player(name)
    make_character(p, clazz=clazz)
    p["level"] = 8
    p["hp"] = 400
    p["unlocked_floor"] = floor
    if arena_on:
        labs.set_flag(p, "arena", True)
    return p


def _hunt(p, floor=6):
    fl = schema.get_floor(floor)
    p["floor"] = floor
    p["location"] = "gate_town"
    p["encounter"] = None
    enc = fl.encounters[0]
    s = combat.start_encounter(p, fl, enc, "wilds")
    return s, fl


def test_off_everywhere_else():
    p = _climber(arena_on=False)
    s, fl = _hunt(p, 6)
    assert s.arena is None
    p["encounter"]["range"] = "close"
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.arena is None
    assert "data-arena" not in render.render_scene_fragment(s)
    p = _climber(arena_on=True, floor=5)
    s, fl = _hunt(p, 5)
    assert s.arena is None
    p["encounter"]["range"] = "close"
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.arena is None


def test_opener_keeps_the_close_up_and_carries_tiles():
    p = _climber()
    s, fl = _hunt(p, 6)
    assert s.arena and s.arena["phase"] == "opener"
    assert s.arena["events"] == []
    assert s.arena["foe"]["id"] == p["encounter"]["id"]
    assert set(s.arena["tiles"]) == {o.id for o in s.options}
    html = render.render_scene_fragment(s)
    assert 'class="banner arena"' not in html        # the close-up stays
    assert 'class="opt atile' in html                 # the tiles are here
    assert 'data-arena="' in html


def test_round_script_same_numbers_and_order():
    p = _climber()
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    e["profile"] = {"type": "plain", "flying": False, "bulwark": False,
                    "speed": 5}
    e["traits"] = []
    e["hp"] = e["hp_max"] = 500
    e["atk"] = 40
    p["training"]["blade"] = 10          # no miss
    hp0, foe0 = p["hp"], e["hp"]
    s = combat.resolve_fight_action(p, fl, "attack")
    a = s.arena
    assert a and a["phase"] == "round"
    ev = a["events"]
    assert ev[0]["who"] == "me" and ev[0]["kind"] == "strike"
    assert ev[0]["outcome"] in ("hit", "glance")
    assert ev[0]["foe_hp"] == max(0, e["hp"])
    assert foe0 - ev[0]["dmg"] == e["hp"] or ev[0]["outcome"] == "glance"
    foe_ev = [x for x in ev if x["who"] == "foe" and x["kind"] == "strike"]
    assert len(foe_ev) == 1
    f = foe_ev[0]
    if f["outcome"] in ("hit", "blocked"):
        assert f["blocked"] == f["raw"] - f["dmg"]
        assert f["me_hp"] == p["hp"]
        assert hp0 - f["dmg"] == p["hp"]
    assert ev.index(f) > 0                    # the player's turn first
    assert a["log"] and all(isinstance(t, str) for t in a["log"])
    assert a["me"]["atk"] == state.atk(p)
    assert a["me"]["def"] == state.dfs(p)
    assert a["foe"]["hp"] == max(0, e["hp"])
    html = render.render_scene_fragment(s)
    assert 'class="banner arena"' in html
    assert "aspect-ratio:320/300" in html
    assert 'class="alog"' in html
    assert "data-kill3d" not in html
    raw = html.split('data-arena="', 1)[1].split('"', 1)[0]
    d = json.loads(raw.replace("&quot;", '"').replace("&amp;", "&"))
    assert d["events"][0]["kind"] == "strike" and d["tint"]


def test_miss_names_the_rank():
    p = _climber()
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    p["training"]["blade"] = 0            # 25% miss
    seen = False
    for _ in range(40):
        e["hp"] = e["hp_max"] = 5000
        p["hp"] = 4000
        s = combat.resolve_fight_action(p, fl, "attack")
        ev = s.arena["events"][0]
        if ev["outcome"] == "miss":
            assert ev["rank"] == 0 and ev["miss_pct"] == 25
            assert "skill level is 0 of 10" in ev["text"]
            seen = True
            break
    assert seen


def test_victory_ends_with_the_foe_dying_and_no_kill3d_attr():
    p = _climber()
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    e["hp"] = 1
    e["profile"] = {"type": "plain", "flying": False, "bulwark": False,
                    "speed": 5}
    p["training"]["blade"] = 10
    s = combat.resolve_fight_action(p, fl, "attack")
    assert p["encounter"] is None
    a = s.arena
    assert a["phase"] == "victory"
    assert a["events"][-1] == {"who": "foe", "kind": "die",
                               "text": a["events"][-1]["text"]}
    assert a.get("kill3d", {}).get("id")
    html = render.render_scene_fragment(s)
    assert "data-kill3d" not in html and 'data-arena="' in html


def test_distance_move_and_chase_recorded():
    p = _climber(clazz="archer")
    p["training"]["bow"] = 8
    s, fl = _hunt(p, 7)
    e = p["encounter"]
    e["range"] = "at_range"; e["gap"] = 1
    e["profile"] = {"type": "plain", "flying": False, "bulwark": False,
                    "speed": 3}
    e["hp"] = e["hp_max"] = 5000
    s = combat.resolve_fight_action(p, fl, "create_distance")
    ev = s.arena["events"]
    assert ev[0]["who"] == "me" and ev[0]["kind"] == "move"
    assert ev[0]["what"] == "back" and ev[0]["gap"] == 2
    assert s.arena["range"]["gap"] == e.get("gap")


def test_death_carries_the_last_beat():
    p = _climber()
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    e["atk"] = 9999
    e["hp"] = e["hp_max"] = 5000
    p["hp"] = 5
    p["daily"]["death_save"] = True
    s = combat.resolve_fight_action(p, fl, "stand")
    assert s.arena and s.arena["phase"] == "death"
    assert s.arena["events"][-1]["kind"] == "die"


def test_wire_round_trip():
    p = _climber()
    s, fl = _hunt(p, 6)
    d = s.to_dict()
    assert Scene.from_dict(d).arena == s.arena
