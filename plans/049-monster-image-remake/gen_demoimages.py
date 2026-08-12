#!/usr/bin/env python3
"""049 demo: floor 1-2 creatures in the pencil-drawing style.

Prompts: pencil STYLE preamble + floor landscape (arrival) + the
creature's name and prose from the floor YAML. Raw model output only —
no 1-bit post-process; the delivery format is decided after review.

Usage:
  python plans/049-monster-image-remake/gen_demoimages.py
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
"""

from __future__ import annotations

import asyncio
import glob
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
FLOORS = os.path.join(_ROOT, "plugin_linear_ascent", "content", "floors")
OUT = os.path.join(_HERE, "demoimages2")

# load providers.py by path — the package __init__ pulls in luna_sdk,
# which this venv doesn't carry and the demo doesn't need
import importlib.util  # noqa: E402

_prov = os.path.join(_ROOT, "..", "plugin-image-gen",
                     "plugin_image_gen", "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _prov)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

STYLE = (
    "Black and white 3D render, semi-realistic, in the style of a dark "
    "arcade fighting-game stage. Wide horizontal landscape backdrop, DARK "
    "and moody, filled completely with dense detail edge to edge — no "
    "empty space, no white paper, every part of the frame carries scenery. "
    "Camera pulled far back — a wide zoomed-out shot where the landscape "
    "dominates. ONE creature standing in full SIDE VIEW (profile), feet "
    "on the ground, positioned at the extreme {side} EDGE of the frame, "
    "small against the vast scenery (about a quarter of the frame "
    "height), sharp readable silhouette picked out by "
    "strong dramatic rim light against the dark background. Monochrome "
    "greyscale only, high contrast, cinematic lighting, realistic "
    "detailed textures and materials. "
    "No color, no text, no borders, no watermark. "
)

NO_TEXT = (" IMPORTANT: render any signs, banners, or lettering mentioned "
           "above as illegible weathered marks — absolutely no readable "
           "letters or words anywhere in the image.")


def api_key() -> str:
    key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if key:
        return key
    env = os.path.join(_ROOT, "..", "luna", ".env")
    if os.path.exists(env):
        for line in open(env):
            line = line.strip()
            if line.startswith("LUNA_GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("LUNA_GEMINI_API_KEY not set (env or luna/.env)")


def load_jobs() -> list[dict]:
    jobs = []
    for path in sorted(glob.glob(os.path.join(FLOORS, "floor_*.yaml"))):
        d = yaml.safe_load(open(path))
        if d["floor"] not in (1, 2):
            continue
        setting = " ".join(d["arrival"].split())
        for e in d["encounters"]:
            prose = " ".join(e["prose"].split())
            style = STYLE.format(side="LEFT" if len(jobs) % 2 else "RIGHT")
            jobs.append({
                "slug": f"floor{d['floor']}_{e['id']}",
                "prompt": (f"{style}Creature: {e['name']}. {prose} "
                           f"Setting: {setting}{NO_TEXT}"),
            })
        prose = " ".join(d["warden"]["prose"].split())
        style = STYLE.format(side="LEFT" if len(jobs) % 2 else "RIGHT")
        jobs.append({
            "slug": f"floor{d['floor']}_warden",
            "prompt": (f"{style}Creature: {d['warden']['name']}, the floor "
                       f"boss guarding the stair-gate. {prose} "
                       f"Setting: {setting}{NO_TEXT}"),
        })
    return jobs


async def gen_one(job: dict, key: str) -> str:
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], job["prompt"],
        aspect="21:9", api_key=key,
    )
    if "error" in res:
        return f"FAIL {job['slug']}: {res['error']} — {str(res.get('detail'))[:200]}"
    ext = "png" if "png" in res.get("mime", "") else "jpg"
    path = os.path.join(OUT, f"{job['slug']}.{ext}")
    open(path, "wb").write(res["image_bytes"])
    return f"ok   {job['slug']}"


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    key = api_key()
    jobs = load_jobs()
    if len(sys.argv) > 1:
        want = set(sys.argv[1:])
        jobs = [j for j in jobs if j["slug"] in want]
    print(f"{len(jobs)} images -> {OUT}")
    for i in range(0, len(jobs), 4):
        batch = jobs[i:i + 4]
        for line in await asyncio.gather(*(gen_one(j, key) for j in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
