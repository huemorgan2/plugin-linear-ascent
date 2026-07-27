# 014 · Scenario 1 — the pack strip and the whisper glyphs

Goal: every scene with meters lists the inventory beneath them as 32×32
single-color 1-bit pixel icons, and every option carries an [i] on its
right whose tooltip appears INSTANTLY and explains what the option
achieves and how it advances the climb — town places most thoroughly.

## Steps

1. Open the Linear Ascent pane (GAME tab) with a playing character in
   Roothollow.
2. **Expect (pack strip):** under the HP/⚡/XP/LV/◈ rail, a strip of
   items: the equipped weapon first (e.g. "Rusted Shiv"), then armor and
   shield if worn (hone level in the name, e.g. "Pigsticker +2"), then
   pack items with ×counts. Each has a 32×32 pixel icon, single ink
   color, visibly 1-bit (hard pixels, no anti-aliasing); equipped gear
   reads brighter than pack items.
3. Hover a pack item. **Expect:** a tooltip appears with NO delay,
   explaining the item's effect in numbers and why it matters for the
   climb (e.g. Medgel: +25 HP, keeps a hunt going without walking back).
4. **Expect (glyphs):** every option row in the square — Forge,
   Apothecary, Lodge, Vault, Pawn, Relay, fields, Guildhall, Stone,
   gate, Muster — has an `[i]` at its right edge.
5. Hover the Forge's [i]. **Expect (instantly):** what the Forge sells,
   that better ATK/DEF is what opens higher floors, and that higher
   floors pay more gold/XP. Repeat for the Vault (banked gold survives
   death, 5%/day) and the Guildhall (training = buying levels; factions).
6. Click an [i] itself. **Expect:** NOTHING happens — the option does
   not fire.
7. Walk: gate → floor 1 → hunt. **Expect:** fight options (Attack /
   Stand / Run / class move / scan) all carry glyphs; hovering Stand
   explains halved damage; the pack strip still renders under the rail
   mid-fight.
8. Visit the Forge and hover a `buy_` option's [i]. **Expect:** the tip
   carries the item's slot, bonus and level requirement. At the
   Apothecary, hover Medgel/Energy cell — effect + daily cap explained.
9. Buy a Medgel. **Expect:** it appears in the pack strip immediately
   with its icon and ×1.
10. In CHAT (not the pane), trigger a scene card if one renders (legacy
    path) — the same strip and glyphs must render there too.

## Pass criteria

- Tooltips are instant (CSS hover, no 500ms+ native title delay), and
  every rendered option in the whole walk has one.
- Icons are crisp 32×32 1-bit pixel art, mask-tinted a single color.
- The [i] never triggers its option, on click or tap.
- Tip text is lore-voiced but unambiguous: numbers present, purpose
  ("how this advances the climb") explicit.
- Creation scenes (race/class/name) still render clean; race/class
  options carry tips; no pack strip before the character exists.
