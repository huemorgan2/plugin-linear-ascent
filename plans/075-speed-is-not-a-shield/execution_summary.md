# 075 — Execution summary

Executed 2026-08-24 (roy). Shipped as **0.100.0** on `main`.
All three phases landed in one pass (curve + wiring + copy are one
mechanism); tuning was done by simulation as planned.

## What shipped

### The mechanism (economy.py, engine/combat.py)
- `economy.p_pursue(pspd, mspd)` — one curve for all monster catch-up:
  `0.90` when the monster is as fast as you or faster; otherwise
  `FLOOR + (BASE − FLOOR) · DECAY^lead`, which decays with your speed
  lead but never reaches zero.
- `economy.PURSUIT_EXTRA` — extra chase turns per player weapon:
  bow 90% for a 2nd turn then 10% for a 3rd; magic 50% for a 2nd;
  melee none (melee rounds keep the classic single close-attempt).
- `combat._pursuit_phase()` — after every ranged/magic action the
  monster runs its pursuit: each turn crosses one pace of ground, and a
  turn with no ground left is a strike (halved; 2nd+ strikes in one
  round quartered so a triple pursuit cannot chain-kill). Wired into:
  the at-range shot, the at-range miss, `open_distance` success, and
  `create_distance` (which no longer has its own parting-blow roll —
  `p_gap_hit` is retired).
