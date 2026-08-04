# 011 — The Veil and the Ladder of Lands (v2, expanded mandate)

Directive (2026-08-04): fold the world-construction canon
(`vision/lore/world-construction.md`) into the story — ALL of it. The
user's explicit mandate: "I don't mind tearing everything down and
changing a lot." So this is no longer a contradiction-patch; it is a
re-grounding. The book, the lore, the floor files, and the art all get
rebuilt on the new world, and the remaining editorial iterations
(3-10) police the result.

The canon being installed (see world-construction.md for full text):

1. **The tower is freed, not weakened.** The Strand's oath is
   unconditional; Wardens hold the LIGHT, not the tower. Killing a
   Warden lifts its floor's veil within a day; the scram kills every
   veil at once. Liberation is visible from the Girdle-sea — grey
   rungs turning gold.
2. **The ladder of lands.** Country-shaped, paper-thin lens trays;
   needle pillars and triangular stays; one offset stair-lift spine
   per gap (down-gate + up-gate per floor, never aligned); ten to
   fifteen terror floors with deep-middle up-gates; the Shear; the
   Kindling; Rimlands vs Deep Middle; central seas and under-rain;
   the Girdle-sea; knot-gardens, bead-towns, stay-roads.
3. **The lid.** The next floor's underside is a visible dark heaven
   the veil's false light paints over. Never "too far up to see."
4. **Three closing rulings.** (a) The scram's ledger — lifts survive
   (counterweighted machinery), veils/false light/broadcast die.
   (b) The countries can never be put back — but freed, they HEAL:
   true light inland, honest green, heavy harvests, dens emptying.
   The epilogue carries both halves. (c) The Made floors (81-100)
   are perfect circles — the only trays without a country's outline.

Status: editorial iterations paused between 2 (committed) and 3.
This plan runs now; iteration 3 resumes at Phase 5 as the
verification pass.

---

## Phase 1 — Canon documents

1. `vision/lore/world-lore.md` — rewrite "The measure of the thing"
   wholesale on the new canon (keep: country-sized floors, own
   weather, eighty-year Theft; replace: iron-wall exterior,
   Wardens-hold-it-up, invisible ceiling). Add the veil, the lens
   geography, the gates walkthrough, the healing ruling, the Made
   circles. Also sweep the rest of world-lore for old-canon phrasing
   (§1-§8 mention the black iron face in places).
2. `book/style-guide.md` — replace the Scale hard-canon block; add
   "The Veil" and "The Ladder" blocks as writing rules: never an
   exterior iron wall; never a tremor at a Warden death; a freed
   floor brightens; the lid is visible; towns live at the rim by
   default; marches cross countries gate to gate.
3. `book/appendices/06-on-the-yoke.md` — align: oath unconditional,
   veil as the Wardens' office, scram ledger (what dies, what
   survives), one sentence so no reader wonders whether the freed
   won a tomb.
4. Mark `world-construction.md` as CANON (v2 adopted).

## Phase 2 — The book re-grounding (two passes)

**Pass A — contradiction sweep (one editor subagent, ~30 edits):**
- Iron-wall exteriors (8 files: 00, 02, 13, 16, 19a, 28, 33, 38a) →
  ladder-of-lands imagery. Black iron survives only as fittings.
- Lid/false-light lines (02, 03, 05, 16, 24, 41) → visible lid; the
  Yoke's counterfeit day bound to the veil.
- 38a reframed: enclosed iron hall → open shelf crossing near the
  spine (wind, real stars, the garden-closes on a dark road).
- Structural-Warden language: verify zero (already grepped clean).

**Pass B — writing the world IN (four part-range subagents, guided
by the style guide; scenes may grow, none may be cut):**
- **Veil-lifts at every on-page Warden death** — the visible reward,
  scaled to the scene (first kill in 07 teaches the rule with Ede;
  35's gold seen by the whole host; 40/41 the ladder turning at
  once, watched from Roothollow/the Girdle-sea).
