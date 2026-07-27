# Phase 008 — Bestiary at scale (floors 11–100)

Goal: the whole tower speaks the new language. Every floor gets 4–5
encounters with a deliberate matchup spread, profiles, lore, and art
for the new monsters.

## Tasks

1. Content retrofit floors 11–100 in band batches (11–20, 21–30, …):
   - 4–5 encounters per floor; per-band spread rule: ≥1 good and ≥1 bad
     target per class, ≥1 fast, ≥1 slow, flyers from band 1 end (floor
     4+ per the staircase), bulwarks from floor 6.
   - `lore:` on every encounter; trait placement follows each band's
     biome story (fusion-halls favor armor, the bio-lit forest favors
     resist, sky-ship wrecks favor flying …).
2. `content/schema.py` lint: enforce the spread rule per band + lore
   presence for floors ≥ 11 (floors 1–10 done in 001/003).
   003 retro: the `lore:` field, ≤160-char cap and prose lint already
   exist — this phase only flips lint from optional to required for
   floors ≥ 11. Authoring pace from 003: ~40 lore lines is one sitting;
   budget 4–5 sittings per ten-band retrofit, ship per band batch.
3. Warden/milestone profiles per plan §2.2 across all bands.
4. Art batch: 1-bit banners for every NEW monster (creature pipeline,
   `tools/generate_creatures.py`); alt text/lore alignment.
5. Vendor sync + deploy; version bump + publish (content-only bumps
   can ship per band batch — don't hold ten bands hostage).

## Tests / acceptance

- Content lint green with the new spread rules across all 100 floors.
- **Matchup sim at scale:** the 001 sim gate runs across every band —
  each class always has a viable hunting pool on its frontier
  (win ≥70% vs at least 2 encounter types per floor).
  001 retro: reuse 001's constants verbatim — hard-counter means
  win <30% OR rounds ≥1.6× plain (closed-form sims compress variance;
  the planned 2× never triggers). Smoothness on income allows upward
  steps (only down-cliffs/regressions fail), and rounds/risk must
  filter through `_is_intended` or off-class monsters poison averages.
  002 retro: sims must be chase-aware or archers lose to everything
  fast — model the class strategies (melee pays one crossing round,
  archer kites and re-opens when caught, sorcerer stands). Ranged vs
  fast is an INTENDED hard counter (`_speed_counters` in the 001 gate)
  — don't "fix" a band by removing its fast monsters. Copy the sim
  loops from `test_017_damage_types.py` / `test_017_speed_chase.py`
  rather than re-deriving them.
  004 retro: the full rung catalog now prices every band — run the
  days-to-afford gate (`test_017_shops.py`) against each band's
  actual income so floors 11-100 fund their rungs on the same smooth
  curve (income tuning lives in floor gold, not in reprints of the
  catalog).
  005 retro: the repair tax rides on rounds-per-fight — if a band's
  retuned encounters push average rounds up, weapon/armor wear per
  day rises with them. Re-run the 005 repair-tax gate
  (`test_017_durability.py`) after each band batch, alongside the
  days-to-afford gate; both read the same income table.
- Art: every encounter id with no shipped art logged and triaged (the
  renderer already skips silently — the list is the deliverable).
- Dojo spot-checks: one floor per band — read three [i] cards, verify
  spread is felt ("this floor has my prey and my predator").

Exit: all bands green, published, worldd synced,
`execution_summary.md`.
