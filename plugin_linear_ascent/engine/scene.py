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


@dataclass
class Meters:
    hp: int
    hp_max: int
    energy: int
    energy_max: int
    mana: int
    mana_max: int
    gold: int


@dataclass
class Scene:
    eyebrow: str                    # "FLOOR 12 · IRONVALE · THE FLOODED MINE"
    headline: str                   # the bottom line, numbers included
    support: str = ""               # one dim line
    shard_note: str = ""            # sidekick whisper (aether stripe)
    body_lines: list[str] = field(default_factory=list)
    options: list[Option] = field(default_factory=list)
    meters: Meters | None = None
    event_kind: str = ""            # "" | loot | death | letter | boss | present
    banner: str = ""                # banner slug, "" = no banner
    scene_id: str = ""              # nonce — ascent_choose must echo the ids of THIS scene

    def to_text(self) -> str:
        """Plain-text fallback — always works, cards are enhancement."""
        lines = [self.eyebrow, self.headline]
        if self.support:
            lines.append(self.support)
        if self.shard_note:
            lines.append(f"◆ {self.shard_note}")
        lines += self.body_lines
        if self.options:
            lines.append("─" * 40)
            for i, o in enumerate(self.options, 1):
                hint = f"   ({o.hint})" if o.hint else ""
                lines.append(f" {i}) {o.label}{hint}")
        if self.meters:
            m = self.meters
            lines.append(
                f"HP {m.hp}/{m.hp_max}   ⚡ {m.energy}/{m.energy_max}   "
                f"✦ {m.mana}/{m.mana_max}   gold {m.gold}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "eyebrow": self.eyebrow,
            "headline": self.headline,
            "support": self.support,
            "shard_note": self.shard_note,
            "body_lines": self.body_lines,
            "options": [
                {"id": o.id, "label": o.label, "hint": o.hint,
                 "aether": o.aether} for o in self.options],
            "meters": vars(self.meters) if self.meters else None,
            "event_kind": self.event_kind,
            "banner": self.banner,
            "scene_id": self.scene_id,
        }

    @staticmethod
    def from_dict(d: dict) -> "Scene":
        meters = Meters(**d["meters"]) if d.get("meters") else None
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
            scene_id=d.get("scene_id", ""),
        )
