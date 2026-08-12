"""019 §1 — the rack speaks in rows: the worn rung stays on sale as a
spare, duplicates ride to the pack (armory fodder), and the next rung is
a LOCKED row that explains itself when clicked. Plus the Option.locked
wire format."""

from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.engine.scene import Option, Scene


def create_character(name, clazz="warrior"):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
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


# ── the worn rung never leaves the rack ──────────────────────────────────

def test_worn_rung_stays_on_sale_as_a_spare():
    p = create_character("spare-row")
    p["gold"] = 1_000
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_scrap_dagger")
    assert p["gear"]["weapon"] == "scrap_dagger"
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_scrap_dagger")
    assert "worn — spare" in row.hint
    assert not row.locked


def test_buying_a_spare_fills_the_pack_not_the_body():
    p = create_character("spare-buy")
    p["gold"] = 1_000
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_scrap_dagger")
    p["hone"]["weapon"] = 2                    # sharpened on the body
    dur = dict(p["durability"])
    s = core.apply_choice(p, "buy_scrap_dagger")
    assert p["inventory"]["scrap_dagger"] == 1   # the spare, in the pack
    assert p["gear"]["weapon"] == "scrap_dagger"
    assert p["hone"]["weapon"] == 2            # nothing on the body moved
    assert p["durability"] == dur
    assert p["gold"] == 1_000 - 200 - 200
    assert "durability_pack" in p and "scrap_dagger" in p["durability_pack"]
    assert any("spare for the pack" in ln for ln in s.body_lines)


def test_spares_stack():
    p = create_character("spare-stack")
    p["gold"] = 1_000
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_scrap_dagger")
    core.apply_choice(p, "buy_scrap_dagger")
    core.apply_choice(p, "buy_scrap_dagger")
    assert p["inventory"]["scrap_dagger"] == 2


# ── the locked next rung ─────────────────────────────────────────────────

def test_locked_rows_carry_the_gate_and_no_lock_prose_remains():
    p = create_character("locked-rows")
    s = core.apply_choice(p, "forge")
    locked = [o for o in s.options if o.locked]
    assert locked                              # every ladder shows its next
    for o in locked:
        assert o.hint.startswith("🔒 level ")
        assert "◈" in o.hint
    assert not any("🔒" in ln for ln in s.body_lines)


def test_clicking_a_locked_row_explains_the_gate():
    p = create_character("locked-click")
    p["gold"] = 10_000
    core.apply_choice(p, "forge")
    # 025: at level 1 the locked row is band 1's next rung, one level up
    s = core.apply_choice(p, "buy_notched_cleaver")
    assert p["gear"]["weapon"] != "notched_cleaver"
    assert p["gold"] == 10_000                 # nothing charged
    assert "level 2" in s.shard_note


# ── the wire format ──────────────────────────────────────────────────────

def test_option_locked_survives_the_dict_round_trip():
    s = Scene(eyebrow="X", headline="x", options=[
        Option("a", "Open door"),
        Option("b", "Barred door", "🔒 level 6", locked=True)])
    d = s.to_dict()
    assert [o["locked"] for o in d["options"]] == [False, True]
    back = Scene.from_dict(d)
    assert back.options[1].locked and not back.options[0].locked
