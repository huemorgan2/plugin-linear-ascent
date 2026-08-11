# Phase 8 — execution summary

Status: DONE. Full suite 1061 passed, 1 skipped, 1 xfailed.
Commit: `048 phase 8: the words teach — polish + playtest log`.

## 1. Teaching texts (the words teach)

- `tips.py` — five tips rewritten to the weapon voice: `begin` (the
  gate's Rusted Sword + two ranks of bladework, School sells the
  rest), `shield_wall` (blade rank 4), `sleep_spell` (staff rank 6),
  `treeline_shot` (bow rank 4), `create_distance` (gap pays only
  from rank 8 — ×1.25/×1.5, below it plain ×1.0; test_040's "1.5"
  assertion kept).
- `core.py` — the rank-10 invitation card gained the banner-hall
  line: "a tenth rank is toasted in every banner hall — the tower
  knows its masters by name". School door/scene text audited —
  already 048-native, no edits.
- `profile.py` — the dead `clazz` display replaced by the public
  hands line: `hands: ⚔ 4 · ➶ 1 · ✦ 2`, rank 10 reads GOLD,
  studied mastery reads MASTER. Old worldd payloads without a
  training key simply don't render the line.
- `worldd/app/social.py` — profile payload now carries `training`
  and `mastery` (parent-repo commit rides with the submodule
  pointer).
- Combat polish found by the playtest driver: **article doubling** —
  17 monsters are named with their own article ("The lamp-eater",
  "The Seep", "The last pack") and 29 combat.py template sites
  printed "the The lamp-eater". New `combat._the(name, cap)` helper;
  all 29 sites swept (21 capitalised, 8 lower). Suite re-run green.

## 2. Three-question audit (fun law)

One monster per sign, floor 4, N=200 per cell, fair vs countered
path at ranks 0/5/10 (probe: `audit_048.py`).

| monster (sign) | path | rank 0 | rank 5 | rank 10 |
|---|---|---|---|---|
| glare_moth ⚡ (fly) | FAIR bow | 1.00 | 1.00 | 1.00 |
| | WRONG blade | 0.00 | 0.00 | 0.00 |
| lamptree_wight ⛨ (armoured) | FAIR staff | 0.62 | 0.74 | 0.86 |
| | WRONG bow | 0.12 | 0.23 | 0.54 |
| lamp_eater ✧ (magic_resist) | FAIR blade | 0.17 | 0.23 | 0.55 |
| | WRONG staff | 0.15 | 0.22 | 0.38 |

- **Can I lose?** Yes — every cell below 1.00 loses for real; the
  moth is the hard teacher (blade literally cannot reach it).
- **Can I tell why?** The verdict block names each held weapon's
  answer + rank before the fight; the defeat card names the cause:
  blade-vs-moth → "It flew; your blade never reached it once. A bow
  answers in full — the armory sells one." staff-vs-lamp_eater →
  "Its spellguard ate your casts down to a glance. Steel bites
  full; arrows take half." Rank-0 defeats blame the hands and point
  at the School; high-rank defeats on plain walls say "Better gear,
  or run".
