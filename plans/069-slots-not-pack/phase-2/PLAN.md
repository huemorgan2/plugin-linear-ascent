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

## Execution status
Executed 2026-08-18. combat.py: `pouch/spend_pouch/lucky/_wear_charm`;
`_relic_options` reads the pouch and the quiver only; `drink_medgel` /
`drink_trauma_kit` fight rows (+HP, monster answers); `use_oil` row gone;
stone/spell/tonic/veil/apple/severing/net/hook/strip/curse/polymorph all
guard `pouch(p)==slug` and empty the slot; spare-spell leak removed;
drop tables `alpha_drop_table(p)`/`warden_drop_table(p)` +CHARM_LOOT_PCT
when lucky, `rare_loot_pct`; charm wears one per victory. core.py: pack
offers nothing in a fight (arrows: "bind before the fight"; charm kinds:
POUCH_ONLY_WHY); on the road `use_weapon_oil` slicks the lead,
`nock_<slug>` moves the stack to `quiver`; luck charm buy lands in the
pack, no `luck_day` writes/reads remain. tips: drink_medgel /
drink_trauma_kit / use_weapon_oil / nock_. Tests: 9 new in
test_069 (inert pack == empty pack for options, odds, death; pouch
tonic/medgel; stone pack vs pouch; nock road-only + quiver decrement;
oil road-only; worn luck fattens rare drop and wears out; pack luck is
not luck; wear refused mid-fight); test_017_death_relics `_fight`
routes kwargs to quiver/oil/pouch, spare-spell test rewritten to "pack
spells neither fire nor leak"; test_017_characters / test_027 updated.
Suite: 1273 passed, 6 pre-existing failures (unchanged list).
