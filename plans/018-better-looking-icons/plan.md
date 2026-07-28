# 018 — better looking icons

## The complaint

The pack strip and the shop rows are carrying 16×16 one-bit glyphs that
look crude even by one-bit standards: flat, axis-aligned, bilaterally
symmetric, and floating in two or three pixels of dead margin. At 32 px
next to a label they read as wireframes, not objects.

Nothing else about the card is wrong, so this is an art problem, not a
renderer problem.

## The constraint we are keeping

One bit, and this time literally. Every icon stays a **single-colour
alpha mask tinted by `background-color`**, because the tint is
load-bearing: equipped items draw in `TEXT`, everything else in `DIM`,
shop rows brighten on hover, specimen variants recolour. Colour icons
would throw all of that away.

An earlier pass tried to buy shading with four levels of
`fill-opacity`. That is not one bit, it is four, and it was dropped.
**Every pixel the page emits is ink or nothing.**

The digits in the grids survive as *authoring* marks — they record how
lit each part of a shape is so a style can decide what to do with it —
but every renderer turns them into on/off pixels before they reach the
SVG.

    '.'  hole      — outside the shape
    '1'  shadow    — the turned-away edge
    '2'  mid       — the body in shade
    '3'  base      — the body in light
    '4'  highlight — the lit edge, facing top-left

## What one bit forces

Four rules, each learned by drawing the wrong thing first.

> **Shading is dither, not a second tone.** Lit parts stay solid ink,
> shaded parts break into a pattern. Squint and it is tone; look close
> and every pixel is on or off. Light falls across the shape's own
> diagonal from the top-left, in two bands only — a third band eats the
> shape at 32 px.

> **A detail can only be a hole.** A brighter mark inside a solid body
> has nowhere to go when there is no second tone. The buckler's boss
> was drawn as ink and was therefore invisible in every style; as a
> two-pixel hole it reads everywhere.

> **Dither eats a two-pixel detail.** A hole only survives if the ink
> ringing it is held at full ink. Either ring each enclosed hole, or
> outline the whole shape — the winner does the latter, which gets it
> for free.

> **Only a surface can be shaded, never a stroke.** The checker runs
> along the same diagonal the light does, so a stroke running that way
> gets chewed lengthwise into dashes. Shading by area made the bolt and
> the wrench look broken rather than lit. Ink is body only if it sits on
> a full 3×3 of ink; everything thinner is rim, and comes out
> untouched. This is what lets one rule cover objects and inline
> markers alike, with no per-icon exceptions.

> **Silhouette beats size.** The bold pass drew everything edge to
> edge; the star became an anvil and the jerkin became a heart. A shape
> needs its own outline more than it needs the extra pixels.

An earlier attempt split each shape down the middle, light on the left
and dark on the right. It looked worse than what ships: two flat halves
that had been torn apart, not an object with volume.

## The bake-off

Eight items — blade, bow, buckler, jerkin, boots, charm, medgel, crate
— in three shape sets, against the shipping set as a control.

| | set | idea |
|---|---|---|
| **A** | current | what ships. Flat, one bit, the control. |
| **S1** | rim | today's silhouettes, lit from the top-left. |
| **S2** | carved | the same, plus interior holes as line work. |
| **S3** | bold | the same lighting on much larger shapes. |

Crossed with the ways to spend the pixels: `solid`, `outline`,
`inked`, `dither`, `shaded`, `shaded + details kept`, `hatch`,
`hatch + details kept`, `outline + shaded`.

Open `mock.html` — the page renders all of them at 16 / 32 / 48 px, in
every tint the game uses, at 8× for judging the drawing itself, and
finally inside a rebuild of the shop card that started this.

`draft_icons.py` is the source: the grids live there as plain ASCII,
it validates every one (16 rows × 16 legal characters) and regenerates
the page.

    python3 draft_icons.py && open mock.html

## Where it landed

**`outline + shaded` on the S1 shapes.** A solid one-pixel outline
around the silhouette and around every enclosed hole, with the body
dithered on the far side of the diagonal. It wins on three counts:

- The outline keeps every silhouette the game has already taught
  players to recognise, so nothing has to be relearned.
- The dithered body gives the buckler, the jerkin and the boot obvious
  volume at 32 px, where the flat set reads as a wireframe.
- Because the outline already rings interior holes, small details come
  through for free — the fuller down the blade, the boss on the
  buckler, the lace holes on the boot, the X-brace on the crate.

It is also the only style in the shaded family that **survives 16 px**,
which settles the dossier-row question: the un-outlined dither columns
go mushy at half size, the outlined one holds.

Two notes for anyone reading the source:

- `hatch` was accidentally identical to `shaded` — `(x+y)%2` is a
  checkerboard, not a diagonal. Real hatching needs a period of at
  least 3; it is now two on, two off.
- The details drafted for S2 that plan A blessed have been raided into
  S1: the fuller, the boss-as-hole, the crate's X-brace. The quilted
  jerkin and the ringed buckler were not — they turn to noise.

## Shipped

The draft assumed the grids would have to carry shading marks. They do
not: **the style is derived entirely from the silhouette**, so the
grids stayed plain on/off ink and the audit that asserts exactly that
(`set(row) <= {'#', '.'}`) still holds. That collapsed step 1 into one
function.

**1 · `icons._painted`.** Turns a grid into the pixels the mask paints:
rim, then body — solid on the lit side of the diagonal, checkered on
the side turned away. `icon_data_url` merges runs over its output
instead of over the raw grid. Still a single-colour alpha mask, so
every tint works untouched.

**2 · Seven silhouettes ported** from S1, the ones that had no interior
mass for the style to work with: the buckler went from a two-pixel
frame to a solid shield with the boss as a hole, the boot and the
medgel gained bodies, the blade gained its fuller, the crate its
X-brace, and the star was redrawn. `armor` already matched.

**3 · Two tests** in `test_014_inventory_tooltips.py` pin the two
properties that hold the style up: shading may only turn ink *off*
(never paint outside the silhouette, or the tint bleeds), and a hole
keeps its ring even on the parity the checker drops.

**Result across the 34 keys:** 17 untouched — every line-art glyph,
including the inline bolt and the wrench — and the chunky ones give up
15–22% of their ink to the dither, which is the volume. `preview.py`
renders the whole set flat against shaded at both sizes; that page is
how the bolt problem was caught.

Left for a release: version bump, marketplace publish, and a worldd
deploy (the vendor copy is already synced, and its 53 tests pass).

## Open

- S3 (bold) is too loud for a row of eight cells, but might carry a
  large single-item surface later — a loot card, a dossier header.
- The 17 untouched glyphs are untouched because they are line art. If
  any of them should read as an object rather than a symbol, it needs
  redrawing with interior mass — the renderer cannot invent volume that
  the silhouette does not have.
- Banners and creature art are a separate pipeline (`tools/`,
  Bayer-dithered PNGs) and are untouched by this.
