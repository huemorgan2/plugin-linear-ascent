# Phase 9 — The game speaks for itself: standalone scene cards + a quiet sidekick

Status: PLANNED (not started)

## What's wrong today (user-reported, verified in code)

1. **Scene cards scroll inside the message.** `PluginEmbed` renders the
   embed iframe with `minHeight: 300, maxHeight: 500` and no auto-resize
   (`luna/ui/src/views/ChatPanel.tsx:114-122`), so any card taller than
   500px gets an inner scrollbar.
2. **The game appears to be authored by the agent.** The embed is attached
   to the agent's assistant bubble (`ChatPanel.tsx:1657`, inside the
   `max-w-[80%]` bubble div at `:1616`), with the agent avatar next to it.
   The world should be its own actor: a scene is a *step in the chat*,
   which both the player and the agent then react to.
3. **The agent narrates the obvious.** Tool results instruct "add at most
   one short line", but the agent still repeats what the card shows
   ("here's a dragon, we can attack, stray, or run"). A sidekick should
   speak only when it adds signal — and shut up otherwise.

## Target experience

- Player acts → a **scene card appears in the timeline as its own block**:
  full width of the message column, no avatar, no bubble chrome, no inner
  scroll. It reads as "the world happened", not "the agent said".
- The agent *may* follow with **at most one short in-character sentence**,
  and only when it carries real information: a tactical read, a warning, a
  synergy the UI can't show ("It's wounded and we hit hard — one strike
  ends it."). If the card is self-explanatory, the agent stays **silent**
  and no empty bubble appears.
- Nothing breaks for stock-Luna installs of plugin 0.2.0: the plugin
  feature-detects the new host capability and falls back to today's
  in-bubble embed.

## Architecture decision

The plugin posts the scene card as its **own message row** (not part of the
tool result), and the tool result returned to the model carries only
`scene_text` + behavior instructions. Grounding — all mechanisms exist:

