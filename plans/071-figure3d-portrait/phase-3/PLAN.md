# Phase 3 — Tripo items through level 10

## Goal
Every plain forge piece a level-10 climber can wear, plus the luck
charm, has a GLB in `figure3d/models/items/<slug>.glb`. Catalog maps
slug → file + hold path. Generator is resumable and lives in the
same folder.

## Steps
- `figure3d/tools/gen_items.py` — key from
  `research/3d-fight/3d models/.env` or `TRIPO_API_KEY`. Same Tripo
  v3 pipeline as `gen_models.py` (text-to-model + texture, no rig).
  Manifest `figure3d/models/manifest.json`.
- Prompt law from `vision/1bit-images.md`: light-to-mid textures,
  chunky readable prop, no photoreal micro-texture, single object.
- `catalog.json` written from economy (slug, slot, line, hold, file).
- Run the generator. Failed tasks keep the family fallback.

## Verification
- `catalog.json` lists all 67 level≤10 plain forge slugs +
  `luck_charm`.
- Each row has a `file` that exists or `fallback` to a family mesh
  that exists.
- Balance / credit log in the manifest.

## Rollback
Delete `models/items/` except the three family copies. Catalog still
points at fallbacks.

## Execution status
2026-08-24 — Complete in the working tree. The resumable generator, manifest,
catalog, eight family fallbacks, and 68 generated level-10-or-lower item
meshes are present. The manifest records completed generation and texture
tasks; every catalog item resolves to its own GLB or a supplied fallback.
