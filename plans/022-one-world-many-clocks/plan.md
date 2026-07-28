# Plan 022 — One world, many clocks

Roy's ruling, 28 Jul: **this game is multiplayer, only.** One universe, one
tower, one list of bosses. On top of that premise, the curated feature set
from the progression research — five things to do on five different clocks,
introduced one at a time so nobody drowns in the first hour.

Sources: `research/one-tower-for-everyone.md` (the MMO model and its math),
`research/plan-suggest-ideas.md` (the top list and what was deliberately
deferred), `research/hunting-together-ui-sketch.md` (presence and the
hunting-grounds feel), `research/progression-more-ways-to-earn.md` (the
economy evidence under all of it).

## 1. The two facts this plan exists to fix

**The game runs two warden systems that do not connect.** Every player
privately re-fights all 100 wardens (`combat.py:720-724` — the only place any
floor is unlocked for anyone), while worldd runs a shared warden whose death
bumps a world counter, announces "floor N+1 is open for everyone"
(`worldd/app/social.py:700`), and opens nothing. Three places in the game
describe the shared model as real; none of it is wired.

**Nothing about the shared warden scales.** HP mult (4×), regen (8%/hr) and
the strike formula are flat, so the coordination requirement is ~7 players
with full energy bars **at every floor from 1 to 100**. The finale is exactly
as hard as floor 10. (Derivation: `one-tower-for-everyone.md` §2.)

And one player-experience fact from the research: the whole game runs on a
single clock — energy, 1 per 45 min — so every activity competes with every
other and the only decision is spend-or-save. WoW's endgame lesson (§12 of
the progression research): pacing comes from **many independent clocks**.

## 2. The target, in one table

| Clock | System | Player's sentence |
|---|---|---|
| energy (exists) | hunting | "one more fight" |
| **dawn** | nightly rejuvenation | "I'm healed — a new day" |
| **daily** | contract board | "what are today's three jobs?" |
| **nightly** | night slot: rest *or* work | "what do I do with tonight?" |
| **weekly** | strongbox at the Vault | "which reward do I take?" |
| **the era** | the war — one list of bosses, ending at 100 | "how goes the war upstairs?" |

Plus presence — the floor you hunt shows who is hunting it **with you, right
now** — because none of the above feels multiplayer if the grounds feel empty.

## 3. Phase 0 — prerequisite (already planned)

**Plan 021** (floor/level disambiguation) lands first, unchanged. Without it
the retune below silently mis-tunes every warden above the level cap
(`player_max_hp(floor)` at `economy.py:386`) and locks gear tiers 4–10 behind
levels that can no longer exist (`gear_level_req`). Zero behaviour change,
golden-value tested.

## 4. Phase 1 — One Tower: one list of bosses

### 4.1 Structure — Roy's ruling: ALL 100 wardens are shared. Only 100 exist.

There is **one list of bosses for the whole world, ever**. No personal
wardens at any floor. The personal-unlock system (`combat.py:720-724`) is
**deleted**, not demoted: `unlocked_floor` rides the world frontier for every
floor from 1, and the first climber to fell warden 1 clears the path for
everyone, exactly like the first to fell warden 71. The guardrail against
skipping ahead stays personal: `floor_level_req = max(1, floor − 10)`.

The 1–30 / 31+ boundary is **tuning, not structure**:

- **Floors 1–30:** the shared warden is sized so a single amazing player
  *can* fell it alone — hard, not easy. Mechanically: the warden's regen is
  set **below** one player's maximum sustained output, and its pool is worth
  roughly one to two full energy bars of damage. Solo is achievable by
  arithmetic.
- **Floor 31 up:** regen is set **above** any single player's maximum
  possible output. Solo becomes impossible by arithmetic, not by rule — no
  message says "you can't"; the wound simply closes faster than one blade
  can cut.

**Fighting the warden is a real fight, not a single swing.** The current
shared-warden strike (one swing per 3⚡) merges with the full 12-round warden
fight: you enter the keep, fight the warden properly — rounds, tactics,
range, consumables — and **the damage you dealt persists to the shared pool**
when you die, flee, or run out. If your fight takes the pool to zero, the
warden falls, for everyone, and your name leads the Stone line. At low floors
the pool is about one great fight's damage, so a phenomenal solo kill in a
single session is possible; at high floors your best fight is a cut in a
siege. One combat system, one warden list.

- **Echo fights (optional, cheap):** a fallen warden can be re-fought at the
  keep as an echo — personal reward at a fraction, no world effect — so late
  joiners in a racing era still get boss content.
- **Milestone bosses (40, 50 … 90)** keep their pledge-quorum mechanic; the
  quorum numbers join the same N(F) curve. Floor 100 is the era finale (§7).
- The three lying strings (Stone, worldd announcement, `floor_level_req`
  docstring) become true instead of being rewritten.

### 4.2 The coordination curve

