# Phase 2 — promote gear from the pack

## Goal

Clicking a piece of gear in the pack (out of a fight) offers one action
that equips it into its slot: "Use this" (weapon), "Use as shield"
(shield), "Wear this" (armor), "Wear these" (shoes). One weapon held,
one shield, one armour — enforced by the existing single-slug slots.
Measurable: `pack_actions(p, <pack gear slug>)` returns a `wear_<slug>`
option, and dispatching it swaps the piece into `p["gear"][slot]` with
durability travelling and the old piece landing in the pack.

## Steps

1. `engine/core.py pack_actions()` (~112): in the out-of-fight branch,
   before the FORGE why-string fallback (~165), for `g = FORGE/starter
   lookup` with `slot in DURABILITY_SLOTS` and `inventory[slug] > 0`:
   return `Option(f"wear_{slug}", <label per slot>, hint)`. Hint:
   "swap it into your hand — honing resets" for weapon/shield, "wear it
   — honing resets" otherwise; suppress the action when the same slug is
   already equipped in its slot (why-string: "Already in your hand." /
   "Already worn."). Off-class gear keeps the action (wearing off-class
   is legal; it misses 25% — same rule as the Forge row).
2. `engine/core.py _pack_use()` (~169): accept `option_id.startswith("wear_")`
   in addition to `PACK_USE_IDS`; re-validate against `pack_actions`
   (existing pattern) and call `_wear_from_pack(p, slug, _build_scene)`.
   Also extend the pre-check in `apply_choice` (~236–239) the same way.
3. `engine/tips.py`: `option_tip` already has a `wear_` prefix rule via
   the forge — verify; add one if the prefix only resolves in forge
   context.
4. No render/JS change: `_stamp` serializes the option into
   `cell["acts"]` and the popup dispatches it already.

Inheritance: vendored at ship time.

## Verification

New tests in `tests/test_045_hold_and_endure.py`:
- pack shield → `wear_` option present, labelled "Use as shield";
  dispatch equips it, old shield back in pack, `durability` and
  `durability_pack` swapped, hone reset to 0.
- pack weapon → "Use this"; equipped weapon changes.
- in a fight → no `wear_` option from `pack_actions`.
- equipped slug (count 0 in pack) → no action.
Then the phase-relevant suite: `pytest tests/test_014_inventory_tooltips.py tests/test_engine.py tests/test_045_hold_and_endure.py`.

## Rollback

`git revert` the phase commit — `wear_*` from the pack simply stops
being offered; state written by it (gear/durability swaps) is exactly
what the Forge path writes, so no cleanup.

## Execution status

**Done** — commit `00cb26f` (2026-08-09). `pack_actions` FORGE branch
offers `wear_<slug>` (weapon "Use this", shield "Use as shield" /
sorcerer "Hold this focus", armor "Wear this", shoes "Wear these");
equipped spare refuses with "Already in your hand."/"Already worn." —
an improvement over the old silent no-op that reset honing.
`_pack_use` routes `wear_*` to `_wear_from_pack`; refused mid-fight.
Unit tests: equips + durability travels via `durability_pack`, old
piece back to pack + hone reset, no promotion mid-fight, equipped-spare
refusal. Production dojo 2026-08-10: `wear_scrapwood_buckler` promoted
the packed spare ("+ Scrapwood Buckler back on — the Warded Scrapwood
Buckler goes to your pack"), gear flip confirmed via `/v1/character`,
and its wear (END 1,035/1,083) traveled through the pack intact.
