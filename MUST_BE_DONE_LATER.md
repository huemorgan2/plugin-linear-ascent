# MUST BE DONE LATER

Everything in this file is a tuning decision **proven on floors 1–10** that
floors 11–100 still need. Nothing here is a bug; it is deliberate scope.
The rule we agreed: get the first ten floors right, let Roy play them, and
only then carry the same treatment up the tower.

Owner: whoever runs the next rebalance pass. Source of truth for the
reasoning: `plans/025-the-real-climb/plan.md`.

---

## 1. Monster archetypes — floors 11–100

**Done for 1–10.** Every floor's four (or five) encounters carry stat
archetype traits from the `BODY_ROUNDS` / `BITE_COST` vocabulary, giving
each floor a prey / peer / brute / killer shape.

**Still to do.** Floors 11–100 (≈370 encounters) carry only defense traits
and therefore still share one stat line per floor. Each floor needs an
archetype spread assigned in its YAML.

Rules to carry up:
- Every floor gets at least one `frail`/`feeble` prey and at least one
  animal that can kill an at-level player of that floor.
- Steepness must be re-derived per band, not copied. `BITE_COST` is a
  share of the at-level HP pool a whole fight should cost (fierce 0.50,
  savage 1.00) and the ATK that produces it is inverted through the
  damage formula, so the chip floor (`raw − DEF/2` vs `ceil(raw/4)`) is
  already handled. What does NOT carry is the 0.50/1.00 itself: those
  numbers were measured against the 017 sim on floors 1–10, where fights
  open at range and a short fight lands one halved blow. Re-run the sweep
  per band until brutes sit near a 92% mean win and killers near 74%.
- Keep the defense axis on its `TRAIT_INTRO_FLOOR` staircase; the
  archetype axis is legal everywhere.
- Milestone floors (10, 20 … 100) are quorum bosses — archetypes apply to
  their wilds roster only.

## 2. Danger pays — reward multiplier per band

**Done for 1–10.** `kill_reward_mult(traits)` scales BOTH XP and gold with
the creature's threat, capped so one kill can't outpay a Warden.

**Still to do.**
- Verify the cap holds in bands 2–10, where `gold_per_kill` already
  carries `BAND_INCOME_JUMP ** (tier-1)`. A hulking savage on floor 90 may
  break the daily-income model the hone and tier prices are anchored to.
- Re-check `daily_income(F)` after archetypes land: the design's "≈30
  fights a day" now averages over a spread instead of one animal, so the
  real income per day drifts. Every price in the game hangs off this.
- Decide whether XP variance should compound with the faction XP buff and
  the elf bonus (today it does).

## 3. Wardens that never heal — where does mercy resume?

**Done for 1–10.** No regen, no silence close, no pity: a wound is
permanent until the floor falls (`warden_silence_hours` returns `None`
below `WARDEN_SIEGE_FLOOR`). In exchange the whole 1→30 effort ramp was
raised at its base — `WARDEN_POOL_FIGHTS_MIN` 2 → 3.2 — rather than
multiplying the first ten pools, so the curve stays one straight line
with no cliff at floor 11 (floor 1 is 3.2 fights, floor 30 is 8.0).

**Still to do.**
- Floors 11–30 currently have zero trickle (024) but a 30-hour silence
  window. Decide the boundary: does "never heals" extend to 30 (the solo
  band) or stop at 10?
- Floors 31+ keep the trickle and the 6→30h window — the coordination
  curve depends on it (022/002 gates). Do not touch without re-running
  the era-length model.
- 3.2 fights at floor 1 was chosen to keep "closable in a couple of
  sessions" true while making the gate real. If the base moves again,
  re-run `test_024_first_gate.py` in BOTH repos: worldd resizes live
  pools lazily off `WARDEN_POOL_TUNE`, which has to be bumped in the same
  commit or existing worlds keep the old wall.
- **026 bounded the exchange** (a charge buys `warden_exchange_rounds(F)`
  rounds *or* one `pool_unit(F)` of damage, whichever comes first), so
  "3.2 fights" is now enforced for every striker rather than assumed of an
  at-level one. Two consequences for later bands: the damage budget makes
  a gate cost ≥3 charges from ANY blade, so deep pools can no longer be
  short-circuited by an over-levelled climber; and the round budget is
  derived from the reference kit, so any change to `_at_level_loadout`
  silently changes how long a charge lasts. If a band's reference kit is
  re-anchored, re-read `warden_exchange_rounds` for that band and keep
  `>= 5` rounds — below that, 3 ⚡ is a swindle.
- 026 also fixed a live over-credit bug (`hp_max − hp` instead of
  `hp_join − hp`) that let any wounded gate fall in one or two charges to
  whoever turned up. If shared-body fights are ever added for anything
  other than Wardens, stamp `hp_join` on those encounters too.

## 4. The buy ladder — bands 2 through 10

