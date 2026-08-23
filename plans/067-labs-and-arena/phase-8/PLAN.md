# 067 phase 8 — toolbar under a 320×160 stage; tiles half; regular menu around the fight (roy, production 0.95.0 screenshot, 2026-08-23)

## Goal
1. The option tiles shrink to HALF (30px box, 15px-ish icon scale kept:
   21px picon), the label under the icon, never inside the box; the ATK
   a small gold line of its own under the label.
2. The tiles do NOT ride over the rendered scene. They sit in one
   toolbar row DIRECTLY UNDER the stage (above the log), icons with
   text underneath.
3. The stage is a 320×160 band (half the old height). The 3D layer
   keeps its 320×300 frame; CSS windows the actor band (same px per
   row — nothing squashes), and the floats layer wears the same window
   so the damage numbers keep landing on the heads.
4. Tiles exist ONLY during the fight itself (`phase == "round"`).
   The opener and every end card (victory / death / fled) use the
   REGULAR menu — rows like the town/gate card — and the end cards get
   the profile back.
5. Victory: the XP/GOLD tally (the win card's big line + pips) shows
   OVER the rendered scene, centered; the regular menu under it.

## Steps
- `render.py`:
  - `_arena_banner_html`: aspect 320/160; on victory embed
    `<div class="awin later">tally</div>`; tiles no longer embedded.
  - fragment: `arena_round = phase == "round"`; banner → (round only)
    tiles toolbar → log; the flow tally is skipped when the banner
    carries it; the regular options path runs for every non-round card
    (the opener branch with tiles is deleted); the profile is hidden
    only while `arena_round`.
  - `_arena_tiles_html`: box 30×30, picon 21×21, ATK its own line.
  - CSS: `.banner.arena canvas` + `.afloats` windowed (`--atop`,
    height 187.5%); `.options.arena-opts` a flow row (margin 6px 0 0,
    no border/background); `.awin` centered overlay, tallies on black.
- `worldd/static/site/fight3d/arena3d.js`: no behaviour change needed —
  tile hold/release already null-safe when no `.arena-opts` exists.
  Bump `ARENA3D_URL ?v=4` only if the file changes after visual check.
- Tests `tests/test_067_arena.py`: round card → tiles as the banner's
  SIBLING (not inside), 30px box; opener/victory/death → no
  `arena-opts`, regular `class="options later"`, victory carries
  `class="awin"`; aspect-ratio 320/160.
- Dojo `labs-arena` walkthrough: expectations moved (tiles below the
  stage, end card regular menu + awin), re-run, results 0041.
- Version 0.96.0 → vendor → deploy → marketplace.

## Verification
- `../worldd/.venv/bin/python -m pytest tests/test_067_arena.py tests/test_067_labs.py -q` green.
- Dojo walkthrough green; 420/1440 captures of round + victory reviewed.
- Production /play: floor 6 fight → 160-band stage, toolbar under it;
  victory → tally over the scene, town/gate as regular rows.

## Rollback
Revert the phase-8 commit in plugin + worldd, re-vendor 0.95.0,
deploy.sh, republish 0.95.0 zip.

## Execution status (2026-08-23)
- render.py done as planned; arena3d.js untouched (ARENA3D_URL stays
  ?v=3) — hold/release proved null-safe on end cards.
- Stage window: `--awin-top:-59.4%`, `--awin-h:187.5%` on canvas +
  `.afloats` — 320×300 frame shows rows ~95–255 as a 320×160 band at
  identical scale; floats still land on the heads.
- Narrow stages: container query ≤600px shrinks the awin tally
  (9px tallies, 16px head glyphs, 9px pips) — verified by eye at 420
  after server restart (slab centered, pips inside the band).
- Tests: `test_067_arena.py` 19/19; full plugin suite
  6 failed / 1296 passed — the identical pre-existing six
  (test_008_pace×2, test_013_combat_feel, test_017_damage_types,
  test_017_death_relics, test_kill3d), no regressions.
- Dojo `labs-arena` → results/0041 surfaced two real issues on the
  re-runs (8392/8995/9804 ms "settle", one foe-slab wrap):
  1. S6 measured itself — the serial `Date.now()-t1` counted the
     harness's fixed 3.8 s of float-watching + a screenshot inside the
     budget. A timestamped probe put the real settle at 4.3 s
     (round card 725 ms, canvas 732 ms, beats done 4328 ms). Fixed the
     walkthrough to clock settle with a parallel busy-watcher.
  2. The foe HUD slab wrapped under with a 3-digit-HP foe (Vault boar
     286/286) at a 394 px stage: the HP line is 31ch of `pre`
     (20 blocks + numbers); at 12px two slabs + 4 px gap = 388 px > the
     382 px row. Latent since the phase-7 slab design, content-random.
     Fixed with a ≤440 px container tier (10 px slabs, 10 px aico);
     browser-verified at 420 with forced 1000/1000 — both slabs share
     the top line (170+170 px in 382 px).
  Final run: see 0041/summary.md.
- Captures reviewed at 1440 and 420: round (toolbar of 30px boxes with
  label+ATK under, actors inside the band) and victory (XP/GOLD slab
  over the scene, regular menu rows + profile below); death card shows
  regular rows.
- Released: 0.96.0 vendored, deployed, marketplace-published — shas in
  the root commit and 0041/summary.md.

## Execution status — 0.96.1 follow-up (2026-08-24, roy's three reports on live 0.96.0)

- **The squash (report 1).** The stage was CONDENSED, not cropped: the
  320×300 3D frame stretched into the 160 band (1.875× vertical
  squash). Root cause: `createStage` (worldd fight3d.js) assigns
  `inset:0;height:100%` INLINE on the canvas, which beats the phase-8
  stylesheet window — the CSS rule silently never applied. Run 0041
  had recorded the evidence (canvas rect = banner box) but no check
  asserted the rect. Fix in worldd `arena3d.js attach()`: copy the
  slot's computed `--awin-top`/`--awin-h` onto the canvas as inline
  styles (`?v=4`); render.py keeps the single source of truth. Window
  retuned to rows 115–275 (`--awin-top:-71.9%`) so the actors
  (~150–240) sit centered — sky cut above, ground below. The dojo now
  asserts the RENDERED rect (0042: h/band = 1.864, top/band = −0.717).
- **Victory overlay (report 2).** The tally slab blocked the scene.
  `_tally_html(lean=True)`: big amount lines only — no black slab, no
  pip heaps, no note. pytest asserts `tallies lean` + no `tmarks` in
  the banner.
- **Toolbar tiles (report 3).** Tiles rebuilt as ROWS: 76px box (56px
  picon) with a 4-line 16px text column on the right — `[n]`, label,
  gold ATK, `[i]` pinned to the last line.
- Verification: dojo run 0042 — 36/36 (one harness fix: the S11 gap
  check assumed a single-row toolbar; big tiles wrap on a phone).
  Victory-lean covered by supplementary captures at 1440/420 (the
  walkthrough's fight died, content-random). Plugin suite: 6
  pre-existing fails, 1296 passed. Released as 0.96.1.
