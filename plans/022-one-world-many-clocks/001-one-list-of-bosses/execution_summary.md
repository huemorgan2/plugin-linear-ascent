# Phase 001 — One list of bosses · execution summary

Status: **done** (plugin + worldd, tests green). Deploy/version bump
deferred to the end of the 022 run, as agreed.

## What shipped

1. **The single-swing strike is dead.** "Join the fight" at the frontier
   keep costs 3 ⚡ and opens a full encounter against the world's HP pool
   (`engine/social.py::warden_action` → `combat.start_encounter` with
   `e["shared"] = True`, `e["hp"]/hp_max` seeded from the world warden).
   Every true exit — shared victory, real death, daily-save death,
   successful flee — emits exactly ONE `warden_strike` effect carrying
   the fight's total (`combat._report_shared_strike`, guarded by
   `e["strike_sent"]`; never fired on a Stone-revive continuation).
   The pool the next card renders is updated optimistically client-side;
   the server remains the arbiter (`_fx_warden_strike` clamps, records
   strikers, refunds if the floor already fell, resolves `_warden_fall`).
2. **The personal unlock is deleted in the shared world.** `_victory`
   raises `unlocked_floor` only when `p.get("_world") is None` — local
   dev play is a **world of one**. In the shared world the only door
   opener is the frontier itself (worldd already lifts every doc via
   `_sync_frontier_into_doc`, `max(unlocked_floor, frontier)`).
3. **Echo fights.** A keep below the frontier is an echo of a fallen
   Warden: full fight, rewards × `WARDEN_ECHO_MULT` (0.5) after fade,
   **no** `warden_strike`, **no** unlock, `e["echo"] = True`, honest
   support line on the card.
4. **Solo-band stopgap tuning** (`economy.py` §5b):
   `world_warden_hp_mult(F)` = 1.5 for F ≤ 30 else 4;
   `world_warden_regen_hourly(F)` = 3 %/h for F ≤ 30 else 8 %/h;
   `world_warden_reward_mult(F)` mirrors the pool mult. worldd
   `_warden_regen`/`_warden_fall` now take the floor and call these.
5. **Shared fights refuse the cheese:** `sleep_spell` does not work on
   the world's body; the flee card says the wounds "stay cut".
6. **Truth pass (task 8):** all three flagged strings are now literally
   true — the Stone line ("the lift opens for everyone when a Warden
   falls"), the worldd fall announcement, and the
   `floor_entry_player_level` docstring (fixed in 021).

## Corrections to the plan's premises

- **Task 3 was already built.** worldd's `_sync_frontier_into_doc` and
  `_raise_frontier` predate this phase; nothing new was needed there.
- **Task 4 needed no code.** Wardens already materialise lazily as
  `warden:{floor}` rows when their floor becomes the frontier; "all 100
  are shared" falls out of deleting the personal unlock, not out of
  pre-creating 100 rows.

## Tests

- `tests/test_022_001_one_list_of_bosses.py` (11): two players' wounds
  stack on one body; death persists the wounds; finishing the pool pays
  nothing locally (the server splits it); shared warden can't be slept;
  echo pays half / emits nothing / never moves the frontier; local dev
  still climbs; solo-band constants; **solo-gate sims** — warden 12
  falls inside 2 bars (actual: ~0.25), warden 45 out-heals a lone
  grinder (473 regen/h vs 356 dealt/h sustained).
- `tests/test_multiplayer.py` rewritten to the fight contract (strike
  opens a fight; ONE effect with the fight's total on exit; optimistic
  pool drop).
- worldd `tests/test_multiplayer.py` end-to-end rewritten: A fights and
  flees (wounds persist under A's name), B joins the same wounded body
  and lands the killing blow inside a fight; frontier rises; both names
  on the Stone.
- Full suites: **plugin 487 passed**, **worldd 55 passed** (after
  vendor sync).

## Findings forwarded

- **The banked-bar burst** (written into 002's plan, task 4): one fight
  lasts until flee/death, so an at-level fight deals ~1.6–1.9× the solo
  warden's HP. A full bar ≈ 9 fights out-damages the 4× pool at any
  floor — the regen gate stops grinders, not bursts. 002's `HP(F)`
  derivation must size pools against banked-bar bursts per required
  striker.
- Floors 31–39 are marginally net-positive for a sustained solo grinder
  under the stopgap (the gate flips at ~F40). Acceptable until 002;
  logged in `we_have_to_continue_this.md`.
- The plan's "browser walkthrough" acceptance is deferred to the single
  agent-live-walkthrough pass at the end of the 022 run.
