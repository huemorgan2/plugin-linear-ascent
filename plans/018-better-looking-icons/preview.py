"""018 — what the shipped set actually looks like.

Renders every key in icons._GRIDS twice, flat as it was before 018 and
shaded as it is now, at both sizes the game uses. Run it and look at
the page; the point is to catch a glyph the dither hurts rather than
helps (an inline UI marker has no volume to gain).

    python3 preview.py && open preview.html
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))

from plugin_linear_ascent import icons  # noqa: E402


def url(painted: list[list[bool]]) -> str:
    rects = []
    for y, row in enumerate(painted):
        x = 0
        while x < 16:
            if row[x]:
                run = x
                while run < 16 and row[run]:
                    run += 1
                rects.append(f'<rect x="{x}" y="{y}" '
                             f'width="{run - x}" height="1"/>')
                x = run
            else:
                x += 1
    from urllib.parse import quote
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" '
           'width="32" height="32" shape-rendering="crispEdges" '
           f'fill="#fff">{"".join(rects)}</svg>')
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


def cell(u: str, px: int, tint: str) -> str:
    return (f'<span class="ic" style="width:{px}px;height:{px}px;'
            f'background-color:{tint};'
            f'-webkit-mask-image:url(&quot;{u}&quot;);'
            f'mask-image:url(&quot;{u}&quot;)"></span>')


rows = []
for key in icons.ICON_KEYS:
    grid = icons._GRIDS[key]
    flat = [[c == "#" for c in row] for row in grid]
    new = icons._painted(grid)
    ink = sum(r.count("#") for r in grid)
    off = sum(1 for y in range(16) for x in range(16)
              if flat[y][x] and not new[y][x])
    rows.append(
        f"<tr><td class=name>{key}</td>"
        f"<td>{cell(url(flat), 32, '#8b93a7')}</td>"
        f"<td class=hi>{cell(url(new), 32, '#8b93a7')}</td>"
        f"<td>{cell(url(flat), 16, '#8b93a7')}</td>"
        f"<td class=hi>{cell(url(new), 16, '#8b93a7')}</td>"
        f"<td class=hi>{cell(url(new), 32, '#e6e9f2')}</td>"
        f"<td class=zoom>{cell(url(flat), 112, '#8b93a7')}</td>"
        f"<td class='zoom hi'>{cell(url(new), 112, '#8b93a7')}</td>"
        f"<td class=num>{off}/{ink}</td></tr>")

HTML = """<!doctype html>
<meta charset="utf-8"><title>018 — the shipped set</title>
<style>
 body{margin:0;padding:22px 26px 80px;background:#0b0e14;color:#e6e9f2;
   font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
 h1{font-size:17px;margin:0 0 6px}
 p{color:#8b93a7;max-width:80ch;margin:0 0 16px}
 table{border-collapse:collapse}
 th{color:#8b93a7;font-weight:400;font-size:11px;padding:6px 14px;
   text-transform:uppercase;letter-spacing:.06em;
   border-bottom:1px solid #232a3a}
 td{padding:7px 14px;text-align:center;border-bottom:1px solid #232a3a}
 td.name{text-align:left;color:#8b93a7}
 td.num{color:#5b6275;font-size:11px}
 tr:hover td{background:#11151f}
 .hi{background:#0e1320}
 .ic{display:inline-block;vertical-align:middle;image-rendering:pixelated;
   mask-size:100% 100%;-webkit-mask-size:100% 100%;
   mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat}
</style>
<h1>018 — the shipped set, flat vs shaded</h1>
<p>Every key in <code>icons._GRIDS</code>. The shaded columns are tinted
darker. Last column counts the ink pixels the dither switched off — a
glyph at 0 is untouched, and a high count on something with no volume
to gain (an inline UI marker) is the thing to look for.</p>
<table>
<tr><th>key</th><th>flat 32</th><th>shaded 32</th><th>flat 16</th>
<th>shaded 16</th><th>equipped</th><th>flat 7x</th><th>shaded 7x</th>
<th>off</th></tr>
__ROWS__
</table>
"""

out = os.path.join(HERE, "preview.html")
with open(out, "w") as fh:
    fh.write(HTML.replace("__ROWS__", "\n".join(rows)))
print(f"wrote {out}  ({len(rows)} keys)")
