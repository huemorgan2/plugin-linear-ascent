"""048 phase 4 — classes die.

The class question is gone from creation; the weapon in the hand and
its trained rank decide every gate the class used to. The off-class
system (price ×3, damage ×0.5, 25% miss, arrow burn) dies with it.
No player doc born after this phase carries a clazz; the engine reads
clazz nowhere outside state.py migrations and profile.py's tolerance
of old remote payloads.
"""

import pathlib
import re

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import combat, core, state, tips
from plugin_linear_ascent.sheet import character_sheet


# ── helpers ────────────────────────────────────────────────────────────

def _classless(uid):
    """The new creation walk: intro → race → name. No class question."""
    p = state.new_player(uid)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1", "")
    core.apply_choice(p, "human", "")
    core.apply_choice(p, "", "Testa")
    return p


def _arm(p, weapons, training, slots=None):
    held = [weapons] if isinstance(weapons, str) else list(weapons)
    p["training"] = dict(training)
    p["slots"] = slots or len(held)
    p["held"] = held
    p["gear"]["weapon"] = held[0]
    return p


def _floor_obj(p):
    from plugin_linear_ascent.content import schema
    return schema.get_floor(p["floor"] or 1)


def _fight(p, rng="at_range"):
    core.apply_choice(p, "gate", "")
    core.apply_choice(p, "floor_1", "")
    core.apply_choice(p, "hunt", "")
    assert p["encounter"] is not None
    p["encounter"]["range"] = rng
    p["encounter"]["gap"] = 1 if rng == "at_range" else 0
    p["encounter"]["shot_used"] = False
    p["encounter"].pop("attacked", None)
    return combat.fight_scene(p, _floor_obj(p))


def _opt(s, oid):
    for o in s.options or []:
        if o.id == oid:
            return o
    return None


def _scene_text(s):
    return " ".join([s.headline or "", s.support or "",
                     s.shard_note or ""] + list(s.body_lines or [])
                    + [f"{o.label} {o.hint}" for o in (s.options or [])])


# ── T7: the machinery is gone ──────────────────────────────────────────

def test_class_machinery_is_gone():
    for name in ("CLASSES", "class_starter", "off_class_price",
                 "off_class_offer", "OFF_CLASS_PRICE_MULT",
                 "OFF_CLASS_DMG_MULT", "OFF_CLASS_MISS",
                 "CONTRACT_CLASS_GOLD_MULT", "CONTRACT_CLASS_XP_MULT"):
        assert not hasattr(economy, name), name
    assert not hasattr(combat, "_off_class")
    assert not hasattr(tips, "_CLASS_ANGLE")


def test_path_economy_constants():
    assert economy.BASIC_WEAPON_PRICE == 60
    assert economy.CONTRACT_PATH_GOLD_MULT == 0.5
    assert economy.CONTRACT_PATH_XP_MULT == 0.5


def test_no_clazz_reads_outside_migrations():
    """profile.py tolerates old REMOTE payloads; state.py migrates old
    DOCS. Nothing else in the engine may read clazz."""
    import plugin_linear_ascent as pkg
    root = pathlib.Path(pkg.__file__).parent
    whitelist = {"state.py", "profile.py"}
    pat = re.compile(r"""\[\s*["']clazz["']\s*\]|\.get\(\s*["']clazz["']""")
    bad = []
    for f in sorted(root.rglob("*.py")):
        if f.name in whitelist:
            continue
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if pat.search(line):
                bad.append(f"{f.name}:{i}: {line.strip()}")
    assert not bad, "\n".join(bad)


# ── creation: race → name, sword-and-blade-2 starter ───────────────────

def test_creation_goes_race_to_name():
    p = state.new_player("048p4-create")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1", "")
    s = core.apply_choice(p, "human", "")
    ids = {o.id for o in (s.options or [])}
    assert not ids & {"warrior", "archer", "sorcerer"}
    assert p["stage"] != "creation_class"
    core.apply_choice(p, "", "Testa")
    assert p.get("name") == "Testa"
    assert not p.get("clazz")


def test_new_docs_carry_no_class():
    p = state.new_player("048p4-doc")
    assert not p.get("clazz")


def test_starter_kit_rusted_sword_blade_two():
    p = _classless("048p4-starter")
    assert p["gear"]["weapon"] == "rusted_sword"
    assert p["held"] == ["rusted_sword"]
    assert (p.get("training") or {}).get("blade") == 2


def test_sheet_drops_class():
    p = _classless("048p4-sheet")
    assert "class" not in character_sheet(p)


# ── the armory sells every line to everyone ────────────────────────────

def test_armory_lists_basics_at_sixty_and_no_off_class_rack():
    p = _classless("048p4-forge")
    p["gold"] = 1000
    p["location"] = "forge"
    s = core.current_scene(p)
    text = _scene_text(s)
    assert "Basic Bow" in text
    assert "Worn Wooden Staff" in text
    assert str(economy.BASIC_WEAPON_PRICE) in text
    assert "off-class" not in text.lower()
    ids = {o.id for o in (s.options or [])}
    assert "buy_basic_bow" in ids
    assert "buy_worn_staff" in ids
    gold = p["gold"]
    core.apply_choice(p, "buy_basic_bow", "")
    assert gold - p["gold"] == economy.BASIC_WEAPON_PRICE
    assert ("basic_bow" in (p.get("held") or [])
            or p["inventory"].get("basic_bow", 0) > 0)


