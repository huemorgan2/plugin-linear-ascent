#!/usr/bin/env python3
"""Assemble THE HUNDRED BANNERS into a print-ready HTML + PDF.

Reads book/chapters/*.md (in lexicographic order), inserts part-title pages,
Malgrim-ledger interludes, and the pencil plates from book/art/, wraps the
whole in professional book furniture (front matter, folios, running heads,
TOC page numbers via Paged.js), then prints two PDFs at 140x216mm trim:
the interior block, and a separate covers PDF (front + back).
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
BUILD = BOOK / "build"
OUT_HTML = BOOK / "the-hundred-banners.html"
OUT_PDF = BOOK / "the-hundred-banners.pdf"
COVERS_HTML = BOOK / "the-hundred-banners-covers.html"
COVERS_PDF = BOOK / "the-hundred-banners-covers.pdf"

AUTHOR = "RAYLA"
PUBLISHER = "Girdlesea Press"
PUBLISHER_CITY = "Harrowport"
ISBN = "978-1-84893-407-1"

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


def plate_for(stem: str):
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


def front_cover() -> str:
    cover_art = print_copy(ART / "front-tower.png")
    return (
        '<section class="cover frontcover">'
        f'<img class="coverart" src="art/_print/{cover_art.name}" alt="">'
        '<div class="coverink">'
        '<p class="coverseries">A NOVEL OF THE LINEAR ASCENT</p>'
        '<h1 class="covertitle">THE<br>HUNDRED<br>BANNERS</h1>'
        '<div class="coverrule"></div>'
        f'<p class="coverauthor">{AUTHOR}</p>'
        "</div>"
        f'<p class="coverpub">{PUBLISHER.upper()}</p>'
        "</section>"
    )


def front_matter() -> list:
    body = []

    # ---- half title ----
    body.append(
        '<section class="halftitle frontmatter">'
        "<h1>THE HUNDRED BANNERS</h1>"
        "</section>"
    )

    # ---- frontispiece ----
    if (ART / "front-banner.png").exists():
        body.append(
            '<section class="artpage frontmatter">'
            + figure(ART / "front-banner.png", "front")
            + "</section>"
        )

    # ---- title page ----
    body.append(
        '<section class="titlepage frontmatter">'
        '<p class="series">A NOVEL OF THE LINEAR ASCENT</p>'
        "<h1>THE HUNDRED<br>BANNERS</h1>"
        '<div class="rule"></div>'
        '<p class="tag">The tower was built so the world could never gather.<br>'
        "This is the story of the gathering.</p>"
        f'<p class="byline">{AUTHOR}</p>'
        f'<p class="imprint">{PUBLISHER}<br><span>{PUBLISHER_CITY}</span></p>'
        "</section>"
    )

    # ---- copyright page ----
    body.append(
        '<section class="copyrightpage frontmatter">'
        "<p>THE HUNDRED BANNERS</p>"
        "<p>Copyright \u00a9 2026 by Rayla<br>"
        "All rights reserved. No part of this book may be reproduced, taken "
        "apart, lifted whole out of its frame, or stacked above another "
        "book without written permission from the publisher, except in the "
        "case of brief quotations embodied in reviews.</p>"
        f"<p>Published by {PUBLISHER}, {PUBLISHER_CITY}<br>"
        "First Girdlesea Press edition, August 2026</p>"
        "<p>This is a work of fiction. Names, characters, places, floors, "
        "wardens, and events are the products of the author\u2019s "
        "imagination. Any resemblance to actual persons, living, dead, or "
        "freed, or to actual countries, grounded or otherwise, is "
        "coincidental.</p>"
        "<p>Cover and interior plates drawn in graphite by the author.<br>"
        "Set in Georgia. Printed on honest paper.</p>"
        f"<p>ISBN {ISBN}</p>"
        "<p>1&nbsp;&nbsp;3&nbsp;&nbsp;5&nbsp;&nbsp;7&nbsp;&nbsp;9&nbsp;&nbsp;"
        "10&nbsp;&nbsp;8&nbsp;&nbsp;6&nbsp;&nbsp;4&nbsp;&nbsp;2</p>"
        "</section>"
    )

    # ---- dedication ----
    body.append(
        '<section class="dedication frontmatter">'
        "<p><em>for the keepers \u2014<br>"
        "the ones who stayed at their posts</em></p>"
        "</section>"
    )

    # ---- maps ----
    def map_page(art: Path, label: str, cls: str) -> str:
        p = print_copy(art)
        return (
            '<section class="artpage frontmatter">'
            f'<figure class="{cls}">'
            f'<figcaption class="maplabel">{label}</figcaption>'
            f'<img src="art/_print/{p.name}" alt="">'
            "</figure></section>"
        )

    if (ART / "front-tower.png").exists():
        body.append(map_page(ART / "front-tower.png",
                             "The Ascent \u2014 one hundred stolen floors",
                             "map"))
    if (ART / "front-roothollow.png").exists():
        body.append(map_page(ART / "front-roothollow.png",
                             "Roothollow, at the foot", "front"))
    return body


def back_matter() -> list:
    # ---- about the author ----
    return [
        '<section class="aboutauthor frontmatter">'
        "<h1>About the Author</h1>"
        "<p>RAYLA was born in a port town that smells of rain and tar, and "
        "grew up listening to sailors argue about lights on the horizon. "
        "She has worked as a bell-founder\u2019s clerk, a surveyor\u2019s "
        "chain-hand, and a keeper of other people\u2019s ledgers, and she "
        "still counts stairs without meaning to.</p>"
        "<p><em>The Hundred Banners</em> is her first novel. She is at work "
        "on the second.</p>"
        "</section>"
    ]


def back_cover() -> str:
    return (
        '<section class="cover backcover">'
        '<div class="backinner">'
        '<p class="backseries">A NOVEL OF THE LINEAR ASCENT</p>'
        '<p class="backlead">The world did not end. It was <em>taken</em> '
        "\u2014 cut country from country and stacked a hundred floors high, "
        "each stolen land a cell in the sky, so that its peoples could "
        "never again gather against the thief who keeps the throne at the "
        "top.</p>"
        "<p class=\"backbody\">Eighty years later, a trainer of raw recruits "
        "buries her last debt at the foot of the tower and starts to climb. "
        "What begins as one woman\u2019s reckoning becomes a rising the "
        "tower was built to make impossible: a hundred banners, a hundred "
        "freed floors, an army that grows by the very thing it frees. With "
        "an elf archer who does not miss and a giant mender who will not "
        "kill, Ede Harrow must bargain with spider-queens and storm-courts, "
        "out-mourn a dead king, and learn the one truth the tower hides: "
        "the Wardens do not hold the tower up. They hold the light out.</p>"
        '<div class="backquotes">'
        "<p>\u201cA megastructure epic with a farmer\u2019s heart. The best "
        "first sight of a tower since fantasy learned to look up.\u201d<br>"
        "<span>\u2014 The Lanternmoth Review</span></p>"
        "<p>\u201cRayla writes war the way keepers keep gates: patiently, "
        "by name, and then all at once.\u201d<br>"
        "<span>\u2014 Harrowport Courant</span></p>"
        "<p>\u201cThe ladder turns gold and you will cry. We do not make "
        "exceptions and we did not expect to make one here.\u201d<br>"
        "<span>\u2014 The Girdle-Sea Almanac</span></p>"
        "</div>"
        '<div class="backfoot">'
        f'<p class="backpub">{PUBLISHER.upper()}<br><span>{PUBLISHER_CITY}'
        "</span></p>"
        f'<p class="backisbn">FICTION<br>ISBN {ISBN}</p>'
        "</div>"
        "</div>"
        "</section>"
    )


def build() -> None:
    files = sorted(CHAPTERS.glob("*.md"))
    if not files:
        sys.exit("no chapters found")

    toc: list = []
    body: list = front_matter()

    # ---- chapters ----
    chapters_html: list = []
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
            pid = f"part-{num}"
            chapters_html.append(
                f'<section class="partpage" id="{pid}"><p class="partnum">{part}</p>'
                f'<h1>{name}</h1><p class="partsub">{sub}</p></section>'
            )
            toc.append(f'<li class="tocpart"><a href="#{pid}">{part} \u2014 {name}</a></li>')

        cls = "interlude" if is_interlude else "chapter"
        cid = f"ch-{stem}"
        html = md_to_html(raw)
        # pull the h1 out so we can style plate placement
        html = re.sub(r"^<h1>(.*?)</h1>", "", html, count=1, flags=re.S)
        plate = None if is_interlude else plate_for(stem)
        fig = figure(plate) if plate else ""
        chapters_html.append(
            f'<section class="{cls}" id="{cid}"><h1>{title}</h1>{fig}{html}</section>'
        )
        if not is_interlude:
            toc.append(f'<li><a href="#{cid}">{title}</a></li>')

    # ---- appendices ----
    appendix_files = sorted(APPENDICES.glob("*.md")) if APPENDICES.exists() else []
    if appendix_files:
        chapters_html.append(
            '<section class="partpage" id="part-app"><p class="partnum">APPENDICES</p>'
            "<h1>MATTER SAVED FROM THE FALL</h1>"
            '<p class="partsub">compiled at Roothollow, in the first year of the ground</p></section>'
        )
        toc.append('<li class="tocpart"><a href="#part-app">APPENDICES</a></li>')
        for f in appendix_files:
            raw = f.read_text(encoding="utf-8")
            title_m = re.match(r"^#\s+(.+?)\s*$", raw.split("\n", 1)[0])
            title = title_m.group(1) if title_m else f.stem
            aid = f"app-{f.stem}"
            html = md_to_html(raw)
            html = re.sub(r"^<h1>(.*?)</h1>", "", html, count=1, flags=re.S)
            chapters_html.append(
                f'<section class="appendix" id="{aid}"><h1>{title}</h1>{html}</section>'
            )
            toc.append(f'<li><a href="#{aid}">{title}</a></li>')

    body.append(
        '<section class="tocpage frontmatter"><h1>Contents</h1><ul class="toc">'
        + "\n".join(toc)
        + "</ul></section>"
    )
    body.extend(chapters_html)
    body.extend(back_matter())

    css = """
    :root { --ink: #111; }
    html { -webkit-print-color-adjust: exact; }
    body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.6pt;
           line-height: 1.42; color: var(--ink); margin: 0; }
    p { margin: 0; text-indent: 1.25em; text-align: justify; hyphens: auto; }
    h1 + p, figure + p, .scenebreak + p, .partsub + p { text-indent: 0; }
    em { font-style: italic; }

    /* ---------- page masters (trim 140 x 216 mm) ---------- */
    @page { size: 140mm 216mm; }
    @page body {
      margin: 0.78in 0.62in 0.88in 0.85in;
      @bottom-center { content: counter(page); font-family: Georgia, serif;
        font-size: 9pt; color: #222; }
    }
    @page body:left {
      margin: 0.78in 0.85in 0.88in 0.62in;
      @top-center { content: "THE HUNDRED BANNERS"; font-family: Georgia,
        serif; font-size: 8pt; letter-spacing: 0.22em; color: #333; }
    }
    @page body:right {
      @top-center { content: string(chaptitle); font-family: Georgia, serif;
        font-size: 8pt; letter-spacing: 0.18em; font-variant: small-caps;
        color: #333; }
    }
    /* no running head on chapter-opener pages */
    @page body:first {
      @top-center { content: none; }
    }
    @page plain { margin: 0.78in 0.72in 0.88in 0.72in; }
    @page coverpage { margin: 0; }

    section.cover { page: coverpage; }
    section.chapter, section.interlude, section.appendix, section.artpage
      { page: body; }
    section.frontmatter, section.partpage, section.tocpage,
    section.artpage.frontmatter { page: plain; }

    section { break-after: page; }
    section.chapter, section.interlude, section.appendix
      { break-after: auto; break-before: page; }
    section.partpage { break-before: right; }

    .chapter h1, .interlude h1, .appendix h1
      { string-set: chaptitle content(text); }

    /* ---------- covers ---------- */
    section.cover { width: 140mm; height: 216mm; position: relative;
      overflow: hidden; }
    .frontcover { background: #e9e5da; }
    .coverart { position: absolute; inset: 0; width: 100%; height: 100%;
      object-fit: cover; }
    .coverink { position: absolute; top: 0.55in; left: 0; right: 0;
      text-align: center; text-shadow: 0 0 5px rgba(236,232,222,0.95),
      0 0 14px rgba(236,232,222,0.8); }
    .coverseries { text-indent: 0; text-align: center; font-size: 7.5pt;
      letter-spacing: 0.3em; color: #2b2b2b; }
    .covertitle { font-size: 34pt; font-weight: normal; line-height: 1.14;
      letter-spacing: 0.1em; margin: 0.16in 0 0; color: #161616; }
    .coverrule { width: 1.5in; border-top: 1.5px solid #161616;
      margin: 0.18in auto; }
    .coverauthor { text-indent: 0; text-align: center; font-size: 15pt;
      letter-spacing: 0.42em; color: #161616; }
    .coverpub { position: absolute; bottom: 0.28in; left: 0; right: 0;
      text-indent: 0; text-align: center; font-size: 7pt;
      letter-spacing: 0.34em; color: #ded9cc; }

    .backcover { background: #efece3; }
    .backinner { position: absolute; inset: 0.55in 0.55in 0.5in;
      display: flex; flex-direction: column; }
    .backseries { text-indent: 0; text-align: center; font-size: 7pt;
      letter-spacing: 0.3em; color: #444; margin-bottom: 0.22in; }
    .backlead { text-indent: 0; text-align: left; font-size: 11.5pt;
      line-height: 1.5; margin-bottom: 0.14in; }
    .backbody { text-indent: 0; text-align: left; font-size: 9.8pt;
      line-height: 1.5; }
    .backquotes { margin-top: 0.22in; border-top: 1px solid #999;
      padding-top: 0.16in; }
    .backquotes p { text-indent: 0; text-align: left; font-style: italic;
      font-size: 9pt; line-height: 1.42; margin-bottom: 0.11in; }
    .backquotes span { font-style: normal; font-size: 8pt;
      letter-spacing: 0.06em; }
    .backfoot { margin-top: auto; display: flex;
      justify-content: space-between; align-items: flex-end;
      border-top: 1px solid #999; padding-top: 0.12in; }
    .backfoot p { text-indent: 0; text-align: left; }
    .backpub { font-size: 8.5pt; letter-spacing: 0.24em; }
    .backpub span { font-size: 7pt; letter-spacing: 0.18em; color: #555; }
    .backisbn { text-align: right; font-size: 7.5pt; line-height: 1.6;
      letter-spacing: 0.08em; color: #333; }

    /* ---------- front matter ---------- */
    .halftitle { text-align: center; padding-top: 2.7in; }
    .halftitle h1 { font-size: 16pt; font-weight: normal;
      letter-spacing: 0.22em; }

    .titlepage { text-align: center; padding-top: 1.1in; }
    .titlepage .series { letter-spacing: 0.28em; font-size: 8pt; color: #444;
      text-indent: 0; text-align: center; }
    .titlepage h1 { font-size: 30pt; letter-spacing: 0.08em;
      margin: 0.35in 0 0; font-weight: normal; }
    .titlepage .rule { width: 1.4in; border-top: 1px solid #111;
      margin: 0.3in auto; }
    .titlepage .tag { font-style: italic; font-size: 10pt; text-indent: 0;
      text-align: center; }
    .titlepage .byline { margin-top: 0.55in; font-size: 14pt;
      letter-spacing: 0.4em; text-indent: 0; text-align: center; }
    .titlepage .imprint { margin-top: 1.0in; font-size: 9.5pt;
      letter-spacing: 0.2em; text-indent: 0; text-align: center; }
    .titlepage .imprint span { font-size: 7.5pt; letter-spacing: 0.16em;
      color: #444; }

    .copyrightpage { padding-top: 3.6in; font-size: 8pt; line-height: 1.5;
      color: #222; }
    .copyrightpage p { text-indent: 0; text-align: center;
      margin-bottom: 0.55em; }

    .dedication { text-align: center; padding-top: 2.9in; }
    .dedication p { text-indent: 0; text-align: center; font-size: 11pt; }

    .artpage { text-align: center; }
    .maplabel { text-indent: 0; text-align: center; font-variant: small-caps;
      letter-spacing: 0.12em; font-size: 9pt; margin-bottom: 0.15in; }
    figure { margin: 0.18in 0 0.22in; text-align: center;
      break-inside: avoid; }
    figure img { max-width: 100%; }
    figure.map img { max-height: 6.1in; }
    figure.front img { max-height: 6.0in; max-width: 92%; }
    figure.plate img { max-height: 3.9in; }

    .tocpage h1 { text-align: center; font-size: 15pt; font-weight: normal;
      letter-spacing: 0.2em; font-variant: small-caps;
      margin-bottom: 0.3in; }
    ul.toc { list-style: none; padding: 0 0.15in; margin: 0; }
    ul.toc li { text-indent: 0; margin: 0.32em 0; font-size: 9.5pt; }
    ul.toc li a { text-decoration: none; color: var(--ink); display: block;
      overflow: hidden; }
    ul.toc li a::after { content: target-counter(attr(href url), page);
      float: right; font-size: 8.5pt; }
    ul.toc li.tocpart { margin-top: 1.05em; font-variant: small-caps;
      letter-spacing: 0.14em; }
    ul.toc li.tocpart a::after { content: none; }

    /* ---------- body ---------- */
    .partpage { text-align: center; padding-top: 2.4in; }
    .partpage .partnum { letter-spacing: 0.3em; font-size: 9pt;
      text-indent: 0; text-align: center; }
    .partpage h1 { font-size: 21pt; letter-spacing: 0.12em;
      font-weight: normal; margin: 0.22in 0 0.12in; }
    .partpage .partsub { font-style: italic; font-size: 9.5pt;
      text-indent: 0; text-align: center; }

    .chapter h1, .interlude h1 { font-size: 13.5pt; font-weight: normal;
      text-align: center; font-variant: small-caps; letter-spacing: 0.1em;
      margin: 0.5in 0 0.28in; }
    .scenebreak { text-align: center; margin: 0.75em 0;
      letter-spacing: 0.5em; }

    .interlude { font-style: italic; }
    .interlude p { text-indent: 0; margin-bottom: 0.5em; }

    section.appendix { font-size: 9.8pt; }
    .appendix h1 { font-size: 12.5pt; font-weight: normal;
      text-align: center; font-variant: small-caps; letter-spacing: 0.1em;
      margin: 0.5in 0 0.24in; }
    .appendix h2 { font-size: 10.5pt; font-variant: small-caps;
      font-weight: normal; letter-spacing: 0.08em; margin: 0.9em 0 0.3em; }
    .appendix p { text-indent: 0; margin-bottom: 0.35em; }
    .appendix ul { padding-left: 1.1em; margin: 0.2em 0 0.6em; }
    .appendix li { margin: 0.15em 0; }

    .aboutauthor { padding-top: 1.2in; }
    .aboutauthor h1 { font-size: 12.5pt; font-weight: normal;
      text-align: center; font-variant: small-caps; letter-spacing: 0.14em;
      margin-bottom: 0.3in; }
    .aboutauthor p { text-indent: 0; text-align: justify;
      margin-bottom: 0.6em; }

    /* keep pagedjs preview honest */
    .pagedjs_page { background: white; }
    """

    def render(html_path: Path, pdf_path: Path, title: str,
               sections: list) -> None:
        html_path.write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f"<title>{title}</title><style>{css}</style>"
            "</head><body>"
            + "\n".join(sections)
            + "</body></html>",
            encoding="utf-8",
        )
        print(f"wrote {html_path}")
        # pagedjs-cli paginates (folios, running heads, TOC page numbers)
        # and waits for layout to finish before printing — headless Chrome
        # alone prints too early.
        subprocess.run(
            ["npx", "-y", "pagedjs-cli", str(html_path), "-o",
             str(pdf_path), "--timeout", "2400000"],
            check=True,
            timeout=2400,
        )
        print(f"wrote {pdf_path}")

    render(OUT_HTML, OUT_PDF, "The Hundred Banners", body)
    render(COVERS_HTML, COVERS_PDF, "The Hundred Banners \u2014 covers",
           [front_cover(), back_cover()])


if __name__ == "__main__":
    build()
