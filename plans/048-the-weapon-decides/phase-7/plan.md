# Phase 7 — content retag + mechanics page

Goal: content speaks types natively; the designer's ledger shows
the new game. Legacy trait bridge dies.

## Tests first (red)

1. T7 schema part: content linter accepts only
   fly/armoured/magic_resist/plain (+bulwark ▣); legacy traits
   (armor_*, resist_*, flying, slow, fast) REJECTED.
2. Census test: every floor 1–10 spawns all three signs in weak
   specimens (the classroom law, N8).

## Work

1. `phase-7/retag.py`: map 425 monsters' YAML traits via
   type_from_traits + hand rules (speed traits fold into type);
   banded diff review (floors 1–10 by hand); commit the YAML.
2. `content/schema.py` + linter flip; delete the
   `type_from_traits` runtime bridge from creature_stats (YAML is
   native now; the function stays for doc migration tests only).
3. worldd `tools/gen_mechanics.py`: reference players per
   path×rank (rank 0/5/10 columns), TRAINING tab (cost table,
   miss/floor curves), sim class dropdown → path + rank inputs;
   sign glyphs + HITS kept from 047 work; regen mechanics-data;
   cache-bust both .js references.

## Green =

T7 complete, census, suite; mechanics page renders locally
(worldd venv, spot-check /mechanics).
Commit(s): plugin `048 phase 7: content retagged to types`,
worldd `mechanics: path×rank ledger + TRAINING tab`.

## Learnings applied (from phase 4)

- Mechanics page + TRAINING tab copy speaks PATH words (blade/bow/
  staff): the engine's calling line is race + path ("elf bow"), and
  engine-rendered text may not contain warrior/archer/sorcerer/class
  (test_rendered_text_is_class_free). Slugs/ids keep the old line
  names ("warrior" line, job kind "class") — wire-compat, invisible.
- retag.py: follow sweep_tests.py's pattern — assert-counted
  replaces, atomic per file, script kept in the phase folder.

## Learnings applied (from phase 5)

- **Restore the ≥2 pool rule in BOTH places** once the retag gives
  every path its second full-damage target per floor: the schema
  lint (`_class_pool_errors`, currently ≥1 with a 048 note) AND the
  measured 008 gate in test_017_damage_types (`farmable >= 1` with
  the same note). Ten floors sat at exactly one — the retag must
  fill them deliberately, not incidentally.
- **fast/slow traits are dead air already** (speed rides the type
  since phase 5) — the retag deletes them from YAML with zero
  behavior change; only the linter flip makes them illegal.
- **Retag flips sim premises**: phase-5 test surgery moved kite/
  slow tests to wrapped_husk and fast tests to glare_moth because
  speed now rides the type. After the retag, re-grep tests for
  encounter ids whose type changed — a premise can die silently
  (lane_boar stopped being slow and the test still "passed" red).
- **Bulwark HP rides ×2.2** (BULWARK_HP_MULT) and is orthogonal to
  type — roster/census tooling must not count bulwark as a sign.

## Learnings applied (from phase 6)

- **The mechanics page reads the bake's split**: income tables show
  gold_per_kill (bounty IN, floors ≤10 marked "young-tower bounty");
  price/fee tables (levelup, hone, tiers) anchor on
  base_gold_per_kill/daily_income — un-bountied. Don't render one
  number for both.
- **TRAINING tab numbers**: train_xp fits-the-bar law (cost ≤
  xp_need at the rank's natural level) is worth a printed column —
  rank 10 at L9, MASTERY at L12, CARRY3 at L8.
- **Retag answerability gate exists already**: T5's
  test_the_intended_first_ten_floors asserts every floor-1–10
  monster has a ×1.0 answer among {blade,bow,staff} — the retag
  can't strand a floor without breaking it; run it early in the
  retag loop.
- **New locations need a row in core.py's generic back-handler**
  (before location dispatch) — the School was trapped until phase 6;
  check any scene the mechanics/census work adds.
