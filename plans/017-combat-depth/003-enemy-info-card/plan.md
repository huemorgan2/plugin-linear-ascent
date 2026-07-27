# Phase 003 — The enemy [i] card

Goal: the counter system becomes READABLE — the KR lesson that the
whole overhaul hangs on. [i] badge on the enemy image; dossier with
always-on HP bar, armor/resist/speed tiers, flying flag, lore. Nothing
player-facing from 001/002 is considered "done" until this ships.

## Tasks

1. `icons.py`: 1-bit icon set — 16×16: armor shield, magic shield,
   wing, speed hare, bulwark, durability wrench (for 005); 32×32
   variants for shop rows (004). Follow the existing inline style.
2. `content/schema.py`: optional `lore:` per encounter (≤160 chars,
   linted with the prose rules). Author lore for floors 1–10.
3. `render.py` + `pane.py`:
   - [i] badge top-right on the enemy banner (057 action plumbing —
     a card action, no model in the path).
   - Dossier fragment: enemy HP bar (visible from round 1, mirrors the
     player meters), named tiers with icons, speed tier, lore lines.
   - Range state indicator (at range / close) in the fight header.
   - 001 retro: the opener's `◆ plate Low` line uses the SAME diamond
     as the tactics hint — they read as one system at a glance. Give
     the profile line its trait icons here and retire the bare ◆.
4. `engine/combat.py`: scout upgrade — exact numbers + next intent
   ("it will try to close this round"); headline keeps ATK/DEF but HP
   bar replaces the post-first-exchange HP reveal.
5. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: dossier fragment renders every profile combination; HP bar
  math; lore lint (cap, banned words); icons present for every trait.
- Render specimens: add dossier cases to the card-specimen tooling.
- Dojo (the real gate): open the [i] card on an armored, a flying, and
  a fast monster; confirm a new player can answer "why is this fight
  bad for me" from the card alone in one glance — screenshot evidence
  in the summary.

Exit: all green, published, worldd synced, `execution_summary.md`.
