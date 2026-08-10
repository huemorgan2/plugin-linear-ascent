# 046 — issues for Roy

Open questions and flagged items from the rebalance + simulation runs.
Numbers from runs/046-*-s1.jsonl and the economy as committed.

## Decisions needed

1. **Death at depth (test xfailed, pending your call).**
   `DEATH_WEAPON_LOSS` = 20% chance the weapon is gone for good on an
   unprotected death. The weapon's price rides the pillar; income rides
   the income pillar — so the expected sting grows with the wedge:
   ~1 day at band 2, ~3.4 days at band 7, **weeks at band 10**.
   Options: (a) keep — deep deaths are meant to terrify, the
   reincarnation spell is the answer; (b) replace gone-for-good with a
   durability hit (repair is a running cost — sting stays ~1 day
   everywhere); (c) discount the roll chance by the wedge (same average,
   but rare-catastrophic variance — worst of both).
   Test `test_death_stings_one_to_two_days_where_it_first_bites` is
   xfailed until you decide.

2. **Floor-2 cliff.** ~~Optimal 4.2 days, casual 20 days on floor 2 vs a
   ~0.3-day design line. Cause: LEVELUP_BASE_GOLD floor of ◈200 ≈ one
   full day of floor-1 income per level, hit exactly when the player has
   nothing.~~ RESOLVED by 047 (0.61.0, Roy's call 2026-08-10): training
   fees ride a ×0.25→×1.0 tutorial ramp over levels 1–8 and the tier-1
   weapon sticker opens 20% cheaper, fading by rung 1.5. Floor 2: 4.2→3.1
   optimal, 20→6.5 casual. See conclusions/003.md.

3. **Striker count has no cap.** Your rule as stated: floor-100 warden
   needs 10% of weekly actives — 100 at 1,000 actives, 100,000 at 1M.
   Confirmed intended ("no cap"), noting it here once: a 2,000-cap (or
   any cap) is a one-line change if you ever want one.

## Flagged, not fixed (suspension-of-disbelief / cosmetic)

4. **JS safe-integer overflow.** Floor-100 warden pools reach 9.3e16
   (dark) to 9.3e19 (at 1M actives) — past JS's 2^53. Python side is now
   integer-exact; any worldd payload carrying a raw pool number will
   corrupt in the client. Ship pools as {fraction, formatted string}
   with a K/M/B/T formatter. (/mechanics is safe — its largest numbers
   are ~7e11.)
5. **XP line dips at depth.** Kill XP syncs level to floor
   (2.4·bar^1.5 ÷ wedge) and peaks near bar 38 — milestone-100 XP (927)
   < milestone-10 XP (999). Levels still sync (xp_need is what
   matters), but a reward number that goes DOWN reads wrong. Also XP
   briefly beats gold per kill on floors 4–9 (up to ~1.15×).
6. **Lodge price is linear** (LODGE_PRICE_PER_LEVEL) while everything
   else is exponential — at depth the inn is free in relative terms.
7. **Warden/monster HP ratio dips to 1.8 at floor 10** (elsewhere 4–35,
   growing with depth). Pre-existing shape, survived 046.
8. **Tutorial's worst fight softened.** The exponential is gentler than
   the old linear slope at the very bottom: floor 1's worst draw fell
   from ~25% to ~18% of the daily pool. Test threshold relaxed to 15%.

## Fixed along the way (for the record)

- Over-levelled gate raids: with pillar levels one blow could empty a
  gate — a charge's cut is now truncated at the pool unit, killing blow
  included (combat.py). "Over-levelling buys efficiency, never the
  gate" holds again.
- world_warden_hp lost low bits past 2^53 (float path) — integer-exact
  now.
- worldd census now counts only players active in the last 7 days
  (your "active = last week" rule).
- test_multiplayer's "a counter-blow landed" assertion rode the
  day-seeded roll stream — deterministic now.
