# Scenario 03 — Levels gate gear and floors

## Setup
Two situations, engineered via QA doc edits if needed:
(a) a level-1 character whose `unlocked_floor` is ≥ 11 (tier-2 forge stock);
(b) a low-level character with a high floor open via the world lift.

## Steps
1. (a) Open the Forge showing tier-2 stock at level 1.
   - **Expect:** tier-2 rows visible with a `level 11` requirement in the
     hint/body; buying refuses with a shard note naming the required level.
     Gold NOT charged.
2. Level up past the requirement (QA: grant XP via fights) and buy.
   - **Expect:** purchase succeeds normally.
3. (b) At the tower gate, pick a floor F where `level < F − 10`.
   - **Expect:** refusal with a shard note ("your legs aren't ready" style,
     naming the required level). No floor entry, no energy spent.
4. Pick a floor within `level + 10`.
   - **Expect:** entry works as before.

## Pass
Gates hold with correct thresholds (tier T → level 10·(T−1)+1; floor F →
level F−10), refusals steer instead of dead-ending, and no charges happen
on refusal.