**Done for band 1 (levels 1–10).** Ten gate moments instead of three.
Rungs 1.1 … 1.9 sit between the T1 and T2 rows, one per level: the gate
law generalised to "rung T.k opens k steps into its band", so T.5 still
lands at band_start+5 and nothing pre-025 moved. Bonuses interpolate
linearly and prices geometrically between the two whole tiers, which
reproduces the old mid EXACTLY at k=5 — that is why no existing piece
changed power or price. Each rung also ships keen (+15% bonus, ×0.65
durability, ×1.40 price) and warded (same bonus, ×1.75 durability, ×1.20
price), which are real FORGE items, so equip / hone / wear / pawn / pack
and the off-class twin logic all took them for free.

Two ripples worth remembering, both deliberate:
- **The reference player was re-anchored** (`reference_rung`). Before
  025 the tuning reference read the WHOLE tier (weapon +8) while a
  level-6 player could already own rung 1.5 (+23) — the tower spent
  floors 6–10 tuned against a climber who did not exist, which is a
  large part of why the band played flat. Warden ATK on floors 2–10 and
  wilds HP on floors 2–10 both rose as a result; the warden HP column
  did not move.
- **`reference_hone` is 0 through band 1.** The rung ladder is now the
  within-band growth we tune against; counting honing on top of it put
  the floor-10 reference ABOVE the floor-11 reference — a cliff in a
  tower that must be a straight line. Honing in band 1 is the diligent
  climber's edge over the reference, not the reference.

**Still to do.**
- Bands 2–10 still gate three times per ten levels (T, T.5, next T).
  Levels 12–15, 17–20, 22–25 … all sell nothing. The generator is
  general (`_step_bonus` / `_step_price` take any two tiers); the work is
  ~40 names per band and one decision per band about whether the
  reference should then read the sub-rung there too (it must, or the same
  understatement returns — and `reference_hone` must go to 0 in that band
  in the same pass, for the same cliff reason).
- Styles exist only below `STYLE_MAX_RUNG` (2.0). Decide whether
  keen/warded ride the whole ladder (probably yes — it is the cheapest
  content in the game) or give way to distinct named lines deeper up.
- A style is bonus + durability only. The "same icon in different
  colours" is real (`render._STYLE_TINT`), but no style yet changes
  BEHAVIOUR — no crit, no bleed, no elemental tip. That is the obvious
  next content axis and it needs combat support, not a table.
- The shoes ladder is still 5 items across 100 floors (levels 3, 11, 21,
  41, 61). Speed is the least-served axis in the game.
- Off-class weapons (×3 price, ×0.5 damage) were not touched.

## 5. Consumables and relics

**Done for 1–10.** The existing tactical shelf was pulled down so each
counter arrives one floor after the trait it answers: oil 2, curse
scroll 3, poison arrows and strip potion 4, slowing arrows and the net 5,
sky-hook 6, fire and piercing arrows 8. The flying+bite lint rule now
reads `RELICS["sky_hook"].floor` instead of hard-coding band 2, so moving
the hook moves the law with it.

**Still to do.**
- **No NEW consumables were authored.** The plan listed a throwing net,
  whetstone, smoke pot (guaranteed escape) and sling stones; all four
  need combat support, not a table row, so 025 re-gated what already
  works instead. The smoke pot in particular is the missing piece of the
  rubber band — right now "run" is a speed check, not something you can
  buy your way out of.
- The middle of the relic shelf (floors 11–30) is now thinner still:
  after the re-gate, floor 11 keeps only the reincarnation spell and
  nothing new arrives until 21.
- `veil_draught`, `golden_apple`, `stone_of_undying`, `polymorph_dust` all
  gate at floor 21 — one wall of expensive items instead of a ladder.
- No consumable in the game scales with the floor; a medgel heals 25 HP
  whether you are level 1 or level 30. Consider a tier ladder for heals.

## 6. The rubber band

**Done.** Lethal candidates keep 20% of their hunt weight, scored against
the player's real ATK/DEF/HP and the creature's real profile.

**Still to do.**
- The score is analytic (rounds-to-kill vs damage-taken); it ignores
  consumables, relics, the range phase's opening shot, and dodge. It will
  read a well-equipped archer as more fragile than they are.
- No memory: the band reacts to your sheet, not to your last five deaths.
  A player on a losing streak gets no extra help.
- Decide whether the band should also apply to the specimen roll (an
  alpha of a killer archetype is the deadliest thing in the tower and is
  rolled at a flat 5%).

## 7. Coins drawn as marks

**Done.** `Scene.tally` + coin/aether masks; marks up to 99, numerals at
100+.

**Still to do.**
- Only the victory card draws a tally. The vault, the strongbox, contract
  claims, the interest collect and the pawn sale all still say a number.
- 99 coin masks is a lot of DOM on a big kill; if it ever measures slow,
  group into stacks of 10 with a `×N` badge instead of raw repetition.

## 8. Tests and gates that will need revisiting

- `test_022_002_retune.py` pins at-level win rates 60–85% for floors 5–29
  and ≥88% for 1–4 **against the common specimen only**. Once archetypes
  land, "at-level win rate" needs a per-archetype breakdown or the gate
  measures an average that no longer exists.
- `content/schema.py::lint_floors` per-band spread rules were written for
  the defense axis. They need an archetype-spread rule per floor.
- `test_011_art.py` requires art per encounter id. Adding creatures (as
  opposed to re-statting existing ones) means new PNGs through the 1-bit
  pipeline — that is why 025 re-statted the existing 40 rather than
  authoring new ones.