def test_rendered_text_is_class_free():
    words = re.compile(r"\b(warrior|archer|sorcerer|class)\b", re.I)
    p = state.new_player("048p4-words")
    texts = [_scene_text(core.current_scene(p))]
    while p["stage"] == "intro":
        texts.append(_scene_text(core.apply_choice(p, "1", "")))
    texts.append(_scene_text(core.apply_choice(p, "human", "")))
    texts.append(_scene_text(core.apply_choice(p, "", "Testa")))
    texts.append(_scene_text(core.current_scene(p)))
    p["location"] = "forge"
    texts.append(_scene_text(core.current_scene(p)))
    joined = " ".join(texts)
    # 052: the human line's card at the gate is labeled WARRIOR — the
    # one sanctioned use of the word; it names a climber, not a class.
    joined = joined.replace("WARRIOR", "")
    m = words.search(joined)
    assert not m, f"class word in rendered text: {m.group()!r}"


# ── N7: the weapon+rank gate table ─────────────────────────────────────

def test_treeline_locked_below_rank_four():
    p = _classless("048p4-tree2")
    _arm(p, "basic_bow", {"bow": 2})
    s = _fight(p)
    o = _opt(s, "treeline_shot")
    assert o is not None
    assert o.locked
    assert "needs Bow rank 4 (you: 2)" in (o.label + " " + o.hint)


def test_treeline_open_at_rank_four():
    p = _classless("048p4-tree4")
    _arm(p, "basic_bow", {"bow": 4})
    s = _fight(p)
    o = _opt(s, "treeline_shot")
    assert o is not None
    assert not o.locked


def test_treeline_needs_a_bow_in_hand():
    p = _classless("048p4-treesword")
    _arm(p, "rusted_sword", {"blade": 2, "bow": 10})
    s = _fight(p)
    assert _opt(s, "treeline_shot") is None


def test_open_distance_draw_needs_rank_six():
    p = _classless("048p4-gap5")
    _arm(p, "basic_bow", {"bow": 5})
    s = _fight(p)
    o = _opt(s, "create_distance")
    assert o is not None
    assert o.locked
    assert "needs Bow rank 6 (you: 5)" in (o.label + " " + o.hint)

    p2 = _classless("048p4-gap6")
    _arm(p2, "basic_bow", {"bow": 6})
    o2 = _opt(_fight(p2), "create_distance")
    assert o2 is not None
    assert not o2.locked
    assert "×" not in (o2.label + o2.hint)


def test_gap_draw_multiplier_needs_rank_eight():
    p = _classless("048p4-gap8")
    _arm(p, "basic_bow", {"bow": 8})
    o = _opt(_fight(p), "create_distance")
    assert o is not None
    assert not o.locked
    assert "×" in (o.label + o.hint)


def test_shield_wall_gate():
    p = _classless("048p4-wall4")
    _arm(p, "rusted_sword", {"blade": 4})
    p["gear"]["shield"] = "gate_buckler"
    o = _opt(_fight(p, rng="close"), "shield_wall")
    assert o is not None
    assert not o.locked

    p2 = _classless("048p4-wall3")
    _arm(p2, "rusted_sword", {"blade": 3})
    p2["gear"]["shield"] = "gate_buckler"
    o2 = _opt(_fight(p2, rng="close"), "shield_wall")
    assert o2 is not None
    assert o2.locked
    assert "needs Blade rank 4 (you: 3)" in (o2.label + " " + o2.hint)

    p3 = _classless("048p4-wallnoshield")
    _arm(p3, "rusted_sword", {"blade": 10})
    p3["gear"].pop("shield", None)
    assert _opt(_fight(p3, rng="close"), "shield_wall") is None


def test_sleep_spell_gate():
    p = _classless("048p4-sleep6")
    _arm(p, "worn_staff", {"staff": 6})
    o = _opt(_fight(p, rng="close"), "sleep_spell")
    assert o is not None
    assert not o.locked
    assert "XP" in o.hint

    p2 = _classless("048p4-sleep5")
    _arm(p2, "worn_staff", {"staff": 5})
    o2 = _opt(_fight(p2, rng="close"), "sleep_spell")
    assert o2 is not None
    assert o2.locked
    assert "needs Staff rank 6 (you: 5)" in (o2.label + " " + o2.hint)

    p3 = _classless("048p4-sleepsword")
    _arm(p3, "rusted_sword", {"blade": 2, "staff": 10})
    assert _opt(_fight(p3, rng="close"), "sleep_spell") is None


def test_one_attack_row_per_held_weapon():
    p = _classless("048p4-slots")
    _arm(p, ["rusted_sword", "basic_bow"], {"blade": 6, "bow": 3}, slots=2)
    s = _fight(p, rng="close")
    assert _opt(s, "attack") is not None
    o = _opt(s, "attack_basic_bow")
    assert o is not None
    joined = o.label + " " + o.hint
    assert "Basic Bow" in joined
    assert "3" in joined

    p2 = _classless("048p4-oneslot")
    _arm(p2, "rusted_sword", {"blade": 6})
    s2 = _fight(p2, rng="close")
    assert _opt(s2, "attack") is not None
    assert not [o for o in s2.options if o.id.startswith("attack_")]
