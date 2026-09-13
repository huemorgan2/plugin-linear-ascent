# Collection, group combat and gathering

## Problem and evidence

The approved redesign is implemented on `change_everything`, coordinated by the parent repository's `plans/015-weapon-combat-progression/PLAN.md` and its phase folders. The integrated actual-engine baseline reaches floor4 at the population median in30 days and only four of24 players reach floor8. The published wiki already contains proposed grades, weapon families and425 creature identities, but the live resolver still uses individual old encounters, paid weapon slots and XP clipping.

## Root cause and mitigation

Research content and the game have separate rules. Source/plugin and published vendor also differ in map art, marker dots and version. Preserve original workspace changes in a separate branch and use this isolated worktree. No production mitigation or conversion has occurred.

## Phases

1. Align this package with published vendor0.112.0 without changing gameplay. Copy only the audited render.py, version.py and eight floor3–10 map files from the parent vendor. Record matching package hashes and baseline tests. Rollback: revert this alignment commit; parent rollback is `git revert -m 1 1f45fb1` before candidate writes.
2. Add engine-owned catalog, versioned collection instances, exactly three deck cells, XP reserve, migration preview/receipts and expedition/group state. Keep new enrollment behind `ASCENT_RULESET=collection-v1`; an already converted save must stay readable. Remove only School slot sales. Verify ownership, duplicate IDs, JSON round trips, legacy encounter completion, local/HTTP parity and repeated requests. Rollback: stop enrollment, settle active candidate documents, retain readers; never restore old snapshots over new earnings.
3. Implement first-ten-floor group combat and two floor3 gathering sites, Forge, collection/profile/opening and game-style rendered scenes. Verify actual local engine, worldd, browser and Luna before widening.
4. Expand all64 grade drawings,425 authored creatures, statuses/arrows and eight themed gathering sites; generate wiki from engine definitions.
5. Exercise real-engine heuristic/random/investing/gathering players, serial/parallel replay and held-out strategy search. Tune measured costs/rewards gradually; report fastest and population median with censored players retained.
6. Integrate immediate concurrent warden damage and continuous healing through worldd; test finite energy, race/retry settlement and floor100 closure.
7. Verify migration/recovery and both clients through full coded suites and real multi-turn browser/Luna scenarios.
8. Pin vendor/source, then perform the parent plan's coherent release and post-release verification. No partial candidate release.

## Verification and operational notes

Use the parent phase plans for exact commands and evidence locations. Run targeted tests then the complete relevant suite. Plugin commits precede the parent's vendor/pointer commit; secret-pattern scan before every commit. Each phase requires browser evidence under the parent dojo results. Do not report missing checks as passed. Parent S01–S15 cover the player-facing scenarios, including resistance popups and gather/ambush/extract.

## Execution status

Phase1 in progress. Planning committed before source alignment. Phases2–8 not started.
