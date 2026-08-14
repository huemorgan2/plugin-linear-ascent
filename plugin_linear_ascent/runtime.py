"""Shared mutable backend state — the plugin plays in ONE shared world.

007: world connection is mandatory. On load (and lazily at every tool
call) the plugin auto-enrolls against the default world with a
persistent install_id. The local backend still exists but is only
consulted when ASCENT_DEV_LOCAL=1 (tests, dojo runs) — a real install
that cannot reach the world gets an honest "lift is down" scene, never a
silent private world.

Tools and routes both import this module and read `state` at call time.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid

DEFAULT_WORLD_URL = "https://ascent-worldd.onrender.com"

# Vault credential names (plugin-owned prefix → no grant prompt needed).
VAULT_URL = "plugin_linear_ascent.world_url"
VAULT_TENANT = "plugin_linear_ascent.tenant"
VAULT_SECRET = "plugin_linear_ascent.secret"
VAULT_INSTALL = "plugin_linear_ascent.install_id"

ENROLL_RETRY_S = 30            # min seconds between auto-enroll attempts

state: dict = {
    "remote": None,       # WorldClient when joined to a shared world
    "local": None,        # LocalBackend — dev flag / migration source only
    "world_url": "",      # for the settings page status display
    "tenant": "",
    "source": "local",    # "env" | "vault" | "auto" | "local"
    "ctx": None,          # PluginContext (vault access for auto-enroll)
    "enroll_ts": 0.0,     # last auto-enroll attempt (throttle)
    "last_scene": {},     # 009: user -> last scene_id, for /pane/peek —
                          # chat-driven acts update it, so the pane can poll
                          # freshness without a world round trip
    "presence": {},       # 022/003: user -> {"at", "hot"} — grade-2
                          # liveness for /pane/peek, refreshed ≤ once/min
    "agent_pace": {},     # 0.29.5: user -> monotonic time of the last
                          # agent-rendered screen — moves are paced so
                          # the player watches the game the agent plays
}

PRESENCE_REFRESH_S = 60
AGENT_MOVE_GAP_S = 3.0    # 0.29.5: minimum seconds a screen stays up
                          # before the agent's NEXT move replaces it


def pace_mark(user: str) -> None:
    """A screen just rendered for this player (agent tool path only —
    the pane's own clicks are the human's hand and are never paced)."""
    state["agent_pace"][user] = time.monotonic()


async def pace_wait(user: str) -> None:
    """Hold the agent's move until the previous screen has had its
    AGENT_MOVE_GAP_S on the player's display."""
    last = state["agent_pace"].get(user)
    if last is None:
        return
    wait = AGENT_MOVE_GAP_S - (time.monotonic() - last)
    if wait > 0:
        await asyncio.sleep(wait)


async def floor_presence(user: str) -> dict:
    """Presence ints for the pane peek: {"hot", "online", "feed_head"}.
    The hot path is the in-process cache — a world round trip happens at
    most once a minute, and a failed refresh keeps the last honest
    numbers. 056: the same /v1/presence reply now carries the Playing
    button's two ints, so the peek stays one cached call."""
    remote = state["remote"]
    if remote is None:
        return {"hot": 0, "online": 0, "feed_head": 0}
    now = time.monotonic()
    slot = state["presence"].get(user)
    if slot is not None and now - slot["at"] < PRESENCE_REFRESH_S:
        return slot
    # claim the window before the fetch so concurrent peeks don't stampede
    slot = {"at": now, "hot": (slot or {}).get("hot", 0),
            "online": (slot or {}).get("online", 0),
            "feed_head": (slot or {}).get("feed_head", 0)}
    state["presence"][user] = slot
    try:
        d = await remote.presence(user)
        slot["hot"] = int(d.get("hot", 0))
        slot["online"] = int(d.get("online", 0))
        slot["feed_head"] = int(d.get("feed_head", 0))
    except Exception:
        pass
    return slot


def remember_scene(user: str, scene) -> None:
    if getattr(scene, "scene_id", ""):
        state["last_scene"][user] = scene.scene_id


def last_scene_id(user: str) -> str:
    return state["last_scene"].get(user, "")


def dev_local() -> bool:
    """Local single-player is a developer flag, never a player mode."""
    return os.environ.get("ASCENT_DEV_LOCAL", "").strip() not in ("", "0")


def player_key() -> str:
    """The engine's player key. Tools and the card-action route MUST derive
    it identically or clicks would play a different character than typed
    numbers. On a single-user Luna this resolves to "owner" in both
    contexts (the SDK's get_current_user is a FastAPI dependency and can't
    be called bare — the fallback IS the contract)."""
    try:
        from luna_sdk import get_current_user
        u = get_current_user()
        if u:
            return str(getattr(u, "id", None) or
                       getattr(u, "username", None) or u)
    except Exception:
        pass
    return "owner"


