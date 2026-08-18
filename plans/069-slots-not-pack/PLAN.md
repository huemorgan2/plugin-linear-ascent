# 069 — Slots, not pack: worn/held gear is the only gear that counts

Status: executing (roy, 2026-08-18: "ok execute the plan").

## Problem (roy, 2026-08-18)
1. **The pack leaks effects.** Today the pack (`p["inventory"]`) is
   storage AND an active belt: every fight relic (net, hook, apple,
   veil, tonic, severing…), the quiver arrows, the oil flask and both
   death items fire straight from the pack; the luck charm is drunk on
   the shop counter. Shoes/armour/shield are worn-only already, but the
   UI does not make the worn/packed distinction visible.
   **Law wanted:** nothing in the pack has any effect on the player. An
   item counts only when it sits in a slot.
2. **The UI hides the slots.** `_inventory_html` shows a "hand row" and
   a flat grid; there is no fixed slot map, no locked-slot affordance,
   no way to see how many weapons you *could* carry.
   **Wanted (Minecraft layout):** player figure centre; LEFT column top→
   bottom **charm/potion · armour · boots**; RIGHT column **shield ·
   weapon 1 · weapon 2 · weapon 3**. Every slot always drawn: locked =
   dark-grey outline + lock, hover explains the unlock (school purchase,
   level); empty-available = dotted, empty; filled = icon. Click a slot
   item → "Move to pack" (refused with reason when the pack is full);
   click a pack item → "Wear"/"Hold"/"Set" into its slot.
3. **The charm/potion slot** is new: holds ONE luck charm (passive: more
   loot) OR one potion (defence / healing, used during a fight). Sold at
   the School, level 9.
4. **"Main weapon bonus"** — roy wants it gone if it exists. See §Answer.

## Answer — is there a main-weapon attack bonus to remove?
No separate bonus exists. `state.atk(p) = round(3·1.3^(level−1)) +
gear_bonus("weapon")` (state.py:590, economy.py:154). `gear_bonus`
is the bonus of the ONE weapon that swings: choosing `attack_<slug>`
runs `_promote_held` (combat.py:1117) which sets `gear["weapon"]=slug`
before the roll, so a bow swing uses the bow's bonus, a sword swing the
sword's. Nothing is added for "being the main weapon" and held side-
arms add nothing while resting. Two things ARE off and get fixed here:
- **Hone follows the slot, not the item.** `p["hone"]["weapon"]` is
  keyed by slot; `_promote_held` does not touch it, so a sword honed 3
  steps lends its 3 steps to the bow the moment the bow leads. That is
  a free, unearned bonus — the only "crap" in this area. Fix: hone
  rides the weapon slug (`p["hone"]["weapon:<slug>"]`) for weapons;
  shield/armour stay slot-keyed (one piece per slot).
- **The lead reorders the slots.** `held[0]` must equal
  `gear["weapon"]` (state.py:509), so swinging weapon 3 moves it to
  slot 1. With fixed visual slots that is confusing. Fix: `held` order
  is the slot order; `gear["weapon"]` is a pointer into it (the
  "leading" mark), no reordering.
Empty weapon slot still fights with the gate shiv (004 §A.1) — that
stays.

## Root cause / why not a patch
- Effects were attached to the pack because there was no other place;
  the pack pre-dates slots (045/048/064).
- `_inventory_html` derives layout from what the player owns, not from
  a fixed slot map, so unlocked-but-empty and locked slots are
  indistinguishable and un-explained.
- Hone is per slot because weapons were once one per player.

## Inventory of everything that has an effect from the pack / hand today
(each row: today → ruling under the new law)

