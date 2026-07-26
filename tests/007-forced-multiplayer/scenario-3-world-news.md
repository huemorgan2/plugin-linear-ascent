# Scenario 3 — World news: the Morning Crier, once per world day

## Setup
- Enrolled tenant with a playing character. At least a couple of other
  players in the world (any state). Test lever: set the player doc's
  `news_day` to `-1` (or a past day) in the DB to force delivery.

## Steps
1. `show my scene`. Expect the **Morning Crier** card BEFORE the
   regular scene:
   - climber census: total on the roll, how many at the frontier floor,
     how many at the bottom (floor 1 / Roothollow), how many on YOUR
     floor;
   - the shared Warden's condition (name + % HP + blades against it),
     unless the frontier is a milestone floor;
   - gossip lines from your floor (recent happenings there), or an
     honest "quiet" line when there are none — never invented players;
   - a shard-note with concrete advice: WHERE to hunt / strike for the
     fastest advancement given your level vs the frontier.
2. Take the option → the normal town scene follows.
3. `show my scene` again. Expect: NO second crier today (once per
   world day).
4. Verify the advice is truthful: if the character's level is below
   `floor_level_req(frontier)`, the advice must name a reachable floor,
   not the frontier.

## Pass criteria
- Delivered exactly once per world day, only to playing characters,
  only in world mode.
- All numbers come from the world (census, warden HP) — cross-check one
  against the DB.
- The agent treats it as awareness (may mention it naturally), and the
  card reads in-world (crier/notice-board voice, no UI jargon).
