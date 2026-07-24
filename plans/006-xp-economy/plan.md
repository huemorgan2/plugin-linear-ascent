# 006 — XP Economy: Replace Mana with Experience

**Goal:** delete the mana/aether meter and make **XP the game's second resource for
every player** — a per-level pool that fuels abilities and forge services
(spend), and a permanent **level** that gates weapons and areas (status).
Gold stays the third leg: gold buys things, XP earns you the *right* to them.

Owning repo: `plugin-linear-ascent` (submodule). Companion: re-vendor into
`worldd/vendor/` at the end. Produces version: bump `luna-plugin.toml`.

---

## 1. Prior art — how RPGs actually use XP

(Extends `vision/research.md`; that file covers pacing/PvP/groups but not
XP-as-currency, so this section is the research delta.)

| Model | Games | Mechanic | Lesson for us |
|---|---|---|---|
| **Pure progression meter** | WoW, LORD, D&D, RuneScape | XP only fills the level bar; never spent | Legible, zero regret — but XP is meaningless the moment you're not about to level |
| **XP as dropped currency** | Dark Souls (souls), Path of Exile (partial) | XP *is* money: buy levels **or** goods; dropped on death | Maximum tension, but "lose your XP on death" contradicts our v1 "death never takes XP" and LORD-style kindness. Reject the death-drop, keep the dual-use |
| **Spend-from-pool** | Minecraft (enchanting/anvil), EQ AA points | Levels are kept; the *pool* is spent on upgrades, setting back the next level | The exact shape the user asked for — spending delays leveling but buys the tools that make leveling easier |
| **Level as gate** | Everything from Diablo to Torn: gear req., area req. | Level is a permanent badge; requirements separate beginners from veterans | Cheap to implement, instantly readable ("requires level 21") |
| **Prestige/reset** | LORD dragon kill, KoL ascension | XP resets wholesale at the top | Already planned for Vharuk; untouched here |

**Design conclusion:** combine **spend-from-pool** (Minecraft) with **level as
gate** (everywhere) and reject the Souls death-drop. Levels are permanent and
gate content; the XP pool inside the current level is spendable fuel.

## 2. Current state (code audit)

- XP already exists and is already per-level: `_level_ups()` in
  `engine/combat.py` does `xp -= xp_need(level)` on each level-up, so `p["xp"]`
  is "XP inside the current level" with overflow carried. Levels are never
  lost (death takes gold + armor, never XP — economy.md §7).
- XP scaling already matches the "floor 2 pays about double" intuition:
  `xp_per_kill(F) = 12F ±25%`, wardens `60F`, milestones flat thousands.
- Mana ("aether" ✦): cap 10 (+1/20 levels, elf +1), regen 1/90 min, lazy
  meter in `engine/state.py` (`mana_ts`/`mana_val`). **Only one real spend
  exists** — sorcerer Sleep Spell (2 ✦). `COST_SIDEKICK_SCOUT_MANA` is
  vestigial (scout uses item charges). Aether philtre (◈150, +3 ✦, 1/day)
  is the only refill. Mana is dead weight for 2 of 3 classes.

### Touchpoint inventory (what "remove mana" actually touches)

| File | What |
|---|---|
| `economy.py` | `MANA_REGEN_MIN`, `MANA_BASE_CAP`, `mana_cap()`, `COST_SIDEKICK_SCOUT_MANA`, `aether_philtre` shop row, elf/sorcerer descriptions |
| `engine/state.py` | `mana_ts`/`mana_val` init, `mana_now()`, `spend_mana()`, `gain_mana()`, `ensure_current()` |
| `engine/scene.py` | `Meters.mana/mana_max`, `Option.aether` flag, `to_text()` meter line |
| `engine/combat.py` | `meters()`, Sleep Spell branch, fight options/hints |
| `engine/core.py` | aether-philtre purchase branch, medlab scene, forge buy/hone |
| `render.py` | ✦ meter, `_TIP_AE` tooltip, aether key styling (colors stay — see §4.6) |
| `sheet.py` | `"aether"` field |
| `vision/economy.md` §1 §6 | the two-meter table, philtre row, sidekick night job (never implemented) |
| `tests/test_economy.py` (+engine/render/payload tests) | `mana_cap` assertions etc. |
| `worldd/vendor/plugin_linear_ascent/` | re-vendor via `worldd/tools/vendor_game.sh` |
| Stored player docs (production!) | `mana_ts`/`mana_val` keys — **left in place**, simply no longer read (devprocess data-preservation rule; no destructive migration) |

