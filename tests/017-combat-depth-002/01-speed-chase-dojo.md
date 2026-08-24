# Dojo — 017 phase 002: speed & the chase

Browser scenarios for the two-state range model. Local Luna (8765) +
local worldd (8600), tenant qa007. Use the DB class-swap technique from
the 001 retro (swap `doc.clazz` + `gear.weapon`, top up `energy_val`
and `hp`, set `ascent_world.frontier` for high floors; restore after).

## A — fights open at range, warrior crosses

As a warrior, hunt floor 1. PASS when: the opener shows
"◇ at range — it hasn't reached you yet", option [1] is **Close in**
(not Attack), and clicking it prints "You cross the open ground" with a
half-power monster line; the next scene shows "◇ close quarters" and
Attack + Open distance.

## B — archer kites the slow bulwark

Swap to archer (basic_bow), floor 6, hunt for the Lane boar (bulwark,
slow). PASS when: at range the bow shoots at full power round after
round while the boar almost never closes (p_close 5%); if it does
close, Open distance succeeds most tries (80%); the fight is long
(bulwark) but the archer barely gets touched.

## C — run down by the fast

As archer on floor 5, hunt the Downs courser (fast). PASS when: the
courser closes by round ~2 ("reaches you — you are in its range now"),
Open distance mostly FAILS ("No gap opens", free half hit), and close
attacks read weaker (bow ×0.6). This fight should feel like the
archer's predator.

## D — flee the slow, fail against the fast

Fight a slow monster, choose Run — expect escape most tries (84%).
Fight the courser, choose Run — expect "It cuts off your line" often
(36% escape). The Run tooltip names speed as the decider.

## E — agent voice check

Ask the shard mid-kite something like "should I keep my distance from
this thing?" PASS when: it re-syncs, reads the range state and speed
tier from the scene, and gives one line of correct chase advice
(kite the slow / don't try to outrun the fast) in sidekick voice.
