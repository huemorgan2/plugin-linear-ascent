# 015 — The Faction Desk

Faction management becomes a real surface. Founding is a rank privilege
(level 4+), the Guildhall lists the world's banners (top 10 + search),
faction names in COMMUNITY are clickable, and every faction gets an ADMIN
DESK — rename, join requests (accept/reject), kick, promote admins,
accept the week's challenge from the coin vault. The founder is always
marked. All of it lives inside the pane in ANSI-style blocks with inline
monospace text inputs — no popups, no chat round-trips.

## Directives (user)

1. "Build a faction" gated to level 4+ (it was gold-only before).
2. Guild lists existing factions: top 10 + search.
3. COMMUNITY faction names clickable → faction page.
4. Admin section per faction (reachable from COMMUNITY and the Guildhall):
   - name / rename the faction
   - accept challenges, paid from the faction coin vault (treasury)
   - accept / reject join requests, kick members
   - promote members to admin
5. Founder permanently marked as FOUNDER.
6. UI: ANSI design blocks, same monospace font, inline text inputs that
   save to the server, member-request accept/reject/kick inline. No popups.

## Model decisions

- **Admin == steward.** The existing `role='steward'` becomes multi-holder;
  the UI labels it ADMIN. Founder = `ascent_factions.founder_*` (badge, not
  a role). Admins manage members; an admin cannot kick another admin unless
  they are the founder.
- **Joining becomes a request.** `ascent_faction_requests` (one open
  request per player, PK tenant+player). No gold moves at request time;
  the join fee is charged when an admin ACCEPTS (if the requester can't
  pay, the accept fails and the request stays). The Guildhall `join_`
  option now files a request via a `faction_request` effect.
- **Rename cascades.** Migration 008 adds ON UPDATE CASCADE to the members
  FK; rename updates `ascent_faction_weeks` / `ascent_faction_ledger`
  rows manually (plain-text columns) so wins and audit history follow the
  banner. Docs' `guild` strings resync lazily (existing contract).
- **Founding gate**: level ≥ 4 enforced engine-side (option hidden with a
  hint line) AND in `/v1/faction/create` (403).

## Phases

1. **worldd** — migration `008_faction_desk.sql` (requests table + FK
   cascade); `factions.py`: request/cancel/approve/reject, rename,
   promote, detail, search, level gate; `main.py`: `/v1/faction/request|
   cancel_request|approve|reject|rename|promote|detail`, `list` gains
   `q`+top-10, `create` gains the level check, `kick` gains founder
   protection; `social.py`: `faction_request` effect, hall list top 10 +
   `requested` flag, member panel gains founder + pending request count.
2. **engine** — `social.py`: level-4 gate on `found_guild`, `join_` files
   a request, member panel shows ADMIN/FOUNDER tags + requests-waiting
   line pointing at the desk.
3. **client** — `WorldClient` new methods (+ create fee/dues fix);
   `routes.py` pane proxies for all desk actions.
4. **pane UI** — COMMUNITY: THE LEDGER (top 10 + FIND input), clickable
   faction names everywhere, faction page with roster/badges, ASK TO
   JOIN / WITHDRAW, and the ADMIN DESK (rename input+SAVE, requests
   ACCEPT/REJECT, members PROMOTE/KICK with inline confirm, challenge
   ACCEPT paid from the vault). GAME tab shows a "► FACTION DESK" bar
   when the scene is the Guildhall (switches tab).
5. Tests (worldd integration + plugin unit), version 0.10.0, vendor
   sync, browser E2E per `tests/015-faction-desk/`.

## Acceptance

- Level 3 character: no "Raise a new banner" option, refused by API too.
- Search "wol" finds Wolfpack; ledger shows ≤10 by members.
- Clicking a faction name in COMMUNITY opens its page; founder shows ★.
- Request → appears in that faction's desk → ACCEPT charges the fee and
  seats the member; REJECT clears it; both inline.
- Rename saves from the inline input, uniqueness enforced, wins history
  follows.
- PROMOTE makes a second ADMIN who can run the desk; founder badge stays
  where it was.
- Challenge ACCEPT debits the treasury exactly once.
- Old flows (donate, leave, train) unchanged; all pre-015 tests green.