Let `A` = active players (hot definition, §5). Required strikers:

    R100 = max(min(50, 0.5 × A), 0.10 × A)      # scaled-minimum small-world rule
    N(F) = 1                     for F ≤ 30      # soloable — hard, achievable
    N(F) = ceil(R100 ^ ((F − 30) / 70))  after   # grows to R100 at floor 100

Enforced with the two knobs that already exist plus one new:

- **HP sets the rally size:** `HP(F) ≈ N(F) × 8` strike-damages (a full
  energy bar is ~8 strikes).
- **Regen sets the minimum head count:** tune `regen(F)` so fewer than
  `N(F)/2` sustained strikers visibly lose ground.
- **The silence window forces the rally:** wounds persist only while strikes
  keep landing; silence for `W(F)` hours closes them fully. `W` scales ~6h at
  floor 31 to 24h+ at floor 90+, so "coordinated" means *same day*, never
  *same minute* — this is an async game in mixed time zones.
- **Pity ramp:** each fully-closed wound on the same warden permanently
  shaves ~3% off its max HP. A world can always eventually win; a siege can
  still fail.

### 4.3 The Grand Retune (one tuning pass, once)

Per Roy: if we tune the system, tune it once for all. The same spreadsheet
pass covers:

- **`LEVEL_CAP = 30`** (none exists today). XP curve compressed so the cap
  arrives in the first weeks. At cap, XP becomes pure currency (spells,
  scans, honing — all existing sinks).
- **Gear carries the growth from 31 up:** weapon bonus rescaled from `8 × T`
  toward ~`30 × T`; **armor gains an HP contribution** (today max HP is 100%
  level and would flatline at 400); energy cap re-keyed off gear band or
  floor instead of `level // 10`.
- **Warden/monster re-derivation falls out for free** — they are derived from
  the reference player (`_at_level_loadout`), so retuning the reference
  propagates. 021's `reference_level()` is the switch point.
- **N(F), HP(F), regen(F), W(F)** from §4.2, targeted at a 4–6 month era.

Acceptance for the pass: a simulation script (like plan 004's difficulty
review) walking the reference player floor 1–100 and a reference *world* of
200 / 1,000 / 10,000 actives through the siege curve, asserting era length
lands in the target band.

## 5. Phase 2 — Presence: the grounds feel inhabited

The cheapest phase and the one that makes everything else feel multiplayer.

- **Hot / camped, Roy's rule:** *hot* = acted on this floor within **3
  minutes** — the only tier that counts as "with you"; *camped* = within the
  hour — texture, letters, never company. A stale count is worse than a
  small one; the counter's product is trust.
- Derived, never subscribed: `floor + last_seen` heartbeat off the action
  sync that already happens; indexed count per floor; cache TTL ~30s (must be
  shorter than the window or the number lies).
- **Where it shows:** the gate list ("Floor 12 — 3 hot · 2 camps"), the floor
  header, every fight round. Grade-2 liveness: one integer added to
  `/pane/peek` (`routes.py:265`), lazily refreshed, so the number breathes
  while the pane idles.
- **Torches block** on the floor card: named hot players with one-word
  status ("hunting the north scarp", "at the keep, hurt").
- **Deltas are story, not UI:** changes fold into the next card as lines —
  "two more torches on the ridge since you last looked", "Kettle's torch
  gutters… and flares again."

## 6. Phase 3 — The clocks

Each item is deliberately shallow; the variety is the feature, not the depth.

