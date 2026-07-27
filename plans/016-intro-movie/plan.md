# 016 — Intro Movie

## Goal

Replace the single wall-of-text intro card (`_intro_scene` in `engine/core.py`) with a
comic-book style opening movie: a sequence of scenes, each showing **one looping 1-bit
GIF** with **text typed onto it gradually** and a single **Next** button. The movie ends
on the existing title card, whose button ("Walk to the tower gate") flows into the
existing character creation (race → class → name).

The movie must make a brand-new player understand, in under two minutes:

1. **The world** — what Aldervale was, and what was done to it.
2. **The villain and the stakes** — Vharuk stole the world; everyone's home is up there.
3. **Who the player is** — a refugee of a stolen realm, therefore a climber.
4. **The structure** — 100 floors, a Warden on each, the Demon King on the last.
5. **The hope** — nobody climbs alone: lifts open for everyone, names on the Stone,
   climbers muster together to break the great Wardens.

## Player experience

- Each scene: the GIF plays (ambient loop), the scene's text types on at reading speed,
  then a `Next ▸` option appears. Final scene shows the title card with
  `Walk to the tower gate`.
- There is deliberately NO skip — every new climber sees the whole story once. A click
  mid-typing completes the current scene's text instantly, so an impatient player can
  still get through fast by clicking.
- The movie plays once per new character (the `intro` stage); it is not shown again
  after creation.

## The story — scene by scene

Voice: the game's dry, diegetic narrator (this is the shardmind's feed, even before the
player knows what a shardmind is — scene 8 makes that land retroactively). Each scene's
text is short enough to type on in a few seconds. Image descriptions below are written
to be adapted into Veo prompts in the house style (`STYLE` block in
`tools/generate_event_gifs.py`: locked-off camera, 1-bit poster look, silhouettes
against luminous gradients, no text in frame).

---

### Scene 1 — The world that was

**Image:** A wide, peaceful panorama of Aldervale at dusk. A river winds past a human
port-town; slender signal towers blink along its banks. On one side, an elven forest
glows from within with soft bio-light; on the far horizon, dwarven mountains with the
warm furnace-glow of fusion-forges at their roots. Only gentle motion: water glinting,
lights pulsing slowly. **Ambient loop.**

**Text:**

> Aldervale was whole once — and it was never primitive.
>
> Human river-ports under blinking signal towers. Elven woods lit from within. Dwarven
> forges splitting atoms beneath the mountains.
>
> Magic and machine were one craft there. They called it aether.

---

### Scene 2 — The theft

**Image:** The same land at night — and it is being *stolen*. Cracks of blinding light
split the ground; an entire realm — hills, a small town, its windows still lit — tears
free of the earth and rises slowly into a black sky. Tiny silhouettes stand at the rim
of the crater, watching their home leave without them. **One-shot, hold on the risen
land hanging in the sky.**

**Text:**

> Then Vharuk, the Demon King, rose from below.
>
> He did not burn the world. He stole it — realm by realm, torn out of the ground with
> everyone still on it.

---

### Scene 3 — The Ascent

**Image:** The stolen realms, stacked. A colossal tower of a hundred layered bands
fills the sky — black iron seams between captured lands, great anchor chains of aether
light, grav-engines flaring along the welds. Low horizon, the top lost in cloud. Only
motion: cloud deck drifting, chain-lights pulsing. (Same subject family as the existing
`ascent_open` GIF — can reuse or reshoot closer.) **Ambient loop.**

**Text:**

> He welded what he took into a tower of a hundred floors — black iron, grav-engines,
> chains of aether.
>
> Every floor is a captured realm. The people below gave it the only name that fits:
> the Ascent.

---

### Scene 4 — The Wardens

**Image:** Inside a floor: a dark stolen meadow under harsh industrial floodlights. At
the far end, enormous sealed lift doors — and before them, the silhouette of a Warden:
half beast, half war-machine, shoulders of welded plate, paired eye-lamps burning.
Floodlights flicker; the Warden's frame rises and falls as if breathing. **Ambient
loop.**

**Text:**

> On every floor, a Warden holds the lift to the next — half beast, half war-machine.
>
> And on the hundredth floor, in a citadel half throne room, half reactor core, the
> Demon King sits with the whole world stacked beneath him.

---

### Scene 5 — You

**Image:** Low angle from behind a lone figure walking through wreckage-strewn ground
toward the base of the tower, which fills the entire sky above them. The figure is
small, carrying almost nothing. Dust drifts; the tower's chain-lights pulse far above.
**Ambient loop (steady walking).**

**Text:**

> You were on one of those floors.
>
> Your home is up there now — locked behind a hundred Wardens. You walked out of the
> wreckage with a rusted shiv and fifty coins.
>
> That makes you what everyone here is: a refugee. And a climber.

---

### Scene 6 — Roothollow

**Image:** A shantytown huddled at the tower's foot at night — tarps stretched over
titanium wreckage, a plasma forge throwing white sparks beside a horse trough, cookfires
with silhouettes of every race around them: tall elves, broad dwarves, small halflings,
humans. Warm gradient glow against the black mass of the tower behind. **Ambient loop.**

**Text:**

> At the tower's foot stands the last free settlement: Roothollow.
>
> Tarps over titanium. A plasma forge next to a horse trough. Refugees of every stolen
> realm, all of them climbers now.
>
> Every climb starts here — and every dead climber wakes here. The tower does not get
> to keep you.

---

### Scene 7 — No one climbs alone

