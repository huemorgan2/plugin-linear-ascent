#!/usr/bin/env python3
"""Assemble THE HUNDRED BANNERS into a print-ready HTML + PDF.

Reads book/chapters/*.md (in lexicographic order), inserts part-title pages,
Malgrim-ledger interludes, and the pencil plates from book/art/, then prints
to PDF with headless Chrome at 6x9in trim.
"""
import re
import subprocess
import sys
from pathlib import Path

import markdown

BOOK = Path(__file__).resolve().parent.parent
CHAPTERS = BOOK / "chapters"
APPENDICES = BOOK / "appendices"
ART = BOOK / "art"
OUT_HTML = BOOK / "the-hundred-banners.html"
OUT_PDF = BOOK / "the-hundred-banners.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PARTS = {
    1: ("PART I", "THE DEBT", "Roothollow \u00b7 floors 1\u201320"),
    9: ("PART II", "THE BANNER WAR", "floors 21\u201340"),
    17: ("PART III", "THE GATHERING", "floors 41\u201360"),
    24: ("PART IV", "THE SCATTERED SKY", "floors 61\u201380"),
    32: ("PART V", "THE MADE", "floors 81\u2013100 \u00b7 and the descent"),
}

MD = markdown.Markdown(extensions=["smarty"])


def md_to_html(text: str) -> str:
    # scene breaks: a lone ⁂ line becomes a styled divider
    text = re.sub(r"(?m)^\s*\u2042\s*$", '<div class="scenebreak">\u2042</div>', text)
    MD.reset()
    return MD.convert(text)


def plate_for(stem: str) -> Path | None:
    # matches "07-", "08a-" (inserted chapters) but not "08x-" (interludes)
    m = re.match(r"^(\d\d[a-w]?)-", stem)
    if not m:
        return None
    p = ART / f"plate-{m.group(1)}.png"
    return p if p.exists() else None


PRINT_ART = ART / "_print"


def print_copy(path: Path) -> Path:
    """Downscaled grayscale JPEG for embedding, so the PDF stays printable
    but under repo size limits."""
    PRINT_ART.mkdir(exist_ok=True)
    out = PRINT_ART / (path.stem + ".jpg")
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "80",
             "-Z", "1200",
             "--matchTo",
             "/System/Library/ColorSync/Profiles/Generic Gray Profile.icc",
             str(path), "--out", str(out)],
            check=True, capture_output=True,
        )
    return out


def figure(path: Path, cls: str = "plate") -> str:
    p = print_copy(path)
    return f'<figure class="{cls}"><img src="art/_print/{p.name}" alt=""></figure>'


