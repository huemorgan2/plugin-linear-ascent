# 032 — the banner hall

Factions have a ledger, a treasury, a weekly challenge, an armory — and
no *place*. The faction page is a report, not a room. This plan gives
every banner a hall behind the Guildhall: a home screen with the sigil
flying over it, the week's goal shouted at the top, and doors you walk
through — the coffer, the chest, the bulletin board, the bunks — each
its own area, app-style, like the forge is its own area. The hall
starts as a rented back room and is bought up, tier by tier, with the
faction's own gold.

## The ask (verbatim intent)

1. Faction sigil to the **left of the name** in every list.
2. **Donate gold** to the faction (preset amounts or custom) and
   **donate items** any member can take.
3. The faction page becomes **a real place** — large banner on top,
   somewhere that feels good to stay in.
4. **Room tiers with different art.** Start small; pay to scale up —
   never automatic.
5. A **vault** for the money and a **chest** for the stuff — entered as
   separate areas, not one long page. The chest lists takeable items
   **card-style, like the forge**.
6. A **bulletin board**: members write one-line notes; the latest note
   sits prominently near the top — world-day, author, short line, all
   fitting one line.
7. **Buyable faction furnishings**: bigger chest (basic holds 4
   items), bigger vault (basic holds ◈200), and **beds** — a member
   sleeping in a faction bed is safe for the night, free. Beds fit
   from the second room up: 2, then 6, then 10.
8. The **weekly goal super prominent**. The faction buys into a goal
   (costs gold, from the store — already built); once entered, the
   goal owns the top of the page. Not entered → the same slot shows
   this week's challenge and the way in.

## What exists (so we change little)

- **The weekly machine is done** (010): the world posts one challenge
  per week (`hoard`/`cull`/`climb` cycling, `factions.py:106-109`),
  the steward enters for ◈5 × members **from the store**
  (`enter_week`, `worldd/app/factions.py:519-557`), progress is
  derived from `ascent_ledger`, resolution is lazy and idempotent
  (`maybe_resolve` :216-256), prizes are minted, never taken. This
  plan builds no mechanics here — only **loudness**.
- **Donations exist** (`/v1/faction/donate`, `main.py:407`; engine
  effect `faction_donate`) — carried gold only, by design ("donating
  is a deliberate act"). Missing only the preset-or-custom UI.
- **The armory exists** (017/§9 of vision/economy.md): a shared gear
  rack, economically neutral (no gold crosses it, wear rides through),
  member-only, one take per player per world-day, donor name kept.
  That *is* the chest — it just needs a door, a card grid, and a
  capacity that starts small and is bought up.
- **Safety-for-the-night exists**: the Lodge sells `lodged_until_day`
  for ◈10 × level (`engine/core.py:1737`, `economy.py:1728`), and PvP
  target selection already skips anyone holding it
  (`worldd/app/social.py:481-499`). A faction bed is a second,
  free way to set the **same flag** — no new combat logic.
- **The render grammar has everything we need**: `grid=True` card
  walls (forge, `engine/core.py:1027-1123`), sub-area navigation via
  `p["location"]` + option ids (`_dispatch_location`,
  `engine/core.py:814-869`), the `banner` slot for a 320×112 sigil on
  top, `strip` for a wide art band, `notices` for blue "something
  waits" bars, inline `ask` inputs (no popups, ever — 015/027 law).
- **Sigils-beside-names is half-shipped**: `.fbanner.small` (64px,
  `pane.py:76`) already rides in THE LEDGER rows and HALL OF BANNERS
  rows. The FIND results, MOST CLIMBERS, RICHEST STORE and HIGHEST
  BLADES rows still show bare names.
- **Store outflows have exactly one sink** (the weekly entry). Room
  tiers, chest/coffer upgrades and beds become the sinks the store
  has been waiting for — and they keep 010's iron law intact:
  **nobody, steward included, can ever pocket the store.** Gold goes
  in from members, and out only to the world (entries, furnishings).

## Naming

The town bank is already **the Vault**, and 022 gave it a personal
weekly strongbox — the faction money-room cannot also be "the vault".
In the hall the user's "vault" ships as **THE COFFER** (the store,
given a door), and the user's item-store ships as **THE CHEST** (the
armory, given a door). Community-board headings follow: "RICHEST
STORE" → "RICHEST COFFER". Everything member-facing says *coffer* for
faction gold from now on; "store" survives only in old ledger prose.

