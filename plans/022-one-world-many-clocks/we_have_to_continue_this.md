# We have to continue this

Everything the 022 run deliberately skipped or shipped as a stopgap.
Nothing here is optional — it's deferred. Add to this file every time a
phase cuts a corner; strike items through when they land.

## Tuning (the big one)

- **Deep tuning is floors 1–20 only.** Formulas exist for all 100
  floors, and cheap arithmetic smoke checks run at 31/50/100, but no
  play-tested validation past floor 20. Before real players reach the
  30s, the whole 21–100 band needs the full tuning pass (the last one
  took ~20 hours — budget for it).
- ~~**Floors 31–39 solo-grindable under the 001 stopgap.**~~ Closed by
  002's curve: N ≥ 2 from floor 31, regen breaks even at N/2, gated
  numerically in `test_022_002_retune` for every floor and population.
- ~~**Banked-bar burst.**~~ Closed structurally in 002: pools are
  N × 8 honest strike-fight units (≥ 16 fights) vs a ≤ ~11-fight bar;
  `test_banked_bar_burst_cannot_break_a_deep_warden` pins it.
- **Warden solo band tuned against the WARRIOR sim only.** The
  0.82 damage budget was measured with the warrior's trade-blows game;
  archers kite and sorcerers ignore flat DEF, so their at-level warden
  win rates are probably higher. Measure per-class and decide whether
  the spread is a feature (class identity) or needs a lever.
- **The era model is arithmetic, not telemetry.** 4–6 months is gated
  on documented assumptions (weekly rally appetite, 1.5 organize-days
  per floor, +20% window overhead). When a real era runs, calibrate the
  constants against the live pace — especially the rally appetite,
  which is pure guess.

## Deferred by agreement

- **Version bump + publish + worldd deploy:** once, at the end of the
  022 run, not per phase.
- **Browser walkthroughs per phase:** replaced by one
  agent-live-walkthrough pass at the end of the run.

## Watch list

- Echo rewards (0.5×) are a guess — nobody has measured whether echoes
  become the dominant XP farm at some level band.
- Local dev "world of one" keeps the personal unlock path alive in
  `combat._victory`. When multiplayer is the only mode that matters,
  delete it and give dev mode a fake world instead.
- The wilds-HP monotonicity law now tolerates ≤ ~2.2% dips on the two
  floors after each deep band start (reference re-hones from zero on
  fresh steel). If band boundaries or hone caps move, re-measure the
  worst dip — the tolerance is pinned at 0.977 in `test_008_pace`.
- Sim-vs-paper drift: 002 found the warden damage budget 70 points off
  its comment. Any future phase that touches combat math should re-run
  the measured win-rate gates, not trust derivations (the gates exist
  now; keep them in the loop).
- Presence (003) is single-process cached on both ends (worldd 30s,
  plugin peek 60s). If worldd ever runs more than one worker, the
  cache becomes per-worker — fine for counts, but revisit before
  building anything that needs cross-worker agreement.
- The torch status line reads the SAVED doc, so a climber who closed
  the app mid-fight shows "hunting" for up to 3 minutes. Harmless
  today; revisit if statuses ever gate mechanics (008 flares target
  hot players — the flare must tolerate a stale "hunting").
- **The board turns over if the frontier moves mid-day (004).** The
  cull's floor is a function of the LIVE frontier, so a Warden falling
  mid-day reshuffles the board and voids half-finished culls. Rare
  (deep frontiers move in days, not hours) and it reads as world flavor
  — but the honest fix is worldd pinning the day's generation frontier.
  Revisit when 006 puts the war on every surface.
- **"Gear-tier token" shipped as a repair token (004).** The plan's
  occasional contract bonus was a *gear-tier* token; no such item
  exists yet, so the board hands out the repair token instead. Design
  the real token (a rung discount? a free hone?) — 005's strongbox
  wants the same item for its reward slot.
- **Contract payouts are multiplier-priced, not play-measured (004).**
  Cull ≈ 0.8× the kills' raw gold, class jobs 0.5× off the tower's
  waist, warden 0.5× frontier warden pay, XP at half weight throughout.
  Same trap as the old warden budget: when telemetry exists, measure
  what fraction of daily income the board actually adds (target: a
  bonus, never a wage).
- **Dawn can heal mid-fight (004).** touch_daily runs on every act; if
  the world day ticks while a fight is open the player heals to full
  between rounds. Rare and reads as "dawn breaks" — but it's a free
  potion for whoever times the boundary. Watch for abuse at the tick.
