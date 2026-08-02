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
Landscape, light, weather — and the moment the Theft froze here.

## Flora
- **Trees / canopy:** …
- **Ground & water plants:** …
- **Under the Yoke:** what the fever did to the growing things.

## Three places
- **The cave — {name}.** What it is · a quest seed.
- **The peak — {name}.** What it is · a quest seed.
- **The gate in the mountain — {name}.** The stair-lift gate, carved into
  living rock · a quest seed.

## The people
Who they are, how they live, what they love, what they fear.
**The keeper:** {name}, {role} — their one line.

## The six
Six beasts. Each: **was** (the true creature) → **now** (the fevered shape),
a sentence of behavior/story, and what a kill sets free. Tag (N)/(P)/(W).

## Three finds  *(quest seeds — a spell, an ore/metal, a potion/relic)*
- **{name} — {kind}.** What it is · where it hides · the quest it could seed.
- …
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