## The design

### 1. Sigils beside names, everywhere

Every faction name in the Community tab gets its `.fbanner.small`
sigil to the left: FIND results, MOST CLIMBERS, RICHEST COFFER,
HIGHEST BLADES (the top-5 chip rows, `pane.py:406-423`), and any place
a bare name survives. The API payloads already carry the slug
(`banners` map / `f.banner`) — this is pane JS only.

### 2. The hall — one home screen, five doors

Members stop landing on a report. The Guildhall member panel's
faction half moves into a new location: `p["location"] = "hall"`,
reached by a "YOUR HALL" row at the Guildhall (and a door on the town
square once a banner is joined). The Guildhall keeps founding,
joining, training, and the hall-of-banners browsing for the
unaffiliated.

The hall home screen, top to bottom:

1. **The faction sigil, large, on top** — the `banner` slot, tinted
   as today.
2. **The room art band** — a `strip` (320×50) whose art is the room
   tier's interior. Different tier, different room, visibly.
3. **THE WEEK box — the loudest thing on the page** (see §8).
4. **The latest bulletin line** — `DAY 34 · Kettle — "dues land
   tonight, pay up"` — one line, dim, clickable through to the board.
5. **The doors**, as option rows with `option_art`:
   `THE COFFER — ◈140 of ◈200` · `THE CHEST — 3 of 4 slots` ·
   `THE BULLETIN BOARD` · `THE BUNKS — 2 beds, 1 claimed` (tier ≥ 2)
   · `THE WORKS — buy up the hall` · roster/desk rows as today ·
   `[back]` to town.

Every area is its own Scene; `back` returns to the hall, from the
hall to town. Sub-state rides `p["hall_area"]` exactly the way the
founding wizard rides `p["founding_guild"]` (`engine/social.py:476`).

### 3. Rooms — four tiers, bought, never granted

| tier | name | interior art | beds fit | price (from the coffer) |
|---|---|---|---|---|
| 1 | the back room | a curtained alcove behind the Guildhall | 0 | — (every new banner starts here) |
| 2 | a hall of your own | plank walls, one long table | 2 | ◈500 |
| 3 | the long hall | stone hearth, racked spears | 6 | ◈2,000 |
| 4 | the high hall | arcanotech chandelier over old timber | 10 | ◈6,000 |

Buying up is a steward action in THE WORKS, paid from the coffer,
one tier at a time, never automatic, never downgraded. No member-count
gate — the user asked for paid scaling, so a rich trio may sit in a
high hall it rattles around in. Room tier is worn proudly: it shows on
the Community faction page and the hall-of-banners rows.

### 4. The coffer — the store, capped, with a door

The treasury gets a **capacity**, and the capacity is bought:

| coffer tier | holds | upgrade price |
|---|---|---|
| 1 | ◈200 | — |
| 2 | ◈600 | ◈120 |
| 3 | ◈2,500 | ◈400 |
| 4 | ◈8,000 | ◈1,200 |

