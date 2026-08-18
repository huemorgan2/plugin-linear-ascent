# Phase 2 — Effects move from the pack to the slots

## Goal
An item in the pack changes nothing: no fight row, no death save, no
loot odds, no oil. The same item in its slot (charm pouch / bow quiver /
oiled weapon slot) works as before.

## Steps
- `combat._relic_options`: source = `gear["charm"]` (one item → its
  row) and `p["quiver"]` of the lead archer weapon (nock rows list
  bound stacks only). Remove `use_oil` row and `inv` reads.
- `combat._resolve_round`: every `use_*`/`drink_tonic` consumes from
  `gear["charm"]` (count 1 → slot empties); `nock_*` selects among
  bound arrows; `_quiver_shot` decrements `p["quiver"]`.
- Death: `stone_of_undying` / `reincarnation_spell` fire only if
  `gear["charm"]` is that slug; remove `SPARE_SPELL_LEAK` path.
- Oil: new pack verb `oil_<slug>` (out of fight) → `p["oil"][slug] =
  OIL_STRIKES`, consumes the flask.
- Arrows: new pack verb `nock_<slug>` out of fight moves the whole
  stack to `p["quiver"]` (needs a held archer weapon); mid-fight nock
  from pack removed; `unquiver_<slug>` returns to pack (capacity check).
- Luck charm: remove instant-drink in `_medlab_buy` and `luck_day`
  writes; `lucky(p) = gear["charm"]=="luck_charm"` replaces every
  `luck_day` read (combat.py:1422, core.py:659); drop tables at
  combat.py:1505/1531 add `CHARM_LOOT_PCT` to the rare weight when
  lucky; `_drop_ranges`/`_warden_drop_ranges` take `p` and mirror it;
  `charm_dur` −1 per victory, at 0 the charm crumbles (note line).
- Fight-only refusal: `wear_*`/`unequip_*` on any slot mid-fight →
  "Not in a fight — set it before you go down."

## Verification
- pytest: pack-only doc == empty-pack doc for options/odds/death;
  charm tonic → row → drink → slot None; stone in pack → death; stone
  in slot → revive; nock from pack refused mid-fight; quiver shots
  decrement `quiver`; lucky doc → `_drop_ranges` == realised weights.

## Rollback
`git revert`; docs with `quiver`/dict-oil load on phase-1 engine
(keys ignored / migrated).
