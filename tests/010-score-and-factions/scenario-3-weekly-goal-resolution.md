# 010 · Scenario 3 — dues, the world challenge, and the weekly turn

Goal: the week turn collects dues from every member (arrears for those
who can't pay), scores the challenge only for banners that ENTERED it,
and the prize math pays the right multiplier — driven through the API/DB
(a week can't pass in a browser session), then verified in the pane.

## Steps (scripted against a local worldd)

1. Seed: faction of 2 (dues ◈5), ENTERED week row for last week (HOARD
   100); both members have kill ledger rows worth ≥ 100 gold inside the
   window; attendance 4 + 4 days (8/8 = ratio 1.0).
2. Trigger resolution (any member scene/act or faction API read in the
   new week). **Expect:** dues ◈5 collected from each member (gold
   first, then bank) → store +10 with two `dues` ledger rows; week row
   resolved + won; prize = 15% × 100 = 15 gold split by days,
   `faction_prize` ledger rows — prize MINTED, never store gold.
3. Re-trigger. **Expect:** NO double dues, NO double payment.
4. Broke member variant (gold 0, bank 0): **Expect:** `arrears` flag
   set, member skipped from the split (their share stays in the pool),
   the Guildhall roster marks them ▲; solvent next week → flag clears.
5. Not-entered variant: attendance + earnings but no entry row.
   **Expect:** dues still collect; note "sat the week out — no entry,
   no prize"; no payout.
6. Attendance 3/8 (< 50%): multiplier 0, no payout. 7 days both
   (14/8): capped 1.75. 5 members: base 20%.
7. CULL variant: **Expect:** eligible members get `faction_buff` hp for
   next week; engine max_hp grows by the pct during that week only.
8. Challenge cadence: week k posts kind k % 3 (HOARD → CULL → CLIMB);
   the Crier announces the new week's challenge; `/v1/faction/enter`
   freezes kind + target at entry time.
9. In the pane: COMMUNITY (the news board) shows last week's winner
   with the prize note, the wins ranking (#1 called out), most
   climbers / richest store / highest blades panels, and the ticker.

## Pass criteria

- Dues: gold-first-then-bank, exactly once per week, always ledgered.
- Arrears members stay seated but never share a prize until solvent.
- Only ENTERED weeks pay; entry costs ◈5 × members from the store and
  is refused with the shortfall shown.
- Multiplier math: 0 below 50%, proportional to the 175% cap; 15%
  under 4 members, 20% at 4+.
- The news board renders sanely with zero factions.
