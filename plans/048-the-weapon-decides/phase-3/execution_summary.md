# Phase 3 — execution summary

**Status: complete.** Suite: 1014 passed, 1 known baseline-red
(test_034 shield wall, pre-048, phase-8 item), 2 skipped, 1 xfailed.
Commit: `048 phase 3: the School — train, mastery, carry, holding`.

## What landed

- **The School** — a room in every gate town (`school` option, tip
  registered). Scene shows three path bars (▰/▱, rank, exact
  next-cost with CURRENT frontier gold) + the "what improves"
  sentence (miss X%→Y%, worst swing A%→B%) per row. Location
  `"school"`, `back` → gate town.
- **Train flow** — `train_<path>` deducts XP (from the level bar)
  + gold, bumps rank; refusals name both numbers; rank-10 guard
  answers "nothing left to teach" (row also leaves the menu).
- **Mastery** — rank 10 turns the bar gold, MASTERY row offers the
  948-XP study (`MASTERY_XP = round(train_xp(10)*1.5)`); buying
  records `p["mastery"][path]` (EFFECTS deferred to phase 5, skip
  marker in tests); hitting rank 10 fires the invitation card once
  (`flags.invited_<path>`); any mastery discounts the OTHER paths'
  ranks 1–5 to 80% XP (`train_xp_cost`, blade-1 for 16 XP).
- **Carry** — `p["slots"]` (default 1), 2nd slot 60 XP + ◈ 30 at
  any level, 3rd slot 900 XP + `round(200·pillar(front))` ◈ gated
  `needs level 8 — you: N` (exact sentence, locked row + refusal).
- **Holding** — `p["held"]` (held[0] IS the equipped weapon),
  self-healing sync in `ensure_current`; promote-from-pack keeps
  the old weapon in a free slot ("stays in your other hand") or
  bumps it to the pack; refused mid-fight WITH a reason.
- **Sheet** — `trained` (3 path ranks), `slots`, `holding` (names).
- **Tooltip** — a bagged weapon of an untrained path warns on the
  promote row: "untrained bow — miss 25%, weak swings".

## Findings

1. **The XP bar is the real gate on School goods.** Training spends
   `p["xp"]`, which is hard-capped at `xp_need(level)`. So rank 10
   (632 XP) needs a level-10 bar (759), MASTERY (948) needs level
   12 (998), and the 3rd carry slot (900 XP) is unpayable at its
   own level-8 gate (bar 543) — first affordable ≈ level 12.
   Elegant for ranks (rank-10 ≈ level 10 falls out for free),
   **misleading for carry3** — the gate says 8, the wallet says 12.
   → open question for roy; phase-6 bake should either lower
   CARRY3_XP ≤ 543 or raise CARRY3_LEVEL to 12.
2. **Unreachable menu rows can't be exercised through
   `apply_choice`** — option validation answers first. Guards
   behind removed rows are tested via the action handler directly
   (`core._school_action`).
3. **Every writer of `gear["weapon"]` must maintain `held`.** The
   ensure_current sync alone double-banked a Forge swap (old piece
   sent to pack by `_gear_purchase` AND banked by the truncation).
   Writers now: `_gear_purchase`, `_wear_from_pack`, + the sync.
4. Repo guards that catch new content: `test_020` (register
   *_LEVEL constants in unlocks.py + guard set), `test_014` (every
   option id needs a tips.py entry).
5. `test_045::test_no_promotion_mid_fight` contract updated: the
   mid-fight promote refusal now returns a scene with a reason
   instead of silent None (nothing on the body moves either way).

## Learnings applied forward

- Phase 4 (classes die): route ALL weapon equips through one held
  helper; off-class blocks in `_gear_purchase`/`pack_actions` die;
  School discount check stays path-based (already classless).
- Phase 5: mastery effects hook exists (`p["mastery"]`); held list
  is the scaffolding for the fight-time weapon choice.
- Phase 6: carry3 XP-vs-bar collision (finding 1) goes into the
  bake; re-anchor keeps School costs payable on schedule.
