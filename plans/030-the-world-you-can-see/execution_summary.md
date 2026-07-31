# 030 — the world you can see · execution summary · 2026-08-01

All nine phases shipped to main. Version 0.34.0 → 0.35.0.

## What landed, phase by phase

1. **One coin, one colour** — `render._paint_amounts` colours ◈ gold,
   ⚡ energy and XP as icon+number in one colour each, on every surface;
   `to_text()` keeps the plain glyphs (parity unit-tested).
2. **The profile block** — every playing card carries a full-body
   100×200 1-bit portrait (armour-keyed: rags → leather → chain →
   scale → plate → aegis by FORGE tier), meters beside it, and ATK/DEF
   as 10-icon pip rows: every 3 points is half an icon
   (`icons.icon_data_url(key, "full"|"half"|"outline")`, one 16×16
   grid per key, three masks). Numerals always print.
3. **Rooms are pictures** — 13 rooms regenerated tall at 320×200
   (forge, lodge, vault, medlab, relay, guildhall, stone, gate,
   arcanum, roothollow, greenreach, gnarl, town_lamplit_steading);
   the shard speaks behind its own ◆ mask icon.
4. **The vault strip** — `scene.strip` wire field + 320×50 strongbox
   band ("DEPOSITED: ◈ n" in gold) over black; paper texture for the
   Morning Crier at 320×150 behind the news, with an × close;
   warden progress condensed to one line.
5. **The gate sees the tower** — floor rows ~3× taller with fields +
   warden art side by side (`render._floor_tile_art`).
6. **A voice in every fields** — lodge keeper NPC with rotating
   tellings; per-floor lore NPC (name/role/greet/lore/warn in the
   floor yaml, linted) who quotes on the reel and talks on the floor,
   warn lines carrying real warden numbers.
7. **The fight tells its odds** — enemy plate top-right over the art
   (ATK/DEF pips player-style, HP bar, range chip); dossier carries
   the story line and coin/XP drop bullets via `scene.enemy["drops"]`.
8. **The arrival reel** — first entry to a floor plays two beats
   (world → warden, or "has already fallen" naming the slayers from
   worldd's new `fallen_by` map) before the arrival card; any click
   advances; once per floor (`floor_seen_{n}`); animated 1-bit GIF
   loops floor{1..10}_world/_warden + a shared warden_fall one-shot
   (Veo 3.1 → Bayer 1-bit, crossfaded loop seams). Floors 11+ fall
   back to still banners — the level-10 rule.
9. **Tuned to 10, quick everywhere** — `economy.TUNED_FLOOR_CAP = 10`;
   the bestiary's floors 11–100 sims self-skip and the retune sim
   stops at the cap unless `ASCENT_FULL_SIMS=1` (pre-ship ritual).
   Full default suite: **753 passed, 1 skipped, ~5s**, no ignore
   flags. A conftest auto-stepper walks the reel for pre-030 tests;
   `@pytest.mark.reel` opts the reel's own tests out.

## Commits

plugin-linear-ascent (straight to main):
- `2e5859a` Phase 8 — the floor arrival reel + reel passthrough
- `0dd9c32` Phase 9 — TUNED_FLOOR_CAP, sims behind ASCENT_FULL_SIMS
- `cd7a52c` Phases 1–7 wiring + 030 art (portraits, tall rooms,
  vault/paper bands) + tools + 25-test 030 suite
- `6f1d28e` chain-portrait reroll + `tools/qa_030_shots.py` harness
- `21f80dc` floor-reel GIFs (21 loops, Veo 3.1 → 1-bit)
- (this ship) `plugin 0.35.0: manifest sync`

outer repo:
- `5d63066` worldd: `fallen_by` map (who broke each keep) persisted
  and served on `world.warden`
- `21dcfe7` dojo 0030 visual pass (14 screenshots + summary)
- (this ship) vendored worldd game + submodule pointer bump

## Verification

- pytest: 753 passed / 1 skipped in ~5s (the whole game, no ignores);
  `ASCENT_FULL_SIMS=1` path exercised for the capped modules.
- Dojo: render-harness pass at level 1 and ~10 —
  `dojo/results/0030-the-world-you-can-see-2026-08-01/` (14 shots).
  The full worldd+QA-Luna stack is blocked on this machine (no
  Postgres), so worldd's DB-backed suite did not run here;
  `fallen_by` was verified as a pure function and through the
  harness's synthesized world payload.
- Art: every asset in the plan's ledger generated (nano-banana-pro →
  1-bit for stills, Veo 3.1 → 1-bit for the reel loops), spot-checked
  visually; one chain-portrait reroll for a dither artifact.
