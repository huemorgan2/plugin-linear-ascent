# Execution summary — Phase 008: together (the flare, assists, the fire)

Status: DONE (tests green; version bump + publish + deploy happen once
at the end of the 022 run, next).

## What was built

All shared state rides `ascent_world` side rows — never a write into
another player's doc. That was 007's forward correction and it shaped
everything here: the flared player is by definition mid-fight, so both
sides read a `flare:{floor}` row instead of anyone reaching into a doc.

**The flare, dying side** (plugin `combat.py`): below a quarter of the
bar, in world mode, once per fight — "Send up a flare" burns
`FLARE_AETHER` (10 XP) and does not spend the round; instead the burst
startles the monster (`flare_guard`: its next landed swing is halved —
that is the plan's "death timer stretch" translated into an engine
with no timer). The fx writes the floor's flare row. When a later
round's injection shows `answered_by`, the fight card folds it in as
story and arms one guaranteed disengage: the next "Run" simply
succeeds — the monster has a new front. Rescue possible (you must
live until someone answers), never guaranteed.

**The answer, rescuer side** (plugin `core.py` + worldd): a live flare
(fresh, someone else's, unanswered) puts a RED FLARE line and an
"Answer the flare" option on the floor card. Answering costs the
normal 1 ⚡ and starts a REAL fight against the same prey ("the
rescuer's round — the {monster} turns from {name} to you"). The claim
races server-side: `_fx_flare_answer` is first-tap-wins — pay
(`flare_answer_gold(floor)` = 0.5× a kill's gold, plus 10 XP), a
ledger row, and the permanent-for-this-era Stone line ("Brakka
answered a flare on floor 7 — Moss lives to tell it"), exactly once.
Late answerers still fought a real fight; they just miss the plaque.

**Assist strikes** (plugin `_victory` + worldd `kills:{floor}` ring):
every wilds kill in world mode drops a `kill_note` fx into the floor's
rolling ring (12 entries, pruned past `ASSIST_WINDOW_MIN` = 15 min).
At victory, `_assist_partner` scans the injected ring: same prey,
another blade, inside the window → "+ ◈ N assist" at
`ASSIST_BONUS_PCT` (25%) of the kill's gold, its own `assist` ledger
row. Gold ONLY — the assist carries zero XP, so the rested pool
(which pays exclusively on kill XP inside `_victory`) structurally
cannot double-dip; a test pins the row's `xp == 0`. Contract credit
stays exactly one `note_kill` per participant because each blade
scored their own kill — no kill-stealing exists, by construction.

**The long fire** (lodge): the lodge card shows the five-seat fire
(`fire` world row, one seat per name, latest first). "Sit the fire,
say a word" speaks one of five canned `FIRE_WORDS` (deterministic
pick, no free text, nothing to moderate). "Stand a stranger a stew"
(◈ 5) sends a canned letter to a named fire-sitter through the
existing letters table. Alone at the fire, the stew option hides.

## Rulings made while executing

- "The dying player's death timer stretches" → one halved monster
  swing at flare time + one guaranteed disengage once answered. The
  engine has no death timer; these are the same promise in its terms.
- The rescuer "lands in the fight" → a fresh fight against the same
  encounter id, full pay. Synchronous shared rounds stay a future plan
  (as the plan itself says).
- Assist bonus goes to the FINISHER (the second blade) only — the
  first blade already banked a full solo kill and cannot be paid
  retroactively without writing into their doc. Combined payout still
  clears two solo kills, which is the plan's requirement.
- Wardens are excluded from assist strikes: the shared warden pool
  already splits rewards by damage — it IS the assist mechanic there.
- The flare works in warden fights too (any fight, any kind) — a
  dying blade at the keep can call the floor like anyone else.

## Tests

- `plugin tests/test_022_008_together.py` (15): flare gating (quarter
  bar, world mode, once per fight, aether refusal), the startle
  round's exact halving arithmetic, the answered-flare free disengage,
  the floor card's flare surface and its hiding rules, the rescuer
  round on the same prey, assist bonus math + `xp == 0` + no assist
  from own/stale/other-prey entries, rested no-double-dip, the long
  fire card, the stew's cost/refusal, no stew alone.
- `worldd tests/test_together.py` (6): one live flare per floor (fresh
  cry holds, guttered cry yields), first-answer-wins exactly once
  (pay + Stone + ledger, own-cry refused, second tap unpaid), kill
  ring cap + prune on both write and read, injection shapes
  (own/other/absent), five fire seats one per name, stew letter +
  unknown-name no-op.
- Full suites: 571 plugin + 76 worldd, all green.
