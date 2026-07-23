# Game execution — Phase 6: Content build-out & banners

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 6 · [002-full-game](../../002-full-game/plan.md) workstreams C+D.

## Goal

All 100 floors authored and lint-clean; the tier banner set complete.

## Deliverables

- **Tier packs 2–10** per the 002 pipeline: each tier = biome flavor pack (world.md §1 table) + ~4 mob families + regular-warden flavor + 1 milestone Warden (economy §5 names/stats) + ~2 signature items. Floor YAML carries ONLY names/prose/flavor/deviations — every number computed by the loader from economy formulas (balance-safe by construction).
- Authoring: LLM-drafted (this agent) directly as schema-valid YAML, tier by tier, voice per story.md; banned out-of-world vocabulary.
- **Lint gate** (`content/lint.py`, runs in CI/tests): schema validation, name collisions, prose length caps, vocabulary lint, economy fields absent, option-id stability.
- **Banners**: ~18 new via `tools/generate_banners.py` (Gemini key from `../luna-plugins/luna/.env`): per tier 2–10 one zone banner + one milestone-Warden banner. Add SCENES entries per pixel_art.md composition rules; review each as tinted preview; regenerate until it reads.
- Rendered-card human pass: read each tier's gate-town + one encounter + warden as cards in the browser (the tone gate the lint can't do).

## Exit gate

`content/lint.py` green for all 100 floors; every tier's banner set generated and previewed; spot-checked tiers render in chat with correct computed numbers (verify floor 25/55/95 monster stats against economy.md §4 table).
