"""Plugin HTTP surface.

Settings tab (007: the world is mandatory): connection status plus a
manual "connect now" for when auto-enroll hasn't landed yet. The
settings iframe calls these with the host's bearer token. Credentials
live in Luna's vault; runtime.state switches the game backend live.

Card actions (057): POST /act is the direct game loop for interactive
cards. The chat shell's card-action bridge calls it when the player
clicks an option button — pure engine, no model in the path. The route
posts the next scene as its own card and, on big beats only, nudges the
agent to react in character (a "moment"), so the sidekick responds to
the game like the player does instead of driving it. Ordinary acts are
completely silent (017): the agent re-syncs with ascent_scene when the
player talks to it.
"""

from __future__ import annotations

import asyncio
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from luna_sdk import PluginContext, get_current_user

from . import runtime

_ctx: PluginContext | None = None

# Which event kinds warrant an agent nudge. A "moment" runs a genuine
# reaction turn (the sidekick speaks on its own). 017: ordinary acts do not
# notify AT ALL — no awareness rows, no periodic digest (Roy, 2026-07-27:
# "lose the 5 min digest completely"). The agent re-syncs itself with
# ascent_scene when the player talks to it (_SHARED_RULES cover this).
# awaits_text still notifies immediately: the agent must know to pass the
# player's typed reply through.
_MOMENT_KINDS = {"death", "boss", "matchup"}


class JoinIn(BaseModel):
    # module level, not inside register_routes: with postponed annotations
    # FastAPI can't resolve closure-local models and mistakes the body for
    # a query parameter.
    world_url: str = Field(default="", max_length=200)
    name_hint: str = Field(default="", max_length=32)


class FactionNameIn(BaseModel):
    name: str = Field(min_length=1, max_length=24)


class FactionTargetIn(BaseModel):
    tenant: str = Field(min_length=1, max_length=64)
    player: str = Field(min_length=1, max_length=128)


class ActIn(BaseModel):
    option: str = Field(default="", max_length=64)
    text: str = Field(default="", max_length=200)
    # 009: the game pane acts directly — no chat card gets posted back.
    mode: str = Field(default="", max_length=16)
    scene_id: str = Field(default="", max_length=64)
    # Injected by the chat shell's bridge, not by the card itself.
    conversation_id: str | None = Field(default=None, max_length=64)
    message_id: str | None = Field(default=None, max_length=64)


def _state_line(scene) -> str:
    """One compact line of game state for awareness rows — never HTML."""
    bits = [scene.eyebrow, scene.headline]
    m = scene.meters
    if m:
        bits.append(f"HP {m.hp}/{m.hp_max} · ⚡{m.energy}/{m.energy_max} "
                    f"· XP {m.xp}/{m.xp_need} · LV {m.level} · ◈{m.gold}")
    if scene.options:
        bits.append("options: " + ", ".join(o.label for o in scene.options))
    return " · ".join(b for b in bits if b)


def _notify_agent(scene, conversation_id: str | None,
                  player: str = "") -> None:
    """Fire-and-forget sidekick nudge (017). Big beats (death, boss) get
    an instant moment. awaits_text gets an instant awareness row (the
    agent must know to pass the typed reply through). Everything else is
    completely silent — the agent re-syncs via ascent_scene when spoken
    to. Never blocks the click response — the pane must feel like code."""
    kind = scene.event_kind
    send = getattr(_ctx, "send_muted_message", None) if _ctx else None
    if send is None:
        return

    if kind in _MOMENT_KINDS:
        channel = "moment"
    elif scene.awaits_text:
        channel = "awareness"
    else:
        return

    if channel == "moment":
        from .plugin import _VOICE_RULES
        if kind == "matchup":
            # 007: first fight vs a type that hard-counters the class.
            # 001 retro: the scene text names the CURRENT enemy and
            # floor — react to THAT enemy only, never a guessed one.
            frame = (
                "The player just ran into a monster type that hard-"
                "counters their build for the FIRST time — the scene "
                "below is ALREADY on their screen. You are their "
                "shardmind sidekick: give ONE short tactical read about "
                "THIS exact enemy (name it as the scene names it), or "
                "stay silent if the scene already says it all.")
        else:
            frame = (
                "The player just advanced Linear Ascent from the game "
                "pane — the scene below is ALREADY on their screen. You "
                "are their shardmind sidekick, reacting to what just "
                "happened.")
        content = frame + "\n\n" + scene.to_text() + "\n\n" + _VOICE_RULES
    else:
        content = (
            "Linear Ascent state (the player is playing in the game pane; "
            "this is for your awareness only — do not respond): "
            + _state_line(scene))
    if scene.awaits_text:
        content += (
            "\n\nIMPORTANT: the game is now waiting for the player to TYPE "
            f"something in chat — {scene.awaits_text}. If their next "
            "message plausibly is that reply, pass it straight into the "
            "game with ascent_choose text=<their exact message> — no "
            "confirmation question first; the engine validates input and "
            "refuses anything bad with a friendly note. Only skip the "
            "pass-through when the message is clearly about something "
            "else entirely.")
    title = f"Linear Ascent — {kind or 'the climb continues'}"

    async def _fire():
        try:
            await send(title, content, channel=channel,
                       conversation_id=conversation_id)
        except Exception:
            pass  # a lost whisper must never break the game loop

    asyncio.get_running_loop().create_task(_fire())


