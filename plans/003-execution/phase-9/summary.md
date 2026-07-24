# Phase 9 — execution summary (our end: plugin + worldd)

Status: **our end shipped** (plugin 0.3.0 published, worldd redeployed).
Luna core (plan 056: card kind, auto-height listener, `post_chat_card`,
empty-bubble suppression) is being implemented by Luna in parallel — the
plugin is ready for it the moment it lands, via feature detection.

## Done (Tracks B + C of the plan)

- **B1 payload fork**: `build_payload(scene, card_posted)` at module level
  (testable), `_deliver()` in the tools tries
  `getattr(ctx, "post_chat_card", None)` → posts the rendered card as its
  own chat message and returns text-only tool results; any absence/failure
  falls back to the 0.2.x inline `embed_iframe` payload. Verified in the
  browser on stock Luna: fallback path intact.
- **B2 height reporting**: every card document now posts
  `{type:"luna:embed:height", height}` to the parent on load + resize
  (ResizeObserver). Dormant until Luna's listener ships; confirmed present
  in live chat srcdoc.
- **C1+C2 sidekick voice** (revised calibration — flavor allowed, silence
  only for repetitive beats): `_VOICE_RULES` with 4 contrastive examples,
  composed into `_EMBED_RULES` (fallback) and `_CARD_RULES` (card mode);
  compact voice reminder added to `ascent_scene`/`ascent_choose`
  descriptions. Live check: agent replied to a scene with
  "◆ Teeth before steel, Torvald. The tower's waiting." — flavor beat, no
  card narration.
- **Shipped alongside** (from the parallel art session, tests green):
  intro "story so far" scene (`stage: "intro"` → creation), title banner
  (320x200), flexible banner sizes in the renderer.
- **Tests**: plugin 42/42 (new `test_payload.py`: card/fallback payloads,
  voice rules presence, height script), worldd 13/13 after vendor sync.
- **Deployed**: worldd `dep-d9hj3hsvikkc73acijag` live on Render (health
  ok); `plugin-linear-ascent-0.3.0.zip` published to the official
  marketplace, index sha256 verified.

## Remaining (blocked on Luna's 056)

- Standalone bubble-less cards + no-scroll auto-height in the chat UI.
- Empty-reply suppression (agent silence currently still shows a bubble).
- Once 056 lands: restart QA Luna, run the full dojo playtest from the
  plan (cards standalone, reload persistence, silence with no artifact),
  then re-verify the stock fallback by hiding the capability.

No worldd schema/API changes in this phase; phase-8 join flow untouched
(regression-checked: plugin loads, settings routes mount, prod health ok).
