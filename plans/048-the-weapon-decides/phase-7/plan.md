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
