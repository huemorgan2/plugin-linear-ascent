# 010 — Balance & release: execution summary

Shipped as v0.27.0. The closing phase: a full-tower margin scan and
retune, a stacked-drain economy gate that now includes the consumable
spend, a rehearsal of the v1→v4 migration against real production
docs, refreshed player-facing docs, and a three-class release playtest
in a real browser.

## What was built

1. **Margin scan** (`scan_margins.py`). The 009 lesson made policy:
   a threshold gate passing isn't enough — anything within ~0.1× of a
   bar (win 0.75 / drag 1.6×) counts as unshipped. The scan reports
   FAILING (safe AND quick for the countered class) and NEAR-MARGIN
   walls across floors 11–100 using the exact gate math from the test
   suite (day pinned to `_SIM_DAY = 137`).
2. **Six retraits** — 5 of the 6 near-margin walls were med tiers,
   confirming the med-tier rule at scale (med tiers barely register at
   reference gear; felt walls want high tiers): floor 20 honor_guard
   and 24 rig_wight and 59 road_thane → armor_high; floor 47
   scar_salamander and 63 nest_drake → resist_high; floor 26 peat_king
   gained resist_med. Each change is mirrored in its 008 band spec
   with a dated comment.
3. **Weights re-tuned, not floors hand-poked.** The peat_king retrait
   raised its bounty and broke the income-smoothness gate (warrior
   −18% at 26→27). Rerunning `008/.../tune_weights.py` rewrote five
   encounter weights (floors 26, 27, 47, 48) and restored smoothness —
   the weights are the smoothing knob, and they must be re-run after
   ANY trait retune.
4. **Stacked-drain gate extended** (`test_017_death_relics.py`). The
   old gate summed repairs + the rational death line; the new
   `test_the_drain_with_a_daily_wall_push_still_leaves_room` adds one
   class-appropriate wall-push per day (warrior: net÷3 or oil÷2;
   archer: 3 arrows; sorcerer: one vial) and holds the total ≤ 40% of
   daily income for every class at every tier.
5. **Consumable reprice** (`economy.py`, mirrored in plan.md §3.7
   with dated strikethrough notes): quivers 0.3→0.2 DI, piercing
   0.5→0.35, mage vials 0.3→0.1. The sorcerer was the forcing case —
   one vial is one FIGHT, so at 0.3 DI the mage's wall-push cost 3.6×
   the warrior's; at the new prices all three classes' per-push cost
   sits in the same 0.08–0.12 DI lane, and the gate passes without
   being weakened.
6. **Prod migration rehearsal** (009's `soak.py` vs the live Render
   DB): all 8 production docs migrate v1→v4 clean, 0 halflings,
   0 errors. `soak.py` gained an asyncpg fallback (the worldd venv has
   no psycopg); prod access needed `?sslmode=require` and a TEMPORARY
   ipAllowList PATCH on the Render Postgres (restored to empty after).
7. **Docs refresh** — `vision/economy.md` caught up with 017 (variable
   pawn rate, the 006 death economy, halfling retirement, a new §9 on
   combat depth and the counter economy incl. the reprice); README
   gained the combat-depth paragraph and the new layout rows.

## Verification

- 407 plugin tests green (margin gate, stacked-drain-with-push gate,
  smoothness across the retunes); 53 worldd tests green against the
  synced vendor.
- **Release playtest** (real browser, all screenshots read — evidence
  in `dojo/`, record in `tests/017-combat-depth-010/01-release-playtest.md`):
  - Warrior: creation (3-race slate, name through the CHAT), floor-1
    fight card with every modifier named, [i] dossier, typed kill
    (`wolf_kill_melee` in the doc), spell purchase at 0.5 DI, then the
    full death ladder — shard save first ("Once a day, I have you"),
    spell burn second (inventory `{}`, nothing else lost), unprotected
    third (exact 40% roll shown, weapon survived its 20% roll, bank
    untouched).
  - Archer: retuned forge prices live (570 / 1,000), boots + slowing
    arrows bought with exact gold math, quiver consuming one arrow PER
    SHOT and un-nocking when empty.
  - Sorcerer: vials live at 360 = 0.1 DI, the matchup moment firing
    exactly once on first resist_high contact, `use_strip` stripping
    spellguard, the retraited rod-wisp killed.
  - Moments budget held: 3 deaths + 1 matchup, one line each, no
    chatter anywhere else.

## Learnings (propagated to skills — the final retro)

- **Margins are the gate.** Scanning for near-margin walls (not just
  failures) found six retunes the passing suite was hiding. Any
  project with threshold gates should ship a margin report next to
  the pass/fail run.
- **Reprice before you weaken a gate.** The sorcerer's 0.44–0.54
  drain was a pricing bug (per-fight consumable priced like a
  per-push one), not an over-tight ceiling.
- **Pane free text is read-only** — `POST /act` from the iframe cookie
  session returns 403; names and any free text go through the real
  chat (which also exercises the agent's pass-through).
- **IO-thrash symptoms**: at host load ~90 (Google Drive sync storm)
  worldd scene calls spike to 30–77 s and Luna shows the in-fiction
  "lift is down" retry scene. Use change-detection before re-clicking
  (duplicate clicks queue server-side) and verify uncertain states via
  the psql doc stage; the retry option always resyncs.
- **Screenshot paths**: `browser_take_screenshot` with a relative
  filename lands in the HOME directory, not the workspace — pass
  absolute paths or collect from `~` after.
- **Death order**: shard save fires BEFORE the spell — the first death
  of a day never burns a spell. Tests and playtests must expect it.
