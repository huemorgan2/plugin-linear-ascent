# 067 phase 5 — the arena card, redressed (roy's production feedback, 2026-08-18)

## Goal
The live arena card (0.91.0) reads wrong on desktop: a 13px HUD in two
translucent boxes with the HP number printed over the name, CSS-div bars,
tiles in a menu block far under the stage, the profile (portrait / CONNECT
GMAIL / pack) still under the fight. After this phase:
1. Both stat lines wear the regular fight's grammar (`_estat_html`): the
   VGA face at card size on a black slab, `HP ▓▓▓▓░░ n/m   ATK n   DEF n
   SPEED n`, HP green/gold/red as it drains, ATK gold, SPEED aether — the
   climber's slab top-left, the foe's slab under it right-aligned. No
   names, no gear glyphs, no type badges (the [i] dossier keeps them).
2. The option tiles sit INSIDE the 3D scene along its bottom edge; nothing
   renders under the stage but the log. Each tile shows the item's own
   1-bit art (the bow's own bow, the arrows' arrows — same 30×48 faces
   the pack uses), scaled with the scene (container units) and pixelated;
   `[n] LABEL` under it, `[i]` in the corner. Consumables that are usable
   this round (nock_/use_/throw_/drink_) show their own art.
3. The profile block (portrait or connect box, meters, pack, faction
   strip) is not rendered while the arena is live (round/victory/death/
   fled cards).
4. Floats hold ~500 ms at full ink, then fade over the rest of a 3 s
   travel (was 0.9 s).

## Steps
- `engine/arena.py` `tile()` → adds `"art": <slug>` (attack → the lead
  weapon; attack_<slug> → slug; nock_/use_/throw_/drink_ → the item;
  spells/treeline → the lead weapon).
- `render.py`: `_arena_hud_html` → two `.astat` slabs built from
  `_blocks`; `_abar` keeps the `.abar.me/.foe[data-hp][data-max]` hook,
  now `<span class="blocks">▓░</span> <span class="anum">n/m</span>`;
  `_arena_banner_html(scene)` embeds `_arena_tiles_html` when the phase is
  `round`; the fragment skips the below-stage tiles for `round`, and skips
  `_profile_html`/`_faction_block` while `arena_live`; `_arena_tiles_html`
  renders `<img class="aart">` from `_gear_art_url` when the art ships,
  `.aico` fallback; CSS: `.astat`, `.banner.arena .arena-opts` absolute
  bottom, `container-type:inline-size`, `.aart` in cqw, floats 3 s.
- `worldd/static/site/fight3d/arena3d.js`: `setBar` rewrites the ▓░ text +
  colour instead of a fill width; float removal at 3.2 s. `ARENA3D_URL
  ?v=2` in webplay.py.
- Tests: `tests/test_067_arena.py` (tiles inside `.banner.arena`, no
  `.profile` on a round card, `▓` in the HUD, `aart` for a bow); worldd
  `tests/test_067_arena3d.py` unchanged; dojo `labs-arena` re-run.
- Version 0.92.0 → vendor → commit → push → deploy → marketplace.

## Verification
- `python -m pytest tests/test_067_arena.py tests/test_067_labs.py -q` green.
- Dojo walkthrough 26/26 + desktop screenshots (`W=1440`) show: slabs,
  tiles inside the stage, no profile, art icons.
- Production /play: labs on, floor 6 hunt, first strike → new card.

## Rollback
`git revert` the phase-5 commit in plugin + worldd; re-vendor 0.91.0;
deploy.sh. No data migration.

## Execution status (2026-08-18)
- Done. Plugin commits be0ab82 + bd8d191 on main (on top of 069 phases
  1–4, unreleased); the SAME two commits cherry-picked onto db35540
  (0.91.0) as branch `release/0.92.0` — that tree is what worldd vendors
  and ships, so production = 0.91.0 + this phase, no 069 in it.
- Tests: `tests/test_067_arena.py` 10/10, `test_067_labs.py` 6/6; full
  plugin suite 1256 pass / 6 pre-existing fails on the release tree
  (identical set on db35540); worldd 193/193.
- Dojo 0037 (`dojo/results/0037-067p5-arena-dress-2026-08-18/`): 26/26
  against the release tree; desktop (1440) + mobile (420) stills of the
  regular vs arena card in `desktop/`.
- Follow-ups noted, not done: the 320×300 stage stretches to the full
  760px card on desktop (as the regular banner does) — no cap asked for.
