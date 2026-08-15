"""Scene — the single shape every game message takes.

The renderer contract from design/chat_components.md: the engine emits a
Scene; one renderer maps it to a card; the plain-text fallback is generated
from the same object. Content never contains markup.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields


def _known(cls, raw: dict) -> dict:
    """Only the fields THIS version knows about.

    worldd runs the engine and the installed plugin renders what it sends, so
    the two are routinely different versions. A scene from a newer engine must
    never crash an older client: 0.33.0 put `badge` inside each option dict and
    every 0.28-0.32 install builds `Option(**o)`, which made one new field read
    as "the world signal is gone" for everyone who had not updated.
    """
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in raw.items() if k in names}


@dataclass
class Option:
    id: str                 # stable id, e.g. "attack", "buy_scrap_dagger"
    label: str
    hint: str = ""          # right-aligned cost/class hint, e.g. "1 ⚡"
    aether: bool = False    # class/sidekick option — aether key chip
    locked: bool = False    # 019: a gated row — dimmed, still clickable;
                            # choosing it returns the scene with the
                            # refusal that explains the gate
    badge: int = 0          # 027: things waiting behind this door — drawn
                            # as a bright blue count chip. The text
                            # surface writes it as "(n)" after the label.


@dataclass
class Meters:
    hp: int
    hp_max: int
    energy: int
    energy_max: int
    xp: int             # the XP pool inside the level (hard-capped at need)
    xp_need: int        # xp_need(level) — full bar = licensed to train
    gold: int
    level: int = 1      # 012: shown next to the gold
    atk: int = 0        # 030: total ATK/DEF ride the wire so the renderer
    dfs: int = 0        # can draw pip rows without reading the player doc.
                        # Defaults 0 = "not sent" (older engine): the
                        # profile block simply omits the rows.
    spd: int = 0        # speed on the same wire — base plus footwear.
                        # 0 = not sent (older engine): row omitted.
    name: str = ""      # 031 §4: the profile header — who is climbing.
    race: str = ""      # "" = not sent (older engine): the header line
    clazz: str = ""     # simply omits the missing parts.
    faction: str = ""   # the faction you swore to; "" = none (or an
                        # older engine that never sent it).
    # 059: the faction block under the profile — its banner slug, the
    # table's size and how many of them are on the floors right now;
    # for the unaffiliated, how many factions fly (-1 = not sent).
    faction_banner: str = ""
    faction_members: int = 0
    faction_online: int = 0
    factions_total: int = -1


@dataclass
class Scene:
    eyebrow: str                    # "FLOOR 12 · IRONVALE · THE FLOODED MINE"
    headline: str                   # the bottom line, numbers included
    support: str = ""               # one dim line
    shard_note: str = ""            # sidekick whisper (aether stripe)
    body_lines: list[str] = field(default_factory=list)
    options: list[Option] = field(default_factory=list)
    meters: Meters | None = None
    event_kind: str = ""    # "" | loot | death | letter | boss | present | matchup
    banner: str = ""                # banner slug, "" = no banner
    banner_variant: str = ""        # 008 specimen: "" | runt | tough | alpha — retints the art
    fx: str = ""                    # 011 event animation slug (kill GIFs, gate open, title)
    scene_id: str = ""              # nonce — ascent_choose must echo the ids of THIS scene
    awaits_text: str = ""           # 010: "" | what the scene wants typed in
                                    # chat, e.g. "the banner's name" — the
                                    # sidekick forwards the player's next
                                    # message as ascent_choose text
    tally: list[dict] = field(default_factory=list)
                                    # 025/006: a haul the renderer DRAWS
                                    # instead of stating. Entries:
                                    # {kind: "gold"|"aether", n: int}.
                                    # Under TALLY_CAP the card lays out
                                    # one mark per point — a number can
                                    # say 37, only 37 coins can show it.
                                    # The text surface stays words.
    inventory: list[dict] = field(default_factory=list)
                                    # 014: the pack strip — stamped by core on
                                    # every playing scene. Entries:
                                    # {slug, name, count, kind, equipped?}
                                    # kind ∈ weapon|shield|armor|item
    notices: list[dict] = field(default_factory=list)
                                    # 027: the notice board — what WAITS for
                                    # the player, drawn at the top of the
                                    # card as clickable shortcuts. Entries:
                                    # {door, opt, n, kind, text}, kind ∈
                                    # collect|plan. A count is never left to
                                    # be guessed at.
    ask: dict | None = None         # 027: an input the card owns —
                                    # {kind: "text"|"number", label,
                                    #  placeholder, max, min, submit}.
                                    # Rides with awaits_text: the box is the
                                    # fast path, the chat still works.
    gallery: list[dict] = field(default_factory=list)
                                    # 027: clickable picture tiles —
                                    # {opt, slug, label, sub}. Faction
                                    # sigils are art, not filenames.
    paper: dict | None = None       # 030 Phase 5: the Morning Crier —
                                    # {headline, items[], closable}. Drawn
                                    # as a broadsheet over paper art; ✕
                                    # posts news_close. Top-level and
                                    # optional — older clients drop it.
    strip: dict | None = None       # 030: a thin art band with one big
                                    # number — {art, text}. The vault's
                                    # strongbox shelf: 320×50 art, the
                                    # text drawn large and centered over
                                    # it. Top-level and optional: older
                                    # clients drop it, text keeps parity.
    enemy: dict | None = None       # 017/003: the fight dossier payload —
                                    # {name, hp, hp_max, atk, def, profile,
                                    #  range, lore, specimen, pspd, dtype,
                                    #  dodge}. The renderer draws the enemy
                                    #  HP bar, range chip and [i] card from
                                    #  this; content stays markup-free.
    option_art: dict = field(default_factory=dict)
                                    # 031 §13/§14: art slug per option id,
                                    # riding BESIDE the options (wire law —
                                    # a key inside an option dict crashes
                                    # 0.28-0.32 clients). {"hunt": "gnarl"}
    grid: bool = False              # 031 §14: draw the options as a card
                                    # grid — image on top, label + hint
                                    # under it, [i] kept on the card. The
                                    # forge's stock uses this.
    npc: dict | None = None         # 031 §9: a face beside the words —
                                    # {name, portrait}. The portrait
                                    # (100×200) sits left of the body.
    activity: str = ""              # 031 §11: the lodge's evening state,
                                    # drawn as a filled band under the
                                    # options. "" = no band.
    location: str = ""              # 042: the room the player stands in
                                    # (p["location"] verbatim) — the sound
                                    # layer keys its music on it. A new
                                    # TOP-LEVEL key: old clients drop it.
    players_here: list[dict] = field(default_factory=list)
                                    # 042: who else stands in this room —
                                    # the presence grid, 7 tiles per row.
                                    # Entries: {opt, name, level, race,
                                    # armor, sleeping, gold, energy, sub,
                                    # rank}. opt is the click target
                                    # ("pv:<name>"); sub is an optional
                                    # line under the tile (warden boards
                                    # write damage there). A new TOP-LEVEL
                                    # key: old clients drop it.
    players_title: str = ""         # 042: heading over the grid — "" hides
    players_total: int = 0          # the TRUE room population — the card
                                    # says MORE N PLAYERS past the tiles
                                    # it ("PLAYERS HERE", "THE STRIKERS",
                                    # "THE HONORED FALLEN").
    refusal: str = ""               # 050: a rule said no — one short line
                                    # ("Can't buy this — not enough ◈").
                                    # The pane shows it as the top toast and
                                    # SKIPS the card swap; the in-card note
                                    # still rides for older clients. A new
                                    # TOP-LEVEL key: old clients drop it.
    kill3d: dict | None = None      # PLAN3: the live 3D kill finisher —
                                    # {id, race, line, breed, specimen},
                                    # stamped on a wilds victory card only.
                                    # The WEBSITE's fight3d layer mounts a
                                    # canvas over the banner from it; every
                                    # other surface (and any client without
                                    # the bundle/WebGL/the GLB) ignores it
                                    # and plays the fx GIF as today. A new
                                    # TOP-LEVEL key: old clients drop it.

    def to_text(self) -> str:
        """Plain-text fallback — always works, cards are enhancement."""
        lines = [self.eyebrow, self.headline]
        if self.support:
            lines.append(self.support)
        # 027: the notice board reads as words on every surface — the card
        # draws it, the agent says it.
        for nt in self.notices:
            lines.append(f"! {nt.get('text', '')}")
        # 030 Phase 5: the agent reads the same paper the card draws.
        if self.paper and self.paper.get("items"):
            lines.append("— THE MORNING CRIER —")
            if self.paper.get("headline"):
                lines.append(self.paper["headline"])
            lines += [f"· {it}" for it in self.paper["items"]]
        if self.awaits_text:
            lines.append(f"⌨ waiting for a typed chat reply: "
                         f"{self.awaits_text}")
        if self.enemy:
            en = self.enemy
            _sp = (f" · SPD {en['mspd']}" if en.get("mspd") else "")
            lines.append(f"{en['name']} HP {en['hp']}/{en['hp_max']} · "
                         f"ATK {en['atk']} · DEF {en['def']}{_sp}")
            if en.get("tiers"):
                lines.append("◈ " + " · ".join(en["tiers"]))
            # 030 Phase 7: the odds ride the text card too
            drops = en.get("drops") or {}
            if drops.get("gold"):
                lines.append(f"· coins ◈ {drops['gold'][0]}–"
                             f"{drops['gold'][1]}")
            if drops.get("xp"):
                lines.append(f"· XP ✦ {drops['xp'][0]}–{drops['xp'][1]}")
            if en.get("range") == "at_range":
                lines.append("◇ at range — it hasn't reached you yet")
            elif en.get("range") == "close":
                lines.append("◇ close quarters — it is on top of you")
        if self.shard_note:
            lines.append(f"◆ {self.shard_note}")
        if self.strip and self.strip.get("text"):
            lines.append(self.strip["text"])
        for b in self.body_lines:
            # 007 fold markers degrade to a plain divider in text
            if b == "▣.":
                continue
            lines.append(f"— {b[2:]} —" if b.startswith("▣ ") else b)
        if self.options:
            lines.append("─" * 40)
            for i, o in enumerate(self.options, 1):
                hint = f"   ({o.hint})" if o.hint else ""
                badge = f" ({o.badge})" if getattr(o, "badge", 0) else ""
                lines.append(f" {i}) {o.label}{badge}{hint}")
        # 031 §11: the evening state reads as words on every surface
        if self.activity:
            lines.append(self.activity)
        # 042: the presence grid reads as words — the agent names who is
        # here the same way the card draws them.
        if self.players_here:
            lines.append(self.players_title or "PLAYERS HERE")
            for pl in self.players_here:
                tag = " (sleeping)" if pl.get("sleeping") else ""
                sub = f" — {pl['sub']}" if pl.get("sub") else ""
                rank = (f"{pl['rank']}. " if pl.get("rank") else "")
                lines.append(f"· {rank}{pl.get('name', '?')} "
                             f"L{pl.get('level', 1)}{tag}{sub}")
            extra = int(self.players_total or 0) - len(self.players_here)
            if extra > 0:
                lines.append(f"· … and {extra} more")
        if self.meters:
            m = self.meters
            stats = (f"   ATK {m.atk}   DEF {m.dfs}"
                     + (f"   SPD {m.spd}" if getattr(m, "spd", 0) else "")
                     if getattr(m, "atk", 0) else "")
            lines.append(
                f"HP {m.hp}/{m.hp_max}   ⚡ {m.energy}/{m.energy_max}   "
                f"XP {m.xp}/{m.xp_need}   LV {m.level}   gold {m.gold}"
                f"{stats}")
        # 010.1: ⚡/🔒 are one-character markers for the HTML renderer's
        # 1-bit glyphs; the text surface (the agent reads this) speaks in
        # words so no emoji ever leaks into a chat reply.
        return ("\n".join(lines)
                .replace("⚡", "energy").replace("🔒", "locked"))

    def to_dict(self) -> dict:
        return {
            "eyebrow": self.eyebrow,
            "headline": self.headline,
            "support": self.support,
            "shard_note": self.shard_note,
            "body_lines": self.body_lines,
            "options": [
                {"id": o.id, "label": o.label, "hint": o.hint,
                 "aether": o.aether, "locked": o.locked}
                for o in self.options],
            # A count rides BESIDE the options, never inside them: an older
            # client splats each option dict into its Option, so a key it has
            # never heard of costs it the whole world. Unknown TOP-LEVEL keys
            # are dropped by every version ever shipped.
            "option_badges": {o.id: o.badge for o in self.options if o.badge},
            "meters": vars(self.meters) if self.meters else None,
            "event_kind": self.event_kind,
            "banner": self.banner,
            "banner_variant": self.banner_variant,
            "fx": self.fx,
            "scene_id": self.scene_id,
            "awaits_text": self.awaits_text,
            "inventory": self.inventory,
            "tally": self.tally,
            "notices": self.notices,
            "ask": self.ask,
            "gallery": self.gallery,
            "paper": self.paper,
            "strip": self.strip,
            "enemy": self.enemy,
            "option_art": self.option_art,
            "grid": self.grid,
            "npc": self.npc,
            "activity": self.activity,
            "location": self.location,
            "players_here": self.players_here,
            "players_title": self.players_title,
            "players_total": int(self.players_total or 0),
            "refusal": self.refusal,
            "kill3d": self.kill3d,
        }

    @staticmethod
    def from_dict(d: dict) -> "Scene":
        md = dict(d["meters"]) if d.get("meters") else None
        if md and "mana" in md:
            # pre-006 stored scene (pending event): the ✦ meter was mana.
            # Map the keys so old docs still load; values are stale anyway.
            md["xp"] = md.pop("mana")
            md["xp_need"] = md.pop("mana_max")
        meters = Meters(**_known(Meters, md)) if md else None
        badges = dict(d.get("option_badges") or {})
        options = []
        for raw in d.get("options", []):
            opt = Option(**_known(Option, raw))
            if not opt.badge:
                opt.badge = int(badges.get(opt.id, 0) or 0)
            options.append(opt)
        return Scene(
            eyebrow=d.get("eyebrow", ""),
            headline=d.get("headline", ""),
            support=d.get("support", ""),
            shard_note=d.get("shard_note", ""),
            body_lines=list(d.get("body_lines", [])),
            options=options,
            meters=meters,
            event_kind=d.get("event_kind", ""),
            banner=d.get("banner", ""),
            banner_variant=d.get("banner_variant", ""),
            fx=d.get("fx", ""),
            scene_id=d.get("scene_id", ""),
            awaits_text=d.get("awaits_text", ""),
            inventory=list(d.get("inventory", [])),
            tally=list(d.get("tally", [])),
            notices=list(d.get("notices", [])),
            ask=(dict(d["ask"]) if d.get("ask") else None),
            gallery=list(d.get("gallery", [])),
            paper=(dict(d["paper"]) if d.get("paper") else None),
            strip=(dict(d["strip"]) if d.get("strip") else None),
            enemy=(dict(d["enemy"]) if d.get("enemy") else None),
            option_art=dict(d.get("option_art") or {}),
            grid=bool(d.get("grid", False)),
            npc=(dict(d["npc"]) if d.get("npc") else None),
            activity=d.get("activity", ""),
            location=d.get("location", ""),
            players_here=list(d.get("players_here", [])),
            players_title=d.get("players_title", ""),
            players_total=int(d.get("players_total", 0) or 0),
            refusal=d.get("refusal", ""),
            kill3d=(dict(d["kill3d"]) if d.get("kill3d") else None),
        )
