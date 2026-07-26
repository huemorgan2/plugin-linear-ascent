# 010 · Scenario 3 — attendance math and the weekly prize

Goal: the weekly resolution pays the right multiplier — driven through
the API/DB (a week can't pass in a browser session), then verified in
the pane.

## Steps (scripted against a local worldd)

1. Seed: faction of 2, HOARD goal 100; both members have kill ledger
   rows worth ≥ 100 gold inside last week's window; attendance rows:
   member A 4 days, member B 4 days (8/8 = ratio 1.0).
2. Trigger resolution (any faction act/status call in the new week).
   **Expect:** `ascent_faction_weeks` row: multiplier 1.0; prize =
   15% × 100 = 15 gold split by days; `faction_prize` ledger rows.
3. Re-trigger. **Expect:** NO double payment (unique week row).
4. Repeat with attendance 3/8 (< 50%). **Expect:** multiplier 0, no
   payout, note says the hall stood empty.
5. Repeat with 7 days both (14/8). **Expect:** multiplier capped 1.75.
6. Repeat with 5 members. **Expect:** base 20% applied.
7. CULL variant: **Expect:** members get `faction_buff` hp for next
   week; engine max_hp grows by the pct during that week only.
8. In the pane: COMMUNITY shows "last week: …" note matching step 2.

## Pass criteria

- Multiplier math: 0 below 50%, proportional to 175% cap.
- 15% under 4 members, 20% at 4+.
- Exactly-once payouts; blessings expire after their week.
