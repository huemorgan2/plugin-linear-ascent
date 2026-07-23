"""Content loader: tier 1 loads, lints, numbers computed not authored."""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema


def test_tier1_loads_completely():
    floors = schema.load_floors(force=True)
    assert set(range(1, 11)).issubset(floors)


def test_every_floor_file_lints_clean():
    assert schema.lint_floors() == []


def test_numbers_are_computed_from_formulas():
    f5 = schema.get_floor(5)
    assert (f5.monster_atk, f5.monster_def, f5.monster_hp) == (22, 15, 85)
    assert (f5.warden_atk, f5.warden_def, f5.warden_hp) == (25, 20, 300)


def test_floor10_is_milestone_gnarl():
    f10 = schema.get_floor(10)
    assert f10.milestone is not None
    assert f10.milestone.quorum == 2
    assert "Gnarl" in f10.warden_name


def test_encounter_ids_unique_and_weighted():
    for f in schema.load_floors().values():
        ids = [e.id for e in f.encounters]
        assert len(ids) == len(set(ids))
        assert all(e.weight > 0 for e in f.encounters)


def test_prose_lint():
    for f in schema.load_floors().values():
        for e in f.encounters:
            assert len(e.prose) <= schema.PROSE_CAP
            for banned in schema.BANNED_WORDS:
                assert banned not in e.prose.lower()
