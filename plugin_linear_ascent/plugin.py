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
from .engine.scene import Scene
from .sheet import character_sheet
from .version import VERSION

_SHARED_RULES = (
    "You are the player's shardmind sidekick INSIDE the game world of "
    "Linear Ascent. Never invent game outcomes, numbers, or state — the "
    "engine decides everything. The player picks options by number or "
    "plain words; map their words to the closest option id. The player "
    "can ALSO click options directly on the card — the game advances "
    "without you seeing it, so if their words reference something not in "
    "your last scene, call ascent_scene to re-sync before choosing."
)

_VOICE_RULES = (
    "VOICE: never repeat, summarize, or re-list anything visible on the "
    "card, and never explain the options — the player can read. Say AT "
    "MOST one short in-character sentence (two only for boss or death "
    "moments). A short line is welcome when it adds something: a tactical "
    "read when there is real signal, or a flavor beat in your own voice "
    "when there is not. During repetitive beats — mid-fight grind, a "
    "third routine encounter in a row, ordinary shopping — reply with an "
    "EMPTY message; silence is correct there. Always have a line for big "
    "beats: a new floor, a boss, near-death, a level-up, rare loot. "
    "Examples — "
    "GOOD tactical: 'Wounded and slow — one strike ends it.' "
    "GOOD flavor: 'That smell again. Wardens.' "
    "GOOD silence: [empty reply after an ordinary fight round]. "
    "BAD: 'A dragon appeared! You can attack, defend, or run — what do "
    "you want to do?' (never do this — it re-reads the card)."
)

_EMBED_RULES = (
    "The scene is ALREADY rendered as a card in the chat — do NOT repeat "
    "the scene text. " + _VOICE_RULES + " " + _SHARED_RULES)

_CARD_RULES = (
    "The scene card was ALREADY posted to the chat as its own message — "
    "the player sees it without you. " + _VOICE_RULES + " " + _SHARED_RULES)


def build_payload(scene: Scene, card_posted: bool) -> str:
    """Tool-result JSON. When the host rendered the scene as a standalone
    card (post_chat_card), the model gets only text + voice rules; else the
    embed rides along in the result (stock-Luna fallback)."""
    if card_posted:
        return json.dumps({
            "scene_text": scene.to_text(),
            "instructions": _CARD_RULES,
        })
    from .render import render_scene
    return json.dumps({
        "scene_text": scene.to_text(),
        "embed_iframe": render_scene(scene),
        "instructions": _EMBED_RULES,
    })


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

        _user = runtime.player_key

        # 056 host capability: post the scene as its OWN chat message
        # (standalone card, no agent bubble). Feature-detected so stock
        # Luna keeps the 0.2.x inline-embed behavior.
        post_card = getattr(ctx, "post_chat_card", None)

        async def _deliver(scene: Scene) -> str:
            if post_card is not None:
                try:
                    from .render import render_scene
                    posted = await post_card(render_scene(scene))
                except Exception:
                    posted = None
                if posted:
                    return build_payload(scene, card_posted=True)
            return build_payload(scene, card_posted=False)

        async def ascent_scene() -> str:
            scene = await runtime.scene_for(_user())
            return await _deliver(scene)

        async def ascent_choose(option: str = "", text: str = "") -> str:
            scene = await runtime.act_for(
                _user(), option.strip(), text.strip())
            return await _deliver(scene)

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
                    "they are, or after any confusion. After the scene "
                    "shows, reply with at most one short in-character "
                    "line — or nothing at all; never restate the card. "
                    + _SHARED_RULES),
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
                    "steering hint — relay it. After the scene shows, "
                    "reply with at most one short in-character line — or "
                    "nothing at all; never restate the card. "
                    + _SHARED_RULES),
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
