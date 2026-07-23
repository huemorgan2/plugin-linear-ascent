#!/usr/bin/env python3
"""Linear Ascent scene banners — 1-bit dithered, card-width.
Grayscale canvas -> Bayer 8x8 ordered dither -> 1-bit ink on transparency.
Native 160x56, shown ~4x in the card. White native assets + tinted previews.
"""
import zlib, struct, os, base64, math

_HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(_HERE, "..", "content", "art", "banners")
SCRATCH = os.path.join(_HERE, "..", "content", "art", "banners", "preview")
W, H = 160, 56

def png(w, h, rgba_rows):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    raw = b"".join(b"\x00" + bytes(row) for row in rgba_rows)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))

BAYER = [
 [0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],
 [12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
 [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],
 [15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]

def dither(c):
    return [[1 if c[y][x] > (BAYER[y % 8][x % 8] + 0.5) / 64 else 0
             for x in range(W)] for y in range(H)]

def out_png(bits, color, scale, bg=None):
    rows = []
    for y in range(H * scale):
        row = []
        for x in range(W * scale):
            on = bits[y // scale][x // scale]
            if bg is not None:
                r, g, b = color if on else bg
                row += [r, g, b, 255]
            else:
                r, g, b = color
                row += [r, g, b, 255 if on else 0]
        rows.append(row)
    return png(W * scale, H * scale, rows)

def hx(s): return tuple(int(s[i:i+2], 16) for i in (1, 3, 5))
DIM, TEXT, VIOLET, GOLD, AETHER, RED = map(hx, (
    "#8b93a7", "#e6e9f2", "#8b5cf6", "#f5a524", "#5eaefc", "#f4645f"))
PANEL = hx("#11151f")

def h2(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 974634599) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) % 10000) / 10000

def canvas(): return [[0.0] * W for _ in range(H)]

def put(c, x, y, v):
    if 0 <= x < W and 0 <= y < H: c[y][x] = v

def add(c, x, y, v):
    if 0 <= x < W and 0 <= y < H: c[y][x] = min(1.0, c[y][x] + v)

def rect(c, x0, y0, x1, y1, v):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            c[y][x] = v

def disk(c, cx, cy, r, v, additive=False):
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                if additive: c[y][x] = min(1.0, c[y][x] + v)
                else: c[y][x] = v

def line(c, x0, y0, x1, y1, v, w=1):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        x = round(x0 + (x1 - x0) * i / steps)
        y = round(y0 + (y1 - y0) * i / steps)
        for dy in range(w):
            put(c, x, y + dy, v)

def stars(c, y_max, p=0.006, seed=1):
    for y in range(y_max):
        for x in range(W):
            if h2(x, y, seed) < p: c[y][x] = 1.0

def speckle(c, y0, y1, p, v, seed=2):
    for y in range(y0, y1):
        for x in range(W):
            if h2(x, y, seed) < p: c[y][x] = v

# ---------------- scenes ----------------

def scene_roothollow():
    c = canvas()
    for y in range(36):                      # night sky, faint gradient up
        pass  # sky stays pure black
    stars(c, 30, 0.008)
    disk(c, 24, 9, 5, 0.95)                  # moon
    disk(c, 27, 7, 4, 0.05)                  # crescent bite
    # the tower's leg — massive diagonal crossing the sky, lit from top-left
    for y in range(0, 40):
        cx = 148 - int(y * 1.55)
        w = 7 + y // 5
        for x in range(cx - w // 2, cx + w // 2 + 1):
            put(c, x, y, 0.30)
        put(c, cx - w // 2, y, 0.85)         # lit edge
        put(c, cx - w // 2 + 1, y, 0.6)
    for i in range(5):                       # cross-struts
        y = 5 + i * 7
        cx = 148 - int(y * 1.55); w = 7 + y // 5
        line(c, cx - w // 2, y, cx + w // 2, y + 2, 0.7)
    # shack roofline on the horizon
    def shack(x0, wdt, hgt, win):
        base = 46
        rect(c, x0, base - hgt, x0 + wdt, base, 0.16)          # wall
        for i in range(wdt // 2 + 2):                          # roof
            line(c, x0 - 1 + i, base - hgt - i // 2, x0 + wdt + 1 - i, base - hgt - i // 2, 0.55)
            if i > wdt // 4: break
        for wx, wy in win: put(c, x0 + wx, base - hgt + wy, 1.0)
    shack(8, 16, 8, [(4, 4), (11, 4)])
    shack(30, 12, 10, [(5, 5)])
    shack(48, 18, 7, [(4, 3), (13, 3)])
    shack(74, 13, 9, [(6, 4)])
    shack(94, 16, 8, [(4, 4), (11, 5)])
    line(c, 36, 30, 36, 36, 0.9); put(c, 36, 29, 1.0)          # antenna + beacon
    for i in range(8):                                          # chimney smoke
        put(c, 52 + i // 2, 36 - i, 0.5 if i % 2 else 0.0)
    rect(c, 0, 47, W - 1, H - 1, 0.0)                          # ground
    speckle(c, 47, H, 0.06, 0.45, seed=3)
    for y in range(47, H):                                      # dirt path
        wdt = (y - 45)
        rect(c, 60 - wdt, y, 60 + wdt, y, 0.30)
    return c

def scene_forge():
    c = canvas()
    rect(c, 0, 0, W - 1, H - 1, 0.0)
    # plasma arc glow, center-left
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - 58, y - 26)
            if d < 30: add(c, x, y, 0.85 * (1 - d / 30) ** 2)
    disk(c, 58, 18, 3, 1.0)                                     # the arc itself
    for a in range(0, 360, 30):                                 # spark rays
        line(c, 58, 18, 58 + int(9 * math.cos(math.radians(a))),
             18 + int(6 * math.sin(math.radians(a))), 0.9)
    # anvil silhouette (dark against the glow)
    rect(c, 44, 30, 76, 34, 0.0)                                # top slab
    line(c, 38, 31, 44, 31, 0.0, 3)                             # horn
    rect(c, 52, 35, 68, 38, 0.0)                                # waist
    rect(c, 48, 39, 72, 42, 0.0)                                # foot
    rect(c, 44, 43, 76, 44, 0.0)                                # block
    put(c, 45, 30, 0.9); put(c, 46, 30, 0.9)                    # lit edge
    # hammer leaning on the block
    line(c, 84, 28, 78, 43, 0.0, 2); rect(c, 82, 25, 88, 29, 0.0)
    # hanging chains
    for x in (108, 118, 128):
        for y in range(0, 22 + (x % 3) * 4):
            if y % 3 != 2: put(c, x, y, 0.55)
    # tool wall, right
    rect(c, 100, 30, 152, 31, 0.35)
    for i, x in enumerate(range(104, 150, 9)):
        line(c, x, 32, x, 38 + i % 3, 0.5)
    rect(c, 0, 45, W - 1, H - 1, 0.04)                          # floor
    for y in range(45, H):                                      # glow on floor
        for x in range(W):
            d = math.hypot(x - 58, (y - 26) * 2.2)
            if d < 34: add(c, x, y, 0.4 * (1 - d / 34))
    speckle(c, 45, H, 0.05, 0.4, seed=5)
    return c

def scene_greenreach():
    c = canvas()
    for y in range(34):
        pass  # sky stays pure black
    stars(c, 14, 0.004, seed=7)
    for cx, cy, r in ((28, 10, 6), (40, 12, 8), (52, 9, 5), (120, 7, 6), (132, 9, 7)):
        disk(c, cx, cy, r, 0.30)                                # cloud banks
        disk(c, cx, cy + 2, r, 0.05)
    # floodlight tower, right
    for y in range(6, 40):
        put(c, 138, y, 0.85); put(c, 143, y, 0.85)
        if y % 5 == 0:
            line(c, 138, y, 143, y + 3, 0.6); line(c, 143, y, 138, y + 3, 0.6)
    rect(c, 136, 4, 145, 6, 0.9)                                # lamp head
    for y in range(7, 40):                                      # light cone down-left
        x0 = 136 - int((y - 6) * 1.6); x1 = 138
        for x in range(max(0, x0), x1):
            add(c, x, y, 0.16)
    # rolling meadow
    for x in range(W):
        yh = 34 + int(3 * math.sin(x / 22) + 1.5 * math.sin(x / 9 + 2))
        put(c, x, yh - 1, 0.5)                                  # lit crest
        for y in range(yh, H):
            c[y][x] = 0.08 + 0.08 * math.sin(x / 6 + y)
    speckle(c, 36, H, 0.10, 0.5, seed=9)                        # tall grass
    # dead tree, left
    line(c, 30, 14, 30, 37, 0.95, 2)
    line(c, 30, 20, 21, 12, 0.9); line(c, 30, 18, 39, 9, 0.9)
    line(c, 31, 24, 40, 20, 0.85); line(c, 30, 22, 23, 18, 0.85)
    line(c, 39, 9, 43, 8, 0.7); line(c, 21, 12, 18, 10, 0.7)
    # wolf silhouette on the crest (dark)
    rect(c, 72, 33, 84, 36, 0.0); line(c, 71, 31, 73, 33, 0.0, 2)
    line(c, 84, 33, 87, 30, 0.0); line(c, 73, 36, 73, 39, 0.0)
    line(c, 82, 36, 82, 39, 0.0); put(c, 71, 31, 0.9)           # eye glint
    return c

def scene_death():
    c = canvas()
    rect(c, 0, 0, W - 1, H - 1, 0.0)
    for a in range(0, 360, 15):                                 # faint rays
        line(c, 80, 26, 80 + int(70 * math.cos(math.radians(a))),
             26 + int(40 * math.sin(math.radians(a))), 0.18)
    disk(c, 80, 28, 17, 0.75)                                   # skull dome
    rect(c, 66, 28, 94, 38, 0.75)                               # jaw block
    rect(c, 63, 24, 66, 33, 0.4); rect(c, 94, 24, 97, 33, 0.4)  # cheek shadow
    rect(c, 70, 24, 77, 30, 0.0); rect(c, 83, 24, 90, 30, 0.0)  # eye sockets
    put(c, 76, 26, 0.9); put(c, 84, 26, 0.9)                    # eye points
    for x in range(68, 93, 4):                                  # teeth gaps
        rect(c, x, 34, x + 1, 39, 0.0)
    line(c, 80, 31, 78, 34, 0.0); line(c, 80, 31, 82, 34, 0.0)  # nasal
    line(c, 88, 12, 96, 4, 0.0, 2)                              # crack in dome
    line(c, 88, 12, 91, 16, 0.0)
    # cracked shard floating above
    line(c, 80, 2, 76, 8, 0.95); line(c, 80, 2, 84, 8, 0.95)
    line(c, 76, 8, 80, 12, 0.95); line(c, 84, 8, 80, 12, 0.95)
    line(c, 79, 5, 81, 9, 0.0)                                  # the crack
    disk(c, 80, 7, 9, 0.12, additive=True)                      # shard glow
    rect(c, 0, 44, W - 1, H - 1, 0.05)                          # ground
    speckle(c, 44, H, 0.07, 0.4, seed=11)
    for x0, y0 in ((20, 46), (130, 48), (44, 50), (108, 51)):   # scattered bones
        line(c, x0, y0, x0 + 6, y0, 0.6); put(c, x0 - 1, y0, 0.8); put(c, x0 + 7, y0, 0.8)
    return c

SCENES = {
    "roothollow": (scene_roothollow, DIM),
    "forge": (scene_forge, DIM),
    "greenreach": (scene_greenreach, DIM),
    "death": (scene_death, RED),
}

def main():
    os.makedirs(ART, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    uris = {}
    for name, (fn, color) in SCENES.items():
        bits = dither(fn())
        with open(os.path.join(ART, f"{name}_{W}x{H}.png"), "wb") as f:
            f.write(out_png(bits, (255, 255, 255), 1))          # white native
        uris[name] = base64.b64encode(out_png(bits, color, 1)).decode()
        with open(os.path.join(SCRATCH, f"banner_{name}_preview.png"), "wb") as f:
            f.write(out_png(bits, color, 4, bg=PANEL))          # 4x tinted preview
    with open(os.path.join(SCRATCH, "banner_uris.txt"), "w") as f:
        for name, b64 in uris.items():
            f.write(f"{name}\tdata:image/png;base64,{b64}\n")
    print("done:", ", ".join(SCENES))

if __name__ == "__main__":
    main()