- **Flyers:** no extra pursuit turns; `open_distance`/`create_distance`
  hidden from the menu and refused in plain words ("It is in the air —
  there is no way to put ground between you."); the bow keeps full
  power vs a flyer at any distance (the ×0.5 cramped-close penalty is
  waived for airborne targets only, preserving bow 1.0 / magic 0.6 /
  sword 0 — the triangle's flyer answer).
- Every flying monster is speed 7 (`TYPE_SPEED`), which is
  `SPEED_FAST`; no content overrides exist (audited: zero `speed:` keys
  in floors content). The content audit passed with no edits.

### Copy (plain English — tips.py, render.py, combat.py)
All the strings from the plan's copy audit are wired verbatim (or with
the factual tail kept where the plan's line dropped real information,
e.g. Run keeps the no-gold/no-XP and Warden 3-in-4 facts). The jargon
gate is a unit test: *bowwork, give ground, gap is armor, parting blow,
speed tells, kite, lengths, toll, rake* no longer appear in any string
this feature touches (`test_075_pursuit.py::test_no_jargon_in_the_touched_copy`).

## Tuning (thousands of simulated fights, real engine)

`sim075.py` drives `engine/combat.py` directly — kitted at-level
players (sim039's loadout law), ~10,000 fights per full run across
speed leads +2…+10, three classes, floors 2/6/10, ground tanks and
flyers.

Starting constants (`FLOOR=0.05, DECAY=0.60`) were too soft: a +5 lead
archer lost only ~12 HP over a 4000-HP grind and the +10 never-zero
check landed at 28%. **Final: `FLOOR=0.10, DECAY=0.70`** (CAP 0.90 and
BASE 0.55 unchanged, extra-turn odds unchanged).

Final full-run numbers (400 fights/cell):

| lead | archer HP lost/4000-HP kill | sorcerer HP lost | gate |
|---|---|---|---|
| +2 | 253.7 | 349.8 | at-level vs a slow tank is bloody |
| +3 | 155.8 | 123.9 | |
| +5 | **56.6** | **58.6** | target band 25–60 ✓ |
| +7 | 33.2 | 41.6 | monotonic ✓ |

(Pre-fix the same measure was **7.7** HP for the archer at +5 and
~10–30 HP for the sorcerer at every lead — that was the hack.)

- **Never zero:** at a +10 lead the monster still lands ≥1 hit in
  **80%** of 4000-HP grinds. The floor is structural (`PURSUE_FLOOR >
  0`), so the chance is never 0 by construction.
- **Survival, at-level, no healing, no fleeing:** archer/sorcerer
  deaths 0% on floors 2–6, 7.0%/6.3% on floor 10; warrior rows
  (19.7%/58.7% on 6/10) are the untouched melee baseline under the same
  fight-to-the-death policy — melee code paths are unchanged.
- **Flyer (grave_moth, floor 6):** archer and sorcerer both 100% win,
  0 deaths; the moth denies the kite (≈50% of rounds are already close)
  and never lands more than its one action per round.

### 039 regression (sim039 --accept)
sim039 was **broken on main** (two stale references from economy
renames: `typed_damage` → `typed_damage_048`, `reward_mult_cap`
retired) — fixed as part of this work. A/B with pursuit neutralized
shows the pre-075 baseline **already fails 6 of the 039 acceptance
checks** (economy drift since 039 — EV curves and deep bands, e.g.
deep death 0% on floors 4–5 in both runs). 075's isolated effect:
- **Normal-hunt death bands: unchanged and passing** (<2% floors 1–3,
  ≤8% everywhere — the "correct play stays survivable" gate).
- Deep hunts floors 9–10: +6 points (16.2→22.0, 23.6→29.3) under
  sim039's no-escape attack-only policy, which overstates real play
  (a real archer steps back when caught). Floor 10 deep is 3.3 points
  over the old 26% cap → **carried into 077's lethality tuning**, which
  re-tunes fight cost anyway.

## Tests
- New: `tests/test_075_pursuit.py` — 12 tests: curve bounds/decay/floor,
  extra-turn tables, melee delegation, pursuit crossing+striking,
  quartered 2nd strike, no pursuit once in reach, fatal pursuit runs
  the death path, flyer single-turn, flyer row hiding+refusal, bow full
  power vs flyer up close, jargon gate.
- Updated to the new model/copy: `test_036_gap_and_grants.py` (p_gap_hit
  → p_pursue, step-back prose), `test_017_info_card.py` (chase lines),
  `test_040_qol.py` (ladder tip), 017 dojo scenario text.
- Full suite: **1356 passed, 4 failed — none from 075**: the 3
  `test_kill3d` failures are pre-existing on committed main (verified
  by stashing all local work and re-running), and the `test_048`
  clazz-gate failure points at `scene.py`/`render.py` lines from the
  concurrent kill3d/avatar work, not lines this plan touched.

## Learnings carried into 077
1. **The step-back treadmill is dead.** Under pursuit, the pre-075
   optimal archer loop (re-extend to gap 3 every round, shoot ×1.5)
   never finishes a fight — the monster re-closes most rounds. The
   sensible play is now "shoot from where you stand, step out only when
   caught". Step-backs became a tool, not a stance. 077's sims must use
   that policy.
2. **Kiting a slow tank is no longer free even at +2** (253 HP per
   4000-HP grind), which means 077's "wrong weapon vs slow tank" case
   is *already damaging* — 077's Lever A (glance can't grind) makes it
   *unwinnable* as well; Lever B needs less crank than feared.
3. **Both glance cells sit on slow (speed 3) tanks** — bow vs armoured
   and magic vs magic_resist — so each class's kite test needs the tank
   its weapon can kill (bow×0.5 vs magic_resist husk; magic×1.0 vs
   armoured weaver). Wrong pairing = 0 kills in 250 rounds, which is
   077's stall behavior showing up before 077 exists.
4. **Deep hunts on floors 9–10 are now slightly over the old death cap**
   (29.3% vs 26%) — retune alongside 077's monster-ATK work.
5. The treeline ambush shot keeps the old single close-attempt (fiction:
   the monster hasn't found you yet; once per fight, no loop possible).

## Not done / follow-ups
- **Dojo browser walkthrough** — runs after 077 lands (one combined
  walkthrough covers pursuit, flyers, and the triangle teeth together).
- No deploy to Render (per plan: not unless roy says so).
- Vendor sync into `worldd/vendor` — done with the commit below.
