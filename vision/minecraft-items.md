# Research: Minecraft — Limited-Item and Relic Design

*Added 2026-07-27 as design reference for the combat-depth overhaul
(`plans/017-combat-depth/`). Companion to
[kingdom-rush.md](./kingdom-rush.md).
Sources: [Totem of Undying (Minecraft Wiki)](https://minecraft.wiki/w/Totem_of_Undying),
[Golden Apple](https://minecraft.wiki/w/Golden_Apple),
[Enchantment](https://minecraft.wiki/w/Enchantment),
[Depth Strider](https://minecraft.wiki/w/Depth_Strider),
[Healing](https://minecraft.wiki/w/Healing).*

## Why Minecraft

Minecraft's combat gear is a catalog of exactly the thing 017 needs:
**dozens of dramatic, memorable powers that never break the game because
every single one carries a hard, legible limitation.** The limitation IS
the design — remove it and the item is broken; keep it and the item is a
story ("I survived because I was holding the totem").

## The template: one dramatic effect + one hard limitation

| Item | The dramatic effect | The limitation that makes it fair |
|---|---|---|
| **Totem of Undying** | Cheats death outright: fatal hit → survive at 1 HP + strong regen burst | **Single-use, consumed on trigger**; must occupy a *hand slot* (opportunity cost while carried); rare drop source only |
| **Golden Apple** | Absorption (bonus temporary hearts) + fast regeneration | Bonus HP is a **decaying overshield**, not a stat raise; effect is timed (minutes) |
| **Enchanted Golden Apple** | Absorption + Regeneration + **Resistance** (flat % damage cut) + Fire Resistance | **Cannot be crafted** — loot-only, genuinely rare; still timed |
| **Tipped arrows** (poison, slowness, harming, weakness…) | Ammo carries a spell: every arrow type is a different tactical answer | Expensive to make, **consumed per shot**, effects deliberately weaker than the drunk potion |
| **Thorns** (armor enchant) | Attackers take damage for hitting you | Proc is **chance-based**, and each proc **burns extra durability** — defensive power literally wears your armor out |
| **Potion of Invisibility** | Enemies detect you only at drastically reduced range | Worn armor stays visible (reduces the effect); **attacking provokes anyway**; timed |
| **Boots enchants: Depth Strider / Frost Walker / Soul Speed** | Terrain-conditional **movement speed** as buyable gear | **Mutually exclusive** with each other (pick a specialty); Soul Speed *burns durability while it works* |
| **Unbreaking / Mending** | Durability relief: chance to ignore wear / repair with XP | Mending is loot-only; on bows **Mending and Infinity are mutually exclusive** — infinite ammo or infinite durability, never both |

## The transferable lessons

1. **Death-cheat items work when single-use + carried + scarce.** The
   totem never trivializes death because you can hold exactly one, it's
   consumed instantly, and you revive nearly dead (1 HP) — saved, not
   restored. Roy's *Stone of Undying* ("you don't rejuvenate completely,
   you can only hold 1") is exactly this shape.
2. **"More HP" should be an overshield, not a stat.** Golden-apple
   Absorption grants temporary hearts that don't regenerate — the power
   fades on its own. Roy's *Golden Apple* (2× HP + half damage) maps to
   Absorption + Resistance, both timed.
3. **Ammo is the perfect limiter for archer power.** Tipped arrows show
   the pattern: one bow, many arrow *types*, each type scarce and
   consumed per shot. Poison (damage over time), slowness (kiting help),
   harming (burst) — every counter-consumable is just a quiver row.
4. **Defensive power can pay in durability.** Thorns damaging its own
   armor per proc, Soul Speed wearing boots down *while sprinting*: the
   item taxes itself in the exact currency of 017's durability system.
5. **Speed is gear.** Minecraft sells movement as a boots line with
   forced choices (Depth Strider XOR Frost Walker). 017's forge shoes
   ladder is genre-native.
6. **Mutual exclusivity creates builds without balance patches.**
   Infinity-or-Mending is a one-line rule that generates a real decision
   forever. Prefer hard either/or rules over percentage tuning.
7. **XP as repair currency is proven** (Mending). 017's "repairs cost
   gold + a few XP" has a working precedent.

## Mapping to Linear Ascent (017)

| Minecraft | Linear Ascent |
|---|---|
| Totem of Undying | **Stone of Undying** — hold 1, consumed on death, revive at partial HP |
| (Enchanted) Golden Apple | **Golden Apple** — timed overshield (2× HP) + damage halved |
| Tipped arrows | **Arrow types**: poisoned / slowing / magic-piercing / fire — bought in 5s–10s |
| Thorns | **Thornmail** — reflects damage, wears itself out per proc |
| Invisibility potion | **Veil Draught** — untargetable until your first attack |
| Boots enchants | **Forge shoes ladder** — speed tiers; degradable like all paid gear |
| Unbreaking / Mending | Durability quality on higher-tier gear / repair-with-XP at the Forge |
| Infinity XOR Mending | Hard either/or relic rules (e.g. can't carry Stone of Undying + Golden Apple active together — pick your insurance) |