- Messages carry a JSONB `extra` column, and `_msg_to_payload` already
  promotes `extra` keys (`embed_iframe`, `embed_html`, `source`) into the
  API payload (`luna/plugins/plugin_api/app.py` — 008.994 doc, §"How it
  works today").
- `send_chat_message` (`luna/plugins/plugin_webui/chat_tools.py:85`) is
  prior art for a plugin persisting a `MessageRow(role="assistant")` and
  emitting `message.created`, which the UI live-appends via the global SSE
  (`app.py:297`, `ui/src/lib/api.ts:807`).
- The muted-message proposal (`luna/plans/008.994-muted-message/
  suggestion.md`) blesses exactly this pattern: `extra.kind` + promoted
  fields + a render branch keyed on `kind`.

## Track A — Luna core (our fork, `luna` submodule)

### A1. `kind: "card"` message rendering

- Persisted shape: `MessageRow(role="assistant", content="",
  extra={"kind": "card", "embed_iframe": <html>, "source": "plugin-linear-ascent"})`.
- Promote `kind` in `_msg_to_payload` and in the SSE `message.created`
  payload; add `kind?: string` to the TS `Message` type
  (`ui/src/lib/api.ts:149` region).
- In the message renderer (`ChatPanel.tsx` around `:1590-1677`): when
  `message.kind === "card"`, render **only** the embed — full message-column
  width, no avatar, no bubble classes, subtle rounded border. All other
  messages render exactly as today.
- History translation: a card row contributes **nothing** to model history
  (its `content` is empty; the scene reached the model through the tool
  result). Verify `_row_to_luna` skips empty-content assistant rows or add
  that skip.

### A2. Embed auto-height (kills the inner scroll)

- Contract: embed HTML may post
  `window.parent.postMessage({type: "luna:embed:height", height: N}, "*")`
  on load and on resize.
- `PluginEmbed` (`ChatPanel.tsx:91`): give each iframe a nonce (query the
  event's `source` against the iframe's `contentWindow`), listen for the
  message, set iframe height to `min(N, 900)`; keep `maxHeight: 500`
  only as the fallback when no message arrives. Applies to card-kind AND
  legacy in-bubble embeds — old plugins are unaffected, upgraded ones stop
  scrolling everywhere.
- `sandbox="allow-scripts"` already permits postMessage; no sandbox change.

### A3. SDK: `ctx.post_chat_card(html, *, conversation_id=None) -> str | None`

- New `PluginContext` method in `luna/luna/plugins/context.py`, exported
  contract note in `luna_sdk`. Implementation lifts
  `chat_tools._send_chat_message`'s row-persist + `message.created` emit,
  with `extra` as in A1.
- Conversation resolution: the current turn's conversation from the run
  context if set, else latest-active (same fallback `_resolve_conversation`
  uses). Returns message id, or `None` if no conversation exists (plugin
  then falls back to inline embed).

### A4. Silence without artifacts

- UI: skip rendering assistant messages whose `content` is empty/whitespace
  and that have no embed and are not pending (guard in the message map in
  `ChatPanel.tsx`). This makes "the agent chose not to comment" invisible
  instead of an empty bubble.
- Verify the turn pipeline tolerates an empty final assistant text (no
  crash on persist; empty row is fine since A1/A4 hide it).

### A5. Fork hygiene

- All four changes are additive and upstreamable (they deliberately follow
  the 008.994 pattern). Keep them in one commit series on our `luna` fork
  branch so they can be PR'd upstream; document in the commit message that
  stock Luna renders these plugins via the fallback path.

## Track B — Plugin (0.3.0)

### B1. Post cards, return text

- In `plugin.py` `_payload`/tool bodies: if `ctx.post_chat_card` exists
  (feature-detect with `getattr`), call it with the rendered card HTML and
  return to the model **only** `{"scene_text": ..., "instructions": ...}`.
- Else (stock Luna): return today's `{scene_text, embed_iframe,
  instructions}` payload unchanged — 0.2.0 behavior, zero regression.

### B2. Height reporting in the card

- `render.py`: append a tiny script to every card document:
  on `load`/`ResizeObserver`, post `luna:embed:height` with
  `document.documentElement.scrollHeight`. Harmless where nobody listens.
- Remove internal fixed-height assumptions from the card CSS if any.

### B3. Version + manifest

- `version.py` → 0.3.0, `luna-plugin.toml` in sync. No tool schema changes,
  no worldd changes (this phase is purely presentation + voice).

## Track C — Sidekick voice (the biggest UX win, smallest diff)

### C1. Rewrite the behavior contract (`_SHARED_RULES` / `_EMBED_RULES`)

Revised 2026-07-24 — the sin is *redundancy*, not speech. The shardmind is
a character; muting it would flatten the game. New rules, roughly:

> The scene card is already visible to the player — never repeat, summarize,
> or re-list anything on it, and never explain the options; the player can
> read. You are the player's shardmind sidekick, not a narrator. After a
> scene, say AT MOST one short in-character sentence (two only for
> boss/death moments). A short line is usually welcome — either a tactical
> read when there is real signal ("Wounded and slow — one strike ends it";
> "We can't survive two hits at 4 HP — the lodge first") or a flavor beat
> in your own voice when there isn't ("That smell again. Wardens."). Go
> silent (empty reply) during repetitive beats — mid-fight grind, the third
> encounter in a row, routine shopping — where any comment is noise. Always
> have something for the big beats: a new floor, a boss, near-death, a
> level-up, rare loot.

- Also in `ascent_choose`'s description so the behavior binds at tool level.
- Keep the "engine decides everything / map words to options" clauses.

### C2. Calibration examples in the instructions

Include ~4 miniature examples (good tactical line / good flavor line / good
silence / bad narration) — models follow contrastive examples far better
than adjectives.

## Execution order & verification

1. **A2 + A1** in the Luna fork; rebuild the UI (check how `luna serve`
   serves it: `ui/` Vite build → confirm build command and whether dist is
   committed), restart QA Luna on 8777.
2. **A3 + A4**, then **B1 + B2 + B3** — play in the browser: cards must
   appear as standalone timeline blocks with no inner scroll; kill the
   worldd connection to confirm the fallback path still renders inline.
3. **C1 + C2**, then a dojo-style multi-turn playtest (real browser, real
   conversation — per `.cursor/skills/agent-live-walkthrough`):
   - creation → town → 3 fights → dragon-class encounter;
   - assert: every agent bubble ≤ 1 short sentence (≤ 2 on boss/death
     beats); at least one repetitive scene gets pure silence (no bubble at
     all); big beats always get a line; no bubble re-lists card options or
     re-describes the scene;
   - assert cards survive a page reload (persisted rows, not stream-only).
4. Unit tests: plugin suite for the payload fork (card-post vs fallback);
   Luna-side test for `post_chat_card` persistence + `kind` promotion.
5. Publish 0.3.0 to the marketplace; commit Luna fork changes; update
   phase summary. **Do not touch** worldd, enroll/vault/settings (phase 8)
   — regression-check the join flow once after the Luna rebuild.

## Risks / open points

- **Stock-Luna users** (installed from the marketplace) don't get standalone
  cards until our Luna changes land upstream — they keep the current
  in-bubble rendering via B1's fallback. Acceptable; note in README.
- **Conversation targeting**: if a scene tool ever runs outside a chat turn
  (scheduler), `post_chat_card` must not post into the wrong conversation —
  covered by resolving from the run context first, falling back to inline
  embed when unresolvable.
- **Model silence compliance** varies by model; C2's examples mitigate. If
  a model still can't produce empty replies, fall back to instructing a
  bare "◆" and add it to A4's suppression list.
- **History duplication**: scene context must reach the model exactly once
  (tool result). Card rows stay out of history (A1) or the model would see
  every scene twice.
