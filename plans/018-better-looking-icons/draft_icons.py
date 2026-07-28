"""018 — icon design drafts, and the bake-off page that shows them.

True one bit. Every pixel the page emits is ink or nothing — one
colour, no opacity, no grey. Same masks as icons.py today.

The digits below are *authoring* marks, not output. They record how
lit each part of the shape is so a style can decide what to do with
it; every renderer turns them into on/off pixels before they reach
the SVG.

    '.'  hole      — outside the shape
    '1'  shadow    — the turned-away edge
    '2'  mid       — the body in shade
    '3'  base      — the body in light
    '4'  highlight — the lit edge, facing top-left

Shading in one bit is done with dither patterns, the way it always
has been: level 4 is full ink, 3 is three pixels in four, 2 is a
checkerboard, 1 is one in four. Squint and it reads as tone; look
close and every pixel is either on or off.

Two rules the one-bit constraint forces: an interior detail can only
be a hole, since a brighter mark has nowhere to go without a second
tone; and dither eats a two-pixel detail, so the *keep* styles hold
the ink ringing an enclosed hole at full ink and dither only the open
body.

Three shape sets, and the ways to spend their pixels:

    S1 rim     today's silhouettes, lit from the top-left
    S2 carved  the same, with interior holes as line work
    S3 bold    the same lighting on much larger shapes

    solid / outline / inked / dither / shaded / shaded+keep
    hatch / hatch+keep / outline+shaded

Run it to regenerate mock.html:

    python3 draft_icons.py
"""

from __future__ import annotations

import json
import os

# ── A · what ships today, straight out of icons.py ────────────────────
CURRENT: dict[str, list[str]] = {
    "weapon": [
        "................", ".......##.......", ".......##.......",
        ".......##.......", ".......##.......", ".......##.......",
        ".......##.......", ".......##.......", ".......##.......",
        "...##########...", "...##########...", ".......##.......",
        ".......##.......", "......####......", "......####......",
        "................"],
    "bow": [
        "................", "................", "..........##....",
        "........##.#....", ".......#...#....", "......#....#....",
        ".....#.....#.#..", "...############.", ".....#.....#.#..",
        "......#....#....", ".......#...#....", "........##.#....",
        "..........##....", "................", "................",
        "................"],
    "shield": [
        "................", "..############..", "..############..",
        "..##........##..", "..##...##...##..", "..##...##...##..",
        "..##........##..", "..##........##..", "...##......##...",
        "...##......##...", "....##....##....", "....##....##....",
        ".....##..##.....", "......####......", ".......##.......",
        "................"],
    "armor": [
        "................", ".#####....#####.", ".######..######.",
        ".##############.", ".##############.", ".##############.",
        "..############..", "..############..", "...##########...",
        "...##########...", "....########....", "....########....",
        ".....######.....", ".....######.....", "................",
        "................"],
    "shoes": [
        "................", "....######......", "....######......",
        "....##..##......", "....##..##......", "....##..##......",
        "....##..##......", "....##..####....", "....##....####..",
        "....##......##..", "..####......##..", ".##..........##.",
        ".##############.", ".##############.", "................",
        "................"],
    "luck_charm": [
        ".......##.......", "........#.......", ".......##.......",
        ".......##.......", "......####......", "......####......",
        ".##############.", "..############..", "...##########...",
        "....########....", ".....######.....", "....###..###....",
        "...###....###...", "..###......###..", "..##........##..",
        "................"],
    "medgel": [
        "................", ".....######.....", ".....######.....",
        "......####......", "....########....", "...##########...",
        "...####..####...", "...####..####...", "...##......##...",
        "...####..####...", "...####..####...", "...##########...",
        "....########....", "................", "................",
        "................"],
    "pack": [
        "................", "................", "..############..",
        "..############..", "..##...##...##..", "..##...##...##..",
        "..############..", "..############..", "..##...##...##..",
        "..##...##...##..", "..############..", "..############..",
        "................", "................", "................",
        "................"],
}