| # | item / mechanism | where | today | ruling |
|---|---|---|---|---|
| 1 | shoes, armour, shield, weapon | state.py:574-614, economy.py:602 | worn-only already | unchanged; add level gate on `wear_*` (missing — only purchase checks) |
| 2 | held side-arms | combat.py:675, :1953 | option rows only, no stat | unchanged; slots 2/3 stay School purchases (`buy_carry2/3`) |
| 3 | fight relics: net, hook, strip potion, curse scroll, polymorph, flare, severing word | combat.py:2043-2198 | fired from pack, cost a round | **charm slot only** — the row appears only for the item in the slot |
| 4 | golden apple, veil draught (life group) | combat.py:2129-2162 | pack, one life item per fight | **charm slot only** (the slot already enforces "one") |
| 5 | trollblood tonic (mid-fight heal) | combat.py:765, :2200 | pack | **charm slot only** — this is the "healing potion" |
| 6 | stone of undying, reincarnation spell (auto on death) | combat.py:1756-1799 | auto from pack, spares leak | **charm slot only**; a stack in the pack does nothing; leak rule dies |
| 7 | quiver arrows (nock) | combat.py:2016, :1219 | nock from pack, free | **bind to the bow**: `nock_*` moves the stack from pack onto the held bow (`p["quiver"][slug]`); allowed out of fight or mid-fight at one round; shots draw from the bow's quiver |
| 8 | weapon oil | combat.py:2026, :1156 | pack use → `p["oil"]` counter | **apply out of fight only** to a weapon in a slot; counter rides the slug (`p["oil"][slug]`); mid-fight `use_oil` row removed |
| 9 | luck charm | core.py:2063 (drunk on purchase), :353 (pack use), combat.py:1422 (gold jitter), core.py:659 (presents) | day flag, no drop-table effect | becomes a **worn charm**: passive while in the charm slot; +`CHARM_LOOT_PCT` weight on the two drop tables (combat.py:1505/1531) AND `_drop_ranges`/`_warden_drop_ranges` mirrored; keeps gold-jitter and present weighting; wears 1/victory from a pool; `luck_day` flag and instant-drink removed |
| 10 | medgel / trauma kit at the fire | core.py:3130 | pack use out of combat | keep (out-of-fight consumption is not "an effect on the player" — roy to veto if he wants these slot-only too) |
| 11 | energy cell | core.py:2063 | instant on purchase | keep (never enters pack) |
| 12 | repair token, job tokens, old packs (064) | core.py, notices.py | inert | unchanged |
| 13 | durability_pack | state.py:52 | pack weapons keep their wear pool | unchanged |
| 14 | relic shops line-locked on held lines; death loses 20% per paid weapon | economy.py:2447, combat.py:1839 | on `held` | unchanged (held is a slot) |
| 15 | gear_band (worn paid slots) | state.py:102 | weapon/shield/armor/shoes | charm slot NOT counted |
| 16 | arena HUD (067) | arena.py payload | `me.weapons[]`, `me.shield/armor` | add `charm`, per-weapon ATK, quiver per bow |
| 17 | sheet.py export | sheet.py:45 | `holding` | add `charm` |
| 18 | weekly strongbox / alpha / warden pay a luck charm into the pack | weekly.py:120, combat.py:1505/1531 | pack | unchanged (it lands in the pack; wear it to use it) |
| 19 | dossier drop odds | combat.py:461-505 | static tables | must show the charm-adjusted odds when a charm is worn |

## Design
### Player doc
- `p["gear"]` gains `"charm": None`. `p["charm_slot"]: bool` (unlocked at
  School). `p["held"]` = slot order (len ≤ `p["slots"]`), `gear["weapon"]`
  ∈ held marks the lead; `ensure_current` repairs: if lead not in held →
  lead = held[0]; no reordering. `p["hone"]` keys: `shield`, `armor`,
  `weapon:<slug>`; migration v11 moves `hone["weapon"]` →
  `hone["weapon:"+gear["weapon"]]`. `p["quiver"]: {slug: count}` (bound
  to the held archer weapon), `p["oil"]: {slug: strikes}` (v11 migrates
  the int onto the lead slug). `p["charm_dur"]: int` pool for a worn charm.
- **Slot map** (single source, `economy.SLOTS`):
  `charm` (left 1, lock: School "Charm pouch", level 9), `armor` (left 2),
  `shoes` (left 3), `shield` (right 1), `weapon` (right 2, always open),
  `weapon2` (right 3, lock: School carry 2), `weapon3` (right 4, lock:
  School carry 3, level 8).
- **Charm slot accepts:** `luck_charm`, `APOTHECARY` heals (`medgel`,
  `trauma_kit`, `trollblood_tonic`), all `RELICS` except quiver arrows
  and `weapon_oil`. Exactly one stack of one slug (count 1 — potions are
  set one at a time; the pack keeps the rest). Swapping the charm item
  mid-fight: refused ("set it before the fight"). Wearing it needs the
  slot unlocked; nothing else (the level gate is on the purchase).
- **School:** `buy_charm_slot` — `CHARM_SLOT_LEVEL = 9`,
  `CHARM_SLOT_XP = 400`, `CHARM_SLOT_GOLD_ANCHOR = 250` (× pillar of the
  frontier, like carry 3). Row shown locked with "🔒 level 9" below.
- **Loot:** `CHARM_LOOT_PCT = 25` — a worn charm adds it to the *rare*
  entry weight of both drop tables (luck_charm 10→35 alpha, 12→37
  warden). First-cut number.
- **Fight options** come from the slots only: `_relic_options(p)` reads
  `gear["charm"]` + the lead weapon's quiver; `_ROUND_ACTIONS` unchanged.
