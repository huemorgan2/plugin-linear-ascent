#!/usr/bin/env python3
"""032 art — the banner hall's rooms and doors.

Same parametric pipeline as generate_030_art.py (imported for the
crop/dither helpers): Gemini paints, center-crop to the target aspect,
downscale, autocontrast, Bayer 8x8 -> 1-bit white ink on alpha.

Jobs (plan 032's asset ledger):
  bands  hall_room_{1,2,3,4}_320x50.png   (the four room-tier interiors)
  doors  hall_{coffer,chest,board,bunks,works,desk}_320x112.png
         (option art beside the hall's door rows)

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_032_art.py [name ...]
  no args = everything missing; --force redoes.
"""

from __future__ import annotations

import asyncio
import io
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import generate_banners as gb  # noqa: E402  (style, BAYER, providers)
import generate_030_art as g30  # noqa: E402  (to_1bit, bits_to_png)

providers = gb.providers
BANNERS = g30.BANNERS
RAW = os.path.join(_HERE, "..", "content", "art", "032", "raw")
PREVIEW = os.path.join(_HERE, "..", "content", "art", "032", "preview")

DIM = g30.DIM
GOLD = g30.GOLD

BAND = (
    "Composition: one extremely wide LOW HORIZONTAL BAND seen "
    "straight-on, everything inside the band, no sky. "
)

# tier -> interior. The room IS the progress bar: each band must read
# richer than the one before it at a glance.
ROOM_JOBS = {
    "hall_room_1": (
        "the inside of a cramped curtained alcove behind a guildhall: "
        "a patched hanging curtain drawn half open at one side, one "
        "small rough table with a single stub of candle, a low bench, "
        "a folded banner cloth on a wall peg, bare plank walls — poor, "
        "dim, one warm glow fading into darkness at both ends."),
    "hall_room_2": (
        "the inside of a modest plank-walled hall: one long timber "
        "table with benches down the middle, a small iron-bound coffer "
        "on a side shelf, two hanging lanterns throwing overlapping "
        "glows, a single banner hung flat on the back wall — honest, "
        "warm, newly swept."),
    "hall_room_3": (
        "the inside of a long stone hall: a blazing hearth at one end "
        "raking light down the band, racked spears and shields along "
        "the wall, banners hanging from roof beams, a long feast table "
        "with tankards, an iron chandelier of candles — established, "
        "proud, war-ready."),
    "hall_room_4": (
        "the inside of a grand high hall where old timber meets "
        "arcanotech: a floating chandelier of glowing power seams and "
        "holographic rings over ancient beams, tall banner drops down "
        "stone columns, a dais with a great table, cables and conduits "
        "woven along the walls between trophies — wealth, power, the "
        "top of the ladder."),
}

# doors — one bold object each, banner grammar (a thing, not a scene)
DOOR_JOBS = {
    "hall_coffer": (
        "a massive iron-bound strongbox coffer seen straight-on, "
        "banded in riveted metal straps with a glowing arcanotech "
        "lock seam, a few gold coins spilled at its feet, backed by a "
        "soft radial glow fading to black."),
    "hall_chest": (
        "a heavy wooden chest with its lid thrown open, faint light "
        "rising from inside over the rim, sword hilts and a helm "
        "poking above the edge, backed by a soft radial glow fading "
        "to black."),
    "hall_board": (
        "a plank bulletin board nailed with overlapping small paper "
        "notes, one dagger pinning the topmost note, the papers as "
        "soft unreadable dither blocks, backed by a soft radial glow "
        "fading to black."),
    "hall_bunks": (
        "a sturdy wooden bunk bed with two blanketed cots, a folded "
        "blanket at the foot, one small lantern hanging from the "
        "post, backed by a soft radial glow fading to black."),
    "hall_works": (
        "crossed mason's tools — a heavy hammer over a chisel and a "
        "coiled measuring line — above a half-built stone wall "
        "course, backed by a soft radial glow fading to black."),
    "hall_desk": (
        "a steward's writing desk seen straight-on with a quill "
        "standing in an inkwell, a stack of sealed letters and a "
        "burning candle, backed by a soft radial glow fading to "
        "black."),
}


def _jobs() -> dict[str, tuple[str, tuple[int, int], str, str]]:
    jobs = {}
    for slug, prompt in ROOM_JOBS.items():
        jobs[slug] = (gb.STYLE + BAND + prompt, (320, 50), BANNERS, GOLD)
    for slug, prompt in DOOR_JOBS.items():
        jobs[slug] = (gb.STYLE + prompt, (320, 112), BANNERS, DIM)
    return jobs


async def gen_one(name: str, job, api_key: str) -> str:
    prompt, (w, h), outdir, tint = job
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], prompt,
        aspect=g30._aspect_for(w, h), api_key=api_key,
    )
    if "error" in res:
        return f"FAIL {name}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(RAW, f"{name}_raw.png"))
    bits = g30.to_1bit(raw, w, h)
    g30.bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(outdir, f"{name}_{w}x{h}.png"))
    g30.bits_to_png(bits, g30._hx(tint), scale=2, bg=g30.PANEL).save(
        os.path.join(PREVIEW, f"{name}_preview.png"))
    ink = sum(map(sum, bits)) / (w * h)
    return f"ok   {name}: {w}x{h} ink {ink:.0%}"


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jobs = _jobs()
    unknown = [a for a in args if a not in jobs]
    if unknown:
        sys.exit(f"unknown jobs: {unknown}; have {sorted(jobs)}")
    for d in (BANNERS, RAW, PREVIEW):
        os.makedirs(d, exist_ok=True)
    names = args or [
        n for n, (_, (w, h), outdir, _) in jobs.items()
        if force or not os.path.exists(
            os.path.join(outdir, f"{n}_{w}x{h}.png"))]
    if not names:
        print("nothing to do — all assets exist (use --force)")
        return
    for i in range(0, len(names), 4):
        batch = names[i:i + 4]
        for line in await asyncio.gather(
                *(gen_one(n, jobs[n], api_key) for n in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
