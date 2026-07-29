# Execution summary — 022 phase 006: the war's face

Status: **DONE** (plugin + worldd + vendor sync; deploy/publish and the
two-account browser walkthrough deferred to the end of the 022 run per
the run agreement).

## What shipped

### The keep card (plugin, `engine/social.py`)
- HP bar (`_war_bar`: never full while wounded, never empty while
  alive), percent, and raw pool.
- The countdown: "the wound closes in 3h 12m — keep striking", read
  straight from worldd's `closes_in_s` — the card computes nothing, so
  countdown truth is the server's within the injection.
- The hour roll: "Kettle, Brakka +24 struck this hour" from striker
  `ts` stamps (top cutters first).
- Faction damage standings: striker `guild` stamps summed, top 3
  banners.
- The pity lines: a standing "it has healed N times — each closing
  left it weaker" plus the once-per-close "The wound has CLOSED…"
  watermarked on the doc (`p["war_seen"]` = floor + pity; a pity bump
  since the last look writes the line exactly once).

### The clock (worldd, `app/social.py::_warden_now`)
- `closes_in_s` added to the pure state read: min(silence deadline,
  full-regen time) — zero new state, the same `ts` the close law
  already reads. Injected through `_world_warden` along with `pity`.

### Sound the horn
- Keep option for banner hands while a wound is open. One tap emits a
  `horn` effect; worldd's `_fx_horn` letters every playing guildmate
  (minus the sounder) with the floor, the percent, and the countdown.
- Once per BANNER per wound: the `horns` slate rides the warden row and
  resets when the wound does; the write never touches `ts` (a horn must
  not feed the silence clock). The doc-side `horn_sent` mark
  (`floor:pity`) stops re-taps client-side; the server slate is the law.

### The Crier and the gate
- Wound thresholds 75/50/25%: `_fx_warden_strike` writes a tower-wide
  happenings line the first time each threshold is crossed per wound
  (the `called` slate rides the row; regen re-crossings can't refire).
- The gate itself says "the war is on floor N — the Warden stands at
  P%" whenever a wound is open; the Morning Crier's warden line now
  carries the countdown too.

### The Stone
- First blood: "Floor N — X drew first blood on Warden" written when
  the row materializes.
- The fall: finisher named FIRST in the cast-down line (the
  clearing-group fame line), preceded by "the deepest cut … was X's
  (N,NNN)".

## Test state

- 548 plugin tests green (+8 in `test_022_006_war_face.py`).
- 66 worldd tests green (+5 in `test_war_face.py`: thresholds once per
  wound, first blood on the Stone, striker ts/guild stamps, horn roster
  exactly-once + ts untouched, keep card countdown end-to-end).

## Decisions worth remembering

- Striker rows now carry `ts` (last strike) and `guild` — denormalized
  at strike time so injection needs no joins. The list stays capped at
  40; the hour roll and standings read only what survives the cap.
- The 002 learning held: not one line of the silence/pity/regen clock
  was re-implemented — `closes_in_s` is arithmetic inside the same
  `_warden_now` read, and the card renders what it is told.

## Forward corrections applied

- `007-the-era/plan.md`: the siege-at-100 announcements can reuse this
  phase's machinery (happenings kind `war`, horn letters,
  `_fmt_countdown` both sides) — noted in the plan.
