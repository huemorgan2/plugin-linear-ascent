# Phase 1 — conftest + the triangle

Goal: the type system exists and is proven, wired to nothing.
Nothing player-visible changes. One commit.

## Corrected scoping (learned before execution)

The master plan's T6 called `tests/conftest.py` "THE chokepoint".
Wrong: `conftest.py` only stubs `luna_sdk`. ~30 test files each
define a LOCAL `create_character(p, race, clazz, name)` that walks
the creation flow (`choose(p, race); choose(p, clazz);
choose(p, text=name)`). Consequence:
- Phase 1 ADDS a canonical helper to `conftest.py` (new tests use
  it; old files untouched, they stay green on the legacy flow).
- The big sweep of local helpers moves wholly to phase 4, done by
  script (regex over the uniform helper shape), not by hand.

## Tests first (red)

New file `tests/test_048_the_weapon_decides.py`, triangle section:

1. `TYPE_SPEED == {"fly":7,"armoured":3,"magic_resist":3,"plain":5}`;
   `TYPE_ATK`, `TYPE_HP`, `TYPE_GOLD` exact per plan N1.
2. `TYPE_MULT` — all 12 cells exact per N2 (fly: 0/1.0/0.6;
   armoured: .5/.15/1.0; magic_resist: 1.0/.5/.15; plain: 1/1/1).
3. `typed_damage_048(path, raw, deff, mtype)`:
   - blade/bow subtract `deff//2`, staff ignores DEF;
   - result `max(1, round(base*mult))` — chip ≥1 everywhere;
   - the single legal 0: blade vs fly;
   - spot values: raw 40 def 20 → blade/armoured 15, bow/armoured 5
     (chip math), staff/armoured 40, bow/fly 30, staff/fly 24.
4. `type_from_traits`: `{"flying"}`→fly; `{"armor_low"}` (any
   armor_*)→armoured; `{"resist_med"}`→magic_resist; armor+resist→
   magic_resist; `set()`→plain; `bulwark` passes through untouched.
5. conftest helper: `conftest.make_character(p, race="human",
   name="Testa", clazz="warrior")` reproduces the legacy flow and
   returns p — asserted by creating one character.

## Code (green)

`plugin_linear_ascent/economy.py` (near typed_damage, ~:675):
- `TYPE_SPEED/TYPE_ATK/TYPE_HP/TYPE_GOLD`, `TYPE_MULT` consts.
- `type_from_traits(traits) -> str`.
- `typed_damage_048(path, raw, deff, mtype) -> int` alongside the
  old `typed_damage` (which keeps serving live combat until ph 5).
`tests/conftest.py`: `make_character` helper (walks movie+creation).

## Green =

`pytest tests/test_048_the_weapon_decides.py` + FULL suite
unchanged (worldd venv). Commit:
`048 phase 1: type tables + triangle (unwired) + conftest helper`.
