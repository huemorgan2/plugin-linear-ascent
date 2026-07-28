# Execution summary — plan 020, the climb ahead

Status: **complete** (with three deliberate deviations, below).

## What was built

- **`plugin_linear_ascent/unlocks.py`** — the registry. One frozen
  dataclass, ~40 entries, every threshold read from its owning constant
  (`economy.*`, `social.FOUND_MIN_LEVEL`) — a view, never a copy. Static
  entries (relay, founding, fields, grants, Arcanum, the two expiring
  protections) plus generated families: gear tiers 2–10, the shoes
  ladder's explicit gates, energy-cap steps, relic shelf floors, honing
  cap resets per band, milestone Wardens with their quorums.
  API: `met`, `ahead`, `just_reached`, `for_option`, `next_line`,
  `climb_ahead_lines`, `protections_active`. Built lazily + cached to
  avoid the social↔unlocks import cycle.
- **The square** — one `NEXT — LEVEL N: …` line, nearest threshold only,
  gifts and bills together ("your own banner (◈ 300) · and beginner's
  mercy ends"). Locked town doors (Arcanum/Relay/fields) now carry
  `locked=True` (019's grammar), same refusal notes as before.
- **The Stone** — `▣ THE CLIMB AHEAD` fold: the ladder grouped by
  threshold, `+ / − / ▲` glyphs, capped at 8 with "…and the tower keeps
  the rest".
- **The gate picker** — floors above your legs are locked rows naming
  the level; milestone floors carry "war party of N" in the hint; the
  floor below a milestone warns at the gate town, before ⚡ is spent.
- **The moments** — `guild_train` announces everything the bought level
  opened AND closed; a warden first-clear names what the new frontier
  opened; the first unprotected death says "the tower is no longer
  gentle with you" exactly once (flagged).
- **The Guildhall** — the value line ("a banner pools coin…") leads the
  non-member hall; the empty state names level + fee.
- **Luna** — `character_sheet()` gains `next_unlocks` +
  `protections_active`; `_GUIDE_RULES` names the level-4 double edge and
  points at the sheet; `option_tip` resolves `found_guild` and any
  registry-backed row dynamically from the constants.

## Tests

- `test_020_unlocks.py` (10): coverage guard **plus a rot guard** (any
  new `*_LEVEL` constant must be registered or exempted), no-drift
  assertions, `ahead` ordering, level-1/level-95 sanity, spoiler cap,
  `just_reached(3→4)` == exactly founding + mercy-ends.
- `test_020_visible_gates.py` (9): NEXT line, locked doors refuse
  kindly, Stone fold with a `−` entry, locked far floors, milestone
  hints and pre-warning, level-4 training card carries both halves,
  first unprotected death named once, the sheet carries the ladder.
- worldd `test_gate_constants.py` (2): worldd's founding gate ==
  plugin's == registry's.
- Suites: plugin **477 passed**, worldd **55 passed**.

## Deviations from the plan (all deliberate)

1. **Members see no locked founding row** — the plan wanted one; 019's
   shipped test (`test_member_never_sees_the_found_row…`) rules the
   opposite and is the later decision. Kept 019's law.
2. **The three town-door hints stay hand-written** (they already read
   the live constants directly — no drift possible); they gained
   `locked=True` so the render grammar is uniform. Regenerating their
   prose from the registry bought nothing.
3. **Fee is ◈ 300, level 4** — the plan's mock said ◈ 500; the constant
   says 300. The registry reads the constant, as designed.

## Learned / forward notes for 022

- `unlocks.py` is exactly the socket 022's clocks need: contract board /
  night slot / strongbox reveals are one registry entry each
  (`level 4/6/10`), and the square + Stone + level-up card advertise
  them for free. Phase 004/005 should ADD ENTRIES, not new surfaces.
- `just_reached` on floor-open is where "the wound out-heals one blade"
  (frontier 31 warning) belongs — one generated floor entry.
- The `registry()` lru_cache means tests that monkeypatch constants must
  call `unlocks.registry.cache_clear()` — worth remembering in 022.
