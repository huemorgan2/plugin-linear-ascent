"""Scene — the single shape every game message takes.

The renderer contract from design/chat_components.md: the engine emits a
Scene; one renderer maps it to a card; the plain-text fallback is generated
from the same object. Content never contains markup.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Option:
    id: str                 # stable id, e.g. "attack", "buy_pigsticker"
    label: str
    hint: str = ""          # right-aligned cost/class hint, e.g. "1 ⚡"
    aether: bool = False    # class/sidekick option — aether key chip
    locked: bool = False    # 019: a gated row — dimmed, still clickable;
                            # choosing it returns the scene with the
                            # refusal that explains the gate


@dataclass
class Meters:
    hp: int
    hp_max: int
    energy: int
    energy_max: int
    xp: int             # the XP pool inside the level (banks past the cap)
    xp_need: int        # xp_need(level) — full bar = licensed to train
    gold: int
    level: int = 1      # 012: shown next to the gold


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
    inventory: list[dict] = field(default_factory=list)
                                    # 014: the pack strip — stamped by core on
                                    # every playing scene. Entries:
                                    # {slug, name, count, kind, equipped?}
                                    # kind ∈ weapon|shield|armor|item
    enemy: dict | None = None       # 017/003: the fight dossier payload —
                                    # {name, hp, hp_max, atk, def, profile,
                                    #  range, lore, specimen, pspd, dtype,
                                    #  dodge}. The renderer draws the enemy
                                    #  HP bar, range chip and [i] card from
                                    #  this; content stays markup-free.

    def to_text(self) -> str:
        """Plain-text fallback — always works, cards are enhancement."""
        lines = [self.eyebrow, self.headline]
        if self.support:
            lines.append(self.support)
        if self.awaits_text:
            lines.append(f"⌨ waiting for a typed chat reply: "
                         f"{self.awaits_text}")
        if self.enemy:
            en = self.enemy
            lines.append(f"{en['name']} HP {en['hp']}/{en['hp_max']}")
            if en.get("tiers"):
                lines.append("◈ " + " · ".join(en["tiers"]))
            if en.get("range") == "at_range":
                lines.append("◇ at range — it hasn't reached you yet")
            elif en.get("range") == "close":
                lines.append("◇ close quarters — it is on top of you")
        if self.shard_note:
            lines.append(f"◆ {self.shard_note}")
        for b in self.body_lines:
            # 007 fold markers degrade to a plain divider in text
            if b == "▣.":
                continue
            lines.append(f"— {b[2:]} —" if b.startswith("▣ ") else b)
        if self.options:
            lines.append("─" * 40)
            for i, o in enumerate(self.options, 1):
                hint = f"   ({o.hint})" if o.hint else ""
                lines.append(f" {i}) {o.label}{hint}")
        if self.meters:
            m = self.meters
            lines.append(
                f"HP {m.hp}/{m.hp_max}   ⚡ {m.energy}/{m.energy_max}   "
                f"XP {m.xp}/{m.xp_need}   LV {m.level}   gold {m.gold}")
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
            "meters": vars(self.meters) if self.meters else None,
            "event_kind": self.event_kind,
            "banner": self.banner,
            "banner_variant": self.banner_variant,
            "fx": self.fx,
            "scene_id": self.scene_id,
            "awaits_text": self.awaits_text,
            "inventory": self.inventory,
            "enemy": self.enemy,
        }

    @staticmethod
    def from_dict(d: dict) -> "Scene":
        md = dict(d["meters"]) if d.get("meters") else None
        if md and "mana" in md:
            # pre-006 stored scene (pending event): the ✦ meter was mana.
            # Map the keys so old docs still load; values are stale anyway.
            md["xp"] = md.pop("mana")
            md["xp_need"] = md.pop("mana_max")
        meters = Meters(**md) if md else None
        return Scene(
            eyebrow=d.get("eyebrow", ""),
            headline=d.get("headline", ""),
            support=d.get("support", ""),
            shard_note=d.get("shard_note", ""),
            body_lines=list(d.get("body_lines", [])),
            options=[Option(**o) for o in d.get("options", [])],
            meters=meters,
            event_kind=d.get("event_kind", ""),
            banner=d.get("banner", ""),
            banner_variant=d.get("banner_variant", ""),
            fx=d.get("fx", ""),
            scene_id=d.get("scene_id", ""),
            awaits_text=d.get("awaits_text", ""),
            inventory=list(d.get("inventory", [])),
            enemy=(dict(d["enemy"]) if d.get("enemy") else None),
        )
