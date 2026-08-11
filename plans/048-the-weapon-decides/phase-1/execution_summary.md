# Phase 1 — execution summary (2026-08-11)

Status: DONE, green. Commit: `048 phase 1: type tables + triangle
(unwired) + conftest helper`.

## What landed

- `economy.py`: `TYPE_SPEED/ATK/HP/GOLD`, `TYPE_MULT`,
  `type_from_traits`, `typed_damage_048` — alongside the old
  `typed_damage`; nothing reads them yet.
- `tests/test_048_the_weapon_decides.py`: 6 cases (tables, all 12
  triangle cells, DEF math, chip law + the single legal 0, legacy
  trait mapping, helper smoke). Red first (5 failed), then green.
- `tests/conftest.py`: canonical `make_character` — the ~30 local
  copies fold into it in phase 4.

## Suite

991 passed, 1 skipped, 1 xfailed, **1 failed = baseline-red**:
`test_034_shield_wear.py::test_shield_wall_pays_for_the_whole_blow`
fails on `main` too (deterministic, 1300→1299 tread, needs ≥2).
Cause: 047 fast-start softened floor-1 blows below 2 tread; the
sibling test pinned floor 3 for this exact reason (043.2 comment).
NOT touched by 048 — logged for phase 8 polish (pin floor 3 per
the sibling's precedent) and flagged to roy.

## Learnings → next phases

1. **Banker's rounding**: Python `round(4.5) == 4`. Plan spot
   values must avoid .5 ties (the master plan's "bow/armoured 5"
   example was wrong at raw 40; used raw 42). Phase 6 bake asserts
   must compute expectations with `round()`, never by hand.
2. **Resist outranks armor** in `type_from_traits` (armor+resist →
   magic_resist), flight outranks both — matches plan N9.
3. Baseline-red policy: "suite green" for phases 1–7 = no failures
   beyond the one baseline-red above.
4. tests/ is a package (`__init__.py`); import the helper as
   `from tests.conftest import make_character` with plain
   `conftest` fallback.
