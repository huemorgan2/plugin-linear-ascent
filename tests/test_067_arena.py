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


def test_opener_keeps_the_close_up_and_regular_menu():
    p = _climber()
    s, fl = _hunt(p, 6)
    assert s.arena and s.arena["phase"] == "opener"
    assert s.arena["events"] == []
    assert s.arena["foe"]["id"] == p["encounter"]["id"]
    assert set(s.arena["tiles"]) == {o.id for o in s.options}
    html = render.render_scene_fragment(s)
    assert 'class="banner arena"' not in html        # the close-up stays
    # 067 phase 8 (roy): tiles ONLY in the fight itself — the opener
    # keeps the regular menu
    assert 'class="opt atile' not in html and "arena-opts" not in html
    assert 'class="options later"' in html
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
    assert "aspect-ratio:320/160" in html            # phase 8: the 160 band
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


# ── 067 phase 5: the card redressed (roy, 2026-08-18) ─────────────────────
def test_phase5_round_card_dress():
    """The HUD is the regular fight's ANSI slab (▓░ via _blocks, both
    sides), the tiles ride INSIDE the stage with the item's own art, and
    no profile / faction strip renders under a live fight."""
    p = _climber(clazz="archer")
    p["quiver"] = {"poison_arrows": 3}          # 069+: the bow's quiver
    p["inventory"]["poison_arrows"] = 3         # ≤ 0.91: the pack
    s, fl = _hunt(p, 6)
    p["encounter"]["range"] = "close"
    p["encounter"]["profile"] = {"type": "plain", "flying": False,
                                 "bulwark": False, "speed": 5}
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.arena and s.arena["phase"] == "round"
    tiles = s.arena["tiles"]
    assert tiles["attack"]["art"] == "basic_bow"
    assert tiles["nock_poison_arrows"]["art"] == "poison_arrows"
    html = render.render_scene_fragment(s)
    # 067 phase 8 (roy): the tiles are a TOOLBAR under the stage —
    # banner, then arena-opts, then the log, in that order
    assert html.index('class="banner arena"') \
        < html.index('class="options arena-opts"') \
        < html.index('<div class="alog"')
    stage = html.split('class="banner arena"', 1)[1] \
                .split('class="options arena-opts"', 1)[0]
    bar = html.split('class="options arena-opts"', 1)[1] \
              .split('<div class="alog"', 1)[0]
    # both slabs, ANSI blocks, the number, ATK/DEF/SPEED words
    assert stage.count('class="astat ') == 2
    assert stage.count("▓") >= 2 and 'class="off"' in stage
    assert 'class="abar me"' in stage and 'class="abar foe"' in stage
    assert "SPEED " in stage and "ATK " in stage and "DEF " in stage
    assert 'class="ahud"' not in html and "afill" not in html
    # no tile ever rides over the picture
    assert 'class="opt atile' not in stage
    assert bar.count('class="opt atile') == len(s.options)
    # the pack's own cell — .abox + .picon mask in ART (art `.gw`)
    assert bar.count('class="abox"') == len(s.options)
    assert bar.count('class="picon gw"') >= 2          # bow + poison arrows art
    assert 'class="picon"' in bar                      # RUN keeps its glyph
    assert f"background-color:{render.ART}" in bar
    assert stage.count("▓") + stage.count("░") == 40   # 20-cell bars, both sides
    after = html.split('<div class="alog"', 1)[1]
    assert "arena-opts" not in after                   # nothing under the log
    assert html.count('class="options arena-opts"') == 1
    assert 'class="profile"' not in html and "facblk" not in html
    assert 'class="rail' not in html


def test_phase5_opener_keeps_regular_menu_and_profile():
    p = _climber(clazz="archer")
    s, fl = _hunt(p, 6)
    assert s.arena and s.arena["phase"] == "opener"
    html = render.render_scene_fragment(s)
    assert 'class="banner arena"' not in html
    assert "arena-opts" not in html                 # phase 8: regular menu
    assert 'class="options later"' in html
    assert 'class="profile"' in html or 'class="rail' in html


# ── 067 phase 6: named, aligned HUD; kind icons; tiles on every live card ─
def test_phase6_hud_names_gear_and_kind_icons():
    p = _climber(clazz="archer")
    p["gear"]["armor"] = "padded_jerkin"
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    e["profile"] = {"type": "armoured", "flying": True, "bulwark": True,
                    "speed": 5}
    e["def"] = 40
    e["hp"] = e["hp_max"] = 5000
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.arena["foe"]["armoured"] and s.arena["foe"]["flying"]
    html = render.render_scene_fragment(s)
    banner = html.split('class="banner arena"', 1)[1].split('<div class="alog"', 1)[0]
    huds = banner.split('<div class="ahuds">', 1)[1]
    assert huds.count('class="aname"') == 2
    assert p["name"].upper() in huds and e["name"].upper() in huds
    # order: climber's slab first (left), foe's second (right)
    assert huds.index('class="astat me"') < huds.index('class="astat foe"')
    foe = huds.split('class="astat foe"', 1)[1]
    assert "t_wing" in foe or 'data-tip="Flying' in foe
    assert 'data-tip="Armoured' in foe
    assert 'data-tip="Bulwark' in foe
    # the armour icon rides right after DEF n
    import re
    assert re.search(r'DEF \d+<span class="aico"[^>]*data-tip="Armoured', foe)
    me = huds.split('class="astat me"', 1)[1].split('class="astat foe"', 1)[0]
    assert 'class="agear"' in me
    assert 'class="aico lead"' in me                # the bow in hand
    assert 'data-tip="Padded Jerkin' in me


