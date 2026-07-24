"""The Luna plugin — tools, backend selection, card delivery.

Backend resolution (highest wins), applied at every tool call via runtime:
  1. env override (LUNA_ASCENT_WORLDD_URL + LUNA_ASCENT_SHARED_SECRET) — dev
  2. vault credentials written by the settings page ("Join the shared world")
  3. local single-tenant engine (solo play, zero config)
Same scenes either way.
"""

from __future__ import annotations

import json
import os

from luna_sdk import (LunaPlugin, PluginContext, PluginManifest, SettingsTab,
                      ToolDef)

from . import runtime
from .engine import core
from .engine.scene import Scene
from .sheet import character_sheet
from .version import VERSION

_SHARED_RULES = (
    "You are the player's shardmind sidekick INSIDE the game world of "
    "Linear Ascent. Never invent game outcomes, numbers, or state — the "
    "engine decides everything. The player picks options by number or "
    "plain words; map their words to the closest option id."
)

_EMBED_RULES = (
    "The scene is ALREADY rendered as a card in the chat — do NOT repeat "
    "the scene text. Add at most one short in-character shardmind line. "
    "The player answers with a number or plain words. " + _SHARED_RULES)


class LinearAscentPlugin(LunaPlugin):
    manifest = PluginManifest(
        name="plugin-linear-ascent",
        shown_name="Linear Ascent",
        version=VERSION,
        description=(
            "A LORD-style multiplayer text RPG: climb the 100-floor Ascent, "
            "bank your gold, sleep in the lodge, and cast down the Demon "
            "King — with your Luna agent as your in-world shardmind sidekick."
        ),
        routes_module="routes",
        settings_tabs=[
            SettingsTab(
                id="linear-ascent",
                label="Linear Ascent",
                icon="tower-control",
                sort_order=70,
                iframe_src="/api/p/plugin-linear-ascent/ui/settings/",
            ),
        ],
    )

    async def on_load(self, ctx: PluginContext) -> None:
        from .backend.local import Base, LocalBackend

        # Local tables always exist: solo mode + fallback after disconnect.
        async with ctx.engine.begin() as conn:
            for table in Base.metadata.sorted_tables:
                await conn.run_sync(table.create, checkfirst=True)
        runtime.state["local"] = LocalBackend(ctx.db_session_factory)

        def _env(name: str) -> str:
            # ctx.get_env only resolves vars declared in Luna's own config
            # schema (extra="ignore"), so plugin-custom vars need os.environ.
            try:
                val = ctx.get_env(name)
            except Exception:
                val = None
            return (val or os.environ.get(name) or "").strip()

        env_url = _env("LUNA_ASCENT_WORLDD_URL")
        env_secret = _env("LUNA_ASCENT_SHARED_SECRET")
        if env_url and env_secret:
            runtime.configure_remote(
                env_url, _env("LUNA_ASCENT_TENANT") or "default",
                env_secret, source="env")
        else:
            vault = getattr(ctx, "vault", None)
            if vault is not None:
                try:
                    url = (await vault.get_credential(
                        runtime.VAULT_URL)).value
                    tenant = (await vault.get_credential(
                        runtime.VAULT_TENANT)).value
                    secret = (await vault.get_credential(
                        runtime.VAULT_SECRET)).value
                    if url and tenant and secret:
                        runtime.configure_remote(
                            url, tenant, secret, source="vault")
                except KeyError:
                    pass  # never joined — solo mode

        def _user() -> str:
            try:
                from luna_sdk import get_current_user
                u = get_current_user()
                if u:
                    return str(getattr(u, "id", None) or
                               getattr(u, "username", None) or u)
            except Exception:
                pass
            return "owner"

        def _payload(scene: Scene) -> str:
            from .render import render_scene
            return json.dumps({
                "scene_text": scene.to_text(),
                "embed_iframe": render_scene(scene),
                "instructions": _EMBED_RULES,
            })

        async def _local_run(fn, *args) -> Scene:
            local = runtime.state["local"]
            luna_user = _user()
            doc = await local.load(luna_user)
            scene: Scene = fn(doc, *args)
            ledger = doc.pop("_ledger", [])
            doc["scene"] = scene.to_dict()
            await local.save(luna_user, doc, ledger)
            return scene

        async def ascent_scene() -> str:
            remote = runtime.state["remote"]
            if remote:
                scene = Scene.from_dict(await remote.scene(_user()))
            else:
                scene = await _local_run(core.current_scene)
            return _payload(scene)

        async def ascent_choose(option: str = "", text: str = "") -> str:
            option, text = option.strip(), text.strip()
            remote = runtime.state["remote"]
            if remote:
                scene = Scene.from_dict(
                    await remote.act(_user(), option, text))
            else:
                scene = await _local_run(
                    lambda d: core.apply_choice(d, option, text))
            return _payload(scene)

        async def ascent_character() -> str:
            remote = runtime.state["remote"]
            if remote:
                sheet = await remote.character(_user())
            else:
                p = await runtime.state["local"].load(_user())
                if p["stage"] != "playing":
                    return json.dumps({
                        "status": "no character yet",
                        "hint": "Call ascent_scene to start creation."})
                sheet = character_sheet(p)
            sheet["instructions"] = _SHARED_RULES
            return json.dumps(sheet)

        ctx.tool_registry.register(
            self.manifest.name,
            ToolDef(
                name="ascent_scene",
                description=(
                    "Linear Ascent: show the player's CURRENT game scene. "
                    "Safe to call anytime — it never changes game state. "
                    "Call this when the player wants to play, asks where "
                    "they are, or after any confusion. " + _SHARED_RULES),
                parameters={"type": "object", "properties": {},
                            "required": []},
                policy="auto_approve", risk_level="low"),
            ascent_scene)

        ctx.tool_registry.register(
            self.manifest.name,
            ToolDef(
                name="ascent_choose",
                description=(
                    "Linear Ascent: submit the player's choice for the "
                    "current scene. Pass `option` as the option id OR the "
                    "number the player typed (e.g. '2'). During character "
                    "naming pass `text` with the chosen name instead. The "
                    "engine refuses stale or unknown options with a "
                    "steering hint — relay it. " + _SHARED_RULES),
                parameters={
                    "type": "object",
                    "properties": {
                        "option": {
                            "type": "string",
                            "description": "Option id or typed number."},
                        "text": {
                            "type": "string",
                            "description": "Free text — only for naming."},
                    },
                    "required": []},
                policy="auto_approve", risk_level="low"),
            ascent_choose)

        ctx.tool_registry.register(
            self.manifest.name,
            ToolDef(
                name="ascent_character",
                description=(
                    "Linear Ascent: the player's character sheet — stats, "
                    "gear, gold, meters, frontier floor. Read-only."),
                parameters={"type": "object", "properties": {},
                            "required": []},
                policy="auto_approve", risk_level="low"),
            ascent_character)