# ── T1 · rim — today's shapes, one-pixel rim light ────────────────────
T1: dict[str, list[str]] = {
    "weapon": [
        "................",
        ".......44.......",
        "......4332......",
        "......4.32......",
        "......4.32......",
        "......4.32......",
        "......4.32......",
        "......4.32......",
        "......4332......",
        "..444444444444..",
        "..222222222221..",
        ".......43.......",
        ".......43.......",
        "......4332......",
        "......2221......",
        "................"],
    "bow": [
        "................",
        "....442.........",
        "...44.2.........",
        "..44..2.........",
        "..4...2.........",
        ".43...2.........",
        ".43...2....44...",
        ".43...24444444..",
        ".43...22222222..",
        ".43...2....22...",
        ".43...2.........",
        "..4...2.........",
        "..44..2.........",
        "...44.2.........",
        "....442.........",
        "................"],
    "shield": [
        "................",
        ".44444444444444.",
        ".43333333333332.",
        ".43333333333332.",
        ".433333..333332.",
        ".433333..333332.",
        ".43333333333332.",
        "..433333333332..",
        "..433333333332..",
        "...4333333332...",
        "...4333333332...",
        "....43333332....",
        ".....433332.....",
        "......4332......",
        ".......21.......",
        "................"],
    "armor": [
        "................",
        ".44444....44444.",
        ".433333..333332.",
        ".43333333333332.",
        ".43333333333332.",
        ".43333333333332.",
        "..433333333332..",
        "..433333333332..",
        "...4333333332...",
        "...1111111111...",
        "....43333332....",
        "....43333332....",
        ".....433332.....",
        ".....222221.....",
        "................",
        "................"],
    "shoes": [
        "................",
        "...444444.......",
        "...433332.......",
        "...433332.......",
        "...43..32.......",
        "...433332.......",
        "...433332.......",
        "...43..32.......",
        "...433332.......",
        "...433332.......",
        "...43333332.....",
        "...4333333332...",
        "..433333333332..",
        "..4333333333332.",
        "..1111111111111.",
        "................"],
    "luck_charm": [
        ".......44.......",
        "......4332......",
        "......4332......",
        ".....433332.....",
        ".....433332.....",
        "...4333333332...",
        "4433333333333322",
        ".43333333333332.",
        "..433333333332..",
        "...4333333332...",
        "...4332..4332...",
        "..4332....4332..",
        "..432......432..",
        ".432........432.",
        ".42..........21.",
        "................"],
    "medgel": [
        "................",
        "......4444......",
        "......4332......",
        ".......43.......",
        ".....444444.....",
        "....43333332....",
        "...4333..3332...",
        "...4333..3332...",
        "...43......32...",
        "...43......32...",
        "...4333..3332...",
        "....43333332....",
        ".....222221.....",
        "................",
        "................",
        "................"],
    "pack": [
        "................",
        "................",
        "..444444444444..",
        "..4.33333333.2..",
        "..43.333333.32..",
        "..433.3333.332..",
        "..4333.33.3332..",
        "..43333..33332..",
        "..4333.33.3332..",
        "..433.3333.332..",
        "..43.333333.32..",
        "..4.33333333.2..",
        "..222222222221..",
        "................",
        "................",
        "................"],
}

