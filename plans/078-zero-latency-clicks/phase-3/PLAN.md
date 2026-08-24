# Phase 3 — all images to static URLs (plugin + worldd vendor)

## Goal

No card fragment carries base64 image data. Every banner, event GIF, gear
icon, portrait, sigil, paper texture and strip band is a cacheable URL under
a static mount on whichever host renders the card. A menu-click response is
≤ 30 KB; repeat views of the same art are HTTP-cache hits (304/„memory
cache"). The tiny generated inline SVG glyphs (≈ 1–5 KB, computed not
files) and the 24 KB WOFF font stay inline — they are not the payload
problem and keep chat cards self-contained.

## Steps

1. **`render.py` — an art-base seam.** Module-level `ART_BASE: str = ""`
   plus `set_art_base(base)`. All 25 data-URL call sites
   (`_banner_data_url`, `_fx_data_url`, `_fx_split`, `_gear_art_url`,
   `_sigil_half_data_url`, `_strip_art_url`, `_paper_tex_url`,
   `_portrait_art`, …) gain a URL twin that returns
   `{ART_BASE}/<dir>/<file>?v={version}` when `ART_BASE` is set and the
   file exists (same existence/size-fallback ladders as today — the
   ladders already know the filenames, so width/height keep coming from
   the probe). `ART_BASE` empty → data URLs, unchanged (test fixtures and
   any host that never wired a mount keep working; the deprecation note
   points here).
   - `?v=` is the plugin version — flips the cache on art regeneration.
   - One-shot event GIFs keep the client-side `?t=` nonce mechanism on
     top (038: frame-0 restart), applied by the existing swap/pane JS —
     nonce goes on the URL the same way it does for `/static/fxart` today.
2. **worldd mounts the whole art tree**: in `worldd/app/main.py`, beside
   the existing fxart mount, `app.mount("/static/laart", StaticFiles(dir=
   vendor content/art))`; `webplay.py` (and routes that render fragments)
   call `set_art_base("/static/laart")` at startup. `/static/fxart` stays
   (site.js, intro movie, lift overlay reference it directly).
3. **Luna host serves the same tree**: the plugin's `routes.py` registers
   its own static route for `content/art` (FileResponse with a safe-path
   guard, mirroring the fxart pattern) and calls
   `set_art_base(<that route's base>)` when the plugin boots inside Luna —
   the chat card and Luna pane fetch art from the plugin's own origin, no
   dependency on worldd being reachable.
4. **Cache headers**: a thin StaticFiles subclass (or response hook) adds
   `Cache-Control: public, max-age=31536000, immutable` to both mounts —
   correct because every URL is versioned by `?v=`.
5. **Vendor sync** (`bash worldd/tools/vendor_game.sh`) + version bump.
6. **Tests**:
   - plugin: with `ART_BASE` set, a rendered fight/shop/profile/reel
     fragment contains zero `data:image/png` and zero `data:image/gif`
     occurrences and all art URLs resolve to files on disk; with it unset,
     the legacy inline behavior is byte-stable.
   - worldd: `/static/laart/banners/<known>.png` → 200 with immutable
     cache header; an act fragment < 30 KB; fragment art URLs all 200
     (walk every URL in one rendered corpus).

## Verification

- Both suites green.
- Browser (dojo phase catches it end-to-end, but gate here too): DevTools
  network on three consecutive menu clicks — art requests appear once,
  then serve from cache; act responses < 30 KB; no 404s on any card played
  through square → gate → fight → loot → shop → profile.

## Rollback

`git revert` (plugin commit, vendor commit). `ART_BASE` unset restores
inline art wholesale — a one-line emergency mitigation
(`set_art_base("")`) exists even without a revert. Static mounts are
additive and harmless to leave.
