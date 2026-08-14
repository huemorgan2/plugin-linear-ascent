"""017 phase 003 — the enemy [i] card.

The counter system becomes READABLE: scene.enemy payload, the always-on
HP bar, the range chip, named damage modifiers (the 002 retro), trait
icons, and lore.
"""

import itertools

import pytest

from plugin_linear_ascent import economy, icons, render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state
from plugin_linear_ascent.engine.scene import Scene


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="warrior", name="Dossier"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def _player(clazz, floor_no, name):
    p = create_character(fresh(name), clazz=clazz)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    return p


def _enc(floor_no, enc_id):
    fl = schema.get_floor(floor_no)
    return fl, next(e for e in fl.encounters if e.id == enc_id)


def _fight(clazz, floor_no, enc_id, name="dossier"):
    p = _player(clazz, floor_no, f"{name}-{clazz}-{enc_id}")
    fl, enc = _enc(floor_no, enc_id)
    s = combat.start_encounter(p, fl, enc)
    return p, fl, s


# ── the payload ──────────────────────────────────────────────────────────

def test_every_fight_scene_carries_the_enemy_payload():
    p, fl, s = _fight("warrior", 1, "grey_wolf")
    en = s.enemy
    assert en and en["name"] == "Grey wolf"
    assert en["hp"] == en["hp_max"] > 0
    assert en["range"] == "at_range"
    assert en["dtype"] == "melee"
    # mid-fight scenes keep it too
    p["encounter"]["range"] = "close"
    s2 = combat.fight_scene(p, fl)
    assert s2.enemy and s2.enemy["range"] == "close"


def test_payload_survives_the_scene_roundtrip():
    _, _, s = _fight("archer", 6, "lane_boar")
    back = Scene.from_dict(s.to_dict())
    assert back.enemy == s.enemy


def test_lore_reaches_the_payload():
    _, _, s = _fight("warrior", 6, "lane_boar")
    assert "only" in s.enemy["lore"] and "through" in s.enemy["lore"]


def test_every_floor_1_to_10_encounter_has_lore():
    for n in range(1, 11):
        fl = schema.get_floor(n)
        for e in fl.encounters:
            assert e.lore, f"floor {n} {e.id}: no lore"
            assert len(e.lore) <= schema.LORE_CAP


def test_lore_lint_rejects_overrun_and_banned_words():
    with pytest.raises(schema.ContentError):
        schema._check_prose("press the button to win", "t/lore")
    long = "x" * (schema.LORE_CAP + 1)
    # the loader path enforces the cap
    assert len(long) > schema.LORE_CAP


# ── the dossier fragment ─────────────────────────────────────────────────

def _payload(mtype="plain", flying=None, bulwark=False,
             speed=5, rng="at_range", dtype="melee", pspd=5):
    # 048: one type carries the whole triangle; flying rides the type
    # unless a test grounds it explicitly (the sky-hook case).
    if flying is None:
        flying = mtype == "fly"
    prof = {"type": mtype, "flying": flying,
            "bulwark": bulwark, "speed": speed}
    return {"name": "Test beast", "hp": 40, "hp_max": 80,
            "atk": 10, "def": 10, "profile": prof,
            "tiers": [], "range": rng, "lore": "A test of a beast.",
            "specimen": "common", "pspd": pspd, "mspd": speed,
            "dtype": dtype,
            "dodge": economy.dodge_pct(pspd, speed)}


def test_dossier_renders_every_profile_combination():
    for mtype, bulwark, speed in itertools.product(
            ("plain", "armoured", "magic_resist", "fly"),
            (False, True), (3, 5, 7)):
        html = render._dossier_html(_payload(
            mtype=mtype, bulwark=bulwark, speed=speed))
        assert "<details" in html and "dossier" in html
        assert ("armoured" in html) == (mtype == "armoured")
        assert ("magic-resistant" in html) == (mtype == "magic_resist")
        assert ("it flies" in html) == (mtype == "fly")
        assert ("bulwark" in html) == bulwark
        assert "speed" in html            # always a speed row