- **Move to pack:** `unequip_<slot>` — refused when
  `not pack_can_take(p, slug)`: "Pack full (n/n). Sell or drop something,
  or buy a bigger pack at the forge." Refused mid-fight for every slot.
  Weapon slot 1 with only one weapon: refuse ("you keep one blade in
  hand" — the shiv fallback is engine law, not a UX path).
- **Wear from pack:** `wear_<slug>` picks the target slot by kind; a
  weapon goes to the first empty weapon slot, else replaces the lead
  (old lead → pack, capacity checked first); adds the missing level gate
  (`rung_player_level_req`, shoe `level`).

### UI (render.py `_profile_html` / `_inventory_html`, CSS in `SCENE_CSS`)
```
[charm ]            [shield]
[armour]  portrait  [weap 1]
[boots ]            [weap 2]
                    [weap 3]
--------------- pack n/cap ---------------
[..][..][..][..][..][..]
```
- `.gearmap{display:grid;grid-template-columns:auto 1fr auto}`; portrait
  scales to the taller column (4 × 60px + gaps ≈ 260px; portrait
  min-height already 200px). Mobile (≤520px): columns stay, slots 48px.
- Slot states: `.slot.locked` (dark grey `#555` outline, lock glyph,
  `data-tiph` = unlock text from `economy.SLOTS[k].lock_text(p)`),
  `.slot.empty` (dotted — today's dashed becomes dotted), filled (icon +
  durability hairline as today). Charm slot with a potion shows `×1`.
- Click filled slot → popover: "Move to pack" (+ per-slot verbs already
  present: hone at forge, etc.). Click pack cell → existing `acts` with
  `wear_*` relabelled per slot ("Wear", "Hold", "Set in pouch"); greyed
  with reason when slot locked / level short / kind not wearable.
- Arena HUD: charm icon under the player HP; each weapon tile shows its
  own ATK (`base + that weapon's bonus`), not the lead's.

## Phases
1. **Slot map + doc migration (engine only)** — `economy.SLOTS`,
   `gear.charm`, `charm_slot`, hone-per-weapon, held-order/lead pointer,
   `quiver`/`oil` per slug, v11 `ensure_current`. `phase-1/PLAN.md`.
2. **Effects move to slots** — `_relic_options` from charm slot + bow
   quiver; death items from slot; oil apply-out-of-fight; luck charm as
   worn passive incl. drop tables + dossier ranges; remove instant-drink
   and `luck_day`. `phase-2/PLAN.md`.
3. **School: charm pouch** — `buy_charm_slot`, level 9, refusals, tips.
   `phase-3/PLAN.md`.
4. **Actions: wear / move-to-pack** — `unequip_<slot>`, pack-full
   refusal text, `wear_*` slot targeting + level gate, mid-fight
   refusals. `phase-4/PLAN.md`.
5. **UI: the gear map** — render + CSS + tips + arena HUD additions.
   `phase-5/PLAN.md`.
6. **Tests + dojo + release** — pytest, `luna/dojo/tests/gear-slots/`,
   bump 0.92.0, vendor, commit. Not deployed unless roy says so.

## Verification (whole plan)
- Pytest: pack items grant nothing — a doc with every relic + luck charm
  + arrows in `inventory` and empty slots produces the same
  `fight_scene` options, drop odds, ATK/DEF/SPD, and death outcome as an
  empty pack; hone: honed sword, bow leads → bow bonus unhoned; slot
  order stable across `attack_<slug>`; charm slot: locked <9 / refused
  purchase / unlocked → wear → tonic row appears → drink → slot empties;
  luck charm worn → drop tables and `_drop_ranges` agree; `unequip_*`
  refuses when pack full with the message; v11 migration round-trip on
  0.90.0 docs; sheet export carries `charm`.
- Dojo: `luna/dojo/tests/gear-slots/scenario.md` — profile shows 7
  slots (3 left, 4 right), locked ones grey with lock + hover text,
  empty dotted; wear boots from pack → left 3 fills, SPD pips rise;
  move armour to pack with pack full → red refusal line with count;
  School <9 → charm row locked; level 9 → buy → slot dotted; set tonic
  → floor fight shows "Drink tonic" tile; tonic in PACK only → no tile;
  arena (067) HUD shows charm and per-weapon ATK; mobile 390px layout.

## Rollback
One commit per phase, `git revert` in reverse order. v11 migration is
additive (new keys; `hone["weapon"]` and int `oil` are kept as legacy
keys until phase 6 confirms) so a reverted engine reads the doc.

## Open decisions for roy (defaults chosen; say the word to change)
- Row 10: medgel/trauma kit usable from the pack at the fire — kept.
- Charm slot cost/level numbers, `CHARM_LOOT_PCT`, charm wear pool.
- Death items (stone/reincarnation) become one-per-slot — the spare
  leak rule dies with them.
- Arrows bind to the bow (row 7) rather than the charm slot.

## Execution status (whole plan)
Phases 1–6 done: 885d519 (v11 doc), e15de03 (pack grants nothing),
46a7a94 (weapon slots + hone per slug), b7831fb/989ffd6 (charm pouch +
gear map, arena pouch/per-weapon ATK), 1828648 (0.93.0). 36 tests in
test_069_slots_not_pack.py; dojo 0038 42/42. Vendored into worldd, not
deployed.
