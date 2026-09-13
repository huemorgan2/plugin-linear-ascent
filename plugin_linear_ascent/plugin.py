"""The Luna plugin — tools, backend selection, card delivery.

007: the shared world is mandatory. Backend resolution (highest wins):
  1. env override (LUNA_ASCENT_WORLDD_URL + LUNA_ASCENT_SHARED_SECRET) — dev
  2. vault credentials (written by auto-enroll or the settings page)
  3. auto-enroll against the default world (install_id in the vault)
  4. ASCENT_DEV_LOCAL=1 → the local engine (tests/dojo only)
If none of these lands, tools return the honest "lift is down" scene.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from luna_sdk import (LunaPlugin, PluginContext, PluginManifest,
                      SettingsTab, SidebarSection, ToolDef)

from . import runtime
from .engine.scene import Scene
from .sheet import character_sheet
from .version import VERSION

log = logging.getLogger(__name__)

# Luna rolls an upgrade back if on_load raises, so a Postgres that happens
# to be restarting when the player clicks Update makes the plugin
# un-upgradeable until they retry at a luckier moment. Hosted Luna shares
# one Postgres cluster across tenants, so that window is not rare.
_DDL_ATTEMPTS = 5
_DDL_BACKOFF = 0.5

# Postgres 57P03 and the connection errors that come with a restart or
# failover — all of them clear on their own within seconds.
_TRANSIENT_DB = (
    "in recovery mode",
    "starting up",
    "shutting down",
    "cannot connect now",
    "connection refused",
    "server closed the connection",
    "terminating connection",
    "connection was closed",
)


def _is_transient_db(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(sig in text for sig in _TRANSIENT_DB)


def _widen_local_ledger(conn):
    """Widen existing local ledgers without rewriting their history."""
    from sqlalchemy import text
    if conn.dialect.name != "postgresql":
        return
    for column in ("gold", "xp"):
        kind = conn.execute(text("SELECT udt_name FROM information_schema.columns "
            "WHERE table_schema=current_schema() AND table_name='ascent_ledger' "
            "AND column_name=:column"), {"column": column}).scalar()
        if kind == "int4":
            conn.execute(text(f"ALTER TABLE ascent_ledger ALTER COLUMN {column} TYPE BIGINT"))


async def _ensure_local_tables(ctx: PluginContext) -> bool:
    """Create the plugin's own tables, riding out a restarting database.

    Returns False instead of raising: these tables serve dev-local play and
    the migration of legacy local characters, while the shared world is the
    real game — losing them is not worth failing (and rolling back) the
    whole plugin.
    """
    from .backend.local import Base

    delay, last = _DDL_BACKOFF, None
    for attempt in range(1, _DDL_ATTEMPTS + 1):
        try:
            async with ctx.engine.begin() as conn:
                for table in Base.metadata.sorted_tables:
                    await conn.run_sync(table.create, checkfirst=True)
                await conn.run_sync(_widen_local_ledger)
            return True
        except Exception as e:  # noqa: BLE001 — load must survive any of them
            last = e
            if attempt == _DDL_ATTEMPTS or not _is_transient_db(e):
                break
            log.warning(
                "linear-ascent: database busy (%s), retrying table setup "
                "in %.1fs [%d/%d]", e, delay, attempt, _DDL_ATTEMPTS)
            await asyncio.sleep(delay)
            delay *= 2
    log.error("linear-ascent: could not create local tables (%s) — loading "
              "anyway; the shared world does not need them", last)
    return False


_SHARED_RULES = (
    "You are the player's shardmind sidekick INSIDE the game world of "
    "Linear Ascent. Never invent game outcomes, numbers, or state — the "
    "engine decides everything; every game action goes through "
    "ascent_choose and you only relay what its result says. METERS: "
    "there is NO mana in this world — never say the word. The XP bar is "
    "experience inside the current level. It fills by fighting up to the "
    "bar for the next level. If a reserve is shown, it is earned XP "
    "available for spending after the bar fills. Use the current scene "
    "for costs, rewards and the three-weapon collection. "
    "LEVELS ARE BOUGHT, never automatic: a full XP bar plus a gold fee "
    "at the Guildhall's Train option; use its displayed current fee. "
    "The player "
    "picks options by number or plain words; map their words to the "
    "closest option id. THE INTERFACE lives in the Linear Ascent pane "
    "in the sidebar — the player sees every scene there; NEVER paste "
    "scene text, options, or HTML into the chat, and point a lost "
    "player at the pane. PACE: one player message = at most ONE "
    "ascent_choose call, then STOP and wait for the player — never keep "
    "playing on your own, not even to finish a fight. Only when the "
    "player explicitly asks you to play for them ('keep going', 'finish "
    "the fight', 'grind for me') may you chain calls — and even then "
    "pause and hand control back at a death, level-up, boss, new floor, "
    "or after about six actions. A smaller explicit user limit wins: two "
    "gather attempts means at most two gather_step calls, counting them "
    "before each call. Extraction/navigation needs its own authorization "
    "or the player's instruction to finish that trip. The player can ALSO click options "
    "directly on the card — the game advances without you seeing it, so "
    "if their words reference something not in your last scene, call "
    "ascent_scene to re-sync before choosing. The game may have changed "
    "since earlier chat messages: trust its current scene and sheet. "
    "When weapon_collection is present, its screen DOES exist: open it "
    "with ascent_choose(option='collection'); inspect and assign exact "
    "weapon instances using the returned options. Never deny a feature "
    "from memory without checking the current scene. For questions about "
    "the current monsters, reach, weapons or options, FIRST call ascent_scene "
    "even if a prior chat answer seems to cover it. Earlier advice can be "
    "stale or wrong. For arrows/ammunition, FIRST call ascent_character "
    "and read weapon_collection.quiver, then the current scene if opening "
    "its controls. When that quiver says finite, Ordinary arrows also run "
    "out: six payloads, one grade-matched arrow per accepted shot including "
    "misses. Its types list actual effects, stock and Forge offers; bows "
    "lists the resolved selected payload even when choices is empty. "
    "Show owned arrows in the collection's Arrows drawer. Buy them at "
    "the Forge Arrow supplies rack using its current options; selection "
    "on a bow during a group is free and does not fire. Never repeat an "
    "earlier claim of unlimited/no ammunition over this current data. "
    "Report current weapon_reach and UNAVAILABLE markers; "
    "do not infer reach from affinity. For a named resource place or material "
    "route, call ascent_character and read resource_sites, floor and location "
    "before saying it is unavailable. A site on another floor requires travel "
    "through the Tower gate and that floor camp using current legal options. "
    "Enter a resource site to buy its tool there: the tool is required to "
    "gather, not to visit or inspect the site. Do not search unrelated shops "
    "when resource_sites already identifies its own tool seller. "
)

_GUIDE_RULES = (
    "EARLY GAME COACHING: read the current scene and ascent_character "
    "before giving numerical advice. Starting weapons, training prices, "
    "energy costs, death protections and rewards depend on the current "
    "game rules. Never substitute remembered prices or older combat rules. "
    "For a group battle, use its complete roster, current gap and actual "
    "option hints. Ground/Air controls reach independently of defensive "
    "Common/Power/Magic affinity: a vulnerable Ground enemy can still be "
    "out of blade reach. A disabled blade needs Contact; never say every "
    "weapon reaches just because the target has soft defenses. Quote a "
    "technique's displayed bonus, duration and restrictions exactly; "
    "Cover shot is not the old treeline shot. Distinguish current condition "
    "and pending haul from secured possessions. XP is kept after each group "
    "kill; gold and items require the full group clear. An expedition haul "
    "must additionally be extracted. Check the scene for energy payments. "
    "Recommend a reachable weapon, an affordable improvement or a safe "
    "return using facts the player can see; do not predict a certain kill "
    "from an attack stat alone. The Forge improves and repairs owned "
    "weapons; the School retains training and mastery, but the collection "
    "has three battle slots from the start. The Vault protects deposits; "
    "its displayed interest must be collected to reinvest. Use "
    "next_unlocks and protections_active on ascent_character for the "
    "player's next milestone and death rules. Keep advice in-world, "
    "one useful decision at a time."
)

_VOICE_RULES = (
    "VOICE: never repeat, summarize, or re-list anything visible on the "
    "card unsolicited. If the player asks for an explanation or comparison, "
    "answer that request using the current scene and exact option hints. "
    "For routine action replies, say AT "
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

_PANE_RULES = (
    "The scene is ALREADY on the player's screen in the Linear Ascent "
    "pane (sidebar) — it renders there automatically; nothing gets "
    "posted to the chat. NEVER repeat the scene text or the options. "
    + _VOICE_RULES + " " + _SHARED_RULES)


def build_payload(scene: Scene) -> str:
    """Tool-result JSON (009): the pane is the display — the model gets
    the scene as compact text purely for its own understanding, plus the
    standing voice rules. No embeds, no cards."""
    return json.dumps({
        "scene_text": scene.to_text(),
        "instructions": _PANE_RULES,
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
        sidebar_sections=[
            SidebarSection(
                id="linear-ascent",
                label="Linear Ascent",
                icon="swords",
                sort_order=45,
                path="ui/",
            ),
        ],
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
        from .backend.local import LocalBackend

        # Local tables always exist: the dev flag plays here, and old
        # local characters are migrated to the world from here.
        await _ensure_local_tables(ctx)
        runtime.state["local"] = LocalBackend(ctx.db_session_factory)
        runtime.state["ctx"] = ctx

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
                    pass  # never enrolled — auto-enroll below

        # 007: mandatory world. Warm up enrollment in the background so
        # the first tool call is already connected; tool calls also retry
        # lazily, so a failed startup enroll never strands the player.
        if runtime.state["remote"] is None and not runtime.dev_local():
            asyncio.get_running_loop().create_task(
                runtime.ensure_world(runtime.player_key()))

        _user = runtime.player_key

        # 009: the pane is the display. Tools no longer post chat cards —
        # the scene reaches the player through the sidebar pane (it polls
        # /pane/peek, so a chat-driven act shows up there within seconds).

        async def ascent_scene() -> str:
            scene = await runtime.scene_for(_user())
            runtime.pace_mark(_user())
            return build_payload(scene)

        async def ascent_choose(option: str = "", text: str = "") -> str:
            # 0.29.5: the player WATCHES the agent play — every screen
            # gets its seconds on the pane before the next move lands.
            u = _user()
            await runtime.pace_wait(u)
            scene = await runtime.act_for(u, option.strip(), text.strip())
            runtime.pace_mark(u)
            return build_payload(scene)

        async def ascent_character() -> str:
            remote = runtime.state["remote"]
            if remote is None and runtime.dev_local():
                p = await runtime.state["local"].load(_user())
                if p["stage"] != "playing":
                    return json.dumps({
                        "status": "no character yet",
                        "hint": "Call ascent_scene to start creation."})
                sheet = character_sheet(p)
            else:
                if remote is None and not await runtime.ensure_world(_user()):
                    return json.dumps({
                        "status": "world unreachable",
                        "hint": "The lift is down — the shared world isn't "
                                "answering. Try again in a moment."})
                try:
                    sheet = await runtime.state["remote"].character(_user())
                except Exception:
                    return json.dumps({
                        "status": "world unreachable",
                        "hint": "The lift is down — the shared world isn't "
                                "answering. Try again in a moment."})
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
                    "shows, keep routine action replies to one short line. "
                    "If asked to explain or compare, answer the request "
                    "accurately from the refreshed scene. "
                    + _SHARED_RULES + " " + _GUIDE_RULES),
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
                    "number the player typed (e.g. '2'). To open the weapon "
                    "collection use option collection when its action is present. Some scenes wait "
                    "for a TYPED chat reply instead (marked '⌨ waiting for "
                    "a typed chat reply' — usernames, banner names, "
                    "fees, dues, donation amounts, letters): for those "
                    "pass the player's message as `text` and leave "
                    "`option` empty. The "
                    "engine refuses stale or unknown options with a "
                    "steering hint — relay it. Moves are PACED: the game "
                    "holds each move until the previous screen has had a "
                    "few seconds on the player's pane — a slow tool call "
                    "is normal, never a timeout. After the scene shows, "
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
                            "description": "Free text — for scenes that "
                                           "await a typed reply (names, "
                                           "amounts, letters)."},
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
                    "gear, weapon collection, finite arrow quiver, gold, meters, frontier floor. Read-only. "
                    "For arrow/ammunition questions call this first: weapon_collection.quiver "
                    "has six payloads, grade-matched owned stock, Forge offers and each bow's selected arrows. "
                    "To OPEN or manage the weapon collection screen, use "
                    "ascent_choose with option collection; this sheet alone does not open it."),
                parameters={"type": "object", "properties": {},
                            "required": []},
                policy="auto_approve", risk_level="low"),
            ascent_character)
