# 079 — shop delta arrows (forge & Arcanum cards say up or down)

## Problem

A shop card names a price and a stat, but the player still has to
cross-reference their own gear to know whether the thing is worth
buying. Request (2026-08-25, roy): every item card in the Forge and the
Arcanum (the magic store) wears a small 16×16 arrow at the top right —
green up when the piece beats what the player owns (worn or in the
pack), red down when it is weaker. The `[i]` glyph moves to sit just
under the arrow. The arrow is drawn in the house icon method (1-bit
16×16 grid, 018 dither shading), not a unicode character.

## Root cause

Nothing broken — a missing affordance. The card wall (031 §14) shows
each item in isolation; the comparison lives only in the player's head.

## Fix (one phase)

All in the renderer — the scene already carries everything needed
(`scene.slots` = worn gear with honed stat, `scene.inventory` = pack
spares), so no wire change, no engine change, and Luna + website get it
from the same fragment.

1. **icons.py** — two new grids, `arrow_up` and `arrow_down`: solid
   chunky arrows in the 16×16 house style; `_painted` shades them like
   every other glyph.
2. **render.py** —
   - `_owned_best(scene)`: best stat per gear slot across worn slots
     (honed `stat_val` counts) and pack cells; weapons compare +ATK,
     shield/armor +DEF, shoes +speed.
   - `_opt_delta(oid, best)`: for `buy_*`/`wear_*` options whose slug is
     FORGE gear — `up` if strictly better than the best owned in that
     slot (or nothing owned), `down` if strictly worse, `""` on equal
     (a spare of the worn rung gets no arrow).
   - Card wall: a `.delta` span (16×16 mask, `OK` green / `RED` red)
     pinned top-right of the `.gcell`; CSS `.delta~.info` drops the
     `[i]` to sit just under it. Non-gear cards (relics, packs, salves)
     draw no arrow — they have no slot to compete on.
3. **version.py** — 0.102.0 → 0.103.0.

Scope note: relic/apothecary/pack cards have no comparable stat and get
no arrow; the mend rows (hone/repair/token) are not purchases and are
untouched.

## Verification

- New tests in `tests/test_render.py`:
  - unit: `_owned_best` / `_opt_delta` on a constructed scene — better
    rung → up, weaker rung → down, equal → none, empty slot → up.
  - integration: drive a fresh player to the Forge and the Arcanum,
    render, assert `.delta` arrows present with the right colors.
- `pytest tests/` (full plugin suite) green.
- Vendor: `worldd/tools/vendor_game.sh`, diff clean between plugin and
  vendor copies (deploy.sh's version gate stays satisfied).
- Dojo: shop walkthrough scenario (forge cards show arrows matching the
  pack) — run when a live BASE/TOKEN is available.

## Rollback

Revert the commit (`git revert`) — renderer-only, no state or wire
migration; vendor re-sync with `vendor_game.sh` restores worldd.

## Operational notes

No deploy in this change; worldd picks the change up on its next
vendored deploy. No secrets touched.

## Execution status (2026-08-25)

- Implemented in one phase: `arrow_up`/`arrow_down` grids (icons.py),
  `_owned_best` / `_opt_delta` / `_delta_arrow` + card-wall wiring and
  `.gcell .delta` CSS (render.py), version 0.103.0. Commit 29ede35.
- Plugin suite: 1366 passed, 9 failed — all 9 fail identically on the
  pre-change tree (test_022/048/058/067/kill3d, pre-existing), 4 new
  tests pass.
- Rendered forge wall for a fresh archer: 20 cards, 13 up arrows,
  0 down, equal gate-kit rungs bare — as designed.
- Vendored into worldd (vendor_game.sh, version gate 0.103.0 matched);
  worldd suite 215/215.
- Dojo scenario committed at luna/dojo/tests/shop-delta-arrows/
  (luna 51c2d30); walkthrough NOT yet run — needs a live BASE +
  DATABASE_URL. Run it before deploy.
- Deployed 2026-08-25: deploy dep-da6kesm1egvs7392u720 (trigger=api,
  commit 8dee30c1, shipped alongside 078 and 080), status live at
  07:46:56Z; /health reports 0.103.0 ("✓ live: 0.103.0"). Dojo
  walkthrough for shop-delta-arrows still not run (scenario committed,
  runner not written).
