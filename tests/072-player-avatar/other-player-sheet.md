# Other player sheet

## Preconditions
A playing climber in town with at least one other climber on the square.

## Scenario
1. Open `/play`.
2. Click another climber's face.
3. Read the card from the top.

## Expected behavior
The other climber's sheet is at the top: name, race/class, faction,
level, coins, figure with worn slots, HP / energy / XP, ATK / DEF / SPD.
Actions include **Loot them** (not "loot their camp"). The viewer's own
profile still sits at the bottom and still works.

## Fail conditions
- The page is only text (no figure, no slots, no meters).
- The option still says "Loot their camp".
- The viewer's pack or live meters jumped to the other climber's numbers.
- Banked gold appears anywhere on the card.

## Verify
The scene JSON has `avatar.name` matching the tile, `avatar.slots` with
seven entries, no `bank` key under `avatar`.