- **Nightly rejuvenation** — HP restores at the night boundary ("dawn — your
  wounds have closed"). No daytime trickle at all, so the potion sink
  survives intact: during a session healing still costs gold and still buys
  time. Generalises the Lodge's +20-at-dawn into the law of the world.
- **Contract board** — three daily contracts, seeded per world day (same
  pattern as the pawn rate: identical board for everyone, discussable).
  Counters checked against the combat ledger; payouts in gold + XP + the
  occasional gear-tier token; expire at the world-day tick. `BOARD_PRICE`
  finally gets a job.
- **Night slot at the Lodge** — one action per night: **rest** (bank a
  capped rested-aether pool, spent as bonus XP on kills only) or **work**
  (gold at dawn, flavoured by the building: forge shift, bar shift).
  Professions with ranks stay deferred; the slot is the socket they later
  plug into.
- **Weekly strongbox at the Vault** — three counters the game already tracks
  (kills, floors, warden strikes) at 2/4/6 thresholds; player picks **one**
  reward at the weekly tick. Distinct from the faction weekly (collective);
  this one is personal.

Economy law for all of the above, written into `vision/economy.md` as part of
this plan: **gold buys time, never power** (and its era corollary: prestige
buys time, never power).

## 7. Phase 4 — The war's face, the ending, reincarnation

- **Siege UX:** the warden card carries the bar, the countdown ("the wound
  closes in 3h 12m"), the hot-striker roll ("Kettle, Brakka +24 struck this
  hour"), faction damage standings, and `Sound the horn` (letter every
  guildmate). Legible at a glance is what turns "please coordinate" into
  "get in here."
- **The grand siege at 100:** declared in advance (Crier, Stone, letters),
  requires `R100` strikers inside the window.
- **Era end:** the fall announced everywhere; the era ledger (first clears,
  top strikers, faction standings) frozen onto a permanent **Stone of Eras**;
  a closing ceremony scene; then the world resets — floors, gold, gear,
  levels, factions, bank. The reset is also the economy's drain: nothing
  compounds across eras.
- **Reincarnation:** one point to every player of the completed era who
  crossed a participation line (default: reached level 5). Earned tiers on
  top: personally stood on floor 100 · struck Vharuk in the final siege ·
  the final blow (one player per era, ever). Points and titles live in a
  permanent worldd ledger outside the reset scope, shown as glyphs by the
  name (✦, ✦✦ …). **Perks buy time, never power:** early Relay/Arcanum
  access, a pre-filled rested pool, echoes from day 1 — no stats, no gear,
  nothing that compounds.
- v1 rulings (Roy can veto): eras cannot end in defeat; PvP history wipes
  with the era; the leading faction of the final siege gets a named line on
  the Stone of Eras.

## 8. Phase 5 — Fighting together, the humble version

Full shared-round party combat (the sketch's guard/flank/mark verbs) is the
best thing on the whole list and the hardest; it stays its own future plan.
This plan ships the two pieces that deliver 80% of the feeling:

- **The shard flare:** at low HP, burn aether — every *hot* climber on the
  floor sees "a red flare — a climber is dying there · Answer the flare".
  Answering pays gold + a permanent Stone line; the death timer stretches
  while help is en route. Rescue possible, never guaranteed.
- **Assist strikes:** acting on the same monster/warden within minutes of a
  floor-mate links the logs ("Brakka's axe bit first — your blade finishes
  it"), pays a small bonus over two solo kills, and grants both full
  contract credit. No kill-stealing exists anywhere, by construction.

## 9. The onboarding ladder

Nothing new before level 4; one reveal per band, each announced through plan
020's "what opens next" registry:

| When | What appears |
|---|---|
| level 1–3 | nothing — hunt, gear; the keep, if the frontier is near |
| day 2 | nightly rejuvenation (noticed, not taught) |
| level ~4 | the contract board |
| level ~6 | the night slot |
| level ~10 | the strongbox |
| frontier 31+ | the wound out-heals one blade — solo hero era ends, the rally era begins |
| era end | reincarnation |

Presence (torches, counters) ships un-gated — it teaches nothing and warms
everything.

## 10. Explicitly deferred

Professions ranks (7), salvage (3), per-fight quality bonuses (4), hirelings
(9), the in-combat regen stat (17), the escalating energy cell (19),
player-built structures (24), full party combat (27's synchronous form).
Each waits for players to say "I've seen it all."

## 11. Order of work and verification

Execution is broken into numbered phase folders (017's pattern), each with
its own plan, tests, and release gate — each releasable on its own:

1. **Plan 021** first (its own plan folder) → golden-value tests green,
   vendor to worldd. **Plan 020** (gate registry) lands before 004.
2. **`001-one-list-of-bosses/`** — all 100 wardens shared, personal unlock
   deleted, keep-fight damage persists to the pool, echoes; stopgap tuning
   keeps floors 1–30 soloable; the three lying strings now true.
3. **`002-the-grand-retune/`** — LEVEL_CAP 30, gear carries power, the
   N(F)/regen/window curves; simulation gate proves the era-length band at
   200/1k/10k actives.
4. **`003-presence/`** — hot/camped tiers (3-minute rule), torches, deltas,
   pane-peek integer; cache-TTL test (a hot count can never outlive its
   window). Independent — may ship any time.
5. **`004-dawn-and-contracts/`** — nightly rejuvenation + the contract
   board; dawn heal preserves the potion sink; contract seed determinism.
6. **`005-nights-and-weeks/`** — night slot (rest/work) + weekly strongbox;
   rested cap, strongbox pick-one.
7. **`006-the-wars-face/`** — siege card, silence countdown, the horn,
   Crier thresholds.
8. **`007-the-era/`** — grand siege, era end, Stone of Eras, reincarnation
   ledger + perks; era-reset dry run against a scratch DB — the permanent
   tables survive the wipe.
9. **`008-together/`** — shard flare + assist strikes + the long fire.
10. After every phase: re-vendor (`worldd/tools/vendor_game.sh`), worldd
   suite, and a browser walkthrough per
   `.cursor/skills/agent-live-walkthrough` — play it like a player before
   calling it done.

Commit to `main` in both repos as work lands (`.cursor/rules/no-branches.mdc`
— no branches, ever). Each phase is releasable on its own; the order is
chosen so the game is never worse mid-way: 021 changes nothing, One Tower
makes the war real, presence warms it, the clocks fill the days, the era
gives it an end.