def _vault():
    vault = getattr(_ctx, "vault", None) if _ctx else None
    if vault is None:
        raise HTTPException(503, "Vault not available")
    return vault


def register_routes(app, ctx: PluginContext) -> None:
    global _ctx
    _ctx = ctx
    router = APIRouter(prefix="/api/p/plugin-linear-ascent", tags=["ascent"])

    @router.get("/status")
    async def status(user=Depends(get_current_user)) -> dict:
        s = runtime.state
        out = {
            "mode": "world" if s["remote"] else "local",
            "source": s["source"],
            "world_url": s["world_url"],
            "tenant": s["tenant"],
            "default_world_url": runtime.DEFAULT_WORLD_URL,
        }
        if s["remote"]:
            try:
                async with httpx.AsyncClient(timeout=6) as c:
                    r = await c.get(s["world_url"].rstrip("/") + "/health")
                out["world_ok"] = bool(r.json().get("ok"))
            except Exception:
                out["world_ok"] = False
        return out

    @router.post("/join")
    async def join(body: JoinIn, user=Depends(get_current_user)) -> dict:
        if runtime.state["source"] == "env":
            raise HTTPException(
                409, "World is pinned by env vars on this host; remove "
                     "LUNA_ASCENT_* from the environment first.")
        vault = _vault()
        url = (body.world_url or runtime.DEFAULT_WORLD_URL).strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise HTTPException(422, "world_url must be http(s)")

        # one stable install id per Luna installation → enroll is idempotent
        try:
            install_id = (await vault.get_credential(
                runtime.VAULT_INSTALL)).value
        except KeyError:
            install_id = uuid.uuid4().hex
            await vault.store_credential(
                runtime.VAULT_INSTALL, install_id, kind="api_key")

        hint = "".join(c for c in body.name_hint
                       if c.isalnum() or c in "-_ ")[:32]
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(url + "/v1/enroll", json={
                    "install_id": install_id, "name_hint": hint})
        except httpx.HTTPError as e:
            raise HTTPException(502, f"world unreachable: {e}")
        if r.status_code == 429:
            raise HTTPException(429, "world enrollment is rate limited; "
                                     "try again in a bit")
        if r.status_code != 200:
            raise HTTPException(502, f"world refused enrollment: {r.text[:200]}")
        d = r.json()

        await vault.store_credential(
            runtime.VAULT_URL, url, kind="api_key")
        await vault.store_credential(
            runtime.VAULT_TENANT, d["tenant"], kind="api_key")
        await vault.store_credential(
            runtime.VAULT_SECRET, d["secret"], kind="api_key")
        runtime.configure_remote(url, d["tenant"], d["secret"],
                                 source="vault")
        return {"joined": True, "tenant": d["tenant"],
                "existing": d.get("existing", False)}

    @router.post("/act")
    async def act(body: ActIn, user=Depends(get_current_user)) -> dict:
        """The game loop. 009: the pane is the primary caller — it acts
        directly and swaps the returned fragment in place; nothing is
        posted to the chat. Clicks on legacy cards still in chat history
        keep working: they mutate state and the result shows in the pane
        (their bridge gets ok + no card, and the old card locks its rows).
        Stale/unknown options are handled by the engine itself (it returns
        the current scene with a steering hint)."""
        from .render import render_scene_fragment

        key = runtime.player_key()
        scene = await runtime.act_for(key, body.option.strip(),
                                      body.text.strip())
        _notify_agent(scene, body.conversation_id, player=key)
        return {
            "ok": True,
            "scene_id": scene.scene_id,
            "event_kind": scene.event_kind,
            "headline": scene.headline,
            "fragment": render_scene_fragment(scene),
        }

    @router.post("/pane/scene")
    async def pane_scene(user=Depends(get_current_user)) -> dict:
        """Current scene for the pane — idempotent read, same fragment
        grammar as /act."""
        from .render import render_scene_fragment

        scene = await runtime.scene_for(runtime.player_key())
        return {
            "ok": True,
            "scene_id": scene.scene_id,
            "event_kind": scene.event_kind,
            "headline": scene.headline,
            "fragment": render_scene_fragment(scene),
        }

    @router.get("/pane/peek")
    async def pane_peek(user=Depends(get_current_user)) -> dict:
        """Freshness probe: the last scene id this process produced for the
        player (chat-driven acts update it too). No world round trip."""
        return {"scene_id": runtime.last_scene_id(runtime.player_key())}

    # ── 010: score & community (worldd proxies with the host's auth) ────

    def _world():
        remote = runtime.state["remote"]
        if remote is None:
            raise HTTPException(
                503, "The world signal is gone — score and factions live "
                     "in the shared world. Try again in a moment.")
        return remote

    async def _proxy(coro):
        from .backend.remote import WorldError
        try:
            return await coro
        except WorldError as e:
            msg = str(e)
            code = 400
            for c in (402, 403, 404, 409, 422, 429):
                if f"worldd {c}" in msg:
                    code = c
                    break
            raise HTTPException(code, msg.split(": ", 1)[-1][:200])
        except httpx.HTTPError:
            raise HTTPException(502, "the world isn't answering")

    @router.get("/pane/score")
    async def pane_score(user=Depends(get_current_user)) -> dict:
        return await _proxy(_world().leaderboard(runtime.player_key()))

    @router.get("/pane/community")
    async def pane_community(user=Depends(get_current_user)) -> dict:
        """The faction news board — the desk (015) hangs off it."""
        return await _proxy(_world().faction_board(runtime.player_key()))

    # ── 015: the faction desk — ledger, pages, requests, admin acts ─────

    @router.get("/pane/factions")
    async def pane_factions(q: str = "",
                            user=Depends(get_current_user)) -> dict:
        """THE LEDGER: top 10 banners; ?q= searches server-side."""
        return await _proxy(
            _world().faction_list(runtime.player_key(), q[:24]))

    @router.post("/pane/faction/detail")
    async def pane_faction_detail(body: FactionNameIn,
                                  user=Depends(get_current_user)) -> dict:
        return await _proxy(
            _world().faction_detail(runtime.player_key(), body.name))

    @router.post("/pane/faction/request")
    async def pane_faction_request(body: FactionNameIn,
                                   user=Depends(get_current_user)) -> dict:
        return await _proxy(
            _world().faction_request(runtime.player_key(), body.name))

    @router.post("/pane/faction/cancel_request")
    async def pane_faction_cancel(user=Depends(get_current_user)) -> dict:
        return await _proxy(
            _world().faction_cancel_request(runtime.player_key()))

    @router.post("/pane/faction/approve")
    async def pane_faction_approve(body: FactionTargetIn,
                                   user=Depends(get_current_user)) -> dict:
        return await _proxy(_world().faction_approve(
            runtime.player_key(), body.tenant, body.player))

    @router.post("/pane/faction/reject")
    async def pane_faction_reject(body: FactionTargetIn,
                                  user=Depends(get_current_user)) -> dict:
        return await _proxy(_world().faction_reject(
            runtime.player_key(), body.tenant, body.player))

    @router.post("/pane/faction/kick")
    async def pane_faction_kick(body: FactionTargetIn,
                                user=Depends(get_current_user)) -> dict:
        return await _proxy(_world().faction_kick(
            runtime.player_key(), body.tenant, body.player))

    @router.post("/pane/faction/promote")
    async def pane_faction_promote(body: FactionTargetIn,
                                   user=Depends(get_current_user)) -> dict:
        return await _proxy(_world().faction_promote(
            runtime.player_key(), body.tenant, body.player))

    @router.post("/pane/faction/rename")
    async def pane_faction_rename(body: FactionNameIn,
                                  user=Depends(get_current_user)) -> dict:
        return await _proxy(
            _world().faction_rename(runtime.player_key(), body.name))

    @router.post("/pane/faction/enter")
    async def pane_faction_enter(user=Depends(get_current_user)) -> dict:
        """Admin accepts the week's challenge — paid from the vault."""
        return await _proxy(_world().faction_enter(runtime.player_key()))

    @router.get("/art/factions/{slug}.png")
    async def faction_banner(slug: str):
        """Faction sigil art for the pane (white-ink 1-bit PNG, tinted
        client-side via CSS mask). Public like the pane shell itself."""
        import os as _os
        import re as _re

        from fastapi.responses import FileResponse
        if not _re.fullmatch(r"[a-z0-9_]{1,32}", slug):
            raise HTTPException(404, "no such sigil")
        path = _os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)), "content", "art",
            "banners", "factions", f"{slug}_320x112.png")
        if not _os.path.exists(path):
            raise HTTPException(404, "no such sigil")
        return FileResponse(path, media_type="image/png",
                            headers={"Cache-Control": "max-age=86400"})

    @router.get("/ui/", response_class=HTMLResponse)
    async def pane_ui():
        from .pane import render_pane
        return HTMLResponse(render_pane())

    @router.get("/ui/settings/", response_class=HTMLResponse)
    async def settings_ui():
        return HTMLResponse(_SETTINGS_HTML)

    app.include_router(router)


