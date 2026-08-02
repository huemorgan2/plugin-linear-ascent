# 033 — when a Warden falls

Three complaints from play, one thread: the Warden fight leaks value on
the way in (the treeline loop) and pays nothing on the way out (no loot
in the card, no spectacle). This plan closes the exploit and makes the
fall the biggest moment the game has: the kill pays in the card, the
Warden dies on screen, and the next floor introduces itself before you
have even caught your breath.

## The items

### 1. The Warden remembers you (treeline shot, once per Warden)

**The exploit.** Treeline shot is a 2× opener, once per fight
(`shot_used`, set on the encounter at `engine/combat.py:177`). Against a
Warden, damage persists when you flee (`_report_shared_strike`,
`engine/combat.py:1597`) — but a fresh encounter re-arms the opener. So
an archer runs, returns, and fires the 2× again, forever. And because
damage is `raw − DEF/2` (`economy.py:454`), the 2× pre-mitigation
becomes 4–10× post-mitigation against a high-DEF Warden: ~50–60 a shot
where a regular blow lands 5–15, at the same ⚡ per swing. Hit-and-run
becomes the archer's optimal play — the loop's only fuel is the free
re-arm.

**The rule (agreed with the user: the 2× stays).** The first arrow from
cover works on a Warden that has not found you. Once you have fled it,
it watches the treeline. *The treeline shot works once per Warden, not
once per fight* — exactly where the wounds persist, the memory persists.

**Scope.** Shared/pool Wardens only (`e["shared"]`). Solo-world Wardens
and echoes reset to full HP on a fresh encounter, so there is nothing to
farm — they keep once-per-fight. One principle: the opener re-arms only
when the fight itself resets.

**Touches.**
- `engine/combat.py:1697` — when the shot fires at a shared Warden,
  record the floor in `p["treeline_wardens"]` (list of ints on the doc)
  alongside `e["shot_used"] = True`.
- `engine/combat.py:177` — when spawning a shared Warden encounter,
  initialise `shot_used` to `floor in p.get("treeline_wardens", [])`.
  The option row at `combat.py:460` already checks `shot_used`, so the
  button disappears with no further work.
- 027 law (say it in the card): on re-engage with the shot spent, one
  line in the keep opener — "It watches the treeline now — that shot is
  spent." No silently missing buttons.
- Cleanup: when a Warden falls (frontier passes the floor), drop the
  floor from `treeline_wardens` — a respawned/next-era Warden is a new
  beast and the flag must not leak across eras.

**Why nothing else needs touching.** Once the opener stops re-arming,
run-and-return is strictly worse than standing: flight is capped at
`WARDEN_FLEE_MAX`, a failed run eats a Warden grab
(`combat.py:1592-1616`), and re-entry re-spends the gate. The loop's
economics collapse on their own — damage numbers, energy costs and the
regular blow stay exactly as tuned.

### 2. The kill pays in the card (loot at the fall, not in the mail)

**The problem.** The shared-Warden victory card
(`_shared_warden_victory`, `engine/combat.py:849`) promises "your share
arrives with the word of it" and shows zero numbers. The real payout is
computed server-side in `worldd/app/social.py` `_warden_fall`: shares
split by damage, finisher's rare-loot roll, then a `pending_events`
card pushed into each striker's doc — which the finisher only sees on
their NEXT click. The player who landed the killing blow stares at a
card with no loot on it. Solo kills already do this right
(`_victory` shows `+XP / +◈ / rare loot` with the 025 §6 tally art);
the shared kill — the bigger moment — shows less.

**The fix.** The settlement already happens in the same request: the
engine resolves the click, emits the `warden_strike` effect, and
`_fx_warden_strike` → `_warden_fall` runs before the response returns —
for the finisher, `_warden_fall` mutates the live doc (`d = doc`)
in-transaction. The numbers exist while the card is being sent; they are
just not in it. So:

- `_warden_fall` writes the finisher's settled receipt onto the doc
  (e.g. `doc["_kill_receipt"] = {xp, gold, loot, names}`) instead of
  (or in addition to) queueing the finisher's pending event.
- The response path patches the outgoing victory card from the receipt:
  the same lines the letter carries (`+ X XP — your share of the kill`,
  `+ ◈ Y from the Warden's hoard`, `▪ the killing blow was yours — rare
  loot: …`, `Struck down by <names>.`) plus the 025 §6 `tally` art —
  one coin per gold, one shard per XP, so a Warden kill *looks* like a
  Warden kill.
- The finisher's `pending_events` letter is dropped (they saw it live);
  other strikers keep theirs unchanged — their share genuinely does
  arrive with the word of it, because they weren't in the room.
- The ledger row stays the single source of record; the card is a view.

One law to keep: the card must never *invent* numbers. It shows the
receipt the server settled, or (if the effect was refunded because the
world moved on) it shows nothing and the existing refund path speaks.

### 3. The fall reel (a Warden dies on screen, all three blades in frame)

**The problem.** A Warden dies with the same treatment as a boar — one
kill GIF picked by the finisher's damage type (`_kill_fx`). The biggest
beat in the game is an anticlimax, and the user has asked repeatedly for
intro-movie-style reels at the big moments.

