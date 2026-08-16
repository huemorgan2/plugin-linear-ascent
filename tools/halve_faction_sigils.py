"""010 phase 3: the strip's sigil at half resolution.

320x112 -> 160x56 with NEAREST (no new greys), then re-threshold so the
result stays pure white-on-transparent 1-bit — the strip tints it via
CSS mask, so any grey would tint too. Writes <slug>_160x56.png beside
each original; rerunnable, overwrites.

Run:  ../luna/.venv/bin/python tools/halve_faction_sigils.py
"""

import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FACTIONS = os.path.join(HERE, "..", "plugin_linear_ascent", "content",
                        "art", "banners", "factions")


def halve(path: str, out: str) -> None:
    img = Image.open(path).convert("RGBA")
    assert img.size == (320, 112), f"{path}: {img.size}"
    small = img.resize((160, 56), Image.NEAREST)
    px = small.load()
    for y in range(56):
        for x in range(160):
            r, g, b, a = px[x, y]
            px[x, y] = (255, 255, 255, 255) if a >= 128 else (0, 0, 0, 0)
    small.save(out, optimize=True)


def main() -> None:
    done = 0
    for name in sorted(os.listdir(FACTIONS)):
        if not name.endswith("_320x112.png"):
            continue
        slug = name.removesuffix("_320x112.png")
        out = os.path.join(FACTIONS, f"{slug}_160x56.png")
        halve(os.path.join(FACTIONS, name), out)
        done += 1
        print(f"{slug}: 160x56 written")
    print(f"{done} sigils halved")


if __name__ == "__main__":
    main()
