# The Liberation Dissolve

The one death effect, identical for every monster in the game. On the
killing blow the fever's magic leaves the body: the monster dissolves
into particles, and what remains is what it was before the tower.

## The effect, frame by frame

Six frames, ~2 seconds total. All in the designed 1-bit banner style.

1. **Kill pose** — the monster takes the final hit, silhouette intact.
2. **Rim flash** — the black silhouette freezes and its white rim
   contour flares bright; hairline cracks of white split the body.
3. **Break** — the silhouette breaks apart from the top down into
   square chunky dither particles (single white/black pixels and 2x2
   blocks) that lift off the body. The magic leaves as a thin RIBBON
   of sparse dither curling up and away from the chest.
4. **Cloud** — the body is fully dissolved: a rising cloud of square
   particles, dense at the center thinning to sparse dots at the top
   edge. Behind the thinning cloud, the TRUE FORM is already standing.
5. **Settle** — particles nearly gone (a few sparse motes drifting
   up), the ribbon fading at the top of frame. The true form reads
   clearly now, TINY next to where the monster stood.
6. **Alone** — particles gone. The true form stands quiet in the same
   spot, at its real size. Scene light unchanged.

## What remains (by kind)

- **Native** (infected animal): the original small animal, at its
  ORIGINAL SMALL SIZE — a fraction of the monster's bulk (a monstrous
  wolf leaves a shy farm-country wolf; the boar leaves an ordinary sty
  boar; the rat leaves a granary rat; the lane wolf leaves a sheepdog).
  The size drop IS the payoff: the fever's lie made visible.
- **Pressed** (conscripted person — goblins, kobolds, orcs, imps):
  the person, unarmored and small, sitting where they fell — freed,
  not killed. Their oversized weapon stays on the ground.
- **Wrongmade** (manufactured — wardens, wights, leaks): nothing
  remains. The particles disperse to empty ground; only wreckage
  (welded plate, snapped blackthorn) stays where it stood.

## Canonical prompt block

Append the stage line (frames 2-6) to this base when rendering
liberation frames. Same wording every time — this is the effect's
identity:

> The monster is dissolving in the LIBERATION DISSOLVE: its solid
> black silhouette breaks apart into square chunky 1-bit dither
> particles — single white and black pixels and 2x2 blocks — that
> lift and scatter upward like sparks, dense at the body thinning to
> sparse dots above, while the fever's magic leaves it as one thin
> ribbon of sparse dither curling up and away. Everything else in the
> scene — background, light gradients, the player character — stays
> exactly the same.

Stage lines:

- Frame 2: "The dissolve is just beginning: the monster's white rim
  contour flares bright and hairline white cracks split its black
  silhouette. The body is still whole."
- Frame 3: "The dissolve is halfway: the upper half of the monster has
  broken into the particle cloud; the legs still stand."
- Frame 4: "The body is fully dissolved into a rising particle cloud.
  Standing on the ground behind the thinning cloud, small and whole:
  {true_form}."
- Frame 5: "Only sparse drifting motes remain of the cloud. {true_form}
  stands clearly in the monster's place, tiny by comparison."
- Frame 6: "The particles are gone. {true_form} stands alone, calm, at
  its real size, in the exact spot where the monster died."

`{true_form}` per kind: native — "the original animal at its true
small size: {was}" (from the floor YAML `was:` field); pressed — "the
freed person, small and unarmored, their oversized weapon left on the
ground"; wrongmade — omit frames 4-6's true form: "nothing but
wreckage where it stood".