**The reel.** On a Warden kill, before returning to the floor, a short
movie in the 016 style (1-bit GIF + text + `Next ▸`):

- **Beat 1 — the fall.** A new Veo shot in the house style
  (`tools/generate_event_gifs.py`, same STYLE block): the Warden's
  silhouette going down under *all three climber classes together* —
  a blade in close, an archer's line from the treeline, a sorcerer's
  light behind — because that is the game's own law (a great Warden
  falls to a war party, not one blade; the 016 muster scene set this
  image up). Split art: `warden_slain_intro` (the fall plays once) +
  `warden_slain_loop` (the frame ticking as it cools). Text: the kill
  receipt from item 2 — the reel and the loot are ONE moment, not two
  cards.
- **Beats 2–3 — the next floor introduces itself.** Flow straight into
  the existing 030 floor movie for floor n+1 (`_floor_movie_scene`,
  `engine/core.py:2159`): the world beat (`floor{n+1}_world`) and the
  keep beat (`floor{n+1}_warden` — the next Warden, still standing:
  the cliffhanger is free, the art already exists).

**Wiring.**
- After `_shared_warden_victory` / the solo first-clear path in
  `_victory` (`combat.py:895`), route into the movie machinery: set
  `movie_floor = n + 1` with a new entry beat for the slain reel (a
  `movie_slain` flag or beat −1 — smallest diff wins), then the
  existing beats take over. `Skip` works on every beat, as 030 demands.
- Watching it from the kill sets `floor_seen_{n+1}`, so first entry at
  the gate (`_gate_pick`, `core.py:2246`) won't replay it — once per
  floor total, whichever door you reach it through. Strikers who
  weren't the finisher, and players who never fought, still get it on
  first entry exactly as today.
- The level-gate nuance: the killer may not yet meet floor n+1's entry
  level (`floor_entry_player_level`). The reel still plays — it is the
  reward for the kill, and a teaser is a reason to level. Entry rules
  are untouched.
- Echoes do NOT get the reel (half pay, no world effect, no spectacle —
  028: nothing twice).

**Art production.** One generic slain reel first — the three-classes
composition is the point and it reads at silhouette scale; per-floor
slain variants (each floor's Warden design going down) are a stretch
goal behind the same slug scheme (`floor{n}_slain` overriding
`warden_slain` when present). Pipeline as in 016: Veo → 20:7 crop →
320×200 → shared-level Bayer dither → white-ink GIF, split intro+loop
with shared dither levels so the seam is invisible.

### 4. Floor movies to floor 10 — status: they exist; finish the hookup

Investigated (the user asked to check first): **030 Phase 8 already
built this.** Per-floor two-beat movies (world + keep), once per
character, skippable, hooked at first entry (`_gate_pick`,
`core.py:2246`), with art shipped for floors 1–10
(`floor1_world…floor10_world`, `floor1_warden…floor10_warden`, plus
`warden_fall` for a keep already broken — that beat even names the
slayers from the `fallen:{floor}` roll). So item "make them until level
10" is **done**; what 033 adds is:

- the Warden-death hook from item 3 (today the movie only plays at the
  gate);
- a verification pass floor by floor, 1–10, in the dojo: first entry
  plays both beats, skip works, `floor_seen` sticks, fallen floors show
  the broken-keep beat with the slayers named;
- floors 11+ have no art yet — confirm the movie degrades gracefully
  there (text beats without fx) and leave art for a future art plan, as
  agreed (until 10 for now).

## Acceptance

1. Archer vs shared Warden: fire treeline shot, flee, re-engage — no
   treeline option, and the keep opener says why. Kill the Warden (or
   let the era turn), meet the next one — the option is back.
2. Damage-per-⚡ for the run-and-return loop is now ≤ standing and
   swinging (verify against the 017 fight sim; the 2× on a first
   engagement is unchanged, including the med+ plate cancellation).
3. Finisher's kill card shows XP share, gold share, rare loot and the
   slayer roll, with tally art — zero clicks after the kill. No
   duplicate letter for the finisher; other strikers' letters unchanged;
   ledger totals identical to before (view changed, money didn't).
4. Warden kill → slain reel (three classes in frame) → floor n+1 world
   beat → floor n+1 keep beat → back to the floor. Skip works on every
   beat. First entry to n+1 later does not replay; a striker who wasn't
   the finisher still gets the floor movie at first entry.
5. Dojo pass over floors 1–10 for the existing movies (beats, skip,
   once-per-floor, fallen-keep variant).
6. Vendor into `worldd/vendor/` per house release flow; version bump.

## Open questions

1. **Warden respawn semantics** — when a pool re-materialises (new era /
   frontier reset), is the Warden "new" (fresh ambush allowed — current
   plan: yes, flag cleared at the fall) or the same beast forever?
2. **Per-floor slain reels** — worth 10 Veo shots now, or ship generic
   and revisit when floors 11+ get their art?
3. **Non-finisher strikers** — should their letter ALSO carry the slain
   reel on next login (they earned the kill too), or is the floor-entry
   movie their moment? Current plan: letter unchanged, movie at entry.