- **The Kindling** — two or three appearances: once explained (a
  keeper's floor-rite), once used tactically or emotionally, once
  in the epilogue as a thing people no longer need but keep.
- **Rim geography in the marches** — gate-towns at the two doors,
  crossings that skirt or dare the Deep Middle, one terror floor
  with its up-gate in the dark heart (candidates: the pale-court or
  coursing floors), the Shear at every rim scene.
- **The strings** — one bead-town seen once (Nix's supply chapter
  19a is the natural home), the Wake's stay-roads named as how they
  always know first (13/31a), a knot-garden glimpsed from a lift.
- **The Made are round** — the crossing clause at 33/34; mirrored in
  the gazetteer's Made entries.
- **The healing** — 40a/41: freed floors greening, harvests, dens
  emptying; the epilogue's old-voice line carrying both halves
  (never going down; things grow).
- Budget: whatever the scenes need, but every insertion earns its
  place — no lore tourism, no sermons. Style-guide rules bind.
- `appendices/02-gazetteer.md`: aligned in the same pass (veil
  status per floor entry where natural).

## Phase 3 — Art

1. **New cover**: `front-tower-v2.png` (generated, approved look:
   thin trays, cables, clouds through the slots, gold rungs
   mid-stack, port at the foot, no visible top) — promote to
   `front-tower.png` (archive the old), and regenerate
   `front-roothollow` to match (port on the Girdle-sea under the
   lowest tray, pillars not wall).
2. Rewrite prompts and regenerate: `plate-01`, `plate-02`,
   `plate-30`, `plate-41`, `plate-19a`, `plate-38a` (open shelf).
3. **Audit all remaining plates** against the new canon (no iron
   walls, no masonry towers, no low ceilings over open country, no
   buildings in 100-mile wide shots); regenerate failures. Archive
   every replaced PNG to `art/_retired/`.
4. plates.tsv stays the single source of truth for prompts.

## Phase 4 — Floor files (full re-grounding, 100 files)

1. Assignment table first (one commit, reviewable): floor → Sky /
   Veil / Land (Rimlands width, Deep Middle contents) / Gates (rim,
   inland, deep-middle — 10-15 terror floors) / Strings (sparse).
   Constraints: no height-tier correlation; heavy veils on the
   dark-mooded floors (fungal, pale-court = Undershadows); boss
   floors cathedral; Made floors round; existing landscapes stay
   (the lens shapes fill, not scenery).
2. Four subagents × 25 floors: add the 5-line card; a geography
   sentence in "The land"; settlements to the rim by default — any
   inland settlement moves OR earns its one-sentence exception
   (mining town, Undershadow folk, shrine on the central sea);
   "Under Yoke" flora tied to the veil; "When it falls" sections
   gain the veil-lift and the healing. Places of interest may be
   relocated/rewritten where the new geography demands it; monsters
   and finds stay.
3. Runs in parallel with Phase 3.

## Phase 5 — Resume editorial iterations 3-10

1. Add the new canon to `book/reviews/critics.md` under the
   Continuity Warden's brief (veil rules, ladder exterior, lid,
   lens geography, gates, healing, round Made, scram ledger).
2. Iteration 3 doubles as verification of Phase 2: the Warden greps
   for regressions; the Literary Critic judges whether the new
   material reads as native or as inserted lore; Pass B's additions
   enter the normal self-audit and can be trimmed by the panel.
3. Iterations 3-10 proceed per the charter (converging budgets,
   final edition, v1-vs-v10 reckoning).

## Phase 6 — Ship

- Commit per phase to `main` (no branches). Push at Phase 3 and
  Phase 6.
- Single PDF rebuild after iteration 10 (unchanged).
- Out of scope, future plan: game-side systems (Kindling event,
  Sunskirt zones, stay-road travel, floor-brightening on
  liberation). The game's frame is its own: it ends when the tower
  is liberated and can start again.

## Verification

- Greps: no "iron wall / cliff-face / iron face" outside fittings;
  no "too far up to see"; no structural language at Warden deaths.
- Every on-page Warden death followed by its veil-lift beat.
- Plates: full-audit checklist pass; cover promoted.
- Floor files: 100/100 carry the card; 10 spot-reads; terror floors
  match the assignment table.
- Iteration 3 panel signs off as self-audit.