async def _local_run(user: str, fn):
    local = state["local"]
    doc = await local.load(user)
    scene = fn(doc)
    ledger = doc.pop("_ledger", [])
    doc["scene"] = scene.to_dict()
    await local.save(user, doc, ledger)
    return scene


def _offline_scene():
    """The honest failure scene — the world is REQUIRED, so an outage is a
    scene the sidekick can empathize with, not a silent mode switch."""
    from .engine.scene import Option, Scene
    return Scene(
        eyebrow="THE TOWER GATE · THE LIFT IS DOWN",
        headline="The Ascent waits",
        support="The great chains are still. The gate crew shrugs at the sky.",
        shard_note="The world signal is gone — not your fault and not "
                   "forever. Pull the lever again in a moment.",
        body_lines=[
            "Roothollow, the tower, every other climber — all of it is "
            "out there, unreachable for now.",
            "Nothing is lost. The world keeps your climb even when we "
            "can't see it.",
        ],
        options=[Option("retry", "Pull the gate lever again")],
        event_kind="",
    )


async def scene_for(user: str):
    """Current scene via the world (idempotent). Dev flag → local engine."""
    from .engine import core
    from .engine.scene import Scene
    if state["remote"] is None and dev_local():
        scene = await _local_run(user, core.current_scene)
    elif state["remote"] is None and not await ensure_world(user):
        scene = _offline_scene()
    else:
        try:
            scene = Scene.from_dict(await state["remote"].scene(user))
        except Exception:
            scene = _offline_scene()
    remember_scene(user, scene)
    return scene


async def act_for(user: str, option: str, text: str = ""):
    """Apply a choice via the world. The single game-action entry point
    shared by the ascent_choose tool, the card /act route, and the pane."""
    from .engine import core
    from .engine.scene import Scene
    if option == "retry":
        # the offline scene's lever: never a game option, always a re-sync
        return await scene_for(user)
    if state["remote"] is None and dev_local():
        scene = await _local_run(
            user, lambda d: core.apply_choice(d, option, text))
    elif state["remote"] is None and not await ensure_world(user):
        scene = _offline_scene()
    else:
        try:
            scene = Scene.from_dict(
                await state["remote"].act(user, option, text))
        except Exception:
            scene = _offline_scene()
    remember_scene(user, scene)
    return scene


async def ensure_world(user: str) -> bool:
    """Auto-enroll against the default world (007 Phase 1). Idempotent per
    install (vault install_id), throttled, safe to call on every turn."""
    if state["remote"] is not None:
        return True
    now = time.monotonic()
    if now - state["enroll_ts"] < ENROLL_RETRY_S:
        return False
    state["enroll_ts"] = now
    vault = getattr(state["ctx"], "vault", None) if state["ctx"] else None
    if vault is None:
        return False
    # env URL without a secret = auto-enroll target override (QA worlds)
    url = (os.environ.get("LUNA_ASCENT_WORLDD_URL") or "").strip() \
        .rstrip("/") or DEFAULT_WORLD_URL
    try:
        try:
            install_id = (await vault.get_credential(VAULT_INSTALL)).value
        except KeyError:
            install_id = uuid.uuid4().hex
            await vault.store_credential(VAULT_INSTALL, install_id,
                                         kind="api_key")
        import httpx
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url + "/v1/enroll",
                             json={"install_id": install_id})
        if r.status_code != 200:
            return False
        d = r.json()
        await vault.store_credential(VAULT_URL, url, kind="api_key")
        await vault.store_credential(VAULT_TENANT, d["tenant"],
                                     kind="api_key")
        await vault.store_credential(VAULT_SECRET, d["secret"],
                                     kind="api_key")
        configure_remote(url, d["tenant"], d["secret"], source="auto")
        await migrate_local_character(user)
        return True
    except Exception:
        return False


async def migrate_local_character(user: str) -> bool:
    """One-time import: a character made in local/dev play is pushed to
    the world on first connect — nobody loses their climber. If the world
    already has one, the world wins (local was the outage shadow)."""
    remote, local = state["remote"], state["local"]
    if remote is None or local is None:
        return False
    try:
        doc = await local.load(user)
        if doc.get("stage") != "playing":
            return False
        sheet = await remote.character(user)
        if sheet.get("status") != "no character yet":
            return False               # world character exists — world wins
        out = await remote.import_doc(user, doc)
        return bool(out.get("imported"))
    except Exception:
        return False


def configure_remote(url: str, tenant: str, secret: str, source: str) -> None:
    from .backend.remote import WorldClient
    state["remote"] = WorldClient(url, tenant, secret)
    state["world_url"] = url
    state["tenant"] = tenant
    state["source"] = source


def clear_remote() -> None:
    state["remote"] = None
    state["world_url"] = ""
    state["tenant"] = ""
    state["source"] = "local"