_SETTINGS_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  :root { color-scheme: dark; }
  body { background: #0b0e14; color: #c9d1d9; margin: 0;
         font: 14px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
         padding: 28px; max-width: 620px; }
  h1 { font-size: 16px; color: #e6edf3; margin: 0 0 4px; }
  .sub { color: #8b949e; margin-bottom: 22px; }
  .card { border: 1px solid #2d333b; border-radius: 8px; padding: 18px;
          margin-bottom: 14px; background: #10141c; }
  .row { display: flex; justify-content: space-between; margin: 4px 0; }
  .k { color: #8b949e; } .v { color: #e6edf3; }
  .ok { color: #3fb950; } .bad { color: #f85149; } .dim { color: #8b949e; }
  button { background: #238636; color: #fff; border: 0; border-radius: 6px;
           padding: 9px 18px; font: inherit; cursor: pointer; }
  button.secondary { background: #21262d; color: #c9d1d9;
                     border: 1px solid #2d333b; }
  button:disabled { opacity: .5; cursor: default; }
  input { background: #0b0e14; color: #e6edf3; border: 1px solid #2d333b;
          border-radius: 6px; padding: 8px 10px; font: inherit; width: 100%;
          box-sizing: border-box; margin: 6px 0 12px; }
  #msg { min-height: 20px; margin-top: 10px; }
  details { margin-top: 14px; } summary { cursor: pointer; color: #8b949e; }
</style></head><body>
  <h1>◆ Linear Ascent</h1>
  <div class="sub">The 100-floor Ascent — one shared world, every install
  plays in it. Connection is automatic.</div>

  <div class="card" id="status-card">Loading…</div>

  <div class="card" id="action-card" style="display:none">
    <div id="join-block">
      <div style="margin-bottom:10px">This install isn't connected yet.
      The game enrolls itself automatically on startup and on your next
      turn — or connect right now:</div>
      <label class="k">Display hint for your world name (optional)</label>
      <input id="hint" maxlength="32" placeholder="e.g. roys-luna">
      <details><summary>Advanced: custom world server</summary>
        <input id="url" placeholder="">
      </details>
      <div style="margin-top:12px">
        <button id="join">Connect to the shared world</button>
      </div>
    </div>
    <div id="msg"></div>
  </div>

<script>
const token = new URLSearchParams(location.search).get('token');
const H = {'Content-Type': 'application/json',
           ...(token ? {'Authorization': 'Bearer ' + token} : {})};
const api = p => '/api/p/plugin-linear-ascent' + p;
const $ = id => document.getElementById(id);

async function refresh() {
  const r = await fetch(api('/status'), {headers: H});
  const d = await r.json();
  const world = d.mode === 'world';
  $('status-card').innerHTML =
    '<div class="row"><span class="k">Mode</span><span class="v">' +
      (world ? 'Shared world' : 'Solo (local)') + '</span></div>' +
    (world ? '<div class="row"><span class="k">World</span><span class="v">' +
      d.world_url + '</span></div>' +
    '<div class="row"><span class="k">Your world id</span><span class="v">' +
      d.tenant + '</span></div>' +
    '<div class="row"><span class="k">World health</span>' +
      (d.world_ok ? '<span class="ok">● online</span>'
                  : '<span class="bad">● unreachable</span>') + '</div>' +
    (d.source === 'env' ? '<div class="row"><span class="k">Config</span>' +
      '<span class="dim">pinned by host env vars</span></div>' : '')
    : '<div class="bad">Not connected — the game retries automatically.</div>');
  $('action-card').style.display = world ? 'none' : '';
  $('join-block').style.display = world ? 'none' : '';
  $('url').placeholder = d.default_world_url;
}

$('join') && ($('join').onclick = async () => {
  $('join').disabled = true;
  $('msg').innerHTML = '<span class="dim">Enrolling…</span>';
  const body = {world_url: $('url').value.trim(),
                name_hint: $('hint').value.trim()};
  const r = await fetch(api('/join'),
    {method: 'POST', headers: H, body: JSON.stringify(body)});
  const d = await r.json();
  if (r.ok) {
    $('msg').innerHTML = '<span class="ok">Joined as ' + d.tenant +
      (d.existing ? ' (existing enrollment restored)' : '') +
      '. Open the chat and play — the world is live.</span>';
  } else {
    const err = typeof d.detail === 'string' ? d.detail
              : JSON.stringify(d.detail || 'join failed');
    $('msg').innerHTML = '<span class="bad">' + err + '</span>';
  }
  $('join').disabled = false;
  refresh();
});

refresh();
</script></body></html>"""