**Image:** Roothollow's square. The Stone of the Climb — a monolith of old granite —
with names lighting up from within, one by one, in bright aether light. Behind and far
above it, one band of the black tower suddenly snaps alight: a floor freed. **One-shot,
hold on the lit floor.**

**Text:**

> No one climbs alone.
>
> When a Warden falls, the lift opens for everyone — every climber, everywhere. And the
> names of those who did it are cut into the Stone of the Climb, lit from within by
> aether.

---

### Scene 8 — The shardmind

**Image:** Close shot: an open, scarred hand. A crystal shard rises from the rubble
before it and ignites with light, hanging above the palm, throwing hard light across
the figure's face in silhouette. **One-shot, hold on the lit shard.**

**Text:**

> At the gate, a shard of old Aldervale will choose you — a machine spirit that
> remembers the world as it was.
>
> It will scout ahead of you, carry what you cannot lose, and drag you back from death.
>
> It is speaking to you right now.

---

### Scene 9 — The muster

**Image:** Before the towering doors of a Warden's keep: a broad line of climber
silhouettes advancing together — blades, bows, a salvaged warframe or two — under
tattered faction banners rippling in the wind. Dozens of shapes, every race, one
direction. The keep doors loom in gradient backlight. **Ambient loop (banners, slow
advance).**

**Text:**

> The great Wardens do not fall to one blade.
>
> Climbers pledge at the keep, and when enough have gathered, they break it — together.
> Floor by floor. Warden by Warden. All the way to the throne.

---

### Scene 10 — Title card (existing)

**Image:** The existing title banner/FX (`banner="title"`, `fx="ascent_title"`): the
tower with Roothollow at its foot, LINEAR ASCENT in the sky.

**Text (headline, no typewriter body):**

> **Climb the Ascent. Cast down the Demon King.**
>
> One hundred floors between Roothollow and the throne.

**Button:** `Walk to the tower gate` → existing `creation_race` scene (unchanged; the
registrar and the shard-bonding scene now pay off scene 8).

---

## Production notes

- **"Play once, then loop the tail":** the GIF format cannot loop a sub-range of
  frames — the Netscape loop extension is a single global counter for the whole file.
  For the one-shot scenes (2: the theft, 7: the Stone) that should settle into an
  ambient tail instead of freezing, cut the same Veo clip into two GIFs: `<slug>_intro`
  (plays once, no loop flag) + `<slug>_loop` (ambient tail, crossfaded seam). B's first
  frame = A's last frame, and dither levels are computed across BOTH segments so the
  seam is invisible. The pane swaps the mask data-URL from A to B after A's exact
  authored duration (both are inlined data URLs — no load flash). Fallback if we want
  zero pane changes: bake N repeats of the tail into one GIF and let it freeze after
  ~30 s (file size grows per repeat; fine at 1-bit sizes).
- **Status: GIFs are generated** (all 320×200, in `content/art/events/`). Ambient
  loops: `intro_aldervale`, `intro_tower`, `intro_warden`, `intro_roothollow`,
  `intro_muster`. Split scenes (`<slug>_intro` + `<slug>_loop` pairs, shared dither
  levels): `intro_theft`, `intro_refugee`, `intro_stone`, `intro_shard`. The `split`
  config key in `tools/generate_event_gifs.py` implements the two-segment output.
  Note: scene 5 (You) was shot as a split — the figure walks, then stops and stands
  looking up at the tower (ambient tail).
- **GIFs:** 8 new ambient/one-shot scenes via the existing pipeline —
  `tools/generate_event_gifs.py` (Veo → center-crop 20:7 → 320×112 → shared-level Bayer
  dither → white-ink GIF). Add slugs `intro_aldervale`, `intro_theft`, `intro_tower`
  (or reuse `ascent_open`), `intro_warden`, `intro_refugee`, `intro_roothollow`,
  `intro_stone`, `intro_shard`, `intro_muster` to the `EVENTS` config. Loop scenes
  crossfade the seam; one-shots hold their final frame while the player reads.
- **Engine:** replace the single `intro` stage with `intro_1 … intro_9` (or an
  `intro_step` counter on the player dict). Each step renders a Scene with the event
  GIF, the scene text as `body_lines`, and a single `Next ▸` option — no skip.
  Step 10 is the existing `_intro_scene` title card.
- **Typewriter:** the "text written gradually" effect is a client/pane rendering
  concern — needs a look at how the game pane renders scene body text (`pane.py` /
  chat components) to decide between CSS/JS typewriter on the pane vs. plain reveal.
  The movie must remain fully readable if the effect isn't feasible in chat cards
  (graceful degradation: text just appears).
- **Cost/scope:** 8 Veo shots at 4–8 s each; the pipeline already handles reshoots
  (`--force`) and reusing clips (`--from-video`).

## Open questions (for review)

1. **Length:** 10 scenes ≈ 90–120 s of reading. If that feels long, the tight cut is
   6 scenes: merge 1+2 (world/theft), 3+4 (tower/Wardens), keep 5 (you), 6+7
   (Roothollow/Stone), 8 (shard), 9→10 (muster → title).
2. **Scene 8 (shardmind):** keep in the movie, or leave the shard reveal entirely to
   the existing gate/creation scene? The movie version sets up "who is narrating".
3. **Scene order:** shard (8) before muster (9) so the movie ends on the collective
   image, per the brief ("at the end — how they gather together to fight"). Alternative:
   shard last, ending intimate instead of epic.
4. **Replayability:** should the movie be re-watchable from somewhere (e.g. the Stone
   or the title screen) after creation?
