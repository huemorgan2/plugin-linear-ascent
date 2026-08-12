"""049.1 — a held weapon is SEEN, and it says what it is.

Three reports from the same play session: a bought side-arm vanished
from every surface (it rode `held`, which nothing drew); its attack
row only appeared in close quarters (hidden, not locked, at range);
and it was called "Pigsticker" — a name with no weapon in it. Now the
pack strip draws held side-arms, the at-range row shows locked and
explains itself, and the blade is the Scrap Dagger everywhere. The
third carry slot also lost its level gate — the price is the gate.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text)


def _character(name):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, "human")
    choose(p, "", text=name)
    return p


def _archer_with_dagger(name):
    """A bow lead with a scrap dagger riding the second carry slot."""
    p = _character(name)
    p["training"]["bow"] = 6
    p["gear"]["weapon"] = "basic_bow"
    p["held"] = ["basic_bow", "scrap_dagger"]
    p["slots"] = 2
    return p


def test_the_dagger_says_dagger():
    g = economy.FORGE["scrap_dagger"]
    assert g.name == "Scrap Dagger"
    assert g.tier == 1 and g.slot == "weapon" and g.line == "warrior"
    assert "pigsticker" not in economy.FORGE


def test_v8_docs_holding_a_pigsticker_wake_with_a_scrap_dagger():
    p = _character("Renamed")
    p["version"] = 8
    p["gear"]["weapon"] = "pigsticker"
    p["held"] = ["pigsticker", "basic_bow"]
    p["inventory"]["pigsticker"] = 1
    p.setdefault("durability_pack", {})["pigsticker"] = 42.0
    state.ensure_current(p)
    assert p["version"] >= 9
    assert p["gear"]["weapon"] == "scrap_dagger"
    assert p["held"][0] == "scrap_dagger"
    assert p["inventory"].get("scrap_dagger") == 1
    assert "pigsticker" not in p["inventory"]
    assert p["durability_pack"]["scrap_dagger"] == 42.0


def test_the_pack_strip_draws_the_held_side_arm():
    p = _archer_with_dagger("Seenhand")
    p.setdefault("durability_pack", {})["scrap_dagger"] = 100.0
    strip = core._pack_strip(p)
    cell = next(c for c in strip if c["slug"] == "scrap_dagger")
    assert cell.get("held") is True
    assert "held" in cell["name"]
    assert cell.get("dur_left") is not None
    # the lead hand is not doubled
    assert sum(1 for c in strip if c["slug"] == "basic_bow") == 1


def test_at_range_the_steel_row_shows_locked_and_refuses():
    p = _archer_with_dagger("Rangebound")
    fl = schema.get_floor(1)
    enc = next(e for e in fl.encounters if e.id == "feral_boar")
    combat.start_encounter(p, fl, enc)
    p["encounter"]["range"] = "at_range"
    s = combat.fight_scene(p, fl)
    row = next(o for o in s.options if o.id == "attack_scrap_dagger")
    assert row.locked
    assert "close in" in (row.hint or "")
    # clicking it refuses without promoting and spends no round
    hp0 = p["hp"]
    s = combat.resolve_fight_action(p, fl, "attack_scrap_dagger")
    assert p["gear"]["weapon"] == "basic_bow"
    assert p["hp"] == hp0
    assert "close in" in (s.shard_note or "")
    # in close quarters the same row is live
    p["encounter"]["range"] = "close"
    s = combat.fight_scene(p, fl)
    row = next(o for o in s.options if o.id == "attack_scrap_dagger")
    assert not row.locked
