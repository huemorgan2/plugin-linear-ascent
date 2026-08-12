#!/usr/bin/env python3
"""049 demo: model-rendered player-in-scene composites -> demoimages4/.

Different tactic from demoimages3 (pixel paste looked glued on): the
model gets TWO reference images — the monster scene from demoimages2/
and the player render from demo-players/ — and re-renders the scene
with the character actually standing in it: grounded, contact shadow,
lit by the scene's light.

Full grid: 14 floor 1-2 monsters x 3 players x 3 weapons = 126
images, named floor-first so they sort by floor:
  floor{NNN}_{monster}_{player}_{weapon}.jpg

Already-existing outputs are skipped, so rerunning fills gaps.

Usage:
  python plans/049-monster-image-remake/gen_demoimages4.py [name ...]
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
"""

from __future__ import annotations

import asyncio
import glob
import importlib.util
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
FLOORS = os.path.join(_ROOT, "plugin_linear_ascent", "content", "floors")
PLAYERS = os.path.join(_HERE, "demo-players")
MONSTERS = os.path.join(_HERE, "demoimages2")
OUT = os.path.join(_HERE, "demoimages4")

_prov = os.path.join(_ROOT, "..", "plugin-image-gen",
                     "plugin_image_gen", "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _prov)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

PLAYER_COMBOS = [f"{c}_{w}"
                 for c in ("fighter", "elf", "giant")
                 for w in ("wand", "bow", "sword")]

PROMPT = (
    "The first reference image is a scene: a dark black-and-white "
    "semi-realistic 3D-rendered landscape with a creature at the {mside} "
    "edge. The second reference image is a character on a black "
    "background. Recreate the FIRST image EXACTLY — same landscape, same "
    "creature in the same pose and position, same lighting, same camera — "
    "and add the character from the second image INTO the scene, standing "
    "on the ground at the {pside} edge of the frame, in full side view, "
    "facing the creature. The character must truly belong to the scene: "
    "feet planted on the terrain, a natural contact shadow, lit by the "
    "scene's own light with the same dramatic rim light, matching grain "
    "and atmosphere, partially framed by foreground depth. Keep the "
    "character's exact appearance, outfit and weapon from the second "
    "image{scale}. Monochrome greyscale only, no color, no text, no "
    "borders, no watermark."
)
HUMAN_IN_SCENE = (", at a realistic human scale for the scene")
GIANT_IN_SCENE = (", a towering giant — noticeably taller and wider than "
                  "a human would be in this scene")


def load_monsters() -> list[dict]:
    """Floor 1-2 monsters in gen_demoimages.py job order, with the
    LEFT/RIGHT edge each was prompted to (parity of the running index)."""
    out, i = [], 0
    for path in sorted(glob.glob(os.path.join(FLOORS, "floor_*.yaml"))):
        d = yaml.safe_load(open(path))
        if d["floor"] not in (1, 2):
            continue
        ids = [e["id"] for e in d["encounters"]] + ["warden"]
        for mid in ids:
            out.append({
                "floor": d["floor"],
                "id": mid,
                "scene": f"floor{d['floor']}_{mid}",
                "side": "LEFT" if i % 2 else "RIGHT",
            })
            i += 1
    return out


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


async def gen_one(job: dict, key: str) -> str:
    res = await providers._gemini_generate(
        providers.MODELS["nano-banana-pro"], job["prompt"],
        aspect="21:9", refs=job["refs"], api_key=key,
    )
    if "error" in res:
        return f"FAIL {job['slug']}: {res['error']} — {str(res.get('detail'))[:200]}"
    ext = "png" if "png" in res.get("mime", "") else "jpg"
    open(os.path.join(OUT, f"{job['slug']}.{ext}"), "wb").write(
        res["image_bytes"])
    return f"ok   {job['slug']}"


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    key = api_key()
    jobs = []
    for m in load_monsters():
        scene_bytes = open(os.path.join(MONSTERS, f"{m['scene']}.jpg"),
                           "rb").read()
        for pw in PLAYER_COMBOS:
            slug = f"floor{m['floor']:03d}_{m['id']}_{pw}"
            pside = "LEFT" if m["side"] == "RIGHT" else "RIGHT"
            scale = (GIANT_IN_SCENE if pw.startswith("giant")
                     else HUMAN_IN_SCENE)
            jobs.append({
                "slug": slug,
                "prompt": PROMPT.format(mside=m["side"], pside=pside,
                                        scale=scale),
                "refs": [
                    (scene_bytes, "image/jpeg"),
                    (open(os.path.join(PLAYERS, f"{pw}.jpg"), "rb").read(),
                     "image/jpeg"),
                ],
            })
    if len(sys.argv) > 1:
        want = set(sys.argv[1:])
        jobs = [j for j in jobs if j["slug"] in want]
    else:
        jobs = [j for j in jobs
                if not os.path.exists(os.path.join(OUT, f"{j['slug']}.jpg"))]
    print(f"{len(jobs)} images -> {OUT}", flush=True)
    fails = 0
    for i in range(0, len(jobs), 4):
        batch = jobs[i:i + 4]
        for line in await asyncio.gather(*(gen_one(j, key) for j in batch)):
            fails += line.startswith("FAIL")
            print(line, flush=True)
    print(f"done, {fails} failed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
