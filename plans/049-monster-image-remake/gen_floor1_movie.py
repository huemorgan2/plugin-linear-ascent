#!/usr/bin/env python3
"""049: floor-1 kill movies -> floor1/movies/.

One Veo clip per (monster, race, weapon line): the player kills the
monster with the weapon of their line, then the kind-correct ending —
  native    -> Liberation Dissolve to the `was:` animal at true size
  pressed   -> the goblin falls; its sword stays in the grass
  wrongmade -> evicted: collapses to dead brush / scrap, nothing living

Identity is the GAME's: race in {human, elf, dwarf}, line in
{blade, bow, staff}. Scene sources still use the demo names
(fighter/elf/dwarf x wand/bow/sword) — mapped below.

Outputs per slug {id}_{race}_{line}:
  floor1/movies/{slug}.mp4   raw Veo movie
  floor1/movies/{slug}.mpg   MPEG conversion
  floor1/movies/{slug}.gif   1-bit frame-by-frame review GIF (640x224)

Usage:
  python gen_floor1_movie.py [slug ...]     (default: every missing one)
Skips slugs whose .mp4 already exists (unless passed explicitly).
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
SCENES = os.path.join(_HERE, "floor1", "scenes")
OUT = os.path.join(_HERE, "floor1", "movies")

GEMINI_ROOT = "https://generativelanguage.googleapis.com/v1beta"
VEO_MODELS = ["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"]

W, H = 320, 112
GIF_FPS = 10
BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
])

RACES = {"human": "fighter", "elf": "elf", "dwarf": "dwarf"}
LINES = {"blade": "sword", "bow": "bow", "staff": "wand"}

PLAYER = {
    "human": "the human woman fighter",
    "elf": "the slender male elf",
    "dwarf": "the stout bearded dwarf",
}

KILL = {
    "blade": ("{player} lunges forward and cuts the monster down with "
              "one clean powerful sword slash"),
    "bow": ("{player} draws their bow and fires a single arrow that "
            "strikes the monster in the chest"),
    "staff": ("{player} raises their wand and fires a single bright "
              "bolt of light that strikes the monster"),
}

DISSOLVE = (
    "Then the LIBERATION DISSOLVE: the monster's black silhouette "
    "flares at the rim, cracks with hairline white lines, and breaks "
    "apart into square chunky dither particles that lift and scatter "
    "upward like sparks, while the fever's magic leaves it as one thin "
    "ribbon of sparse dither curling up and away. When the particle "
    "cloud thins, what remains standing in the monster's place is "
    "{true_form}, calm, at its real small size. "
)

FALL = (
    "The goblin staggers, drops to its knees and falls dead in the "
    "grass. Its notched longsword slips from its hand and stays lying "
    "in the grass beside it. A single thin ribbon of sparse dither "
    "drifts up from the body and fades. Nothing else changes. "
)

EVICT = (
    "Then the EVICTION: the creature's form flares at the rim, and the "
    "aether that held it together leaves as one thin ribbon of sparse "
    "dither curling up and away. {wreck} Nothing living remains. "
)

# id -> (verb, ending prompt)
MONSTERS = {
    "grey_wolf": ("freed", DISSOLVE.format(
        true_form="the shy grey wolf the farm dogs kept past the "
                  "fences — knee-high to the monster it was, thin and "
                  "ordinary")),
    "feral_boar": ("freed", DISSOLVE.format(
        true_form="an ordinary small sty boar, escaped farm stock, "
                  "knee-high and harmless")),
    "hedge_rat": ("freed", DISSOLVE.format(
        true_form="an ordinary small granary rat, hand-sized, "
                  "whiskers twitching")),
    "lane_wolf": ("freed", DISSOLVE.format(
        true_form="one of the steading's own sheepdogs — an ordinary "
                  "farm dog again, ears up, waiting for a whistle")),
    "goblin_straggler": ("fall", FALL),
    "ember_shade": ("evicted", EVICT.format(
        wreck="The man-shape of snarled blackthorn loses its hold and "
              "collapses back into the hedge — a heap of dead brush "
              "and a rotten stile.")),
    "warden": ("evicted", EVICT.format(
        wreck="The welded plate splits at the seams and the whole "
              "beast collapses into a dead heap of scrap plate and "
              "still servos.")),
}


def movie_prompt(mid: str, race: str, line: str) -> str:
    verb, ending = MONSTERS[mid]
    return (
        "Animate this 1-bit pixel art scene. Keep the style at all "
        "times: strictly pure black and pure white, ordered Bayer "
        "dithering, solid dark figures with white rim contours, no "
        "color, no text. The camera and background stay fixed. "
        f"First, {KILL[line].format(player=PLAYER[race])}. "
        "The monster staggers. " + ending
    )


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


def _post(url: str, body: dict, key: str) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _get(url: str, key: str) -> dict:
    """Poll read — rides out transient network/DNS failures."""
    for attempt in range(6):
        try:
            req = urllib.request.Request(
                url, headers={"x-goog-api-key": key})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, OSError):
            if attempt == 5:
                raise
            time.sleep(30 * (attempt + 1))
    raise RuntimeError("unreachable")


def _find_video(node) -> tuple[str | None, str | None]:
    """Recursively find (download_uri, base64_bytes) in the op result."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("bytesBase64Encoded", "videoBytes") and isinstance(v, str):
                return None, v
            if k in ("uri", "videoUri") and isinstance(v, str) \
                    and v.startswith("http"):
                return v, None
            uri, b64 = _find_video(v)
            if uri or b64:
                return uri, b64
    elif isinstance(node, list):
        for v in node:
            uri, b64 = _find_video(v)
            if uri or b64:
                return uri, b64
    return None, None


