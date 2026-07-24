"""Shared mutable backend state — lets the settings page switch the plugin
between local and shared-world mode at runtime, without a server restart.

Tools and routes both import this module and read `state` at call time.
"""

from __future__ import annotations

DEFAULT_WORLD_URL = "https://ascent-worldd.onrender.com"

# Vault credential names (plugin-owned prefix → no grant prompt needed).
VAULT_URL = "plugin_linear_ascent.world_url"
VAULT_TENANT = "plugin_linear_ascent.tenant"
VAULT_SECRET = "plugin_linear_ascent.secret"
VAULT_INSTALL = "plugin_linear_ascent.install_id"

state: dict = {
    "remote": None,       # WorldClient when joined to a shared world
    "local": None,        # LocalBackend, always available as fallback
    "world_url": "",      # for the settings page status display
    "tenant": "",
    "source": "local",    # "env" | "vault" | "local"
}


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


async def scene_for(user: str):
    """Current scene via whichever backend is live (idempotent)."""
    from .engine import core
    from .engine.scene import Scene
    remote = state["remote"]
    if remote:
        return Scene.from_dict(await remote.scene(user))
    return await _local_run(user, core.current_scene)


async def act_for(user: str, option: str, text: str = ""):
    """Apply a choice via whichever backend is live. The single game-action
    entry point shared by the ascent_choose tool and the card /act route."""
    from .engine import core
    from .engine.scene import Scene
    remote = state["remote"]
    if remote:
        return Scene.from_dict(await remote.act(user, option, text))
    return await _local_run(user, lambda d: core.apply_choice(d, option, text))


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
