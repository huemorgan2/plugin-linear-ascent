# 073 — Roothollow square, in districts

## Problem
The square is one flat list of ~15 doors. A player scans every row to
find the Forge, the Vault, or their hall. The Arcanum hint said
"magic gear" / "staves" — it is the magic shop. "THE RACKS" does not
say you buy there.

## Root cause
007 put the gate first and left every later door as a peer. Related
doors (board under the gate, hall under the Guildhall, Stone under
the Relay) sit far apart. No section, no indent.

## Fix
One list, still numbered, no extra click.

- District headers on the first door of each group: THE CLIMB, THE
  MARKET, THE KEEP, THE BANNER, THE WIRE.
- Three nested rows (indent only): contract board under the Gate;
  YOUR FACTION'S HALL under the Guildhall; Stone of the Climb under
  the Relay (or THE WIRE on its own when there is no Relay).
- Arcanum hint: `magic`.
- Sidecar wire keys `option_nest` / `option_section` — never inside
  the option dict (old clients splat that and crash).

## Verification
Town card shows the five headers. Nested rows sit indented. Typed
numbers still match the rows. Solo (no world) still has the Stone.
`test_073_roothollow_square.py`.

## Rollback
Revert. Old clients drop the new top-level keys and see today's list.

## Execution status
Done 2026-08-24. Town list is CLIMB / MARKET / KEEP / BANNER / WIRE.
Board nests under the Gate, hall under the Guildhall, Stone under
the Relay. Arcanum hint is `magic`. Plugin tests `test_073` +
`test_027` + `test_029` + `test_031` 53 passed. Preview
`dojo/results/073-roothollow-square-preview.html`.

Recovered 2026-08-24 onto `0.97.3` (was implemented but uncommitted,
mixed with 070/071). Isolated commit: scene sidecar keys, district
headers, nest indent, Arcanum hint `magic`, `test_063` updated.
`test_073` + `test_063` + shops + visible-gates 62 passed. 070/071
left uncommitted.
