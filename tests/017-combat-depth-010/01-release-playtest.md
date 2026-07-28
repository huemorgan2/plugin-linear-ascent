# 010 dojo — the release playtest (three classes)

Date: 2026-07-28 · local stack: Luna 8765 + worldd 8600 (vendor
synced to the 010 retune) + docker `ascent-postgres` · driven in a
real browser (playwright MCP), every screenshot read by the agent.
Screenshots archived in `plans/017-combat-depth/010-balance-and-release/dojo/`.

## Warrior — Bram Ironhand (human), full creation → death economy

| Step | Evidence | Verdict |
|---|---|---|
| Intro (8 story cards) → tower gate | `010-01-intro.png` — 1-bit Aldervale banner, numbered options | PASS |
| Race menu: exactly Human / Elf / Dwarf, each with [i] | `010-02-races.png` — reshot muster banner above | PASS (no halfling) |
| Name via CHAT — the real path | `010-03-after-name.png` — Luna answers in fiction ("That's a name fit for the Stone."), a worldd timeout was voiced in fiction too ("The lift's down — … pull the lever again") and lost nothing | PASS |
| Floor 1 wolf fight card | `010-04-wolf-encounter.png` — enemy HP bar, "at range" chip, "its blows land at HALF — it hasn't reached you", "ATK 8 with your Rusted Sword, DEF 2 on reflex alone" | PASS — zero unexplained numbers |
| [i] dossier | `010-05-dossier.png` — speed in words, both range modifiers named, lore line | PASS |
| Typed kill ending | `010-06-wolf-kill.png` + psql `scene.fx = wolf_kill_melee` | PASS |
| Reincarnation Spell at the Apothecary | `010-07-spell-bought.png` — ◈1,800 = 0.5 DI at frontier 15; effect AND catch printed; "(you hold 1)" | PASS |
| First death → the shardmind's once-a-day save | `010-08-protected-death.png` — "Once a day, I have you." 1 HP, nothing lost; sidekick DEATH moment (one line) | PASS |
| Second death → spell burns | `010-09-spell-death.png` + psql: inventory `{}`, gold kept, gear repaired, HP 220/220 — "the Weapon Reincarnation Spell burns instead of you — nothing is lost" | PASS |
| Third death → unprotected | `010-10-unprotected-death.png` + psql: gold 1,000→600 — "− ◈ 400 carried gold (40%), gone", weapon survived its 20% roll, "Banked gold untouched" | PASS |

## Archer — Sylra Fleetfoot (elf), shoes + quivers at the new prices

- Forge stock (frontier 12): Poisoned/Slowing/Fire Arrows **◈570 =
  0.2 DI**, Piercing **◈1,000 = 0.35 DI**, Weapon Oil ◈570 — the 010
  reprice is live in the vendored engine. Cobbled Boots ◈500 bought;
  Slowing Arrows ×5 bought; gold 3,000 → 1,930 exact.
- Fight (bilge kobold): archer grammar (`attack` at range,
  `treeline_shot`, `nock_slowing_arrows`); nocked quiver consumed
  **one arrow per shot** — the quiver emptied across the ~6-shot
  fight and un-nocked itself, which is precisely the per-push cost
  the new stacked-drain gate models. `010-11-archer-victory.png`.

## Sorcerer — Thorgrim Emberdeep (dwarf), the wall and the key

- Arcanum stock (frontier 15): Strip Potion / Curse Scroll **◈360 =
  0.1 DI** — reprice live.
- Rod-wisp (the 009 retrait, now resist_high): `010-12-wisp-wall.png`
  — and the **matchup moment fired**, once, in one line: "Spellguard
  is high — your magic will bounce. That strip potion is the key."
  `use_strip` appears only in this fight ("Hurl the strip potion —
  spellguard, gone").
- Vial hurled (gone after one fight), wisp killed: +61 XP, +169 gold
  (`010-13-wisp-defeated.png`).

## Moments budget

Across the whole session the sidekick spoke exactly at moments:
3 deaths (one line each) + 1 first-contact matchup (spellguard). No
chatter anywhere else. The 007 promise holds.

## Findings

1. No dead ends, no unexplained numbers, all three classes play their
   intended grammar, and the 010 reprices/retraits are live end-to-end.
2. Environmental (not the game): with the host IO-thrashed (load ~90
   during a Google Drive sync storm) worldd scene calls spiked to
   30–77 s and Luna's plugin timeout shows the "lift is down" retry
   scene. It recovers cleanly and the retry option always resynced —
   the failure UX did its job, in fiction, with nothing lost.
