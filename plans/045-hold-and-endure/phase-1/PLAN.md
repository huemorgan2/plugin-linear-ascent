# Phase 1 — remove the shard scan

## Goal

No fight card offers "Ask the shard to scan it"; `scout_optics` is gone
from the Medlab; no XP sink named "scan" survives in code, tips, or
prose. The free `[i]` dossier is the only (and sufficient) enemy read.
Measurable: `grep -ri "scout\|scan" plugin_linear_ascent` returns only
the unrelated `frozen_scout` monster and non-mechanic prose left on
purpose (intro lore "It will scout ahead of you").

## Steps

1. `engine/combat.py` — delete the option block at ~608–613 (keep line
   607 `opts += _relic_options(p)`) and the `if option_id == "scout":`
   handler at ~1701–1727.
2. `economy.py` — delete `scan_xp_cost` (~85–87) and the
   `scout_optics` ShopItem (~1739–1740); edit the two prose comments
   listing "scans" among XP sinks (~68, ~636).
3. `engine/core.py` — delete the `elif slug == "scout_optics":` buy
   branch (~1663–1665). Leave intro lore at ~723.
4. `engine/state.py` — drop `"scout_charges"` from the sidekick dict
   (~66); fix the comment at ~179.
5. `engine/tips.py` — delete `_TIPS["scout"]` (~230) and
   `_ITEM_TIPS["scout_optics"]` (~548); rewrite the medlab sentence
   (~47–48).
6. `icons.py` — delete the `scout_optics` grid (~341–359).
7. Prose: `render.py:595` `_TIP_XP`, `plugin.py:93` `_SHARED_RULES`,
   `social.py:285` and the comment at ~1591.
8. Tests: delete `test_engine.py::test_scan_prefers_charges_then_falls_back_to_xp`;
   drop the `scan_xp_cost` line from `test_economy.py:111`; delete the
   two scout tests in `test_017_info_card.py` (~199–217) + docstring
   mention; delete `test_017_damage_types.py::test_scan_includes_the_profile`;
   remove `"scout"` from `STATIC_IDS` in `test_014_inventory_tooltips.py:115`.
9. Markdown scenarios: trim the scan steps from
   `tests/006-xp-economy/04-sleep-and-scan.md` (rename to sleep-only),
   `tests/017-combat-depth-003/01-info-card-dojo.md` section D,
   `tests/006-xp-economy/01-xp-meter-and-medlab.md:13`,
   `tests/014-inventory-tooltips/scenario-1-pack-and-glyphs.md:31`.

Inheritance: worldd picks the change up via `vendor_game.sh` at ship
time (never hand-edit vendor).

## Verification

- `uv run --project ../luna python -m pytest tests/test_engine.py tests/test_economy.py tests/test_017_info_card.py tests/test_017_damage_types.py tests/test_014_inventory_tooltips.py tests/test_017_characters.py`
- Grep check from Goal.
- APOTHECARY-coverage tests (`test_017_characters.py:195`,
  `test_014_inventory_tooltips.py:152`) pass — proving item, icon and
  tip were removed together.

## Rollback

`git revert` the phase commit. No data migration in either direction —
stale `scout_charges` keys in saves are inert and re-created (at 0) by
`new_player` if the revert restores the field.

## Execution status

**Done** — commit `31fa497` (2026-08-09). Scout option + handler out of
combat.py; `scan_xp_cost`/`scout_optics` out of economy.py; medlab buy
branch, sidekick `scout_charges`, tips, and the 16×16 icon removed;
prose scans→mending in economy/plugin/social. 5 test files trimmed,
4 scenario .mds rewritten. Targeted tests green at commit time; full
suite 987 passed on the merged tree (see plan-level status).
Production dojo 2026-08-10: fight card rows
`['close_in','stand','run','shield_wall']`, medlab shelf without
Scout optics, string `scout` absent from every payload probed.
