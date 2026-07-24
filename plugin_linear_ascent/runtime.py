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
