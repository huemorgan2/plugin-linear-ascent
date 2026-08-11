"""048 — the weapon decides. Part I mechanics: the type tables and
the damage triangle (phase 1: unwired — combat still runs the old
tier system; these prove the new tables before anything reads them)."""

from plugin_linear_ascent import economy

try:
    from tests.conftest import make_character
except ImportError:                                   # rootdir import
    from conftest import make_character

from plugin_linear_ascent.engine import state


# ── N1: one type bundles sign, speed, weight ──────────────────────────

def test_type_tables_exact():
    assert economy.TYPE_SPEED == {
        "fly": 7, "armoured": 3, "magic_resist": 3, "plain": 5}
    assert economy.TYPE_ATK == {
        "fly": 0.6, "armoured": 1.4, "magic_resist": 1.4, "plain": 1.0}
    assert economy.TYPE_HP == {
        "fly": 0.9, "armoured": 1.2, "magic_resist": 1.0, "plain": 1.0}
    assert economy.TYPE_GOLD == {
        "fly": 1.2, "armoured": 1.3, "magic_resist": 1.3, "plain": 1.0}


def test_triangle_cells_exact():
    M = economy.TYPE_MULT
    assert M["fly"] == {"blade": 0.0, "bow": 1.0, "staff": 0.6}
    assert M["armoured"] == {"blade": 0.5, "bow": 0.15, "staff": 1.0}
    assert M["magic_resist"] == {"blade": 1.0, "bow": 0.5, "staff": 0.15}
    assert M["plain"] == {"blade": 1.0, "bow": 1.0, "staff": 1.0}


# ── N2: the triangle in damage ────────────────────────────────────────

def test_typed_damage_blade_and_bow_eat_def_staff_ignores_it():
    # raw 42 vs DEF 20: blade/bow base 32, staff base 42
    assert economy.typed_damage_048("blade", 42, 20, "armoured") == 16
    assert economy.typed_damage_048("bow", 42, 20, "armoured") == 5
    assert economy.typed_damage_048("staff", 42, 20, "armoured") == 42
    assert economy.typed_damage_048("blade", 42, 20, "magic_resist") == 32
    assert economy.typed_damage_048("bow", 42, 20, "magic_resist") == 16
    assert economy.typed_damage_048("staff", 42, 20, "magic_resist") == 6
    assert economy.typed_damage_048("bow", 42, 20, "fly") == 32
    assert economy.typed_damage_048("staff", 42, 20, "fly") == 25
    for path in ("blade", "bow", "staff"):
        assert economy.typed_damage_048(path, 42, 20, "plain") == 32 \
            if path != "staff" else True
    assert economy.typed_damage_048("staff", 42, 20, "plain") == 42


def test_blade_cannot_reach_fly_everything_else_chips():
    # the single legal zero (013 chip law survives everywhere else)
    assert economy.typed_damage_048("blade", 999, 0, "fly") == 0
    # glancing answers still chip ≥1 even at hopeless raw
    assert economy.typed_damage_048("bow", 3, 40, "armoured") == 1
    assert economy.typed_damage_048("staff", 3, 40, "magic_resist") == 1
    assert economy.typed_damage_048("blade", 3, 40, "armoured") == 1


# ── N9: legacy trait sets map to the right type ───────────────────────

def test_type_from_traits_legacy_mapping():
    f = economy.type_from_traits
    assert f(("flying",)) == "fly"
    assert f(("flying", "armor_low")) == "fly"
    assert f(("armor_low",)) == "armoured"
    assert f(("armor_high", "slow")) == "armoured"
    assert f(("resist_med",)) == "magic_resist"
    assert f(("armor_med", "resist_med")) == "magic_resist"
    assert f(()) == "plain"
    assert f(("fast",)) == "plain"
    assert f(("bulwark",)) == "plain"        # ▣ is orthogonal, not a type


# ── the shared creation helper (T6 rescoped: canonical in conftest) ───

def test_conftest_helper_builds_a_character():
    p = state.new_player("048-helper")
    make_character(p, race="human", clazz="warrior", name="Proof")
    assert p["name"] == "Proof"
    assert p["stage"] not in ("intro", "creation_race", "creation_class",
                              "creation_name")
