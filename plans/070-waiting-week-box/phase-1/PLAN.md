# Phase 1 — Copy + engine reach

## Goal
The week-pick is a `weekpick` notice with the locked English lines.
`pick_*` resolves from any notice room. The Vault no longer offers the
prizes. The Vault door is not badged for the pick.

## Steps
- `weekly.py`: `HEADER`, `choices()`, receipt strings, fallback
  sentence; `pick()` writes `p["strongbox_note"]`.
- `notices.py`: replace the strongbox COLLECT row with `weekpick`;
  `doors()` skips entries with no `door`.
- `core.py`: handle `pick_*` next to pack-use; `_stamp` prepends
  `strongbox_note`; `_vault_scene` drops `pick_*` options and the
  "box is OPEN" line.
- `tips.py`: `pick_*` match the locked sentences.

## Verification
Pending week → one `weekpick`, no Vault COLLECT about a strongbox;
`doors` does not increment `vault`; `_vault_scene` has no `pick_*`;
`apply_choice(p, "pick_gold")` from town and from the Forge pays and
clears pending; 2-slot list is gold only; 3-slot list is four rows;
jargon absent; fallback uses the new sentence.

## Rollback
`git revert` this phase.

## Execution status
Done 2026-08-23. `weekly.choices` / receipts, `weekpick` notice,
`pick_*` from any notice room, Vault menu stripped of prizes.