## 3. The new design

### 3.1 One rule sentence

> **Levels are forever and open doors; the XP inside your current level is
> aether — spend it and you level slower, hoard it and you level sooner.**

Lore stays intact: *aether is crystallized experience*. The ✦ glyph, the blue
shard styling, and the word "aether" all survive — they now point at the XP
pool instead of a regenerating bar. Abilities "burn what you've learned."

### 3.2 The XP pool (spend side — meaningful for ALL classes)

All costs are priced in **frontier kills** so they scale forever and stay a
real decision at every level (a flat cost would be trivial by floor 20):

| Spend | Cost | Who | Notes |
|---|---|---|---|
| **Forge honing** | gold (existing) **+ ✦ `round(0.5 × xp_per_kill(unlocked_floor))`** | everyone | The Minecraft anvil loop: sharpening your blade sets back your next level but speeds every fight after. This is the change that makes XP matter for warriors and archers too |
| **Sleep Spell** (sorcerer) | ✦ `xp_per_kill(floor)` — and awards **nothing** (today: 2 mana, awards half XP) | sorcerer | Skip-a-fight now costs exactly the kill you're skipping. Clean opportunity-cost |
| **Shard scan** (no optics charges) | ✦ `round(0.5 × xp_per_kill(floor))` | everyone | Scout optics charges stay free-to-use; XP is the fallback when charges run out — replaces the vestigial `COST_SIDEKICK_SCOUT_MANA` |