def build() -> None:
    files = sorted(CHAPTERS.glob("*.md"))
    if not files:
        sys.exit("no chapters found")

    toc: list[str] = []
    body: list[str] = []

    # ---- front matter ----
    body.append(
        '<section class="titlepage">'
        "<p class=\"series\">A NOVEL OF THE LINEAR ASCENT</p>"
        "<h1>THE HUNDRED<br>BANNERS</h1>"
        '<div class="rule"></div>'
        "<p class=\"tag\">The tower was built so the world could never gather.<br>"
        "This is the story of the gathering.</p>"
        "</section>"
    )
    if (ART / "front-banner.png").exists():
        body.append('<section class="artpage">' + figure(ART / "front-banner.png", "front") + "</section>")
    if (ART / "front-tower.png").exists():
        body.append(
            '<section class="artpage"><p class="maplabel">The Ascent \u2014 one hundred stolen floors</p>'
            + figure(ART / "front-tower.png", "map")
            + "</section>"
        )
    if (ART / "front-roothollow.png").exists():
        body.append(
            '<section class="artpage"><p class="maplabel">Roothollow, at the foot</p>'
            + figure(ART / "front-roothollow.png", "front")
            + "</section>"
        )

    # ---- chapters ----
    chapters_html: list[str] = []
    for f in files:
        stem = f.stem
        raw = f.read_text(encoding="utf-8")
        title_m = re.match(r"^#\s+(.+?)\s*$", raw.split("\n", 1)[0])
        title = title_m.group(1) if title_m else stem
        num_m = re.match(r"^(\d\d)([a-z]?)-", stem)
        num = int(num_m.group(1)) if num_m else None
        is_interlude = bool(num_m and num_m.group(2) == "x")
        is_inserted = bool(num_m and num_m.group(2) and not is_interlude)

        if not is_interlude and not is_inserted and num in PARTS:
            part, name, sub = PARTS[num]
            chapters_html.append(
                f'<section class="partpage"><p class="partnum">{part}</p>'
                f"<h1>{name}</h1><p class=\"partsub\">{sub}</p></section>"
            )
            toc.append(f'<li class="tocpart">{part} \u2014 {name}</li>')

        cls = "interlude" if is_interlude else "chapter"
        html = md_to_html(raw)
        # pull the h1 out so we can style plate placement
        html = re.sub(r"^<h1>(.*?)</h1>", "", html, count=1, flags=re.S)
        plate = None if is_interlude else plate_for(stem)
        fig = figure(plate) if plate else ""
        chapters_html.append(
            f'<section class="{cls}"><h1>{title}</h1>{fig}{html}</section>'
        )
        if not is_interlude:
            toc.append(f"<li>{title}</li>")

    # ---- appendices ----
    appendix_files = sorted(APPENDICES.glob("*.md")) if APPENDICES.exists() else []
    if appendix_files:
        chapters_html.append(
            '<section class="partpage"><p class="partnum">APPENDICES</p>'
            "<h1>MATTER SAVED FROM THE FALL</h1>"
            '<p class="partsub">compiled at Roothollow, in the first year of the ground</p></section>'
        )
        toc.append('<li class="tocpart">APPENDICES</li>')
        for f in appendix_files:
            raw = f.read_text(encoding="utf-8")
            title_m = re.match(r"^#\s+(.+?)\s*$", raw.split("\n", 1)[0])
            title = title_m.group(1) if title_m else f.stem
            html = md_to_html(raw)
            html = re.sub(r"^<h1>(.*?)</h1>", "", html, count=1, flags=re.S)
            chapters_html.append(
                f'<section class="appendix"><h1>{title}</h1>{html}</section>'
            )
            toc.append(f"<li>{title}</li>")

    body.append(
        '<section class="tocpage"><h1>Contents</h1><ul class="toc">'
        + "\n".join(toc)
        + "</ul></section>"
    )
    body.extend(chapters_html)

    css = """
    @page { size: 6in 9in; margin: 0.9in 0.85in 1in 0.85in; }
    html { -webkit-print-color-adjust: exact; }
    body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.6pt;
           line-height: 1.42; color: #111; margin: 0; }
    p { margin: 0; text-indent: 1.25em; text-align: justify; hyphens: auto; }
    h1 + p, figure + p, .scenebreak + p, .partsub + p { text-indent: 0; }
    em { font-style: italic; }

    section { page-break-after: always; }
    section.chapter, section.interlude { page-break-after: auto;
      page-break-before: always; }

    .titlepage { text-align: center; padding-top: 1.6in; }
    .titlepage .series { letter-spacing: 0.28em; font-size: 8pt; color: #444; }
    .titlepage h1 { font-size: 30pt; letter-spacing: 0.08em; margin: 0.35in 0 0;
      font-weight: normal; }
    .titlepage .rule { width: 1.4in; border-top: 1px solid #111;
      margin: 0.3in auto; }
    .titlepage .tag { font-style: italic; font-size: 10pt; text-indent: 0;
      text-align: center; }

    .artpage { text-align: center; }
    .maplabel { text-indent: 0; text-align: center; font-variant: small-caps;
      letter-spacing: 0.12em; font-size: 9pt; margin-bottom: 0.15in; }
    figure { margin: 0.18in 0 0.22in; text-align: center; page-break-inside: avoid; }
    figure img { max-width: 100%; }
    figure.map img { max-height: 7in; }
    figure.front img { max-height: 6.6in; max-width: 92%; }
    figure.plate img { max-height: 4.3in; }

    .tocpage h1 { text-align: center; font-size: 15pt; font-weight: normal;
      letter-spacing: 0.2em; font-variant: small-caps; }
    ul.toc { list-style: none; padding: 0 0.4in; }
    ul.toc li { text-indent: 0; margin: 0.35em 0; text-align: center;
      font-size: 9.5pt; }
    ul.toc li.tocpart { margin-top: 1.1em; font-variant: small-caps;
      letter-spacing: 0.14em; }

    .partpage { text-align: center; padding-top: 2.4in; }
    .partpage .partnum { letter-spacing: 0.3em; font-size: 9pt; text-indent: 0;
      text-align: center; }
    .partpage h1 { font-size: 21pt; letter-spacing: 0.12em; font-weight: normal;
      margin: 0.22in 0 0.12in; }
    .partpage .partsub { font-style: italic; font-size: 9.5pt; text-indent: 0;
      text-align: center; }

    .chapter h1, .interlude h1 { font-size: 13.5pt; font-weight: normal;
      text-align: center; font-variant: small-caps; letter-spacing: 0.1em;
      margin: 0.5in 0 0.28in; }
    .scenebreak { text-align: center; margin: 0.75em 0; letter-spacing: 0.5em; }

    .interlude { font-style: italic; }
    .interlude p { text-indent: 0; margin-bottom: 0.5em; }

    section.appendix { page-break-after: auto; page-break-before: always;
      font-size: 9.8pt; }
    .appendix h1 { font-size: 12.5pt; font-weight: normal; text-align: center;
      font-variant: small-caps; letter-spacing: 0.1em; margin: 0.5in 0 0.24in; }
    .appendix h2 { font-size: 10.5pt; font-variant: small-caps;
      font-weight: normal; letter-spacing: 0.08em; margin: 0.9em 0 0.3em; }
    .appendix p { text-indent: 0; margin-bottom: 0.35em; }
    .appendix ul { padding-left: 1.1em; margin: 0.2em 0 0.6em; }
    .appendix li { margin: 0.15em 0; }
    """

    OUT_HTML.write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>The Hundred Banners</title><style>{css}</style></head><body>"
        + "\n".join(body)
        + "</body></html>",
        encoding="utf-8",
    )
    print(f"wrote {OUT_HTML}")

    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={OUT_PDF}",
            OUT_HTML.as_uri(),
        ],
        check=True,
        capture_output=True,
        timeout=600,
    )
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
