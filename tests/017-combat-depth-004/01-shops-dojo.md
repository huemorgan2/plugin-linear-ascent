# Dojo — 017 phase 004: shops, rungs, shoes, Arcanum

Real browser against local Luna (:8765) + local worldd (:8600, tenant
qa007). Class swaps via psql on the worldd doc — fields are `clazz`
and `gear.weapon` (the 002 lesson). Screenshots into the summary.

## Scenarios

A. **The locked Arcanum row.** As a sub-6 character, open the town
   square: "The Arcanum — 🔒 level 6" is a row, not a secret. Click
   it → the shard refuses with the level, the door holds.

B. **Warrior at the Forge.** Blades racked (not bows), the next rung
   greyed "🔒 Iron Sword — level 6", shoes ladder with its own lock,
   the off-class Ashwood Bow at ◈ 750 marked off-class, an Arrow pack
   row. Buy nothing; read everything. Gear icons on the shop rows.

C. **Archer buys boots.** Swap the doc to archer (clazz + basic_bow),
   level 3, gold 1 000. The Forge racks BOWS; buy Cobbled Boots —
   gold drops 500, the pack strip grows a boot, and the locked
   "Wayfarer's Treads — level 11" line shows what's next.

D. **The Arcanum opens.** Sorcerer at level 6 (doc swap): the town row
   loses its lock; inside, Tallowwood/Coalglass staves + the Glass
   Bead Focus rack. Buy the focus — it lands in the shield slot.

E. **Off-class bow in a real fight (spot check).** Warrior + ashwood
   bow + arrows vs a flyer: the fight opens with "Attack" (no Close
   in — the bow shoots at range), arrows tick down, and the moth
   takes damage steel could never deal.

Pass = every rack matches the class, every lock names its level, the
purchase notes read right, and nothing needs explaining out-of-band.
