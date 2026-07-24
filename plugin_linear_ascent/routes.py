"""Plugin HTTP surface.

Settings tab: one-click world enrollment, status, disconnect — the
settings iframe calls these with the host's bearer token. Credentials
live in Luna's vault; runtime.state switches the game backend live.

Card actions (057): POST /act is the direct game loop for interactive
cards. The chat shell's card-action bridge calls it when the player
clicks an option button — pure engine, no model in the path. The route
posts the next scene as its own card and, on big beats only, nudges the
agent to react in character (a "moment"), so the sidekick responds to
the game like the player does instead of driving it.
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

# Which event kinds warrant which agent nudge. A "moment" runs a genuine
# reaction turn (the sidekick speaks on its own); "awareness" just lands in
# history for the agent's next natural turn. Ordinary scenes get neither —
# fast clicking stays silent, exactly like a human watching over your
# shoulder who only speaks when something happens.
_MOMENT_KINDS = {"death", "boss"}
_AWARENESS_KINDS = {"present", "letter", "loot"}


class JoinIn(BaseModel):
    # module level, not inside register_routes: with postponed annotations
    # FastAPI can't resolve closure-local models and mistakes the body for
    # a query parameter.
    world_url: str = Field(default="", max_length=200)
    name_hint: str = Field(default="", max_length=32)


class ActIn(BaseModel):
    option: str = Field(default="", max_length=64)
    text: str = Field(default="", max_length=200)
    # Injected by the chat shell's bridge, not by the card itself.
    conversation_id: str | None = Field(default=None, max_length=64)
    message_id: str | None = Field(default=None, max_length=64)


def _notify_agent(scene, conversation_id: str | None) -> None:
    """Fire-and-forget sidekick reaction on notable beats. Never blocks the
    click response — the card must feel like code, not like a model."""
    kind = scene.event_kind
    channel = ("moment" if kind in _MOMENT_KINDS
               else "awareness" if kind in _AWARENESS_KINDS
               else None)
    if channel is None:
        return
    send = getattr(_ctx, "send_muted_message", None) if _ctx else None
    if send is None:
        return
    from .plugin import _VOICE_RULES
    content = (
        "The player just advanced Linear Ascent by clicking the scene "
        "card — the scene below is ALREADY on their screen as a card. "
        "You are their shardmind sidekick, reacting to what just "
        "happened.\n\n" + scene.to_text() + "\n\n" + _VOICE_RULES)
    title = f"Linear Ascent — {kind or 'the world moved'}"

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
        """The interactive-card game loop: apply the clicked option, post
        the next scene as a standalone card, nudge the agent on big beats.
        Stale/unknown options are handled by the engine itself (it returns
        the current scene with a steering hint), so a click on an old card
        still lands somewhere sensible."""
        from .render import render_scene

        key = runtime.player_key()
        scene = await runtime.act_for(key, body.option.strip(),
                                      body.text.strip())
        posted = None
        post_card = getattr(_ctx, "post_chat_card", None) if _ctx else None
        if post_card is not None:
            try:
                posted = await post_card(
                    render_scene(scene),
                    conversation_id=body.conversation_id)
            except Exception:
                posted = None
        if not posted:
            # No card capability / no resolvable conversation: the click
            # cannot show its result. Tell the bridge so the card can fall
            # back to "reply with a number".
            raise HTTPException(503, "host cannot post scene cards")
        _notify_agent(scene, body.conversation_id)
        return {
            "ok": True,
            "message_id": posted,
            "scene_id": scene.scene_id,
            "event_kind": scene.event_kind,
            "headline": scene.headline,
        }

    @router.post("/disconnect")
    async def disconnect(user=Depends(get_current_user)) -> dict:
        if runtime.state["source"] == "env":
            raise HTTPException(
                409, "World is pinned by env vars; remove them to disconnect.")
        vault = _vault()
        for name in (runtime.VAULT_URL, runtime.VAULT_TENANT,
                     runtime.VAULT_SECRET):
            try:
                await vault.delete_credential(name)
            except KeyError:
                pass
        # install_id is kept: re-joining returns the same tenant + progress
        runtime.clear_remote()
        return {"joined": False}

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
  <div class="sub">The 100-floor Ascent — solo out of the box, one click to
  join the shared world.</div>

  <div class="card" id="status-card">Loading…</div>

  <div class="card" id="action-card" style="display:none">
    <div id="join-block">
      <div style="margin-bottom:10px">Join the shared world: your install
      gets its own credentials automatically and your climb joins everyone
      else's — PvP, letters, guilds, world bosses.</div>
      <label class="k">Display hint for your world name (optional)</label>
      <input id="hint" maxlength="32" placeholder="e.g. roys-luna">
      <details><summary>Advanced: custom world server</summary>
        <input id="url" placeholder="">
      </details>
      <div style="margin-top:12px">
        <button id="join">Join the shared world</button>
      </div>
    </div>
    <div id="leave-block" style="display:none">
      <div style="margin-bottom:12px">Leaving switches back to solo play.
      Your shared-world character is kept — rejoin anytime to continue.</div>
      <button class="secondary" id="leave">Disconnect from world</button>
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
    : '<div class="dim">Playing on this Luna only. No other climbers.</div>');
  $('action-card').style.display = '';
  $('join-block').style.display = world ? 'none' : '';
  $('leave-block').style.display = (world && d.source !== 'env') ? '' : 'none';
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

$('leave').onclick = async () => {
  const r = await fetch(api('/disconnect'), {method: 'POST', headers: H});
  const d = await r.json();
  $('msg').innerHTML = r.ok
    ? '<span class="dim">Disconnected — back to solo play.</span>'
    : '<span class="bad">' + (d.detail || 'failed') + '</span>';
  refresh();
};

refresh();
</script></body></html>"""