Spending never reduces `p["xp"]` below 0 and never touches level. If the pool
is short, the option shows but refuses with a shard note ("You haven't
learned enough yet — ✦ 84 needed."). Shield Wall and Treeline Shot stay free
(they're the class identity, not the resource sink).

### 3.3 Levels (gate side)

- **Levels can never be taken away.** Already true; codify it: death, PvP
  loss, and every future mechanic may touch gold/gear/pool, never level.
  PvP (when built): the winner's bounty is *minted*, not taken from the victim.
- **Level-up resets the pool.** On level-up the pool is consumed. Current
  code carries overflow (`xp -= need`); keep the carry (see Open decision D1
  for the hard-zero variant and why milestone bosses make it painful).
- **Forge gates:** buying tier-T gear requires
  **level ≥ `band_start(T)` = 10·(T−1)+1**. Gold alone can no longer buy a
  veteran's blade — the catalog shows the requirement on locked rows
  (`"level 21"` hint, refuse with shard note). Starter shiv and tier 1 stay
  ungated.
- **Area gates:** entering floor F from the tower gate requires
  **level ≥ F − 10** (on top of the existing warden-unlock). Loose enough to
  never bite a normal climber (design level ≈ floor), tight enough that a
  level-4 player can't ride the world lift to floor 40.
- Honing stays gated by `unlocked_floor` as today (no change).

### 3.4 Earn side (mostly unchanged, one retune)

- `xp_per_kill(F) = 12F ±25%` stays — floor 2 already pays 2× floor 1,
  matching the "each floor pays visibly more" requirement.
- Wardens `60F`, milestones per table — unchanged.
- **Elf racial** (was +1 aether cap): becomes **+5% XP from kills** ("Keen:
  quick studies"). Same flavor slot, now touches the real resource.
- Sleep Spell no longer awards XP (see 3.2).

### 3.5 What gets deleted outright

- The mana meter: cap, regen, `mana_now/spend_mana/gain_mana`, `mana_cap`,
  `MANA_REGEN_MIN`, `MANA_BASE_CAP`, `COST_SIDEKICK_SCOUT_MANA`.
- **Aether philtre** removed from the Apothecary with no replacement —
  selling XP for gold would let wallets shortcut the veteran gate, exactly
  what this plan exists to prevent. (Catalog drops to 6 items; `daily`
  bookkeeping key stays in old docs, unread.)
- economy.md's "sidekick night job 3 ✦" (was never implemented).

### 3.6 UI: the ✦ meter becomes the XP bar

- `Meters.mana/mana_max` → `Meters.xp/xp_need` (rename through scene → combat
  → render → sheet → worldd vendor in one commit; `to_dict()` payload key
  changes with it).
- Rail shows `✦ 340/520` with the block bar = progress **to next level** —
  the meter finally moves every fight instead of sitting full for weeks.
- New tooltip: "✦ Aether — crystallized experience. Fills as you fight; full
  bar = next level (levels are forever). Spent on honing, spells, and shard
  scans — spending slows your level, never lowers it."
- `Option.aether` flag and blue key styling stay — meaning shifts from
  "mana option" to "XP-cost option".
- `sheet.py`: `"aether"` → `"xp": "340/520"`, plus `"level"` already present.

## 4. Execution phases

Per devprocess: branch `006-xp-economy` inside the submodule; scenario files
in `tests/006-xp-economy/` **before** implementation; unit tests still run
against local + worldd HTTP backends; live walkthrough before reporting done.

- **Phase 0 — docs.** Update `vision/economy.md` (§1 one-meter table, §3 XP
  pool rules, §5 no sleep-XP, §6 philtre/gates, elf racial); append the §1
  prior-art table of this plan to `vision/research.md`. Write E2E scenarios.
- **Phase 1 — economy.py.** Remove mana constants/`mana_cap`; add
  `hone_xp(unlocked_floor)`, `sleep_xp_cost(floor)`, `scan_xp_cost(floor)`,
  `gear_level_req(tier)`, `floor_level_req(floor)`, `ELF_XP_BONUS = 0.05`;
  update `RACES`/`CLASSES` text; drop the philtre row.
- **Phase 2 — state.py.** Remove mana meter functions and init keys; add
  `spend_xp(p, amount) -> bool` (floor at 0, never touches level);
  `ensure_current()` tolerates and preserves legacy `mana_*` keys.
- **Phase 3 — engine.** scene.py `Meters` rename; combat.py `meters()`,
  Sleep Spell (new cost/reward), scan fallback option + resolution, elf bonus
  in `_victory`; core.py forge level gates (locked-row hints + refusal),
  hone XP cost (hint shows both prices: `◈ 120 + ✦ 84`), gate-scene floor
  gate, remove philtre purchase branch.
- **Phase 4 — presentation.** render.py meter + tooltip + hints; sheet.py.
- **Phase 5 — tests.** Fix `test_economy.py` (mana asserts → XP-cost and
  gate asserts), engine/render/payload tests; add: spend floors at 0, level
  never drops, gate refusals, elf bonus, hone charges both currencies,
  legacy-doc load (doc with `mana_val` loads clean). Content lint gate.
- **Phase 6 — worldd.** `worldd/tools/vendor_game.sh`; contract tests on both
  backends; **no DB migration** — player docs keep stale `mana_*` keys
  (append-only ledger untouched). Verify a production-shaped doc round-trips.
- **Phase 7 — E2E + live walkthrough.** Run `tests/006-xp-economy/` scenarios
  in a real browser per the run-dojo skill, then the agent-live-walkthrough.
  First user query check: "play linear ascent" → open the character sheet →
  hone at the Forge (see ✦ price charged) → try to buy tier-2 gear at level 1
  (must refuse with the level hint).

Version bump: `luna-plugin.toml` (and manifest text if it mentions meters);
submodule commit first, then parent pointer bump.

## 5. Open decisions (answer before/at execution)

- **D1 — hard-zero on level-up?** You asked for "XP reduced to 0". Current
  code subtracts the level cost, carrying overflow. Recommendation: **keep the
  carry** — a milestone Warden pays 20,000 ✦ while level 20→21 needs ~5,400;
  hard-zero inside the level-up loop would incinerate the rest of the reward
  and make bosses feel like a scam. The carry still gives you the shape you
  want (pool is per-level, spending sets you back). If you want hard-zero
  anyway, we cap wilds overflow only and exempt warden/milestone awards.
- **D2 — floor gate slack.** `level ≥ F − 10` proposed. Tighten to `F − 5`
  if world-lift skipping still feels too easy in the walkthrough.
- **D3 — hone XP price.** 0.5 kills per hone proposed; sim it in
  `plans/004-difficulty-review/sim.py` style during Phase 1 so days-in-tier
  (economy.md §4) stays on the 6→24 line.

Not in scope: PvP XP bounty implementation, prestige reset, XP gifting
(would reopen the wallet shortcut via mules).