- **Strongbox thresholds are summed points, my ruling (005).** "2/4/6
  open slots" was read as kills + keeps + floors, one point each — an
  active week opens all three slots trivially (6 kills is one session).
  The thresholds gate the CHOICE, not the size; if telemetry says that
  is too generous, weight the counters (floors > keeps > kills), don't
  move the thresholds.
- **Night work is offline gold with zero risk (005).** 20% of a
  hunting day, every night, for picking a menu option. It never beats
  playing (a hunting day is 5× that) and can't compound (carried gold
  is lootable, the cell cap holds) — but nobody has measured what 30
  worked nights do to the gear ladder at the 1–20 band. Measure when
  telemetry exists.
- **The "relic" strongbox slot pays a luck charm (005).** Placeholder
  kin of the gear-tier-token TODO — the real relic table (caster
  relics? armory pieces?) is undesigned.
- **The striker list caps at 40 (006).** The hour roll, the faction
  standings, and the fall's reward split all read only the last 40
  blades. A deep siege with more strikers silently sheds the oldest —
  wrong standings AND wrong pay at 100-strikers scale. 007 confirmed
  the grand siege itself is safe (Vharuk runs on the boss-commits
  table, unbounded — the warden pool ends at floor 99), but the deep
  warden floors (60–99) still hit the cap. Move strikers to their own
  table or raise the cap with a size check before the population gets
  there.
- **Horn letters snapshot the roster at tap time (006).** A guildmate
  who joins the banner after the horn gets no letter for that wound.
  Acceptable — the fire talks — but say it in the guildhall copy if it
  confuses anyone.
- **The two-account browser walkthrough for 006** (open a wound, watch
  the bar from both sides, let it close on silence) is folded into the
  end-of-run walkthrough. The silence-close beat needs a time lever to
  test live — plan for a QA world with shortened windows.
- **Era-close fan-out races concurrent acts (007).** `close_era`
  rewrites every playing doc in one transaction to deliver the
  ceremony; a climber mid-act at that moment can have their act's save
  overwrite the ceremony (or vice versa, last-writer-wins). At today's
  population it's a once-per-era, seconds-wide window and the loser
  only misses a scene — but before a real era ends with hundreds
  online, deliver the ceremony as a letter or a lazy per-doc flag
  instead of a bulk doc rewrite.
- **The frozen era keeps only the Stone's last 400 lines (007).** A
  long era's early first-clears fall off the frozen ledger. If the
  Stone matters as history, snapshot it in full (own table keyed by
  era) instead of a jsonb tail.
- **Reincarnation tiers are bragging rights only (007).** stood_100 /
  struck_vharuk / final_blow are frozen and surfaced nowhere except
  the ledger; points pay the perks, tiers pay nothing. Design what a
  tier is worth (a title by the name? a unique ceremony line? nothing,
  on purpose?) before era 1 actually closes.
- **The real era reset is an unrehearsed manual op (007).** The tool
  has a dry run, a permanent-table assertion, and a confirm gate — but
  the full sequence (announce → freeze → reset → players log into a
  fresh world) has never been walked end to end, even on scratch.
  Rehearse the whole ceremony on a QA world before era 1 ends.
- **The first blade of an assist gets no bonus (008).** Only the
  finisher is paid the assist bonus — the first kill was already
  banked and paying it retroactively means writing into a doc from
  outside (the race we just designed around). If telemetry shows
  players gaming the order (waiting to strike second), pay the first
  blade through a letter-with-gold instead.
- **Flare answerers race on stale injections (008).** The floor card's
  flare is read at act start; two answerers can both tap before either
  claim lands. Both fight a real fight, only the first is paid — fair,
  but the second player's card never says why they weren't. Add a
  "another blade got the plaque" line on the victory card when the
  claim was lost. Needs the fx to report back — a small piece of
  plumbing that doesn't exist yet.
- **The flare pays no attention to WHO answered (008).** Any hot
  climber including a level-1 on floor 1 can answer a floor-40 flare
  if they can walk there (the floor gate limits this in practice —
  unlocked_floor gates entry — so it's mostly theoretical; verify).
- **The long fire is world-global, not per-floor or per-lodge (008).**
  One `fire` row for the whole tower reads as one shared hearth in
  Roothollow — intended for now. If gate-town lodges ever exist, key
  the row by floor.
- **Flare/kill/fire rows accumulate in ascent_world (008).** Stale
  `flare:{N}` and `kills:{N}` rows are ignored by TTL but never
  deleted; a hundred floors of rows is nothing, but a cleanup sweep in
  the day tick would be tidy. They wipe with the era anyway.
