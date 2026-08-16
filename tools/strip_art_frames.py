#!/usr/bin/env python3
"""062 — some rendered item arts came back with a picture-frame: a
thin bright rule down one or both sides (sometimes top/bottom) with an
empty gutter between it and the object. Detect the rule on the raw
(the 5:8 crop the shipped pair is cut from), black it out with its
gutter, and re-derive the shipped 100x160 + 30x48 pair through the
same _enforce as the generators.

Usage: python tools/strip_art_frames.py [--dry] [--sheet]
"""
from __future__ import annotations

import glob
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import generate_weapon_art as gw               # noqa: E402
import generate_gear_art as gg                 # noqa: E402

_ROOT = os.path.join(_HERE, "..")
RAWS = (glob.glob(os.path.join(gg.RAW_DIR, "*_raw.png"))
        + glob.glob(os.path.join(gw.RAW_DIR, "*_raw.png"))
        + glob.glob(os.path.join(gw.P1_DIR, "*_raw.png")))
LW, LH, IW, IH = gw.LW, gw.LH, gw.IW, gw.IH


def crop58(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    iw, ih = img.size
    t = LW / LH
    if iw / ih > t:
        nw = int(ih * t)
        return img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    nh = int(iw / t)
    return img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))


def _cuts(prof: list[float], n: int) -> list[tuple[str, int]]:
    """A bright group (≤5% wide, peak ≥ .15) hugging an edge, then a
    dark gutter (≥3%) — that's a frame rule, not the object."""
    edge = int(n * 0.14)
    out = []
    for side in ("lo", "hi"):
        xs = list(range(0, edge)) if side == "lo" \
            else list(range(n - 1, n - 1 - edge, -1))
        # a solid white margin hugging the edge (≥3 columns at ≥.85) is
        # a mat, never the object — cut it whatever follows
        m = 0
        while m < len(xs) and prof[xs[m]] >= 0.85:
            m += 1
        if 3 <= m <= n * 0.08:
            out.append((side, xs[m - 1]))
            continue
        i = 0
        while i < len(xs) and prof[xs[i]] < 0.06:
            i += 1
        j = i
        while j < len(xs) and prof[xs[j]] >= 0.06:
            j += 1
        grp = xs[i:j]
        if not grp or len(grp) > n * 0.05:
            continue
        if max(prof[x] for x in grp) < 0.15:
            continue
        # a near-solid hairline (≤1.5% wide, ≥.85 bright) that far out is
        # a rule even when the object leans on it
        if len(grp) <= n * 0.015 and max(prof[x] for x in grp) >= 0.85:
            out.append((side, grp[-1]))
            continue
        k, gap = j, 0
        while k < len(xs) and prof[xs[k]] < 0.04:
            gap += 1
            k += 1
        if gap >= n * 0.03:
            out.append((side, grp[-1]))
    return out


def detect(img: Image.Image) -> tuple[list, list]:
    w, h = img.size
    px = img.load()
    cols = [sum(px[x, y] for y in range(h)) / (255 * h) for x in range(w)]
    rows = [sum(px[x, y] for x in range(w)) / (255 * w) for y in range(h)]
    return _cuts(cols, w), _cuts(rows, h)


def erase(img: Image.Image, vcuts: list, hcuts: list) -> Image.Image:
    w, h = img.size
    px = img.load()
    for side, x in vcuts:
        rng = range(0, min(w, x + 3)) if side == "lo" \
            else range(max(0, x - 2), w)
        for xx in rng:
            for y in range(h):
                px[xx, y] = 0
    for side, y in hcuts:
        rng = range(0, min(h, y + 3)) if side == "lo" \
            else range(max(0, y - 2), h)
        for yy in rng:
            for x in range(w):
                px[x, yy] = 0
    return img


def ship_paths(slug: str) -> tuple[str, str]:
    for mod in (gw, gg):
        lp, ip = mod._paths(slug)
        if os.path.exists(lp):
            return lp, ip
    raise SystemExit(f"no shipped art for {slug}")


def main() -> None:
    dry = "--dry" in sys.argv
    hits = []
    for p in sorted(RAWS):
        slug = os.path.basename(p)[: -len("_raw.png")]
        img = crop58(Image.open(p))
        v, hz = detect(img)
        if not (v or hz):
            continue
        hits.append((slug, v, hz, img))
        print(f"{slug}: cols {v} rows {hz}", flush=True)
        if dry:
            continue
        fixed = erase(img, v, hz)
        lp, ip = ship_paths(slug)
        gw._enforce(fixed, LW, LH).save(lp)
        gw._enforce(fixed, IW, IH).save(ip)
    print(f"{len(hits)} framed art{'s' if len(hits) != 1 else ''}"
          f"{' (dry)' if dry else ' re-shipped'}")


if __name__ == "__main__":
    main()
