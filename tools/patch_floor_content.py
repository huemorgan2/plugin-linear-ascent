#!/usr/bin/env python3
"""008 bestiary retrofit — apply an authored band spec to floor YAMLs.

Text-based (never yaml.dump): existing prose keeps its exact
formatting; we only INSERT lore lines, traits lines, and whole new
encounter blocks. A spec is a python file assigning SPEC:

    SPEC = {
        11: {
            "lore": {"rust_hound": "one-breath dossier line", ...},
            "traits": {"rust_hound": ["fast"], ...},
            "new": [{"id": "...", "name": "...", "lore": "...",
                     "weight": 2, "traits": ["armor_med"],
                     "prose": "..."}],
        },
        ...
    }

Usage: python tools/patch_floor_content.py <spec.py>
Idempotent: an encounter that already has lore/traits is skipped.
"""

from __future__ import annotations

import os
import re
import sys
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
FLOORS = os.path.join(_HERE, "..", "plugin_linear_ascent", "content",
                      "floors")


def _fold(text: str, indent: int) -> str:
    """Render a >- folded scalar at the given key indent."""
    pad = " " * (indent + 2)
    return "\n".join(pad + ln for ln in textwrap.wrap(
        " ".join(text.split()), width=74 - indent - 2))


def _enc_block(e: dict) -> str:
    lines = [f"  - id: {e['id']}",
             f"    name: {e['name']}",
             "    lore: >-",
             _fold(e["lore"], 4),
             f"    weight: {e.get('weight', 2)}"]
    if e.get("traits"):
        lines.append(f"    traits: [{', '.join(e['traits'])}]")
    lines += ["    prose: >-", _fold(e["prose"], 4)]
    return "\n".join(lines) + "\n"


def patch_floor(num: int, spec: dict) -> list[str]:
    path = os.path.join(FLOORS, f"floor_{num:03d}.yaml")
    src = open(path).read()
    notes: list[str] = []

    for eid, lore in (spec.get("lore") or {}).items():
        m = re.search(rf"(  - id: {re.escape(eid)}\n    name: [^\n]+\n)",
                      src)
        if not m:
            notes.append(f"floor {num}: encounter {eid} not found (lore)")
            continue
        block_after = src[m.end():m.end() + 20]
        if block_after.startswith("    lore:"):
            continue
        ins = "    lore: >-\n" + _fold(lore, 4) + "\n"
        src = src[:m.end()] + ins + src[m.end():]

    for eid, traits in (spec.get("traits") or {}).items():
        m = re.search(
            rf"  - id: {re.escape(eid)}\n(?:    [^\n]+\n|      [^\n]+\n)*?"
            rf"(    weight: \d+\n)", src)
        if not m:
            notes.append(f"floor {num}: encounter {eid} not found (traits)")
            continue
        after = src[m.end():m.end() + 20]
        if after.startswith("    traits:"):
            continue
        ins = f"    traits: [{', '.join(traits)}]\n"
        src = src[:m.end()] + ins + src[m.end():]

    news = spec.get("new") or []
    for e in news:
        if f"  - id: {e['id']}\n" in src:
            continue
        wpos = src.index("warden:")
        src = src[:wpos] + _enc_block(e) + src[wpos:]

    open(path, "w").write(src)
    return notes


def main() -> None:
    spec_path = sys.argv[1]
    ns: dict = {}
    exec(open(spec_path).read(), ns)  # noqa: S102 — authored specs only
    all_notes: list[str] = []
    for num, fspec in sorted(ns["SPEC"].items()):
        all_notes += patch_floor(num, fspec)
    for n in all_notes:
        print("!!", n)
    print(f"patched {len(ns['SPEC'])} floors"
          + (f" — {len(all_notes)} problems" if all_notes else ""))


if __name__ == "__main__":
    main()