def test_phase6_magic_resist_level_on_foe_name():
    p = _climber(clazz="sorcerer")
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    e["profile"] = {"type": "magic_resist", "flying": False,
                    "bulwark": False, "speed": 5}
    e["hp"] = e["hp_max"] = 5000
    s = combat.resolve_fight_action(p, fl, "attack")
    pct = s.arena["foe"]["resist_pct"]
    assert pct > 0
    html = render.render_scene_fragment(s)
    foe = html.split('class="astat foe"', 1)[1]
    assert f"MR {pct}%" in foe and 'data-tip="Magic resistance' in foe


def test_phase8_victory_card_regular_menu_and_tally_over_scene():
    """067 phase 8 (roy): the fight over, the card is a regular card
    again — the town/gate menu as rows, the profile back — and the win
    tally (XP/GOLD) rides OVER the rendered scene, said once."""
    p = _climber()
    s, fl = _hunt(p, 6)
    e = p["encounter"]
    e["range"] = "close"
    e["hp"] = 1
    e["profile"] = {"type": "plain", "flying": False, "bulwark": False,
                    "speed": 5}
    p["training"]["blade"] = 10
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.arena and s.arena["phase"] == "victory"
    assert s.options
    html = render.render_scene_fragment(s)
    assert 'class="banner arena"' in html               # the scene stays
    assert "arena-opts" not in html and 'class="opt atile' not in html
    assert 'class="options later"' in html              # the regular menu
    # every option is a regular row/button
    assert html.count('data-opt="') >= len(s.options)
    # the tally over the scene, inside the banner, exactly once
    if getattr(s, "tally", None):
        banner = html.split('class="banner arena"', 1)[1] \
                     .split('<div class="eyebrow', 1)[0]
        assert 'class="awin later"' in banner
        # 0.96.1 (roy): the overlay is the LEAN tally — big lines only,
        # no mark heaps, no note, no slab behind the amounts
        assert html.count('class="tallies lean"') == 1
        assert "tmarks" not in banner and "tnote" not in banner
    # the profile is back on the end card
    assert 'class="profile"' in html or 'class="inv later"' in html


# ── 0.97.1 (roy): one name per card — the [i] rides the foe's nameplate
# in a live fight; the lean win amounts wear a + and a pixel shadow ──
def test_0963_live_round_info_on_nameplate_not_headline():
    p = _climber(clazz="archer")
    s, fl = _hunt(p, 6)
    p["encounter"]["range"] = "close"
    p["encounter"]["profile"] = {"type": "plain", "flying": False,
                                 "bulwark": False, "speed": 5}
    s = combat.resolve_fight_action(p, fl, "attack")
    assert s.arena and s.arena["phase"] == "round"
    html = render.render_scene_fragment(s)
    # the name is said ONCE — no headline line under the scene
    assert 'class="headline type"' not in html
    # the [i] rides the foe's nameplate and carries the dossier tip
    nm = (html.split('class="astat foe"', 1)[1]
              .split('class="aname"', 1)[1].split("</div>", 1)[0])
    assert 'class="info"' in nm and "data-tiph" in nm and "dossier" in nm


def test_0963_opener_and_victory_keep_their_headline():
    p = _climber(clazz="archer")
    s, fl = _hunt(p, 6)
    assert s.arena and s.arena["phase"] == "opener"
    html = render.render_scene_fragment(s)
    assert 'class="headline type"' in html and ">i</span></div>" in html
    # victory: the encounter is gone — the "evicted/falls" line stays
    p2 = _climber()
    s2, fl2 = _hunt(p2, 6)
    e = p2["encounter"]
    e["range"] = "close"
    e["hp"] = 1
    e["profile"] = {"type": "plain", "flying": False, "bulwark": False,
                    "speed": 5}
    p2["training"]["blade"] = 10
    s2 = combat.resolve_fight_action(p2, fl2, "attack")
    assert s2.arena and s2.arena["phase"] == "victory"
    html2 = render.render_scene_fragment(s2)
    assert 'class="headline type"' in html2


def test_0963_lean_tally_wears_a_plus():
    lean = render._tally_html([{"kind": "gold", "n": 7}], lean=True)
    full = render._tally_html([{"kind": "gold", "n": 7}])
    # the + glyph's middle line is ▀█▀ — no other tally char draws it
    assert "▀█▀" in lean
    assert "▀█▀" not in full
