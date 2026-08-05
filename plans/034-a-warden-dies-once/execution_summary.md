# 034 — execution summary

Three corrections, one spirit: the game charges what it says it charges.
Shipped in `0.46.0`, straight to `main` in both repos (no branches, per
`.cursor/rules/no-branches.mdc`).

---

## §1 The shield spends itself on what it stops

**Before.** Every landed blow wore the shield exactly one use, whether it
blunted 1 damage or 90 — while the card narrated the real number
("your Scrapwood Buckler blunted 9 of it"). A tier-1 buckler survived
~1300 blows, about 216 fights, a week of heavy play. Shield Wall, the one
move that is *entirely* the shield, cost the shield nothing at all.

**Now.** `economy.shield_wear(blocked, shield_bonus, total_def)` prices
the shield's share of the block against the shield's own rating:

```
blocked_by_shield = blocked × shield_bonus / DEF
even_blow         = shield_bonus / 2
wear              = max(1, round(RATE × blocked_by_shield / even_blow))
```

The `shield_bonus` terms cancel, and that is the design, not an accident:
`blocked` grows with DEF, so naive proportional wear would bill a tier-10
shield ~20 uses a blow against a tier-1 shield's ~2 and burn deep gear
four times faster in relative terms. Flattening it leaves 017's pool
curve free to do its job — a measured even blow costs exactly `RATE` at
every tier from 1 to 10, and better shields last longer purely because
their pools are bigger.

**`SHIELD_WEAR_RATE = 3`, not 4.** 4 was the first pick and it broke the
existing repair-tax gate: repairs must stay ≤20% of a day's income at
every band *and* must not step-function between bands, and at rate 4 the
band 1→2 step went to 0.104 against a 0.10 tolerance. At 3 the worst step
is 0.090 and the worst band is 16% of income. A tier-1 buckler now lasts
~72 fights instead of ~216 — three times faster, which is the complaint
answered, without rewriting the repair economy underneath it.

**Shield Wall pays now.** It rolls the blow it turned (without applying it
to HP) and wears the shield on the whole thing — the most expensive round
in the game for the piece doing the work. A monster still crossing open
ground lands nothing to stop, so no wear there.

**Armor was left alone** at one use per blow. The user asked about
shields, and the asymmetry is honest: armor is what you wear, a shield is
what you put in the way. Changing both would have multiplied the whole
repair economy at once.

## §2 The bar is the bar

Two holes, both closed:

1. **`guild_train` subtracted instead of resetting.** Its own docstring
   said "the bar is hard (no overflow to carry)" and then carried it.
   Now `p["xp"] = 0`.
2. **worldd wrote XP raw at four sites**, bypassing `gain_xp` entirely:
   the Warden-fall share, the milestone boss payout, the PvP bounty and
   the flare answer. The milestone was the visible one — floor 10 pays
   1,500 XP into a bar that holds 758, the overflow landed, and the next
   training carried 742 free XP into level 11.

All four now route through `pstate.gain_xp`, which returns what landed —
so **the ledger records the landed number, never the offered one.** A
receipt claiming 1,500 into a 758 bar is a lie the append-only ledger
would keep forever.

And the clip is *said*, per 027: the kill card carries
`▪ 742 XP ran off a full bar — train at the Guildhall before the next
one`, the striker letters carry `(your bar took all it holds)`, and the
milestone letter says to train before the next one. A silent clip reads
as theft.

**`LEVEL_CAP` (30) keeps its exception.** There is no bar at the cap —
training is refused and XP is the currency the bench and the spells
spend. Capping there would strand a capped climber from the sinks XP
exists for, and "you cannot hold more than your bar" is meaningless
without a bar. This is deliberate and pinned by a test.

## §3 A Warden dies once

The frontier Warden was always one shared monster with one world-wide
death. What was not: below the frontier the keep re-armed as an **echo
bout** — a full Warden fight at half pay, repeatable forever, on a card
that said in as many words *"the real one died long ago"* and then paid
out for killing it again. It was the best farm in the game on any cleared
floor and it made the world's biggest event meaningless an hour later.

**Now the keep is a memorial.** New `memorial` location, reached by the
same `keep` option whenever the frontier (or, in local dev play, the
personal unlock) has passed the floor. Free to enter, no ⚡ in the row
before the click, no encounter behind it. It names the Warden, the
slayers, the day and the deepest cut.

**The frontier check runs before the milestone branch** — otherwise a
cleared floor 10 goes on recruiting a war party for a boss that died
weeks ago.

**`fallen:{floor}` grew a date.** It stored the slayer roll as a bare JSON
string with no time at all; it is now
`{names, day, ts, warden, top, top_dmg}`. `social.fallen_record()` reads
**both shapes forever**, so a legacy row keeps its names and the memorial
says "in the early days of the climb" rather than inventing a date. The
map now rides at the top of the world payload as `w["fallen"]` because
`w["warden"]` is `None` at a milestone frontier — 030's names-only
`fallen_by` stays exactly where it was so old clients read it unchanged.

**Migration `014_fallen_dates.sql` is additive only.** Names are copied
verbatim into the new object, the date is recovered from the boss
happening that floor wrote at the fall, and floors whose happening has
scrolled away keep their names with no date. No `DROP`, no `DELETE`, no
row left holding less than it held. Production is at frontier 5 with
floors 1–4 already fallen (MASTER-CHIEF on 2–4, bob on 4).

**Balance fallout, handled.** The one place echo removal could silently
break a daily loop was the contract board: "Answer a keep's horn" counted
echo fights, and with one living Warden left in the tower a climber who
cannot enter the frontier floor cannot answer it. `board_for` now drops
that job for hands that cannot reach the front, rather than posting work
they cannot do; the title names the floor. The other losses (echo XP/gold,
the 12% charm roll, the strongbox `wardens` counter) are the intended
cost — that counter was counting ghosts.

`WARDEN_ECHO_MULT` and the `echo` encounter flag are deleted.

---

## Tests

| Suite | Result |
|---|---|
| plugin `pytest tests` | 861 passed, 1 skipped, **1 pre-existing failure** |
| worldd `pytest` | 119 passed (112 baseline + 7 new) |

New: `tests/test_034_shield_wear.py` (13),
`tests/test_034_the_bar_is_the_bar.py` (8),
`tests/test_034_a_warden_dies_once.py` (13),
`worldd/tests/test_034_the_bar_and_the_fallen.py` (7).

Updated for the new law, not weakened:
`test_017_durability.py` (the repair-tax gate now models the shield's
real rate; the shield/armor "same events" assertion became "different
units"), `test_022_001_one_list_of_bosses.py`,
`test_022_004_contracts.py` (reach-capped pricing now exercised off the
pure board, since `board_for` no longer posts that job to that hand),
`test_033_when_a_warden_falls.py`, `test_multiplayer.py`.

**Pre-existing failure, untouched:**
`test_026_the_gate_bites_back.py::test_a_caught_getaway_costs_real_blood_not_a_chip`
fails identically on the commit before this plan. The test `break`s out
of its 40-attempt loop the moment the first escape succeeds, so it gets
exactly one attempt and scores zero when that one gets away. It is a flee
-tuning/test-structure issue in 026's territory, not 034's, and fixing it
means touching combat tuning — left for its own change.

## Not done

The devprocess mandates a live browser playthrough before calling a plan
complete. That has **not** been run for 034 — the changes are covered by
coded tests only. The memorial card, the clipped-XP wording on a real
kill, and the shield-wear pace in felt play all want a dojo pass.
