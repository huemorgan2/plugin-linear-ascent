# 078 — snappy clicks (latency + cached art acceptance)

## Preconditions

- Local worldd on :8600 with Phases 1–4 landed and vendored; DB seeded
  with ≥ 1,000 playing players (`worldd/tools/seed_scale.py`).
- A signed-in probe account past creation, standing in Roothollow.

## Scenario

1. Instrument the page: wrap the pane's act fetch with `performance`
   marks (or read Network timings) so each click's request→painted-card
   time is captured.
2. Click through: square → shop → back → gate → ride to a floor (lift
   overlay expected — excluded from the latency assertion) → fight one
   round → flee → profile → labs toggle → back to square. Screenshot the
   fight card and the profile.
3. Repeat the square → shop → back loop twice more; watch the network
   panel on the repeats.
4. Read 20 act response sizes from the network log.

## Expected behavior

- Every non-lift click paints its new card in **< 300 ms**; the game feels
  immediate, no perceptible pause between click and card.
- Act responses are **< 30 KB**; no response carries `data:image/png` or
  `data:image/gif` payloads.
- Art (banners, gear icons, portraits) loads from `/static/laart/...`
  once; repeat views hit the browser cache (no re-download on the second
  and third shop visit).
- The fight card's one-shot GIF still restarts from frame 0 (nonce
  behavior preserved); ambient loops keep looping.
- Meters, roster boards, presence and happenings still show live-feeling
  data (staleness never exceeds ~10 s; a frontier raise shows immediately).

## Fail conditions

- Any non-lift click > 1 s, or a visible spinner/blank gap between cards.
- An act response > 100 KB, or inline base64 art anywhere in a fragment.
- Art 404s, broken masks (solid rectangles), missing gear icons, wrong
  banner on any visited card.
- Repeat visits re-downloading identical art.
- Stale world data: another player's warden kill or a frontier raise not
  visible after 10 s / next click.
- Console errors or failed requests at any step.

## Verify

- `worldd/tools/bench_act.py` table inside budget at the seeded scale.
- `EXPLAIN` on roster/census shows index usage, no Seq Scan.
- Second browser as another account: both see each other's presence and
  happenings within the TTL contract.