- **Can I change it?** Every card names the lever: the weapon that
  bites full (and where it's sold), or the rank that steadies the
  swing. Rank visibly buys consistency (0.62→0.86 fair,
  0.12→0.54 wrong).

lamp_eater fair-blade 0.17 at rank 0 reads harsh but is the
at-bar danger fight doing its job — the sign rides at/above-bar
placements by design (037 law, reconfirmed).

## 3. Hand playtest floors 1–12 (driver: `playtest_048.py`)

Ten beats, engine-driven like the dojo: classless open → town-door
sweep → floor-1 hunts → first bow at the Forge → School (bow,
2nd slot) → the three signs fair-handed → deliberate blade-vs-moth
death → staff + ranks → floors 5–12 one fight each → legacy-doc
migration letter. Final log: **zero genuine confusions**.

What the run showed, in play order:

- **Classless open** — race → name only, no class question; kit is
  Rusted Sword + blade 2 + ◈ 50; shard tip immediately points at
  floor-1 hunting and the Forge price ladder.
- **Town doors** — all nine unlocked doors open and their exits
  return to the square. Arcanum is 🔒 level 3, board 🔒 level 2 —
  both announced on the Stone's THE CLIMB AHEAD ladder, so the
  locks read as promises, not walls.
- **Kill cards** — `+ ◈ 18 gold (young-tower bounty)` prints on
  every floor ≤10 kill; beside it the un-inflated prices (levelup
  ◈ 60, rank fees ◈ 18–53 at floor 3) — the doubled paycheck
  contrast lands.
- **Fumble/shallow lines teach the lever every time**: "Rank-2
  hands — your Rusted Sword swings wide. The School trains this
  away." / "Your rank-2 swing lands shallow — 2. A rank-4 hand cuts
  nearer 5." — the exact next rank, in the fight, at the moment of
  the miss.
- **The wrong-weapon death** (blade vs the fly sign, floor 4) plays
  exactly as the audit promised: verdict warns "cannot reach it"
  before the fight, three rounds of "cuts empty air. Steel can't
  touch what flies.", then the defeat card names the bow and the
  armory.
- **First bow** — the Forge sells the gate-issue Basic Bow and Worn
  Wooden Staff alongside the tier steel, so the second path opens
  for pocket change; the buy line explains equip + scrap-bin +
  repair in one breath.
- **School** — refusals are shard-voiced and name the shortfall:
  "Rank 2 bow wants 57 XP — your bar holds 4. Kills fill it."
  Back goes to the gate camp (phase-6 fix holds).
- **Floors 5–12 fair-handed** — wins on 5–10 including a 16-round
  staff kite of the floor-10 Goblin guard (slow + armoured vs
  ranged = the sign system compounding legibly). Deaths on 11–12
  with the tier-0 Rusted Sword; the card correctly blames gear,
  not sign ("Nothing turned your blows — it simply hit harder…
  better gear, or run").
- **Migration letter** — a planted legacy doc (clazz=sorcerer, v6)
  wakes to "The guilds dissolved their halls into one School",
  Staff — trained rank 6 honored.

Driver artifacts worth recording (not game bugs — both taught
correctly in-fiction once the driver read the cards):

- The XP bar soft-clamps to the level threshold on doc heal
  (`state.py` "Soft clamp"); injected XP above the bar vanishes.
  The refusal card explains it ("Kills fill it").
- The Arcanum rack windows to the current tier — the rung-0
  tallowwood staff is off the rack by floor 6; starters live at
  the Forge.
- Test-harness docs must set `held[0] == gear.weapon` by hand;
  real docs heal this on load (state.py load-heal + core equip
  sync). Same artifact the audit probe hit.

## 4. Production checklist — PREPARED, not executed

**No deploy without roy's explicit word.** When given:

1. Version bump proposal: game `0.62.0` (048 — the weapon decides:
   classless creation, path×rank training, signs/types flip,
   verdict + defeat cards, /mechanics ledger).
2. `plugin_linear_ascent/version.py` bump + CHANGELOG entry (draft
   below).
3. Vendor 048 into worldd per release flow.
4. **POST-VENDOR mechanics regen** (mandatory — the phase-7 regen
   read the sibling plugin via ASCENT_GAME_PATH; a pre-vendor bake
   carries stale numbers, as 0.60.0 proved). Cache-bust `?v=`.
5. Parent-repo commit: vendor + regen + submodule pointer.
6. Deploy per marketplace publish flow — only on roy's word.

CHANGELOG draft:

> **0.62.0 — the weapon decides (048).** Classes are gone: pick a
> race, take the gate's Rusted Sword and two ranks of bladework.
> The School trains all three paths, rank by rank, for XP and coin;
> a second and third weapon slot let you carry the answer. Monsters
> wear signs (⛨ armoured, ⚡ flying, ✧ spellguarded) and the weapon
> in your hand decides the bite; the fight card tells you before,
> during, and after. Veterans' guild years are honored rank-for-rank.
> The /mechanics page grew a HITS column, sign glyphs, and the full
> path×rank training ledger.

## 5. Open questions for roy (end of 048)

- Veterans migrate at rank 6 vs 7 (currently 6).
- Mastery studies: ship the invitation-only card now, or hold the
  actual mastery laws for 049?
- The `clazz` slug lingers in old docs — rename/strip pass, or let
  it fade?
- Banner-hall roster mastery glyphs need the worldd member-row
  protocol — deferred to 049.

## Learnings for the next plan (049)

- The playtest driver (`playtest_048.py`, scratchpad) is worth
  keeping as a dojo pattern: drain floor movies before gate-town
  beats, use encounter ids not display names (floor 3 ✧ =
  `windfall_haunt` displaying "Drowned lantern"), and print
  `shard_note` — refusals live there, not in body_lines.
- The article-doubling class of bug (`The {name}` around named
  monsters) is now guarded only by `_the()` discipline — new
  combat text must use the helper, never bare `The {e['name']}`.
