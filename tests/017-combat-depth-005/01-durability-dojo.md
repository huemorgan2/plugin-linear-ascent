# Dojo — 017 phase 005: durability & repair

Run 2026-07-27, local Luna (8765) → local worldd (8600, fresh bind
verified by port-kill first), tenant qa007, real browser via Playwright.
Player: level-6 warrior, ◈20,000, v2 doc (migration exercised live).

## Scenarios & results

1. **Teaching line on first paid purchase** — bought a Pigsticker at
   the Forge. Note read: "+ Pigsticker equipped (weapon +8 ATK) — the
   Rusted Sword goes in the scrap bin — paid gear wears with use; the
   Forge repairs it for a fraction of its price". PASS.
2. **Live v2→v3 migration** — the doc arrived v2 with paid boots and a
   focus equipped; after first load: `durability {shoes: 1300,
   shield: 1300}`, version 3. Paid gear arrives with FULL pools. PASS.
3. **Wear bar + hover** — set weapon durability to 390/1300 (30%) in
   the DB, rebuilt the scene. Pack strip shows a gold hairline bar at
   30% width under the Pigsticker icon; hover reads "… · 30% — repair
   at the Forge". Fresh items show no bar. PASS.
   (Gotcha: the FIRST look showed no bar — the pane replays the scene
   payload cached in the doc, so a DB durability edit isn't visible
   until the next scene rebuild. Also required a Luna restart: the
   plugin's render.py is loaded at serve start.)
4. **Repair row + repair** — Forge offered "Repair Pigsticker —
   ◈ 35 + 12 XP" (= 20% × 250 × 0.7 missing). Clicking it: "+
   Pigsticker made whole on the anvil — every use back in it (− 12
   XP)", bar gone, gold and XP deducted. PASS.
5. **Off-class arrow burn + wear interact** — warrior bought an
   Ashwood Bow (off-class) + arrow pack, killed a Grey wolf in 3
   shots at range. DB after: arrows 10→7, bow 1300→1297 (one per
   shot), focus 1300→1298 (one per blow taken), shoes untouched.
   The swapped-out Pigsticker kept its (full) pool in
   `durability_pack`. PASS.
6. **Shoe wear on chase actions** — hunted again, clicked Run:
   shoes 1300→1299. Standing actions never touch the boots. PASS.

## Screenshots

- `.playwright-mcp/page-2026-07-27T23-23-49-778Z.png` — town scene.
- `.playwright-mcp/durbar-closeup.png` — pack strip with the 30% gold
  bar under the Pigsticker.
