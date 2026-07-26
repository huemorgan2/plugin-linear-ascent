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

Third directive (same day): factions run on a shared purse.

- Founding a faction now sets two numbers besides name and banner:
  the **join fee** (paid once by every climber who enters) and the
  **weekly dues** (collected from every member each world-week —
  small, "not a lot").
- Both land in the **faction store** — a treasury the faction owns,
  visible to every member.
- **Every week the world posts a NEW challenge** to join as a group;
  entering it costs gold, **paid from the store**.
- Any member can **donate** carried gold to the store at any time.

Fourth directive (same day): faction LIFE happens in the game, not
the pane.

- **Join / found a faction at the Guildhall building** in Roothollow
  — game scenes, like every other building. Manage it there too
  (donate, enter the week's challenge, kick, leave).
- The **COMMUNITY tab becomes the faction news board** — read-only:
  who won this week, who is ranked #1, the biggest factions by
  members, the richest by store gold, and the highest-levelled
  rosters. No join/create/manage UI in the pane.

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

## 0b. The faction store — join fee, weekly dues, donations

One treasury per faction; gold only ever flows IN from members
(join fees, dues, donations) and OUT to weekly challenge entries —
prizes are minted by the world, never drawn from the store. Nobody —
steward included — can pocket it, so there is no embezzlement
surface. Disbanding burns the store ("the Ascent keeps it").

**Set at founding** (immutable after, keeps the social contract
honest — pick numbers people can read before they join):

    join_fee      ◈ 0–500    one-time, charged on /join, → store
    weekly_dues   ◈ 1–50     per member per world-week, → store

The founder pays no join fee (the ◈500 founding price is their
buy-in) but pays dues like everyone else.

**Dues collection** — lazy, inside the same weekly resolution
transaction (§3): each member is charged carried gold first, then
bank. A member who can't cover it goes **in arrears**: they stay in
the faction but are excluded from that week's prize split, and the
Guildhall roster marks them (▲) — the steward's kick lever does the
rest. Arrears clear automatically the first week they can pay again.

**Donations** — any member, any time, from carried gold only (the
bank is the safe place; donating should be a deliberate act). No cap.

**Audit** — every store movement (join fee, dues, donation, challenge
entry, prize payout) writes a row in `ascent_faction_ledger`, shown
as the store history at the Guildhall.

## 1. worldd schema — migration `006_factions.sql`

    ascent_factions        name PK, banner (slug from the 30-design
                           set), founder_tenant, founder_player,
                           created_week, join_fee, weekly_dues,
                           treasury                     -- the store
    ascent_faction_members faction, tenant, player, role
                           ('steward'|'member'), joined_day, arrears,
                           PK (tenant, player)          -- one faction each
    ascent_attendance      tenant, player, world_day, PK all three
    ascent_faction_weeks   faction, week, goal_kind, goal_target,
                           entered (bool), entry_paid, progress,
                           ratio, multiplier, prize_note,
                           resolved_at                  -- history
    ascent_faction_ledger  faction, week, kind ('join_fee'|'dues'|
                           'donation'|'entry'|'payout'), amount,
                           tenant, player, note, created_at

Migrate `ascent_guilds` rows into `ascent_factions` (founder becomes
steward); `doc["guild"]` remains the display link and is synced from
the membership table on doc load (kicked players see it cleared on
their next act — same lazy pattern as lodging).

Attendance write: in `game.py`'s act path, `INSERT … ON CONFLICT DO
NOTHING` of `(tenant, player, world_day)` — one cheap upsert per act.

## 2. The weekly challenge — one NEW challenge every week

The world posts it, not the steward: `kind = week % 3` walks
HOARD → CULL → CLIMB, so every faction in the world chases the same
kind the same week (rivalry for free, and the Crier has one headline).
Targets are still per-faction — scaled by member count × average
level so a 3-climber faction isn't chasing a 20-climber number.

**Entering costs store gold.** The steward enters the week's
challenge at the Guildhall; the entry fee is

    entry = ◈ 5 × member count        (small — dues-sized, not rent)

paid from the store at join time. Store can't cover it → the join is
refused with the shortfall shown ("the store is ◈ 12 short — dues
land at week's turn, or pass the hat"); that's what donations are
for. A faction that doesn't enter plays a normal week: attendance is
still recorded, but there is no prize to multiply.

`base_pct` below is the size tier from section 0 — 15% under 4
members, 20% at 4+.

| Week kind | Target | Reached → prize (before multiplier) |
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

1. **collect dues** from every member (gold → bank → arrears flag),
   store += collected, ledger rows per member;
2. if the faction had **entered** the week's challenge: compute
   progress from ledger, attendance ratio, multiplier;
3. pay gold / write blessings into member docs — members in arrears
   are skipped from the split (their share stays in the pool for the
   others);
4. write the `ascent_faction_weeks` history row;
5. post `ascent_happenings` lines ("The Ember Pact met its hoard —
   the Ascent pays out ◈214") — the Morning Crier picks it up free;
   the NEW week's challenge gets its own line ("This week the Ascent
   demands a CULL — 120 heads per banner").

## 4. worldd endpoints (tenant HMAC, same auth as `/v1/act`)

    POST /v1/leaderboard      all stage='playing' players: name, race,
                              class, level, gold (carried), bank,
                              faction, last_seen_days; sorted
                              level desc, then gold. Paginated (50).
    POST /v1/faction/list     name, member count, steward, join fee,
                              weekly dues, current challenge +
                              progress bar data
    POST /v1/faction/create   ◈500 (reuses guild-founding price);
                              body: name + banner slug (validated
                              against the 30-design set) + join_fee
                              (0–500) + weekly_dues (1–50)
    POST /v1/faction/join     charges the join fee (gold → bank) into
                              the store  |  /leave  |  /kick (steward)
    POST /v1/faction/donate   ◈ N carried gold → store, ledger row
    POST /v1/faction/enter    steward enters THIS week's world
                              challenge; ◈5 × members from the store,
                              refused (with shortfall) if it can't pay
    POST /v1/faction/status   my faction: store balance, dues/fee,
                              members with role + days attended this
                              week + arrears flags, this week's
                              challenge (kind, target, entered?,
                              entry cost), goal progress, live
                              projected ratio/multiplier, store
                              ledger (last 20)
    POST /v1/faction/board    the news board (read-only, any tenant):
                              last week's winners (faction, goal,
                              prize note), all-time wins ranking
                              (#1 called out), top factions by member
                              count, by store gold, and by average
                              member level; recent faction happenings

`_roster` (Muster) stays as the in-game flavor location; the
leaderboard is the complete, gold-visible table. Cross-tenant
visibility matches what Muster already exposes, plus carried gold —
one deliberate scope-widening to call out at review.

## 5. Plugin proxy routes

The pane iframe can't sign HMAC, so `routes.py` adds thin
authenticated proxies — both read-only now: `GET /score` and
`GET /community/board` → `WorldClient` gains `leaderboard()`,
`faction_board()`, and the `faction_*()` methods the Guildhall
scenes use. Offline/local-dev fallback: SCORE shows the solo player,
COMMUNITY shows "the world lift is down" (same message the game
already uses).

## 6. Pane UI (fills the 009 placeholders)

Same monospace/dark-panel language as the game tab.

**SCORE** — a ranked table:

    ##  CLIMBER          LVL   GOLD    BANK   FACTION
    01  Vex the Red       14   ◈212   ◈4.1k   Ember Pact
    02  Mudge              12   ◈890   ◈1.2k   —

**COMMUNITY — the faction news board** (read-only; joining and
managing happens at the Guildhall, §6b):

    THIS WEEK          The Ember Pact won the CULL (paid ◈214)
                       Iron Root fell short — 84/120 heads
    HALL OF BANNERS    #1 Ember Pact — 4 wins        ← all-time wins
    MOST CLIMBERS      Ember Pact 9 · Iron Root 7 · …
    RICHEST STORE      Iron Root ◈ 1,240 · Ember Pact ◈ 342 · …
    HIGHEST BLADES     Night Ledger avg lvl 14 · …   ← avg member level

  Each row shows the faction's banner chip; recent faction happenings
  (founded/won/paid out) run beneath as a ticker. Data is one
  `/v1/faction/board` call; empty world renders "no banners raised
  yet — the Guildhall in Roothollow takes founders."

## 6b. The Guildhall — where faction life happens

Faction membership is IN-GAME, at the existing Guildhall building in
Roothollow (game scenes, same option grammar as every building):

- **No faction**: the hall lists factions (banner, members, join fee
  + weekly dues up front) as options → picking one is `/join` (fee
  charged gold → bank, into the store). "Raise a new banner" (◈500)
  runs a short creation flow: name (typed in chat, same pattern as
  character naming) → banner pick → set join fee (◈0–500) → set
  weekly dues (◈1–50), caps enforced by the scene.
- **Member**: the hall shows the store line
  (`STORE ◈ 342 · dues ◈ 5/week`), members with attendance pips
  (`▪▪▪▫▫▫▫ 3/4`, ▲ marks arrears), this week's challenge (kind,
  target, progress, "entered" stamp or the entry option with its
  store cost), projected multiplier, and options: **Donate ◈ N**
  (typed amount, carried gold), **Leave the banner**.
- **Steward extras**: **Enter the week's challenge** (◈5 × members
  from the store — refused with the shortfall shown), **Kick** (pick
  from a member list scene).

All of it speaks the existing worldd faction API (§4) through
`WorldClient`; the scenes emit the same `_effects` pattern as every
other social action, so worldd stays the single writer.

**Faction banner assets** — 30 sigil designs, sci-fi-fantasy, in the
game's 1-bit style: one bold centered emblem per banner (wolf sigil,
chained sun, circuit tree, storm fist…), generated by
`tools/generate_faction_banners.py` — the same Gemini → Bayer 1-bit →
white-ink pipeline as scene banners, output to
`content/art/banners/factions/`. The gallery endpoint just lists the
slugs; the pane renders them tinted on the panel like every other
banner. (Assets already generated alongside this plan.)

Every mutating action (create/join/leave/kick/donate/enter) also
sends an `awareness` muted message so the agent knows ("Roy founded
the Ember Pact"); weekly resolution results ride the existing
happenings → Crier path.

## Execution order

1. Migration 006 (factions + members + attendance + weeks + faction
   ledger, with join_fee / weekly_dues / treasury) + attendance
   upsert + guild migration.
2. Store mechanics: join fee, dues collection, donations, arrears —
   pure functions + worldd endpoints, ledger rows throughout.
3. Resolution engine + multiplier math (pure function first), dues
   collection folded into the same transaction.
4. Weekly world challenge: kind rotation, per-faction targets, entry
   from the store.
5. Ledger `kind='kill'` tagging.
6. worldd endpoints + tests.
7. `WorldClient` methods + plugin proxy routes (score + board).
8. Guildhall scenes: list/join/found flow, member panel, donate,
   enter-challenge, kick, leave.
9. Pane SCORE tab, then COMMUNITY news board.
10. Blessing application in engine (HP/XP).

## Acceptance

- worldd pytest, table-driven on the section-0 examples: 20/20 →
  1.0; 15/20 → 0.75; 9/20 → 0; 35/20 → 1.75; kick removes both
  sides; mid-week join prorates; double-resolution is idempotent.
- Store math, table-driven: join fee lands in the store with a ledger
  row; dues collected gold-first-then-bank; a broke member goes into
  arrears, is skipped by the payout split, and clears when solvent;
  donation moves exactly N carried gold; entry refuses when the store
  is short and shows the shortfall; double dues-collection for one
  week is idempotent.
- Challenge cadence: week k posts kind k % 3; a faction that never
  enters gets attendance history but no prize; entry after the store
  was topped up by a donation succeeds.
- HOARD payout splits by attendance days and lands in docs + ledger;
  CULL blessing raises max HP 20%·multiplier for exactly one week.
- Multiplier tiers: 3-member faction pays on the 15% base, adding a
  4th member bumps the same goal to 20%.
- Dojo, real browser: SCORE lists every seeded player with level and
  gold. At the **Guildhall** (in-game): found a faction — name it in
  chat, pick a banner, set join fee ◈25 / dues ◈5; a second player
  sees fee+dues in the hall list and joins — the store shows ◈25
  with a ledger row; donate ◈30 by typed amount; steward enters the
  week's challenge and the store drops by the entry; attendance pips
  update after acts on two consecutive world-days (time-warped via
  test hooks); week turn collects dues from both members.
- **COMMUNITY tab** shows the news board only (no join/manage
  controls): last week's winner with prize note, #1 by wins, top
  factions by members, by store gold, by average level, happenings
  ticker; renders sanely with zero factions.
- Agent stays silent through all of it unless asked; Crier announces
  the new week's challenge and mentions the payout the next morning.