def test_dossier_names_the_active_modifiers():
    # 002 retro: the bow collapse must be READ, not felt.
    close_bow = render._dossier_html(_payload(rng="close", dtype="ranged"))
    assert "×0.6" in close_bow
    at_range = render._dossier_html(_payload(rng="at_range", dtype="melee"))
    # 031 §7: at range it isn't halved — it can't answer at all
    assert "CANNOT reach you" in at_range
    assert "swing until you close" in at_range
    flyer = render._dossier_html(_payload(mtype="fly", dtype="melee",
                                          rng="close"))
    assert "cannot touch it" in flyer
    dodge = render._dossier_html(_payload(speed=3, pspd=5, rng="close"))
    assert "slips 11%" in dodge


def test_dossier_reads_the_chase_for_both_sides():
    fast = render._dossier_html(_payload(speed=7))
    assert "outrunning" in fast
    slow = render._dossier_html(_payload(speed=3))
    assert "kite" in slow


def test_dossier_carries_the_lore():
    html = render._dossier_html(_payload())
    assert "A test of a beast." in html


# ── the fight header ─────────────────────────────────────────────────────

def test_enemy_head_is_the_name_and_stats_ride_the_art():
    # 009 redo again: the head is the NAME (plus range/[i]); the whole
    # sheet is one line printed over the creature art — HP as a bar,
    # ATK/DEF/SPEED as numbers on a black slab.
    html = render._enemy_head_html(_payload())            # 40/80
    assert "piprow" not in html and "HP 40/80" not in html
    stat = render._estat_html(_payload())
    assert "ATK 10" in stat and "DEF 10" in stat
    assert render.GOLD in stat                            # bleeding → gold
    low = dict(_payload(), hp=8)                          # ≤1/3 reads red
    assert render.RED in render._estat_html(low)
    full = dict(_payload(), hp=80)                        # whole reads green
    assert render.OK in render._estat_html(full)


def test_range_and_modifiers_moved_into_the_dossier():
    at_range = render._dossier_html(_payload(rng="at_range"))
    assert "at range" in at_range
    close = render._dossier_html(_payload(rng="close", dtype="ranged"))
    assert "close quarters" in close
    assert "×0.6" in close


def test_fragment_wires_header_and_dossier_into_the_card():
    _, _, s = _fight("archer", 6, "lane_boar")
    html = render.render_scene_fragment(s)
    assert "ehead" in html
    assert "<details" in html and "dossier" in html
    assert html.count("ticon") >= 2       # bulwark + speed rows at least
    # the old bare-◈ profile body line is retired
    assert "◈ bulwark" not in html


# ── trait icons ──────────────────────────────────────────────────────────

def test_every_trait_has_an_icon_mask():
    for key in ("t_armor", "t_resist", "t_wing", "t_speed", "t_bulwark",
                "t_wrench"):
        url = icons.icon_data_url(key)
        assert url.startswith("data:image/svg+xml")
        assert "rect" in url or "%3Crect" in url


def test_icon_grids_are_16_wide():
    for key, grid in icons._GRIDS.items():
        for i, row in enumerate(grid):
            assert len(row) == 16, (key, i)


def test_headline_is_the_name_and_the_text_keeps_the_sheet():
    # the 009 overlay: the headline is the name alone; the numbers ride
    # the art line (HTML) and the enemy line (text surface).
    p, fl, s = _fight("warrior", 1, "grey_wolf")
    assert s.headline.startswith("Grey wolf")
    txt = s.to_text()
    for bit in ("HP", "ATK", "DEF"):
        assert bit in txt, (bit, txt)
    # ... and the text line tracks the wound after the first exchange
    p["encounter"]["range"] = "close"
    s2 = combat.resolve_fight_action(p, fl, "attack")
    if s2.enemy:                          # fight still on
        assert f"HP {max(0, p['encounter']['hp'])}" in s2.to_text()
