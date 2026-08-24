# Phase 5 — scale proof, dojo, deploy

## Goal

The budgets hold with 10,000 playing players in the local DB, a real
browser confirms the felt snappiness, and (on explicit request) production
receives the same changes with post-deploy verification.

## Steps

1. **Seed script** `worldd/tools/seed_scale.py`: inserts N synthetic
   playing players (varied floors, levels, guilds, sleepers, lodge flags;
   realistic ~9 KB docs) under tenant `seed` with a `player LIKE 'seed_%'`
   convention. Runs only against a DB whose URL contains `localhost` /
   `127.0.0.1` (hard guard — never production). Cleanup =
   `DELETE FROM ascent_players WHERE tenant='seed'` (synthetic rows only;
   the guard plus tenant scoping keeps real player data untouchable).
2. **Benchmark** `worldd/tools/bench_act.py`: signs up a probe account,
   fires 100 mixed acts (menu, gate ride, fight rounds, guildhall,
   square), prints the plan's budget table with measured p50/p95 latency,
   payload sizes, queries/act. Run at 891 (today's data) and at 10,000
   seeded.
3. **Dojo scenario** `tests/078-zero-latency-clicks/01-snappy-clicks.md`
   (in this repo, beside the plan): real browser, real account; walks
   square → gate → floor → fight → shop → profile; measures click-to-paint
   via `performance` marks around each act fetch; asserts < 300 ms per
   click (lift rides excepted — the 5.2 s overlay is intentional), art
   served from cache on repeat views, zero console/network errors. Results
   folder under `dojo/results/NNNN-078-…/` with the numbers table.
4. **Deploy — only when Roy asks.** House shape: secret-scan, commit,
   `worldd/tools/deploy.sh` (version-mismatch hard-fail), poll live.
   Post-deploy: migration 022 applied (columns visible in
   `information_schema`), `/static/laart/...` 200 with immutable header,
   one real production click sequence timed < 500 ms each, `/health`
   clean, and the bench script's read-only subset against production
   numbers recorded here.

## Verification

Steps 2–4 are the proof: bench tables inside budget at both scales, dojo
PASS with screenshots and timings, production checks recorded in this
file's execution status.

## Rollback

- Seeded rows: the cleanup DELETE above (tenant-scoped, synthetic only).
- Deploy: redeploy the previous version via `deploy.sh`; migration 022 is
  additive and stays (harmless under old code, which reads `doc`
  directly) — no schema down-migration needed or wanted.