def veo_generate(prompt: str, image_path: str, key: str,
                 mp4_out: str) -> str | None:
    """Generate one clip; returns None on success, error string on fail."""
    img_b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    last_err = "no veo model accepted the request"
    for model in VEO_MODELS:
        body = {
            "instances": [{
                "prompt": prompt,
                "image": {"bytesBase64Encoded": img_b64,
                          "mimeType": "image/jpeg"},
            }],
            "parameters": {"aspectRatio": "16:9"},
        }
        op = None
        for attempt in range(4):
            try:
                op = _post(f"{GEMINI_ROOT}/models/{model}"
                           ":predictLongRunning", body, key)
                break
            except urllib.error.HTTPError as e:
                detail = e.read()[:200]
                if e.code in (429, 500, 503):
                    time.sleep(45 * (attempt + 1))
                    continue
                last_err = f"{model}: HTTP {e.code} {detail!r}"
                op = None
                break
            except (urllib.error.URLError, OSError) as e:
                last_err = f"{model}: network {e}"
                time.sleep(45 * (attempt + 1))
                op = None
        if not op or not op.get("name"):
            continue
        name = op["name"]
        deadline = time.time() + 15 * 60
        while time.time() < deadline:
            time.sleep(15)
            try:
                op = _get(f"{GEMINI_ROOT}/{name}", key)
            except urllib.error.HTTPError:
                continue
            if op.get("done"):
                break
        if not op.get("done"):
            last_err = f"{model}: operation timed out"
            continue
        if "error" in op:
            last_err = f"{model}: {str(op['error'])[:300]}"
            continue
        uri, b64 = _find_video(op.get("response", {}))
        if b64:
            open(mp4_out, "wb").write(base64.b64decode(b64))
            return None
        if uri:
            sep = "&" if "?" in uri else "?"
            req = urllib.request.Request(f"{uri}{sep}key={key}")
            with urllib.request.urlopen(req, timeout=300) as r:
                open(mp4_out, "wb").write(r.read())
            return None
        last_err = f"{model}: done but no video in response " \
                   f"{str(op.get('response'))[:300]}"
    return last_err


def to_1bit(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    iw, ih = img.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    a = np.asarray(img, dtype=np.float64)
    ty, tx = np.indices(a.shape)
    bits = np.where(a / 255 > (BAYER8[ty % 8, tx % 8] + 0.5) / 64,
                    255, 0).astype(np.uint8)
    return Image.fromarray(bits).convert("RGB").resize(
        (W * 2, H * 2), Image.NEAREST)


def mp4_to_mpg(mp4: str, mpg: str) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-i", mp4, "-c:v", "mpeg2video", "-q:v", "4",
         "-an", mpg],
        check=True, capture_output=True)


def mp4_to_gif(mp4: str, gif: str) -> None:
    reader = imageio.get_reader(mp4)
    fps = reader.get_meta_data().get("fps", 24)
    step = max(1, round(fps / GIF_FPS))
    frames = [to_1bit(Image.fromarray(f))
              for i, f in enumerate(reader) if i % step == 0]
    reader.close()
    if not frames:
        sys.exit(f"FAIL gif: no frames decoded from {mp4}")
    durations = [int(1000 * step / fps)] * len(frames)
    durations[-1] = 1500  # hold the ending
    frames[0].save(gif, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0)


def all_slugs() -> list[str]:
    return [f"{mid}_{race}_{line}"
            for mid in MONSTERS for race in RACES for line in LINES]


def scene_path(slug: str) -> str:
    mid, race, line = slug.rsplit("_", 2)
    return os.path.join(
        SCENES, f"floor001_{mid}_{RACES[race]}_{LINES[line]}.jpg")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    key = api_key()
    explicit = sys.argv[1:]
    todo = explicit or [s for s in all_slugs() if not os.path.exists(
        os.path.join(OUT, f"{s}.mp4"))]
    print(f"{len(todo)} movies -> {OUT}", flush=True)
    failed = 0
    for slug in todo:
        mid, race, line = slug.rsplit("_", 2)
        if mid not in MONSTERS or race not in RACES or line not in LINES:
            print(f"FAIL {slug}: bad slug", flush=True)
            failed += 1
            continue
        scene = scene_path(slug)
        if not os.path.exists(scene):
            print(f"FAIL {slug}: missing scene {os.path.basename(scene)}",
                  flush=True)
            failed += 1
            continue
        mp4 = os.path.join(OUT, f"{slug}.mp4")
        if not os.path.exists(mp4):
            err = veo_generate(movie_prompt(mid, race, line), scene,
                               key, mp4)
            if err:
                print(f"FAIL {slug}: {err}", flush=True)
                failed += 1
                continue
        mp4_to_mpg(mp4, os.path.join(OUT, f"{slug}.mpg"))
        mp4_to_gif(mp4, os.path.join(OUT, f"{slug}.gif"))
        print(f"ok   {slug}", flush=True)
    print(f"done, {failed} failed", flush=True)


if __name__ == "__main__":
    main()
