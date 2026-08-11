"""048 phase 7 — T7: content speaks types natively.

The legacy trait bridge (armor_*/resist_*/flying/fast/slow →
type_from_traits) dies. YAML carries at most ONE type trait per
monster — fly / armoured / magic_resist, plain = no type trait —
beside the archetype (body, bite) and the orthogonal bulwark. The
linter enforces the new vocabulary; the intro staircase survives in
type words; the classroom census and the restored ≥2 pool rule make
the retag deliberate, not incidental.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema


# ── the native vocabulary ──────────────────────────────────────────────

def test_allowed_traits_are_the_native_set():
    assert schema.ALLOWED_TRAITS == {
        "fly", "armoured", "magic_resist", "bulwark",
        "frail", "lean", "sturdy", "hulking",
        "feeble", "fierce", "savage",
    }


@pytest.mark.parametrize("legacy", [
    "flying", "fast", "slow", "armored",
    "armor_low", "armor_med", "armor_high",
    "resist_low", "resist_med", "resist_high",
])
def test_legacy_traits_are_rejected(legacy):
    with pytest.raises(schema.ContentError):
        schema._check_traits((legacy,), 20, "floor_020/_x")


def test_native_type_reads_straight_off_the_trait():
    assert economy.type_of(("fly", "frail")) == "fly"
    assert economy.type_of(("armoured", "hulking")) == "armoured"
    assert economy.type_of(("magic_resist",)) == "magic_resist"
    assert economy.type_of(("feeble", "lean")) == "plain"
    assert economy.type_of(()) == "plain"
    # bulwark is orthogonal — never a type
    assert economy.type_of(("bulwark",)) == "plain"


def test_profile_reads_native_traits():
    prof = economy.profile_from_traits(("fly", "frail"))
    assert prof["type"] == "fly" and prof["flying"]
    assert prof["speed"] == economy.TYPE_SPEED["fly"]
    prof = economy.profile_from_traits(("armoured", "bulwark"))
    assert prof["type"] == "armoured" and prof["bulwark"]
    # the legacy bridge no longer reaches the runtime: legacy names
    # read as plain here (type_from_traits stays for doc migration)
    assert economy.profile_from_traits(("flying",))["type"] == "plain"


def test_no_yaml_carries_a_legacy_trait():
    legacy = {"flying", "fast", "slow", "armored",
              "armor_low", "armor_med", "armor_high",
              "resist_low", "resist_med", "resist_high"}
    for n in range(1, 101):
        for e in schema.get_floor(n).encounters:
            assert not (set(e.traits) & legacy), (n, e.id, e.traits)


def test_one_type_trait_per_monster():
    types = {"fly", "armoured", "magic_resist"}
    for n in range(1, 101):
        for e in schema.get_floor(n).encounters:
            assert len(set(e.traits) & types) <= 1, (n, e.id, e.traits)


# ── the intro staircase, in type words ─────────────────────────────────

def test_intro_staircase_survives_the_retag():
    assert schema.TRAIT_INTRO_FLOOR == {
        "armoured": 2, "magic_resist": 3, "fly": 4, "bulwark": 6}
    for n in range(1, 11):
        for e in schema.get_floor(n).encounters:
            for t in set(e.traits) & set(schema.TRAIT_INTRO_FLOOR):
                assert n >= schema.TRAIT_INTRO_FLOOR[t], (n, e.id, t)


# ── the classroom census (N8) ──────────────────────────────────────────

def test_classroom_floors_spawn_every_sign():
    """Floors 4–10 carry all three signs — every hunt on the young
    tower can meet every lesson. Floors 1–3 stay the staircase:
    plain first, plate on 2, spellguard on 3, wings on 4."""
    for n in range(4, 11):
        types = {economy.type_of(e.traits)
                 for e in schema.get_floor(n).encounters}
        assert {"fly", "armoured", "magic_resist"} <= types, (n, types)
    assert all(economy.type_of(e.traits) == "plain"
               for e in schema.get_floor(1).encounters)
    assert {economy.type_of(e.traits)
            for e in schema.get_floor(2).encounters} <= {"plain", "armoured"}
    assert {economy.type_of(e.traits)
            for e in schema.get_floor(3).encounters} <= {
                "plain", "armoured", "magic_resist"}


# ── the pool rule, restored to ≥2 ──────────────────────────────────────

def test_every_path_owns_two_full_targets_per_floor():
    """008/048: with the retag done, no path is ever down to a single
    farmable answer — schema lint and the measured gate both sit at
    ≥2 again (floor 1 exempt for bow/staff: it is all plain by the
    staircase, and plain answers every path)."""
    for n in range(1, 101):
        fl = schema.get_floor(n)
        for path in ("blade", "bow", "staff"):
            good = sum(
                1 for e in fl.encounters
                if economy.TYPE_MULT[economy.type_of(e.traits)][path] >= 1.0
                and not economy.profile_from_traits(e.traits)["bulwark"])
            assert good >= 2, (n, path, good)