# ── T2 · carved — the rim, plus holes doing the line work ─────────────
T2: dict[str, list[str]] = {
    "weapon": [
        "................",
        ".......44.......",
        "......4332......",
        "......4.32......",
        "......4.32......",
        "......4.32......",
        "......4.32......",
        "......4.32......",
        "......4332......",
        "..444444444444..",
        "..2.22222222.2..",
        ".......43.......",
        ".......43.......",
        "......4332......",
        "......4332......",
        ".......22......."],
    "bow": [
        "................",
        "....442.........",
        "...44.2.........",
        "..44..2.........",
        "..4...2.........",
        ".43...2.........",
        ".43...24...44...",
        ".4....24444444..",
        ".4....22222222..",
        ".43...22...22...",
        ".43...2.........",
        "..4...2.........",
        "..44..2.........",
        "...44.2.........",
        "....442.........",
        "................"],
    "shield": [
        "................",
        ".44444444444444.",
        ".4.3333333333.2.",
        ".43333333333332.",
        ".4333.4444.3332.",
        ".4333.4334.3332.",
        ".4333.4444.3332.",
        "..433333333332..",
        "..433333333332..",
        "...4333333332...",
        "...4.333333.2...",
        "....43333332....",
        ".....433332.....",
        "......4332......",
        ".......21.......",
        "................"],
    "armor": [
        "................",
        ".44444....44444.",
        ".433333..333332.",
        ".43.33333333.32.",
        ".43.33333333.32.",
        ".43.33333333.32.",
        "..4.33333333.2..",
        "..111111111111..",
        "...4.333333.2...",
        "...4.333333.2...",
        "....43333332....",
        "....43333332....",
        ".....433332.....",
        ".....222221.....",
        "................",
        "................"],
    "shoes": [
        "................",
        "...444444.......",
        "...433332.......",
        "...4.33.2.......",
        "...433332.......",
        "...4.33.2.......",
        "...433332.......",
        "...4.33.2.......",
        "...433332.......",
        "...4333322......",
        "...43333332.....",
        "...4333333332...",
        "..433333333332..",
        "..4333333333332.",
        "..1111111111111.",
        "................"],
    "luck_charm": [
        ".......44.......",
        "......4432......",
        "......4432......",
        ".....443322.....",
        ".....443322.....",
        "...4433333322...",
        "443333.33.333322",
        ".4333.3333.3332.",
        "..43.333333.32..",
        "...4333..3332...",
        "...4332..4332...",
        "..4332....4332..",
        "..432......432..",
        ".432........432.",
        ".42..........21.",
        "................"],
    "medgel": [
        "................",
        "......4444......",
        "......4332......",
        ".......43.......",
        ".....444444.....",
        "....44333332....",
        "...4433..3332...",
        "...4433..3332...",
        "...44......32...",
        "...44......32...",
        "...4433..3332...",
        "....44333332....",
        ".....222221.....",
        "................",
        "................",
        "................"],
    "pack": [
        "................",
        "................",
        "..444444444444..",
        "..4.33333333.2..",
        "..43.333333.32..",
        "..433.3333.332..",
        "..4333.33.3332..",
        "..43333..33332..",
        "..4333.33.3332..",
        "..433.3333.332..",
        "..43.333333.32..",
        "..4.33333333.2..",
        "..222222222221..",
        "................",
        "................",
        "................"],
}

# ── T3 · bold — the same lighting, drawn edge to edge ─────────────────
T3: dict[str, list[str]] = {
    "weapon": [
        "......4444......",
        ".....443322.....",
        ".....443322.....",
        ".....443322.....",
        ".....443322.....",
        ".....443322.....",
        ".....443322.....",
        ".....443322.....",
        ".....443322.....",
        "4444444444444444",
        "2222222222222221",
        ".....443322.....",
        ".....443322.....",
        "....44333222....",
        "....44333222....",
        ".....222211....."],
    "bow": [
        "....44.2........",
        "..44...2........",
        ".44....2........",
        ".4.....2........",
        "43.....2........",
        "43.....2........",
        "43.....2.....44.",
        "43.....244444444",
        "43.....222222222",
        "43.....2.....22.",
        "43.....2........",
        ".4.....2........",
        ".44....2........",
        "..44...2........",
        "....44.2........",
        "................"],
    "shield": [
        "4444444444444444",
        "4333333333333332",
        "4333333333333332",
        "4333333443333332",
        "4333334444333332",
        "4333333443333332",
        ".43333333333332.",
        ".43333333333332.",
        "..433333333332..",
        "..433333333332..",
        "...4333333332...",
        "....43333332....",
        ".....433332.....",
        "......4332......",
        ".......22.......",
        "................"],
    "armor": [
        "...4444..4444...",
        "..44444..44444..",
        ".444444..444444.",
        "4333333333333332",
        "4333333333333332",
        "4333333333333332",
        ".43333333333332.",
        "..111111111111..",
        "..433333333332..",
        "..433333333332..",
        "...4333333332...",
        "...4333333332...",
        "....43333332....",
        "....43333332....",
        ".....433332.....",
        ".....222221....."],
    "shoes": [
        "..4444442.......",
        "..4333332.......",
        "..4.333.2.......",
        "..4333332.......",
        "..4.333.2.......",
        "..4333332.......",
        "..4333332.......",
        "..4333332.......",
        "..43333332......",
        "..433333332.....",
        "..4333333332....",
        "..43333333332...",
        "..4333333333332.",
        ".433333333333332",
        "1111111111111111",
        "................"],
    "luck_charm": [
        "......4444......",
        "......4433......",
        ".....443322.....",
        ".....443322.....",
        "....44333222....",
        "..443333333322..",
        "4444444444444444",
        "4333333333333332",
        ".43333333333332.",
        "..433333333332..",
        "...4333333332...",
        "..4332....3222..",
        ".4332......3222.",
        ".432........222.",
        "432..........222",
        "42............21"],
    "medgel": [
        "......4444......",
        "......4332......",
        ".....443322.....",
        "....44333222....",
        "...4433333222...",
        "..44333..33222..",
        ".443333..332222.",
        ".4433......2222.",
        ".4433......2222.",
        ".443333..332222.",
        ".443333..332222.",
        "..44333..33222..",
        "..443333332222..",
        "...4433332222...",
        ".....222211.....",
        "................"],
    "pack": [
        "................",
        "4444444444444444",
        "4333333..3333332",
        "4333333..3333332",
        "1111111111111111",
        "4333333..3333332",
        "4333333..3333332",
        "1111111111111111",
        "4333333..3333332",
        "4333333..3333332",
        "1111111111111111",
        "4322222..2222221",
        "4322222..2222221",
        "2222222222222221",
        "................",
        "................"],
}

