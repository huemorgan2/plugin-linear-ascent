# 051 — The Postbox: player feedback, admin desk, replies

## What

A FEEDBACK button on the lower toolbar (the sound bar, next to SOUND and
MUSIC) opens an in-pane overlay in the game's ANSI look. Players file
feedback — subject + large text area + up to 3 screenshot attachments —
stored in the world database with the player's identity. Two named users
(MasterChief, huemorgan3) get an extra ADMIN button on the same toolbar:
a table of every feedback thread, WhatsApp-sorted (latest message first).
Opening a thread — from either side — is a chat: player messages on one
side, admin replies on the other, attachments allowed in every message.
An admin reply lights an unread badge on the player's FEEDBACK button;
a player message lights the admin's badge.

## Where things live (both doors, one world)

- worldd owns the data. New migration + `app/feedback.py` + `/v1/feedback/*`
  (tenant HMAC) + `/play/api/pane/feedback/*` (site cookie, webplay.py).
- The plugin proxies `/pane/feedback/*` → worldd via `WorldClient`
  (backend/remote.py), same as the faction desk.
- The pane (pane.py) is the whole UI for both doors; sfx.py's sound bar
  gains the two buttons.

## DB — `worldd/migrations/017_feedback.sql`

- `ascent_feedback` (threads): id, tenant, player, author (character
  name at filing), subject, created_at, last_msg_at, last_sender,
  player_unread int, admin_unread int. Indexes: (tenant, player,
  last_msg_at DESC) and (last_msg_at DESC).
- `ascent_feedback_messages`: id, feedback_id FK cascade, sender
  ('player'|'admin'), author (character name), body, created_at.
- `ascent_feedback_attachments`: id, message_id FK cascade, mime, bytes
  (bytea). Screenshots live in the DB — no object store to run.

## Server — `worldd/app/feedback.py`

- Admins: `ASCENT_FEEDBACK_ADMINS` env, default `masterchief,huemorgan3`,
  matched against the CHARACTER name lowercased (004: names are unique
  world-wide, so a name is an identity).
- `create` (subject 3–80, body 1–4000, ≤3 attachments, png/jpeg/webp/gif,
  ≤2 MB each decoded), `my_threads`, `thread` (marks the reader's side
  read), `reply` (bumps last_msg_at, increments the other side's unread),
  `unread` (badge poll: {n, admin, admin_n}), `admin_threads` (all, last
  message first), `attachment` (owner or admin only).
- Endpoints: `/v1/feedback/{create,mine,thread,reply,unread,admin,att}`
  in main.py; cookie mirrors in webplay.py, attachment as a real image
  response there; the plugin's att route decodes the HMAC answer back to
  an image response.

## Plugin — routes.py + backend/remote.py

New `WorldClient.feedback_*` methods; new `/pane/feedback/*` routes via
the same `_proxy` used by the faction desk. Dev-local mode (no world)
answers 503 like score/community already do.

## Pane UI — pane.py, icons.py, sfx.py

- icons.py: a 16×16 envelope glyph (`postbox`) for the button; ADMIN
  reuses the letter style with a badge dot drawn by CSS, not art.
- Sound bar: `FEEDBACK` button (always) + `ADMIN` button (hidden until
  the unread poll says admin) + unread count badges. Poll every 60s and
  on every postbox action — never on the 2s peek hot path.
- Overlay `#fbpanel`: fixed, full viewport, INK background, same panel /
  eyebrow / btn / ti grammar as the rest of the pane. Views:
  - Player: THE POSTBOX — new-feedback form (subject, large textarea,
    attach up to 3 screenshots with thumbnails) above the list of their
    threads with unread tags.
  - Thread (both roles): chat — my messages right-shifted, theirs left,
    author + time meta line, attachment thumbnails (click opens full),
    composer with textarea + attach + SEND at the bottom.
  - Admin: table of all threads — from (author), subject, last line,
    when, NEW tag — sorted like WhatsApp; click opens the same chat with
    sender=admin.
- Screenshots are downscaled client-side (canvas, ≤1400px, JPEG) before
  upload; sent base64 in JSON so the HMAC door signs them like any body.

## Tests

- `worldd/tests/test_051_feedback.py` (docker ascent-postgres, port 5434):
  create→mine round trip with player identity; admin gate 403 for
  non-admins, open for MasterChief and huemorgan3 by character name,
  case-insensitive; reply flips unread both ways and re-sorts the admin
  table; thread read clears unread; attachments round-trip with the right
  mime and are refused to strangers; validation limits (subject, body,
  count, mime, size); the web-door mirror (sign up, file, badge, admin).
- `plugin-linear-ascent/tests/test_051_postbox.py`: render_pane carries
  the buttons, the overlay and the feedback JS in both web and iframe
  flavors.

## Ship

Version 0.67.0 is already bumped in the working tree by in-flight work —
no second bump. After tests: `worldd/tools/vendor_game.sh`. No commit, no
deploy — roy's word.
