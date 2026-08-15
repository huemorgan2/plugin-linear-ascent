"""PLAN3 — the live 3D kill finisher wire + the first-sighting beat.

The engine stamps `kill3d` on a wilds victory Scene (id, race, line,
breed, specimen); render.py adds the banner tint and emits the whole
payload as data-kill3d on the card div. The website's fight3d.js is the
only consumer — old clients and the chat card drop the unknown top-level
key by wire law and keep the GIF.
"""

import json

from plugin_linear_ascent import render
from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.engine.scene import Scene
from plugin_linear_ascent.render import render_scene_fragment


def _character(name, clazz="warrior"):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
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


def _to_floor(p):
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    if any(o.id == "skip" for o in s.options):       # arrival reel
        core.apply_choice(p, "skip")


def _hunt_victory(p):
    if not p.get("encounter"):
        _to_floor(p)
    core.apply_choice(p, "hunt")
    enc_id = p["encounter"]["id"]                # cleared by the victory
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    p["encounter"]["traits"] = []
    p["encounter"]["profile"] = {}
    return core.apply_choice(p, "attack"), enc_id


def test_wilds_victory_carries_kill3d():
    p = _character("Kest")
    s, enc_id = _hunt_victory(p)
    k3 = s.kill3d
    assert k3, "wilds victory must stamp kill3d"
    assert k3["id"] == enc_id
    assert k3["race"] == "human"
    assert k3["line"] == "blade"                 # the killing weapon line
    assert k3["breed"] in ("native", "pressed", "wrongmade")
    assert k3["specimen"] in ("common", "runt", "tough", "alpha")


def test_kill3d_card_ships_no_ending_gif():
    # PLAN4: where the 3D finisher plays, the old GIF ending is GONE —
    # fx rides INSIDE the spec as the client's degrade slug, the card
    # carries no reel, and the banner slot is bare black for the canvas.
    p = _character("Sorrel")
    s, _ = _hunt_victory(p)
    assert s.fx is None
    assert "fx" in s.kill3d                      # the degrade path's name
    html = render_scene_fragment(s)
    assert 'class="banner"' in html              # the mount slot exists
    assert "mask-image" not in html.split('class="banner"', 1)[1] \
        .split("></div>", 1)[0]                  # ...and wears no reel


def test_kill3d_line_follows_the_class():
    p = _character("Fenn", clazz="sorcerer")
    s, _ = _hunt_victory(p)
    assert s.kill3d["line"] == "staff"


def test_fragment_emits_data_kill3d_with_banner_tint():
    p = _character("Moss")
    s, _ = _hunt_victory(p)
    html = render_scene_fragment(s)
    assert "data-kill3d=" in html
    raw = html.split('data-kill3d="', 1)[1].split('"', 1)[0]
    k3 = json.loads(raw.replace("&quot;", '"'))
    assert k3["id"] == s.kill3d["id"]
    # the ink is the SAME hex the banner mask would tint for this creature
    assert k3["tint"] == render._banner_tint(k3["id"], k3["specimen"])
    assert k3["tint"].startswith("#")


def test_no_kill3d_without_a_wilds_kill():
    # a plain non-victory scene renders without the attribute
    s = Scene(eyebrow="E", headline="H", scene_id="s1")
    assert "data-kill3d" not in render_scene_fragment(s)


def test_kill3d_survives_the_doc_round_trip_and_old_wire():
    s = Scene(eyebrow="E", headline="H", scene_id="s2",
              kill3d={"id": "grey_wolf", "race": "elf", "line": "bow",
                      "breed": "native", "specimen": "alpha"})
    back = Scene.from_dict(s.to_dict())
    assert back.kill3d == s.kill3d
    # an old doc without the key must load clean (wire law)
    d = s.to_dict()
    del d["kill3d"]
    assert Scene.from_dict(d).kill3d is None


def test_first_sighting_line_fires_once_per_creature():
    p = _character("Tarn")
    _to_floor(p)
    s = core.apply_choice(p, "hunt")             # the opener fight card
    first_id = p["encounter"]["id"]
    assert any("First sighting" in ln for ln in s.body_lines), s.body_lines
    assert first_id in p.get("seen_creatures", [])
    # win it, then hunt until the same creature returns: no line
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    p["encounter"]["traits"] = []
    p["encounter"]["profile"] = {}
    core.apply_choice(p, "attack")
    for _ in range(40):
        s = core.apply_choice(p, "hunt")
        again = p["encounter"]["id"]
        lines = s.body_lines
        p["encounter"]["range"] = "close"
        p["encounter"]["hp"] = 1
        p["encounter"]["traits"] = []
        p["encounter"]["profile"] = {}
        core.apply_choice(p, "attack")
        if again == first_id:
            assert not any("First sighting" in ln for ln in lines), lines
            return
        assert any("First sighting" in ln for ln in lines), (again, lines)
    raise AssertionError("the first creature never came back in 40 hunts")


# ── warm hints: the card names what fight3d should fetch, nothing more ──

def test_playing_card_names_the_climbers_rig():
    # every playing card: data-rig3d="race:line" — one rig, not fifteen
    p = _character("Wren", clazz="archer")
    _to_floor(p)
    s = core.current_scene(p)
    assert s.meters.line == "bow"
    html = render_scene_fragment(s)
    assert 'data-rig3d="human:bow"' in html
    assert "data-foe3d" not in html              # no fight, no foe


def test_fight_card_names_the_foe():
    p = _character("Tam")
    _to_floor(p)
    s = core.apply_choice(p, "hunt")
    foe = p["encounter"]["id"]
    assert s.enemy["id"] == foe
    html = render_scene_fragment(s)
    assert f'data-foe3d="{foe}"' in html
    assert 'data-rig3d="human:blade"' in html


def test_old_wire_without_line_emits_no_rig():
    from plugin_linear_ascent.engine.scene import Meters
    m = Meters(hp=1, hp_max=1, energy=1, energy_max=1, xp=0, xp_need=1,
               gold=0, race="elf")               # older engine: no line
    s = Scene(eyebrow="", headline="", meters=m, scene_id="x")
    assert "data-rig3d" not in render_scene_fragment(s)