SHAPES = [("S1", "rim shapes", T1),
          ("S2", "carved shapes", T2),
          ("S3", "bold shapes", T3)]

STYLES = [("solid", "solid — filled silhouette"),
          ("outline", "outline — one pixel, hollow"),
          ("inked", "inked — outline + lit edge"),
          ("dither", "dither — drawn shadow, checkered"),
          ("shaded", "shaded — light across the diagonal"),
          ("shadekeep", "shaded + details kept solid"),
          ("hatch", "hatch — the same, in diagonals"),
          ("hatchkeep", "hatch + details kept solid"),
          ("outshade", "outline + shaded")]

ORDER = ["weapon", "bow", "shield", "armor", "shoes", "luck_charm",
         "medgel", "pack"]
LABEL = {"weapon": "Pigsticker (blade)", "bow": "Ashwood Bow",
         "shield": "Scrapwood Buckler", "armor": "Padded Jerkin",
         "shoes": "Cobbled Boots", "luck_charm": "Luck charm",
         "medgel": "Medgel", "pack": "pack (fallback)"}


def validate() -> list[str]:
    """Every grid is 16 rows of 16 legal characters."""
    bad = []
    legal = set(".#1234")
    sets = [("CURRENT", CURRENT)] + [(t, g) for t, _, g in SHAPES]
    for tag, grids in sets:
        for key in ORDER:
            if key not in grids:
                bad.append(f"{tag}: missing {key}")
                continue
            grid = grids[key]
            if len(grid) != 16:
                bad.append(f"{tag}.{key}: {len(grid)} rows, want 16")
            for i, row in enumerate(grid):
                if len(row) != 16:
                    bad.append(f"{tag}.{key} row {i}: {len(row)} chars "
                               f"— {row!r}")
                stray = set(row) - legal
                if stray:
                    bad.append(f"{tag}.{key} row {i}: stray {sorted(stray)}")
    return bad


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>018 — true 1-bit icon styles</title>
<style>
  :root{
    --ink:#0b0e14; --panel:#11151f; --panel2:#161b28; --border:#232a3a;
    --dim:#8b93a7; --faint:#5b6275; --text:#e6e9f2; --gold:#f5a524;
    --violet-soft:#a78bfa; --ok:#3ad29f; --tint:#8b93a7;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--ink);color:var(--text)}
  body{font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
       padding:22px 26px 90px}
  h1{font-size:17px;margin:0 0 4px}
  h2{font-size:12px;margin:34px 0 8px;color:var(--gold);
     letter-spacing:.1em;text-transform:uppercase}
  p.note{color:var(--dim);margin:0 0 8px;max-width:84ch}
  b{color:var(--text);font-weight:400}
  .bar{position:sticky;top:0;z-index:5;background:var(--ink);
       border-bottom:1px solid var(--border);padding:10px 0 12px;
       display:flex;gap:22px;align-items:center;flex-wrap:wrap}
  .bar label{color:var(--dim);display:flex;gap:6px;align-items:center}
  .bar select{background:var(--panel2);color:var(--text);
    border:1px solid var(--border);padding:2px 6px;font:inherit}
  .err{color:#f4645f;white-space:pre-wrap}

  .ic{display:inline-block;flex:none;vertical-align:middle;
      background-color:var(--tint);image-rendering:pixelated;
      mask-size:100% 100%;-webkit-mask-size:100% 100%;
      mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat}

  table.cmp{border-collapse:collapse;margin-top:4px}
  table.cmp th{color:var(--dim);font-weight:400;padding:6px 16px;
    border-bottom:1px solid var(--border);font-size:11px;
    letter-spacing:.06em;text-transform:uppercase}
  table.cmp th.name{text-align:left}
  table.cmp td{padding:9px 16px;text-align:center;
    border-bottom:1px solid var(--border)}
  table.cmp td.name{text-align:left;color:var(--dim);white-space:nowrap}
  table.cmp tr:hover td{background:var(--panel)}

  .sheet{display:flex;gap:20px;flex-wrap:wrap;margin-top:8px}
  .cell{background:var(--panel);border:1px solid var(--border);padding:11px;
        display:flex;flex-direction:column;gap:7px;align-items:center}
  .cell .cap{color:var(--faint);font-size:11px}

  .ctxwrap{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}
  .card{background:var(--ink);border:1px solid var(--border);width:400px;
        padding:8px}
  .cardcap{color:var(--gold);font-size:11px;letter-spacing:.08em;
    text-transform:uppercase;padding:2px 4px 8px}
  .say{padding:2px 4px 10px}
  .opt{display:flex;gap:10px;align-items:center;width:100%;
       background:var(--panel);border:1px solid var(--border);
       color:var(--text);font:inherit;text-align:left;padding:8px 10px;
       margin-bottom:4px;cursor:pointer}
  .opt .ic{background-color:var(--dim)}
  .opt:hover{background:var(--panel2);border-color:var(--faint)}
  .opt:hover .ic{background-color:var(--text)}
  .opt .key{color:var(--violet-soft);flex:none;width:2.4ch}
  .opt .lbl{flex:1}
  .opt .hint{color:var(--faint)}
  .opt .hint b{color:var(--gold)}
  .inv{display:flex;gap:15px;align-items:center;padding:10px 6px 2px;
       border-top:1px solid var(--border);margin-top:8px;flex-wrap:wrap}
  .inv .lab{color:var(--faint);letter-spacing:.1em;font-size:11px}
  .item{display:flex;gap:7px;align-items:center}
  .item .pname{color:var(--dim)}
  .item.eq .pname{color:var(--text)}
  .item.eq .ic{background-color:var(--text)}
  .item .ic{background-color:var(--dim)}
  .durbar{display:block;height:2px;width:26px;margin:2px auto 0;
          background:var(--ok)}
  .pico{display:flex;flex-direction:column;align-items:center}
</style>
</head>
<body>

<h1>018 — one-bit icon styles</h1>
<p class="note">
  <b>One bit. One colour. Every pixel is ink or nothing</b> — no
  opacity, no grey, no second tone. Where these differ is in how the
  pixels are <i>spent</i>: as a filled silhouette, as a one-pixel
  outline, or as a dither pattern, which is how 1-bit art has always
  faked shading. Pick the shape set with the dropdown; the columns are
  the styles.
</p>
<p class="note">
  Two rules fall out of the constraint. <b>A detail can only be a
  hole</b> — a brighter mark inside a solid body has nowhere to go when
  there is no second tone. And <b>dither eats a two-pixel detail</b>,
  so the <i>details kept</i> columns hold the ink around every enclosed
  hole at full ink and let only the open body break up.
</p>

<div class="bar">
  <label>shapes <select id="shapes"></select></label>
  <label>size
    <select id="size">
      <option value="16">16 px</option>
      <option value="32" selected>32 px — shop / pack</option>
      <option value="48">48 px</option>
    </select></label>
  <label>tint
    <select id="tint">
      <option value="#8b93a7" selected>DIM — resting row</option>
      <option value="#e6e9f2">TEXT — equipped / hover</option>
      <option value="#f5a524">GOLD</option>
      <option value="#a78bfa">VIOLET_SOFT</option>
    </select></label>
</div>
<div class="err" id="err"></div>

<h2>1 · at real size, on the real background</h2>
<table class="cmp" id="cmp"></table>

<h2>2 · 8x — every pixel, on or off</h2>
<div class="sheet" id="zoom"></div>

<h2>3 · in the shop card that started this</h2>
<div class="ctxwrap" id="ctx"></div>

<script>
const CURRENT = __CURRENT__;
const SHAPES  = __SHAPES__;
const STYLES  = __STYLES__;
const ORDER   = __ORDER__;
const LABEL   = __LABEL__;

/* ── grid -> 16x16 of 0..4.  '#' is level 4, so the shipping set
      passes through untouched. ─────────────────────────────────── */
const levels = grid => grid.map(row =>
  [...row].map(c => c === '.' ? 0 : (c === '#' ? 4 : +c)));

/* the shape's own edge: ink with at least one empty 4-neighbour */
function edgeOf(L){
  const e = [];
  for(let y = 0; y < 16; y++){
    e.push([]);
    for(let x = 0; x < 16; x++){
      if(!L[y][x]){ e[y].push(0); continue; }
      const out = (a, b) => a < 0 || a > 15 || b < 0 || b > 15
        || !L[b][a];
      e[y].push(out(x - 1, y) || out(x + 1, y) || out(x, y - 1)
        || out(x, y + 1) ? 1 : 0);
    }
  }
  return e;
}

/* An enclosed hole is detail — the fuller down a blade, a lace hole,
   the boss on a buckler. Dither swallows a two-pixel detail whole, so
   the ink that rings one is held at full ink however the rest shades.
   Holes that reach the border are just background and get no ring. */
function detailRim(L){
  const outside = [...Array(16)].map(() => Array(16).fill(false));
  const stack = [];
  for(let i = 0; i < 16; i++)
    stack.push([i, 0], [i, 15], [0, i], [15, i]);
  while(stack.length){
    const [x, y] = stack.pop();
    if(x < 0 || x > 15 || y < 0 || y > 15 || outside[y][x] || L[y][x])
      continue;
    outside[y][x] = true;
    stack.push([x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]);
  }
  const near = (x, y) => x >= 0 && x < 16 && y >= 0 && y < 16
    && !L[y][x] && !outside[y][x];
  const r = [];
  for(let y = 0; y < 16; y++){
    r.push([]);
    for(let x = 0; x < 16; x++)
      r[y].push(L[y][x] && (near(x - 1, y) || near(x + 1, y)
        || near(x, y - 1) || near(x, y + 1)) ? 1 : 0);
  }
  return r;
}

/* Dither is the only honest way to shade with one colour: lit parts
   stay solid ink, shaded parts break into a pattern. Coverage runs
   full / half / quarter — squint and it is tone, look close and every
   pixel is on or off. */
const CHECK = {
  4: () => true,
  3: () => true,
  2: (x, y) => ((x + y) & 1) === 0,
  1: (x, y) => (x & 1) === 0 && (y & 1) === 0,
};
/* True hatching needs a period of at least 3: (x+y)%2 is a
   checkerboard, not a diagonal, so it renders the same as CHECK. Two
   on, two off reads as a line at 32 px. */
const DIAG = {
  4: () => true,
  3: () => true,
  2: (x, y) => (x + y) % 4 < 2,
  1: (x, y) => (x + y) % 4 === 0,
};

/* Light from the top-left, falling across the shape's own diagonal:
   the near half stays solid ink, the far half goes to a half
   checker. Two bands only — a quarter band eats the shape at 32 px.
   Derived, so it needs no extra drawing. */
function bandsOf(L){
  let lo = 99, hi = -99;
  for(let y = 0; y < 16; y++)
    for(let x = 0; x < 16; x++)
      if(L[y][x]){ const d = x + y; if(d < lo) lo = d; if(d > hi) hi = d; }
  const span = Math.max(1, hi - lo);
  return (x, y) => (x + y - lo) / span < 0.48 ? 4 : 2;
}

const RENDER = {
  solid:    (L, E, B, D, x, y) => L[y][x] > 0,
  outline:  (L, E, B, D, x, y) => !!E[y][x],
  inked:    (L, E, B, D, x, y) => !!E[y][x] || L[y][x] === 4,
  dither:   (L, E, B, D, x, y) => L[y][x] > 0 && CHECK[L[y][x]](x, y),
  shaded:   (L, E, B, D, x, y) => L[y][x] > 0 && CHECK[B(x, y)](x, y),
  shadekeep:(L, E, B, D, x, y) => L[y][x] > 0
             && (!!D[y][x] || CHECK[B(x, y)](x, y)),
  hatch:    (L, E, B, D, x, y) => L[y][x] > 0 && DIAG[B(x, y)](x, y),
  hatchkeep:(L, E, B, D, x, y) => L[y][x] > 0
             && (!!D[y][x] || DIAG[B(x, y)](x, y)),
  outshade: (L, E, B, D, x, y) => !!E[y][x]
             || (L[y][x] > 0 && CHECK[B(x, y)](x, y)),
};

/* every rect is full ink — nothing here carries an opacity */
function maskUrl(grid, style){
  const L = levels(grid), E = edgeOf(L), B = bandsOf(L),
        D = detailRim(L);
  const on = RENDER[style];
  let r = '';
  for(let y = 0; y < 16; y++){
    let x = 0;
    while(x < 16){
      if(on(L, E, B, D, x, y)){
        let run = x;
        while(run < 16 && on(L, E, B, D, run, y)) run++;
        r += `<rect x="${x}" y="${y}" width="${run - x}" height="1"/>`;
        x = run;
      } else x++;
    }
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" `
    + `width="32" height="32" shape-rendering="crispEdges" fill="#fff">`
    + `${r}</svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

function iconEl(grid, style, px){
  const s = document.createElement('span');
  s.className = 'ic';
  s.style.width = s.style.height = px + 'px';
  const u = maskUrl(grid, style);
  s.style.maskImage = s.style.webkitMaskImage = `url("${u}")`;
  return s;
}

const shapeSet = () => SHAPES.find(
  s => s[0] === document.getElementById('shapes').value)[2];

/* the shipping icons are already flat 1 bit — always shown as control */
const COLS = () => [['A · current', CURRENT, 'solid']].concat(
  STYLES.map(([id, name]) => [name, shapeSet(), id]));

function buildTable(px){
  const t = document.getElementById('cmp');
  t.innerHTML = '';
  const hr = t.insertRow();
  const th0 = document.createElement('th');
  th0.className = 'name'; th0.textContent = 'item';
  hr.appendChild(th0);
  COLS().forEach(([name]) => {
    const th = document.createElement('th');
    th.textContent = name;
    hr.appendChild(th);
  });
  ORDER.forEach(key => {
    const tr = t.insertRow();
    const td = tr.insertCell();
    td.className = 'name'; td.textContent = LABEL[key];
    COLS().forEach(([, grids, style]) =>
      tr.insertCell().appendChild(iconEl(grids[key], style, px)));
  });
}

function buildZoom(){
  const z = document.getElementById('zoom');
  z.innerHTML = '';
  const cols = COLS();
  ORDER.forEach(key => {
    const cell = document.createElement('div');
    cell.className = 'cell';
    const row = document.createElement('div');
    row.style.display = 'flex'; row.style.gap = '9px';
    cols.forEach(([, grids, style]) =>
      row.appendChild(iconEl(grids[key], style, 112)));
    cell.appendChild(row);
    const cap = document.createElement('div');
    cap.className = 'cap';
    cap.textContent = LABEL[key] + '   ·   '
      + cols.map(c => c[0].startsWith('A ·') ? 'current' : c[2])
          .join(' / ');
    cell.appendChild(cap);
    z.appendChild(cell);
  });
}

const SHOP = [['1','Ashwood Bow','bow','250',''],
              ['2','Padded Jerkin','armor','200',''],
              ['3','Cobbled Boots','shoes','500',''],
              ['4','Pigsticker','weapon','750',' · off-class']];
const PACK = [['Pigsticker','weapon',true,''],
              ['Scrapwood Buckler','shield',true,''],
              ['Luck charm','luck_charm',false,' x2']];

function buildCtx(){
  const wrap = document.getElementById('ctx');
  wrap.innerHTML = '';
  COLS().forEach(([name, grids, style]) => {
    const card = document.createElement('div');
    card.className = 'card';
    const cap = document.createElement('div');
    cap.className = 'cardcap'; cap.textContent = name;
    card.appendChild(cap);
    const say = document.createElement('div');
    say.className = 'say';
    say.textContent = 'Pigsticker — not your weapon: x3 the coin, half '
      + 'the bite, and one shot in four goes wide';
    card.appendChild(say);
    SHOP.forEach(([n, label, key, price, extra]) => {
      const b = document.createElement('button');
      b.className = 'opt';
      const k = document.createElement('span');
      k.className = 'key'; k.textContent = '[' + n + ']';
      b.appendChild(k);
      b.appendChild(iconEl(grids[key], style, 32));
      const l = document.createElement('span');
      l.className = 'lbl'; l.textContent = label;
      b.appendChild(l);
      const h = document.createElement('span');
      h.className = 'hint';
      h.innerHTML = '<b>&#9670; ' + price + '</b>' + extra;
      b.appendChild(h);
      card.appendChild(b);
    });
    const inv = document.createElement('div');
    inv.className = 'inv';
    const lab = document.createElement('span');
    lab.className = 'lab'; lab.textContent = 'PACK';
    inv.appendChild(lab);
    PACK.forEach(([nm, key, eq, ct]) => {
      const it = document.createElement('div');
      it.className = 'item' + (eq ? ' eq' : '');
      const pico = document.createElement('div');
      pico.className = 'pico';
      pico.appendChild(iconEl(grids[key], style, 32));
      if(eq){
        const d = document.createElement('span');
        d.className = 'durbar'; pico.appendChild(d);
      }
      it.appendChild(pico);
      const sp = document.createElement('span');
      sp.className = 'pname'; sp.textContent = nm + ct;
      it.appendChild(sp);
      inv.appendChild(it);
    });
    card.appendChild(inv);
    wrap.appendChild(card);
  });
}

function redraw(){
  document.body.style.setProperty('--tint',
    document.getElementById('tint').value);
  const px = +document.getElementById('size').value;
  buildTable(px); buildZoom(); buildCtx();
}

const sel = document.getElementById('shapes');
SHAPES.forEach(([tag, name]) => {
  const o = document.createElement('option');
  o.value = tag; o.textContent = tag + ' · ' + name;
  sel.appendChild(o);
});
['shapes','size','tint'].forEach(id =>
  document.getElementById(id).addEventListener('input', redraw));
redraw();
</script>
</body>
</html>
"""


def build() -> None:
    bad = validate()
    if bad:
        raise SystemExit("grid errors:\n  " + "\n  ".join(bad))
    shapes = [[tag, name, {k: g[k] for k in ORDER}] for tag, name, g in SHAPES]
    html = (PAGE
            .replace("__CURRENT__", json.dumps({k: CURRENT[k] for k in ORDER}))
            .replace("__SHAPES__", json.dumps(shapes))
            .replace("__STYLES__", json.dumps(STYLES))
            .replace("__ORDER__", json.dumps(ORDER))
            .replace("__LABEL__", json.dumps(LABEL)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "mock.html")
    with open(out, "w") as fh:
        fh.write(html)
    print(f"wrote {out}  ({len(ORDER)} items x {len(STYLES) + 1} styles "
          f"x {len(SHAPES)} shape sets)")


if __name__ == "__main__":
    build()
