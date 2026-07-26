# 010 — Score & Community: leaderboard, factions, weekly goals

Directive (2026-07-26), building on the 009 pane tabs:

- **SCORE** — list all players: level and gold.
- **COMMUNITY** — join a faction or create a new one. The founder
  names the faction and picks its banner from a set of 30 designs.
  Factions have weekly goals; reaching one grants a top-up (different
  goals give different rewards). Faction management can remove members
  who don't contribute. The prize is scaled by attendance: everyone
  showing up 4 days that week = 100% of the prize; fewer days deduct
  proportionally; below 50% total → nothing; more days pay
  proportionally more, up to full 7-day attendance (175%).

Follow-up directive (same day): the attendance mechanic already favors
small factions that actually show up — lean into it, but keep scale
worthwhile: factions **under 4 members get a 15% base bonus; 4+
members get 20%**.

## 0. Attendance math (the whole trick, pinned down)

World weeks: `week = world_day // 7` (world_day already rolls at
06:00 UTC, `engine/state.py`). A player "attended" a day if they
performed at least one act that world_day.

At week resolution for a faction:

    required   = Σ over members of min(4, days member was in faction that week)
    attended   = Σ over members of unique attendance days while a member
                 (each member capped at 7)
    ratio      = attended / required

    multiplier = 0                    if ratio < 0.5
               = min(ratio, 7/4)      otherwise        # cap 175% (confirmed)

    base_pct   = 15%  if members at resolution < 4
               = 20%  if members at resolution ≥ 4

    prize      = base_pct of goal × multiplier

So a 5-member faction needs 20 member-days for the full 20%; 15 days
gives 75% of it; 9 days (45%) gives zero; a perfect 35 days gives
175% of the 20% (= 35% of the goal). A 3-member faction plays the
same curve on a 15% base — small crews that reliably show up still
win big per head, but crossing 4 members bumps the whole pool.

Anti-gaming: kicking a no-show removes their days from *both* sides
of the ratio — that is the intended management lever, not an exploit.
Mid-week joiners are prorated (`min(4, days remaining at join)`), so
recruiting on day 6 can't dilute or juice the ratio.

## 1. worldd schema — migration `006_factions.sql`

    ascent_factions        name PK, banner (slug from the 30-design
                           set), founder_tenant, founder_player,
                           created_week, goal_kind, goal_target
    ascent_faction_members faction, tenant, player, role
                           ('steward'|'member'), joined_day,
                           PK (tenant, player)          -- one faction each
    ascent_attendance      tenant, player, world_day, PK all three
    ascent_faction_weeks   faction, week, goal_kind, goal_target,
                           progress, ratio, multiplier, prize_note,
                           resolved_at                  -- history

Migrate `ascent_guilds` rows into `ascent_factions` (founder becomes
steward); `doc["guild"]` remains the display link and is synced from
the membership table on doc load (kicked players see it cleared on
their next act — same lazy pattern as lodging).

