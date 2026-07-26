# 009 — Game pane: move the interface out of the chat

Directive (2026-07-26): the game UI leaves the chat. A "Linear Ascent"
entry appears in Luna's left side menu; entering it shows the current
HTML render in the middle pane. Clicking an option swaps the next scene
in place — the *same exact render code we have now*, just not in chat.
Every option click still sends the agent a message with the new state,
under the same standing instruction: interfere only when you have
something important to say. Chatting with the agent stays in the chat;
seeing the interface is the middle pane.

The pane gets a top tab bar — same monospace font — with three tabs:
**GAME · SCORE · COMMUNITY**. This plan ships GAME and the tab
scaffolding; SCORE and COMMUNITY content is plan 010.

## How it plugs in (no shell rewrite)

Luna already supports exactly this pattern: a plugin declares
`SidebarSection` in its manifest and the shell renders
`/api/p/<plugin>/<path>` in an iframe in the middle pane
(`luna/ui/src/views/Shell.tsx` `PluginIframe`, ~521–587), passing the
auth token via `postMessage({type:'luna-auth', token})`. Marketplace
and Dojo Bridge already use it. So the work is almost entirely
plugin-side.

## 1. Sidebar section

In `plugin.py` `PluginManifest`, add:

    sidebar_sections=[
        SidebarSection(id="linear-ascent", label="Linear Ascent",
                       icon="swords", sort_order=45, path="ui/"),
    ]

Luna-side: add `swords` (lucide `Swords`) to `ICON_MAP` in
`luna/ui/src/lib/sectionIcons.tsx` (currently 9 icons; unknown names
fall back to FileText). Mobile needs nothing — `BottomNav.tsx` already
includes the first two plugin sections automatically.

## 2. Pane page — `GET /api/p/plugin-linear-ascent/ui/`

One self-contained HTML app served from `routes.py` (same pattern as
the existing settings page). No build step, no framework — vanilla JS,
the exact monospace stack and dark-panel CSS from `render.py`
(`ui-monospace, "SF Mono", Menlo, Consolas…`, `#11151f`, sharp
corners, `█░` meters).

Layout:

    ┌──────────────────────────────────────┐
    │  GAME   SCORE   COMMUNITY            │   ← tab bar, monospace,
    ├──────────────────────────────────────┤     active tab inverted
    │                                      │
    │  (scene panel — identical markup     │
    │   to today's chat card)              │
    │                                      │
    └──────────────────────────────────────┘

Boot sequence: page loads → waits for `luna-auth` postMessage →
stores token → fetches the current scene → renders. SCORE and
COMMUNITY tabs render a placeholder panel ("The scorekeeper is still
sharpening his quill") until plan 010.

## 3. Same render code, new host

Refactor `render.py` so the scene panel is produced once and used by
both hosts:

- `render_scene_fragment(scene) -> str` — the panel `<div>` (banner,
  eyebrow/headline/support/body, `[n]` options, meters rail,
  typewriter script). This is a mechanical extraction of what
  `render_scene` builds today; zero visual change.
- `render_scene(scene)` (legacy chat card) = fragment + card document
  shell + `luna:card:action` bridge script. Kept only so any old cards
  already sitting in chat history still render.
- The pane wraps the same fragment, but its option clicks call
  `fetch('/api/p/plugin-linear-ascent/act', {Authorization: Bearer})`
  directly and swap the returned fragment in place — no card bridge,
  no new chat message.

`POST /act` gains a `mode: "pane"` flag (or an `Accept` variant) and
returns `{scene, html_fragment}` so the pane swaps in place. Keep the
typewriter + option-key UX identical.

## 4. Chat retirement

- `_deliver` in `plugin.py` stops calling `post_chat_card`. The
  `ascent_scene` / `ascent_choose` tools keep working (the agent can
  still act for the player on request) but return **compact text
  state** for the model plus a one-line pointer the agent can relay:
  "the board is live in your Linear Ascent pane."
- Old cards in chat history: their clicks still hit `/act` and still
  mutate state — the result simply appears in the pane, not as a new
  card. Acceptable; the card's existing 6s fallback line covers
  confusion.
- Tool descriptions (`_SHARED_RULES`) get one added sentence: the
  interface lives in the sidebar pane; never paste scene HTML into
  chat.

## 5. Agent gets every state change — and stays quiet

Today `routes._notify_agent` only nudges on death/boss (moment) and
present/letter/loot/news (awareness); grind acts send nothing. New
behavior — **every** `/act` notifies the agent:

| Event class | Channel | Effect |
|---|---|---|
| death, boss, level-up, floor clear | `moment` | agent takes a turn, with the existing silence invite ("react only if genuinely worth a word; otherwise reply with nothing at all") |
| everything else | `awareness` | recorded in history, **no model turn** |

The awareness payload is a compact state line, not HTML:
`floor 3 · HP 42/60 · ◈118 · fought marsh wolf (tough) — won, +14 gold · at: fields`.
This is exactly "the agent gets a message with the new state, with the
same instructions to interfere only when it matters": awareness rows
give it full context whenever it *does* speak, and moments remain the
only thing that spends a model turn — one turn per click would burn
tokens on grind for silence.

Voice rules (`_VOICE_RULES` / `_CARD_RULES`) are unchanged.

## 6. Pane freshness

State can change without a pane click (agent acts via `ascent_choose`,
world events). Cheap approach, no websockets:

- refetch the scene whenever the pane tab regains visibility
  (`visibilitychange`);
- poll `GET /scene/peek` (new tiny route returning `{scene_id}`) every
  15s while visible; refetch the fragment only when the id changed.

## Execution order

1. `render.py` fragment extraction + snapshot test (fragment identical
   to the panel inside today's card output).
2. `/ui/` route + tab bar + auth handshake + scene fetch/act/swap.
3. Manifest `sidebar_sections` + `ICON_MAP` addition (luna repo).
4. `/act` pane mode, `_notify_agent` on every act, `_deliver` chat
   retirement, tool text updates.
5. `/scene/peek` + freshness wiring.

## Acceptance (dojo, real browser)

- Left menu shows Linear Ascent; entering it renders the current scene
  in the middle pane with the tab bar; chat panel stays alongside.
- Clicking `[2]` swaps the next scene in place; **no new chat
  messages appear**; the click round-trip feels like today's card.
- Kill a grind monster → agent says nothing; die → agent reacts with
  one short line (moment path intact).
- Ask the agent "what just happened" after a few silent acts → it
  answers accurately from awareness rows.
- Chat-driven play still works: tell the agent "take option 1" →
  state changes → pane updates within one poll cycle.
- Mobile viewport: section reachable from BottomNav, pane fills the
  screen, tabs tappable.
