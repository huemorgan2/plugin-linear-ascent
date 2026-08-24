"""077 — the triangle decides: right weapon or flee.

The glance cells (bow-vs-armoured, magic-vs-magic_resist) drop from
x0.15 to x0.04 and lose the >=1 chip floor: a wrong-weapon fight
stalls instead of slowly winning. After two wasted attack rounds the
card says so in plain words. Half and full cells are untouched.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="archer", name="Tri"):
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


def _player(clazz, floor_no, name):
    p = create_character(fresh(name), clazz=clazz, name=name)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    return p


def _start(p, floor_no, mtype):
    fl = schema.get_floor(floor_no)
    enc = fl.encounters[0]
    combat.start_encounter(p, fl, enc)
    traits = () if mtype == "plain" else (mtype,)
    p["encounter"]["profile"] = economy.profile_from_traits(traits)
    p["encounter"]["hp"] = 100_000          # never dies — watch the stall
    return fl


# ── the glance math ──────────────────────────────────────────────────────

def test_glance_is_0015_and_floorless():
    assert economy.GLANCE_MULT == 0.015
    assert economy.TYPE_MULT["armoured"]["bow"] == 0.015
    assert economy.TYPE_MULT["magic_resist"]["staff"] == 0.015
    # a kitted floor-6-ish hit (base ~60) scratches for ~1, not ~9
    assert economy.typed_damage_048("bow", 80, 40, "armoured") == 1
    # a small hit does NOTHING — no >=1 floor on a glance
    assert economy.typed_damage_048("bow", 10, 10, "armoured") == 0
    assert economy.typed_damage_048("staff", 8, 0, "magic_resist") == 0
    # half and full cells keep the >=1 chip law
    assert economy.typed_damage_048("blade", 3, 40, "armoured") == 1
    assert economy.typed_damage_048("bow", 3, 40, "magic_resist") == 1


def test_a_glance_cannot_grind_a_kill_at_level():
    # at-level archer vs an armoured monster: >= 300 rounds of shooting
    # would be needed — the fight effectively cannot be won
    raw = 100                                 # generous kitted swing
    per_hit = economy.typed_damage_048("bow", raw, 40, "armoured")
    assert per_hit <= 4
    # +2 levels (x1.69 damage) still stalls
    per_hit_p2 = economy.typed_damage_048("bow", round(raw * 1.69),
                                          40, "armoured")
    assert per_hit_p2 <= 6


# ── the steering line ────────────────────────────────────────────────────

def test_steering_line_after_two_wasted_rounds(monkeypatch):
    p = _player("archer", 6, "steer-bow")
    fl = _start(p, 6, "armoured")
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    s1 = combat.resolve_fight_action(p, fl, "attack")
    assert not any("barely mark its plate" in ln for ln in s1.body_lines)
    s2 = combat.resolve_fight_action(p, fl, "attack")
    assert any("barely mark its plate" in ln for ln in s2.body_lines)
    assert any("or run" in ln for ln in s2.body_lines)


def test_steering_line_for_magic_and_blade(monkeypatch):
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    p = _player("sorcerer", 6, "steer-staff")
    fl = _start(p, 6, "magic_resist")
    combat.resolve_fight_action(p, fl, "attack")
    s = combat.resolve_fight_action(p, fl, "attack")
    assert any("spells slide off" in ln for ln in s.body_lines)
    q = _player("warrior", 6, "steer-blade")
    fl = _start(q, 6, "fly")
    q["encounter"]["range"] = "close"
    q["encounter"]["gap"] = 0
    combat.resolve_fight_action(q, fl, "attack")
    s2 = combat.resolve_fight_action(q, fl, "attack")
    assert any("blade cannot reach it" in ln for ln in s2.body_lines)


def test_no_steering_for_the_right_weapon(monkeypatch):
    p = _player("archer", 6, "steer-none")
    fl = _start(p, 6, "fly")            # bow vs fly = the right answer
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    combat.resolve_fight_action(p, fl, "attack")
    s = combat.resolve_fight_action(p, fl, "attack")
    assert not any("or run" in ln for ln in s.body_lines)


def test_piercing_arrow_resets_the_stall():
    p = _player("archer", 6, "steer-pierce")
    _start(p, 6, "armoured")
    p["encounter"]["_stall"] = 5
    assert combat._steer_wrong_weapon(p, pierce=True) == ""
    assert "_stall" not in p["encounter"]
