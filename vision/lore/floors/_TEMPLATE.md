# Per-floor lore — template & rules

*One file per floor: `floor_001.md` … `floor_100.md`. Each is written from
[`../world-lore.md`](../world-lore.md) — that master doc is canon; a floor
file elaborates its single row and must never contradict it (people, world,
headline animals, trapped folk, and Warden all come from the table).*

**Standing rules (from world-lore.md):**
1. World first, numbers later — write the place; the mechanics get tuned to it.
2. **No firearms.** Bows, blades, spears, axes, chains, siege engines; power
   is **aether**, never gunpowder. ("powder" = blasting/mining powder only.)
3. A kill *frees*: Natives are **cured** (the fever's shape drops away and the
   true animal walks off), Wrongmade are **evicted**, the Pressed are the
   tragic ones (a real death; liberation is breaking their collar). Write every
   beast so its kill reads as one of these.
4. Six kinds of home in the **People** line: three peoples (Men, Giants,
   Elves) and three that are not peoples — **Deep** (shared under-caverns,
   delvers of every race), **Waste** (burned borderlands, borderland folk),
   **Made** (the built upper tower, captives + manufacture).

---

## The shape every floor file follows

```
# Floor N — {World} ({People})

> *one-line epigraph, in-world*

**Cut from:** {origin} · **Gate-town:** {town} · **Warden:** {Warden}

## The land
Landscape, light, weather — and the moment the Theft froze here. Name where the
stair-lift stands (the gate the Warden holds) here, in a line — it does not
need to be one of the three places below.

## Flora
- **Trees / canopy:** …
- **Ground & water plants:** …
- **Under the Yoke:** what the fever did to the growing things.

## Places of interest
Three places, each **different in kind** and **grown from this specific land** —
a ruin, a keep, a lake, a mill, a shrine, a wreck, a bridge, a barrow, a
market, a mine-head, a drowned wood, whatever *this* country would actually
hold. **Do not** reuse the cave/peak/gate formula, and do not repeat the same
three kinds every floor — a farm floor and an ice floor should have wholly
different places. Each gets a name, what it is, and a quest seed.
- **{name}.** What it is · a quest seed.
- **{name}.** What it is · a quest seed.
- **{name}.** What it is · a quest seed.

## The people
Who they are, how they live, what they love, what they fear.
**The keeper:** {name}, {role} — their one line.

## The six
Six beasts, each fitting *this* land. Each: **was** (the true creature) →
**now** (the fevered shape), a sentence of behavior/story, and what a kill sets
free. Tag (N)/(P)/(W).
- **Fit the land.** Natives are the real animals this country would hold — no
  desert salamanders in a marsh, no sky-harpies underground, unless the story
  earns it.
- **Explain every exception.** A goblin, kobold, Red Orc, imp, hellknight, or
  any beast that does *not* belong to this land is here for a *reason* — a
  stray from the garrison marched down the wrong lift, a conscript left behind
  when the war-band climbed, a creature dragged up when its own floor was cut
  and welded here. The line must say *why it's here and where it's from*, the
  way the Fencerows' left-behind goblin straggler does. These misplacements are
  the Theft's fingerprints — make each one a small story, not a filler mob.

## Finds  *(quest seeds — anything of use, grown from this land)*
Two to four useful things this floor could yield — and *not* a fixed
spell/ore/potion set. It can be a spell or cantrip, a metal or material, a brew
or tonic, a tool, a map or knowledge, a key, a craft, a tamed/cured beast that
follows the climb, a relic — whatever this land would actually give up. Make
the mix differ floor to floor. Each: what it is · where it hides · the quest it
seeds.
- **{name} — {kind}.** What it is · where it hides · the quest it could seed.
- …

## The Warden — {name}
The native beast it was built from + the war-engine welded over it + how it
fights + what breaking it opens.

## When it falls
The rising: what these freed people become, and what they send up the tower.
```

*Keep each file self-contained and legible. Invent freely **within** the row's
canon; where a keeper or town is already named in
`plugin_linear_ascent/content/floors/floor_NNN.yaml`, use that name.*