Caps are sized so each room is reachable one coffer tier ahead of it
(room 2 needs coffer 2, room 3 needs coffer 3, room 4 needs coffer 4).
**Every inflow clips to the space left** — a donation that doesn't fit
is taken only up to the brim ("the coffer takes ◈37 of your ◈100 —
it is full"), dues likewise. Nothing is ever burned out of a member's
pocket by a full coffer. Existing factions at migration are
grandfathered: coffer tier is set to the smallest tier whose cap
covers their current balance.

The coffer area shows: the balance against the cap, the last 8 ledger
rows (as the panel does today), and the **donate** rows —
`◈10 · ◈50 · ◈100 · a sum of your naming` — the last one an inline
`ask` input, presets one tap. Carried gold only, as designed.

### 5. The chest — the armory, reborn as a card wall

The armory becomes THE CHEST, and its flat 50-row cap becomes slots
that are bought:

| chest tier | slots | upgrade price |
|---|---|---|
| 1 | 4 | — |
| 2 | 8 | ◈150 |
| 3 | 16 | ◈400 |
| 4 | 32 | ◈1,000 |

Inside, the forge treatment exactly: `grid=True`, each item a
`.gcard` with its gear icon on top, name + donor underneath
(`donated by Kettle`), `[i]` dossier pinned to the corner. Empty slots
render as dark sockets, the pack way (031 §3), so the bought capacity
is *visible*. A `PUT IN` row lists your donatable pack items.

The 017 exploit-proofing is law and does not move: no gold crosses
the chest boundary, wear rides through unchanged, member-only both
ways, **one take per player per world-day**, donor kept for audit.
Existing armories over the new slot count are grandfathered
(tier set to fit), never truncated.

### 6. The bulletin board

New table, new area, one mechanic: any member writes **one line**
(≤ 64 chars, plain text, inline `ask` input). The board shows the
last 20, newest first: `DAY 34 · Kettle — dues land tonight, pay up`.
The newest line also sits on the hall home screen (§2.4) — the
prominent slot the user asked for. Writing is free; a member may hold
at most one note per world-day (writing again the same day replaces
it — no flooding, no moderation surface). Notes die with the era, as
all faction things do.

### 7. The bunks — a free safe night

In THE WORKS the steward buys **beds at ◈250 each**, capped by room
tier (0 / 2 / 6 / 10). In THE BUNKS any member takes
`SLEEP HERE TONIGHT — free` while claims remain: first come, first
bunked, one claim per member per night, shown by name ("tonight:
Kettle, Moss — 1 bed open"). A claim sets `lodged_until_day =
world_day + 1` — the *same* flag the Lodge sells for ◈10 × level —
so PvP target selection (`worldd/app/social.py:481-499`) already
honors it, untouched. The bed buys **safety only**: no Lodge night
job, no rested-XP — dawn heals everyone regardless, as always. That
a wealthy banner undercuts the Lodge is the point; it is what the
dues bought.

### 8. THE WEEK, made loud

The top box of the hall, directly under the room strip, full width,
notification-blue border when action waits:

- **Entered**: `THE WEEK — CLIMB · 374 / 800 ✦` with a fat progress
  bar, the attendance pips `▪▪▪▫▫▫▫ 3/4`, and the projection line
  `on pace for ×1.25 — prize is minted at week's turn`.
- **Not entered, challenge open**: the same box shows the offer —
  `THIS WEEK THE ASCENT DEMANDS A CULL — 120 heads` — and beneath it,
  for a steward, the live row `ENTER THE WEEK — ◈5 a head from the
  coffer (◈15)` (refusal with shortfall if the coffer is light, as
  today); for a member, `the steward signs the banner in — nudge
  them`. The row is a proper option, never prose (019 law).
- A steward with an un-entered week also gets a blue **notice** on
  the town square scene: `the week stands unentered at your hall`.

No new mechanics — `enter_week`, targets, multipliers, resolution all
stand. This section is purely: the thing the faction lives for gets
the biggest slot on its page, every day, without hunting for it.

### 9. The Community tab mirrors it

The pane faction detail page (`pane.py:531-601`) adds: the room tier
name under the big banner, coffer balance *of* cap, chest slots used,
bed count, and the latest bulletin line (members only — outsiders see
the room tier and nothing private). "RICHEST STORE" →
"RICHEST COFFER". Board mechanics untouched.

## Data and wire

**Migration `worldd/migrations/011_faction_hall.sql`:**

```sql
ALTER TABLE ascent_factions
  ADD COLUMN room_tier   int NOT NULL DEFAULT 1,
  ADD COLUMN coffer_tier int NOT NULL DEFAULT 1,
  ADD COLUMN chest_tier  int NOT NULL DEFAULT 1,
  ADD COLUMN beds        int NOT NULL DEFAULT 0;

CREATE TABLE ascent_faction_notes (
  id bigserial PRIMARY KEY,
  faction text NOT NULL REFERENCES ascent_factions(name)
    ON DELETE CASCADE ON UPDATE CASCADE,
  tenant text NOT NULL, player text NOT NULL,
  world_day int NOT NULL, line text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (faction, tenant, player, world_day)   -- one note/member/day
);

CREATE TABLE ascent_faction_bed_claims (
  tenant text NOT NULL, player text NOT NULL,
  faction text NOT NULL REFERENCES ascent_factions(name)
    ON DELETE CASCADE ON UPDATE CASCADE,
  world_day int NOT NULL,
  PRIMARY KEY (tenant, player, world_day)       -- one bed/member/night
);
```

Tier→cap/price tables live in code (`factions.py`), one dict each,
next to `FOUND_FEE` — a single tuning surface. Grandfathering runs in
the migration transaction (set `coffer_tier`/`chest_tier` up to fit
existing balances/rows). Both new tables join the era wipe list
(`worldd/app/era.py:28-30`).

**Engine effects** (through `social.execute_effects`,
`worldd/app/social.py:515-616`, same shape as `faction_donate`):
`hall_room_buy`, `hall_coffer_up`, `hall_chest_up`, `hall_bed_buy`
(steward, coffer-paid, ledger kinds `works_*`), `hall_bed_claim`
(member, free, capacity-checked in one transaction), `hall_note`
(member, upsert on the day key). Chest put/take ride the existing
armory effects with the slot check added.

**Scene injection**: the faction panel worldd already injects
(`social._faction_panel`, `worldd/app/social.py:205-271`) grows a
`hall` key: `{room_tier, coffer: {bal, cap}, chest: {used, cap},
beds: {count, tonight: [names]}, notes: [last 20], works: [priced
upgrade rows]}`. **Wire-compat law**: all new Scene data rides
top-level keys, never new keys inside option dicts
(`engine/scene.py:13-23`) — old renderers drop unknown top-level keys
gracefully.

## Art to generate

Through the existing Gemini → Bayer 1-bit pipeline
(`tools/generate_faction_banners.py` as the template):

- 4 room interiors, 320×50 strip format — alcove / plank hall /
  long hall / high hall.
- Card/option art for the doors: coffer (iron-bound box), chest
  (open lid), board (nailed notes), bunks (blanketed cot),
  the works (mason's tools). 1-bit, retintable masks like all art.

## Phases

1. **worldd** — migration 011, tier tables, clip-to-cap on every
   coffer inflow, effects, panel `hall` injection, era wipe, board
   heading rename. Tests beside the existing faction tests.
2. **engine (vendored)** — the hall location + five areas, the WEEK
   box, donate presets + ask, chest card grid on the armory, bulletin,
   bunks, works; steward notice on the square.
3. **art** — generate, place under `content/art/`, wire slugs.
4. **pane** — sigils beside every name (§1), faction detail additions
   (§9).
5. **ship** — bump `version.py`, `worldd/tools/vendor_game.sh`,
   commit `0.40.0: the banner hall`, deploy, then the acceptance
   gate: verify `/health` game field AND the marketplace renderer
   both live before calling it done.

## Tuning table (every number in one place)

| knob | value |
|---|---|
| room tiers | ◈500 / ◈2,000 / ◈6,000 |
| coffer caps | 200 / 600 / 2,500 / 8,000 |
| coffer upgrade prices | ◈120 / ◈400 / ◈1,200 |
| chest slots | 4 / 8 / 16 / 32 |
| chest upgrade prices | ◈150 / ◈400 / ◈1,000 |
| bed price | ◈250 |
| beds by room tier | 0 / 2 / 6 / 10 |
| bulletin line | ≤ 64 chars, 1/member/day, board keeps 20 |
| weekly entry | ◈5 × members from the coffer (unchanged) |

All prices are coffer-paid and world-bound (burned) — the 010 law
that no player can ever draw faction gold back out stands untouched.

## QA (dojo)

A `0011-banner-hall` run: found a banner → back room, ◈200 cap ·
donate ◈50 preset + custom ◈7 · overfill the coffer, watch the clip ·
buy coffer 2, room 2, one bed · second member claims the bed, third
bounces · verify the claimant vanishes from `pvp_targets` · chest:
put 4, refuse the 5th, take 1 (day-capped) · write two notes same
day, see the upsert · enter the week from the hall, watch the box
flip from offer to progress · Community: sigils in all five lists,
room tier + latest line on the detail page.