Attendance write: in `game.py`'s act path, `INSERT … ON CONFLICT DO
NOTHING` of `(tenant, player, world_day)` — one cheap upsert per act.

## 2. Goals — three kinds, three top-ups

Steward picks next week's goal from a menu; suggested targets scale
with member count × average level so a 3-climber faction isn't chasing
a 20-climber number.

`base_pct` below is the size tier from section 0 — 15% under 4
members, 20% at 4+.

| Goal | Target | Reached → prize (before multiplier) |
|---|---|---|
| **HOARD** | faction earns ≥ G gold this week | gold pool = base_pct of G, split among members proportional to attendance days |
| **CULL** | faction kills ≥ N creatures | +base_pct max-HP blessing, all members, following week |
| **CLIMB** | faction gains ≥ X total XP | +base_pct XP blessing, all members, following week |

Blessings scale with the multiplier (4+ members at ratio 0.75 →
+15% HP; perfect week → +35%). Stored on the doc as
`faction_buff = {kind, pct, until_week}`; engine applies it in
`combat.py` (max HP) / XP award path — a small, gated engine change
that is inert when the field is absent (local backend unaffected).

Progress is aggregated at resolution from `ascent_ledger` (gold/xp
deltas are already audited there) — kills need ledger rows tagged
`kind='kill'`; add that tag where combat writes the ledger. No new
per-act counter plumbing.

## 3. Weekly resolution — lazy, like everything else

No cron. On the first faction-touching request of a new week (any
member's act, or a faction API read), resolve the previous week inside
one transaction:

1. compute progress from ledger, attendance ratio, multiplier;
2. pay gold / write blessings into member docs;
3. write the `ascent_faction_weeks` history row;
4. post an `ascent_happenings` line ("The Ember Pact met its hoard —
   the Ascent pays out ◈214") — the Morning Crier picks it up free.

## 4. worldd endpoints (tenant HMAC, same auth as `/v1/act`)

    POST /v1/leaderboard      all stage='playing' players: name, race,
                              class, level, gold (carried), bank,
                              faction, last_seen_days; sorted
                              level desc, then gold. Paginated (50).
    POST /v1/faction/list     name, member count, steward, current
                              goal + progress bar data
    POST /v1/faction/create   ◈500 (reuses guild-founding price);
                              body: name + banner slug (validated
                              against the 30-design set)
    POST /v1/faction/join     |  /leave  |  /kick (steward only)
    POST /v1/faction/goal     steward sets next week's goal
    POST /v1/faction/status   my faction: members with role + days
                              attended this week, goal progress,
                              live projected ratio/multiplier

`_roster` (Muster) stays as the in-game flavor location; the
leaderboard is the complete, gold-visible table. Cross-tenant
visibility matches what Muster already exposes, plus carried gold —
one deliberate scope-widening to call out at review.

## 5. Plugin proxy routes

The pane iframe can't sign HMAC, so `routes.py` adds thin
authenticated proxies: `GET /score`, `GET/POST /community/*` →
`WorldClient` gains `leaderboard()` and `faction_*()` methods.
Offline/local-dev fallback: SCORE shows the solo player, COMMUNITY
shows "the world lift is down" (same message the game already uses).

## 6. Pane UI (fills the 009 placeholders)

Same monospace/dark-panel language as the game tab.

**SCORE** — a ranked table:

    ##  CLIMBER          LVL   GOLD    BANK   FACTION
    01  Vex the Red       14   ◈212   ◈4.1k   Ember Pact
    02  Mudge              12   ◈890   ◈1.2k   —

**COMMUNITY** —

- No faction: list of factions (banner + join button) + "Found a
  faction" flow (◈500): the founder types the faction's name
  (server-side validation, unique) and picks a banner from the
  30-design gallery — same 320×112 1-bit white-ink banners the game
  already uses, tinted per role like scene banners.
- Member: faction panel — the faction banner across the top, members
  with attendance pips for the week
  (`▪▪▪▫▫▫▫ 3/4`), goal progress in `█░`, live projected multiplier
  ("on pace for 110% of the prize"), leave button.
- Steward extras: kick button per member, goal picker for next week.

**Faction banner assets** — 30 sigil designs, sci-fi-fantasy, in the
game's 1-bit style: one bold centered emblem per banner (wolf sigil,
chained sun, circuit tree, storm fist…), generated by
`tools/generate_faction_banners.py` — the same Gemini → Bayer 1-bit →
white-ink pipeline as scene banners, output to
`content/art/banners/factions/`. The gallery endpoint just lists the
slugs; the pane renders them tinted on the panel like every other
banner. (Assets already generated alongside this plan.)

Every mutating action (join/create/kick/goal) also sends an
`awareness` muted message so the agent knows ("Roy founded the Ember
Pact"); weekly resolution results ride the existing happenings →
Crier path.

## Execution order

1. Migration 006 + attendance upsert + guild migration.
2. Resolution engine + multiplier math (pure function first).
3. Ledger `kind='kill'` tagging.
4. worldd endpoints + tests.
5. `WorldClient` methods + plugin proxy routes.
6. Pane SCORE tab, then COMMUNITY tab.
7. Blessing application in engine (HP/XP).

## Acceptance

- worldd pytest, table-driven on the section-0 examples: 20/20 →
  1.0; 15/20 → 0.75; 9/20 → 0; 35/20 → 1.75; kick removes both
  sides; mid-week join prorates; double-resolution is idempotent.
- HOARD payout splits by attendance days and lands in docs + ledger;
  CULL blessing raises max HP 20%·multiplier for exactly one week.
- Multiplier tiers: 3-member faction pays on the 15% base, adding a
  4th member bumps the same goal to 20%.
- Dojo, real browser: SCORE lists every seeded player with level and
  gold; found a faction — name it, pick a banner from the gallery,
  banner shows on the faction panel and list; second player joins,
  steward kicks them, goal set; attendance pips update after acts on
  two consecutive world-days (time-warped via test hooks).
- Agent stays silent through all of it unless asked; Crier mentions
  the payout the next morning.
