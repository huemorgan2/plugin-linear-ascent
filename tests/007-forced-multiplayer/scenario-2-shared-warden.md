# Scenario 2 — One shared Warden per floor: strikes, kill opens for all

## Setup
- Two enrolled tenants (two Luna installs, or one browser + one scripted
  HMAC client) with playing characters. World frontier at a
  non-milestone floor N.

## Steps
1. Player A: tower gate → floor N → "The Warden's keep". Expect the
   SHARED warden scene — one HP pool shown as `HP x/x_max`, a
   "Strike" option costing 3 ⚡, and copy that says the Warden is one
   monster for the whole world.
2. Player A strikes twice. Expect: each strike shows the damage landed
   and a counter-hit; the shown HP drops; ⚡ drops 3 per strike.
3. Player B visits the same keep. Expect: B sees the SAME reduced HP
   and A's name listed among the blades against it.
4. Set the Warden's HP low (test lever: `UPDATE ascent_world` on the
   `warden:N` key), then Player B lands the final strike. Expect on B's
   next scene: a "Warden has fallen" report with B's and A's shares.
5. Player A (without doing anything warden-related): next scene shows
   the fall report too; the tower gate now lists floor N+1 for BOTH
   players; the Stone of the Climb names both strikers; town happenings
   carry the kill.
6. Floor N-1 keep (below frontier): expect the old per-player echo
   fight (solo combat, XP only, no frontier effect).

## Pass criteria
- HP pool is one world value: both tenants see and affect the same number.
- The kill opens the floor for every player, not just the killer.
- Rewards are split by damage dealt; the finisher gets the rare-loot roll.
- Milestone floors (10, 20, …) still run the quorum pledge flow.
