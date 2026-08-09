# Scenario 01 — The ✦ meter is XP now, and the philtre is gone

## Setup
Fresh character (any race/class) on a QA Luna with the 006 plugin build.

## Steps
1. Say "play linear ascent", walk creation (race → class → name).
2. In Roothollow, read the meter rail on the town card.
   - **Expect:** `✦ 0/60` (level 1 needs 60 XP) with an empty block bar.
     No regenerating mana meter anywhere.
   - Hover/read the ✦ tooltip: it must describe crystallized experience,
     "full bar = next level", "levels are forever", and spending on
     honing/spells/mending. No mention of regeneration per minutes.
3. Enter the tower gate → floor 1 → hunt → win one fight.
   - **Expect:** the ✦ meter moved (e.g. `✦ 11/60`), blocks partially filled.
4. Ask for the character sheet ("show my character").
   - **Expect:** `xp` and `xp_to_next` fields; **no `aether` field**.
5. Go to the Apothecary & Medlab.
   - **Expect:** 6 items. **No "Aether philtre"** row.
6. Reply with a plain-text option number ("1") somewhere along the way.
   - **Expect:** text fallback works; meter line in text form reads
     `✦ <xp>/<need>`.

## Pass
All expectations hold; nothing on any card still says "mana", shows a
regen-style ✦ bar, or sells the philtre.
