# 028 — Nothing twice

One complaint, one diagnosis: **the game says everything in sentences, and says most of it twice.** The forge lists twenty items as full prose lines *and* as option rows. Combat buries every number mid-sentence. The death card is a twelve-line paragraph wall. Meanwhile the card grammar already owns rows, chips, icons, meters, tallies, folds and instant tips — and the body text keeps narrating the same facts on top of them. This plan is presentation only: no combat math, no pools, no prices move (the 020/027 rule holds).

## The complaint (verbatim, 2026-07-31)

> the game has too much text to read and it's mostly unreadable and not clear — go over all of it, make a plan to reduce text, make more ui surfaces that are clearer like the pack itself and icons in the options like in the forge.

Two asks in there:

1. **Less text** — the walls go away.
2. **More surfaces** — the pack strip and the iconed forge rows are the model; more of the game should look like that.

## The audit (read first, believe it)

Ranked by pain, from a full read of every scene builder:

1. **Forge / Arcanum / Medlab racks** — `_forge_scene` (`engine/core.py:1009-1101`), `_rack` (`core.py:886-939`), `_relic_rows` (`core.py:953-974`). Every rack item renders as a full-sentence body line (`f"{g.name}{flavor} — {_stat(g)}"`, core.py:918) **and again** as an option row. ~250–400 words per visit, the screenshot that triggered this plan.
2. **Combat round notes** — resolvers in `engine/combat.py:1205-1691`, `_strike_text` :592-616, `_counter_text` :556-589. Damage, mitigation, chase odds all mid-sentence, 40–80 words per round, dozens of rounds per session. The renderer already regex-extracts these numbers just to color them (`_HIT_HP`/`_HIT_DMG`, `render.py:229-241`) — proof they belong in fields, not prose.
3. **Death** — `_death` (`combat.py:1003-1142`): ~12 lines mixing gold %, gear breakage, mercy rules and flavor.
4. **Warden keep** — `warden_scene` (`engine/social.py:929-1017`): charge-economics paragraph (:993-997), heal-rules paragraph (:965-973) as walls.
5. **Vault** — `_vault_scene` (`core.py:1694-1757`): interest stubs and the 3-slot strongbox pitch (:1726-1737) as prose.
6. **Lodge** — `_lodge_scene` (`core.py:1489-1563`): night-slot pitch + fire prose + fire log + stew, every visit.
7. **Guildhall member panel** — `social.py:326-387`: store, dues, week, 8 member rows, armory — pure data as sentences.
8. **Morning Crier** — `_news_scene` (`core.py:292-350`) + `_news_advice` (:396-419): daily advice that repeats what tips already say.
9. **Pawn shop** — `_pawn_scene` (`core.py:1825-1883`): sell rows duplicated in body and options.
10. **Transaction notes** — `_gear_purchase` (`core.py:1190-1264`) and refusals throughout: 2–4 sentences to confirm one purchase.

The structural fact that makes this cheap: **`engine/tips.py` is already a complete parallel information layer.** Every option has a 2–5 sentence tooltip with the numbers (`_buy_tip`, tips.py:293-330, duplicates the whole shop line). Most body-line information is the redundant copy. We are not writing a new layer — we are deleting the duplicate one.

## The laws

1. **Nothing twice.** A fact lives in exactly one register — row, chip, icon, meter, tally, fold, or tip — never also in a sentence. If a body line restates an option row, the body line dies.
2. **Options are the list.** `body_lines` never enumerates merchandise, sell offers, members, or anything else that is clickable below. The rack *is* the option list (extends the 019 law: "every actionable or aspirational state is a proper option row").
3. **Numbers live in chrome.** Stats, prices, damage, percentages go in hints, chips and meters — set in tabular figures, scannable in a column. Sentences carry only flavor.
4. **Flavor is short and stays.** Item names, one-clause flavor, shard whispers, YAML floor prose, refusal one-liners survive untouched. Personality was never the problem; double-booked information was.
5. **The agent loses nothing.** `to_text()` prints option labels + hints, so every load-bearing number moved into a hint stays on the text surface word for word. Information may move registers; it may not move behind hover-only tips *unless* it also survives in a hint or line.
6. **Body budget: 6.** Outside combat, a scene body is at most 6 lines. Anything longer folds behind `▣ ` (the fold grammar at `render.py:952-962` exists everywhere and is used almost nowhere — that changes).

## Phase 1 — the racks stop talking

**What's wrong.** `_rack` (core.py:886-939) emits one sentence per item into `body_lines`, then `_forge_scene` adds the same items as options. The Honing bench line (core.py:1088), the off-class ×3 lecture (core.py:1034-35), the "rung you're saving for" lines (core.py:939) are body prose whose content already exists in tips (tips.py:293-330).

**What ships.**
- `_rack` and `_relic_rows` stop writing body lines entirely. Merchandise renders **only** as option rows: `[n]` key chip · 32×32 icon · name · right-aligned hint carrying stat + price (`+23 ATK · ◈ 900`). Locked rungs stay locked rows (019 law) with hint `next rung · +23`.
- `_opt_gear_icon` (`render.py:526-545`) currently resolves icons only for `buy_`/`wear_` ids over FORGE/RELICS slugs. It extends to **every shop register**: Medlab consumables (all 6 icons already exist in `icons.py` and today render only once the item is in your pack — a plain gap), Arcanum relics, pawn `sell_` rows, and combat-relic options. One resolver, every row.
- Style tinting moves onto shop rows: keen = orange ink, warded = aether ink on the icon — the same tint law the pack strip already obeys (render.py:421). "Ember-tempered — keener than it should be, and it knows it" becomes an orange icon plus a tip; the sentence leaves the card.
- The Boarspine off-class lecture, honing-bench pitch, and milestone warnings become tips on their rows (they are already there nearly verbatim); the body keeps at most one flavor line per shop ("Blades, bows, plate and boots.").
- Forge body after this phase: headline, one flavor line, the relic fold if stocked. That's it. From ~25 body lines to ≤3.

## Phase 2 — combat counts in chrome

**What's wrong.** Round notes concatenate 3–6 clauses with the numbers buried inside; the renderer parses them back out with regexes to color them. Victory stacks kill line + XP + gold + assist + spoils + charm + a Guildhall pitch that `notices.py:57-69` already delivers as a notice. Death is a 12-line wall.

**What ships.**
- Round results split into **one flavor clause + structured hit lines**. The hit lines use the existing `+`/`−` convention (render.py:963-968): `− 7 HP · its plate turned part of it` / `+ 11 dealt · deep`. `_strike_text`/`_counter_text` shrink to the flavor clause; the numbers ride the colored lines and the enemy HP header (`_enemy_head_html`, render.py:463-480) tweens via the 027 `data-m` count-up.
- Victory: kill line stays, payouts become the drawn `tally` (already implemented, render.py:253-275) + `+ XP` lines. `_train_nudge` (`combat.py:749-756`) is deleted — it duplicates the notice board.
- Death becomes a **ledger**: one flavor sentence, then itemized `−` lines (gold lost, each broken piece, mercy applied), each ≤ 8 words. The mercy/reincarnation *rules* move to a `▣ what death costs` fold, rendered only the first two deaths.
- `_driven_back` (`combat.py:1145-1176`) gets the same ledger treatment.

## Phase 3 — civic rooms read as ledgers

**What's wrong.** Vault, Lodge, Warden keep, Guildhall and the Crier are data rooms rendered as essays.

**What ships.**
- **Vault:** balance and interest stubs as `+`/`−` lines with coin marks — this also pays down MUST_BE_DONE_LATER §7 ("Coins drawn as marks", :179-184): the interest collect and strongbox draw the tally instead of saying a number. The strongbox pitch (core.py:1726-1737) collapses to a locked option row with hint; the mechanics go to its tip.
- **Lodge:** the night-slot pitch is already a notice (notices.py:126-128 — and it's 3 sentences; it becomes 1). The card keeps fire flavor (FIRE_WORDS stays) + option rows; the last-5-fires log folds behind `▣ the fire remembers`.
- **Warden keep:** the charge bar and fights-left lines stay (they're already good); the charge-economics and heal-rules paragraphs (social.py:993-997, :965-973) move to an `[i]` details block — the dossier pattern (`render.py:483-523`) generalized to a room.
- **Guildhall:** member pips, store, dues, week become the pane's `.kv`/chip-row idiom inside the card — label · value columns, not sentences. Armory rows get icons (same resolver as Phase 1).
- **Morning Crier:** happenings stay one line per event (that rule already exists, `chat_components.md:44`); `_news_advice` (core.py:396-419) is deleted — every piece of it exists as a tip on the option it advises.
- **Pawn shop:** body duplicate rows die; `sell_` options get icons and price hints.
- **Ascent Stone:** `climb_ahead_lines(limit=14)` folds everything past the next 5 rungs behind `▣ the climb ahead`.

## Phase 4 — two new surfaces

**What's wrong.** The pack has no room of its own — the strip + popup is the whole inventory UI (019 noted per-copy wear needs one). The character sheet (`sheet.py:9-53`) returns JSON for the agent to narrate — zero visual surface; it's the only screen in the game with no card.

**What ships.**
- **The pack card.** A `pack` option (town + camp) opens a real scene: one row per carried thing — 32×32 icon, name, ×count, durability hairline, equipped state in bright ink — and each row's actions as ordinary options (`wear_`, `quaff_`, `drop_`), reusing `pack_actions` (core.py:107-161). The popup stays for quick taps; the card is where you *read* your pack. No new engine verbs (027 rule: the engine gains no verbs it did not already validate).
- **The sheet card.** `ascent_character` keeps returning the dict for the agent, and additionally renders a scene: meters rail, gear rows with icons and hone marks, trait chips (`t_*` icons exist), class/race/faction line, era progress. One card, zero paragraphs.
- **Icons for doors and deeds.** ~8 new 16×16 grids in `icons.py` (`_GRIDS` append, zero build step): door, bed, letter, contract, flame, boar/beast, anvil-spark, ladder-rung. Town/lodge/board option rows get them the way forge rows do — this is the "icons in the options" ask generalized past gear. Every glyph obeys 018 law: single-colour mask, shading is dither, a detail can only be a hole.

## Phase 5 — the budget is a test

**What's wrong.** Nothing enforces any of this; the next feature will re-grow the prose (022's presence lines, 026's gate warnings each added body lines).

**What ships.**
- `Scene` gets no new fields. The budget is enforced by test, not schema: the scripted full walk (the 014 coverage-guard pattern) asserts, for every rendered scene: **(a)** body ≤ 6 lines outside combat unless folded, **(b)** no body line contains the label of any option on the same scene (the nothing-twice check, mechanical), **(c)** every shop/pawn/armory option resolves an icon, **(d)** every option still has a tip.
- `to_text()` parity assertion: for each scene, every `◈` price and every stat that appears in the HTML also appears in the text surface (hints ride `to_text` already, scene.py:106-149 — the test pins it).
- One doc paragraph in `design/chat_components.md` recording laws 1–6, so 029+ inherits them.

## Decisions taken (change here, not in code)

- **Tips are not a dumping ground.** A number may move to a tip only if it also survives in a hint or line (law 5). Hover-only is for *why*, never for *how much*.
- **Combat narration stays prose-first.** One flavor clause per round is the voice of the game; we move the arithmetic out, not the drama.
- **The intro movie is untouched.** It's 9 beats of pure flavor watched once; cutting it saves nothing nightly. (A skip affordance is a different plan.)
- **No verbosity config flag.** One reading experience, tuned; not two half-tuned ones.

## What was rejected first

- **A persistent HUD panel under the pane card** (the GAME tab has free vertical space) — rejected: the card is the surface; a second surface below it splits attention and breaks the chat-card parity that makes the pane pixel-identical.
- **Tables in body_lines** — rejected: the option list *is* the table (019). Adding a second tabular register invites the duplication back.
- **Shrinking `tips.py`** — rejected: tips are hover-side, cost nothing on the card, and are the safety net for law 5.

## Tests

`tests/test_028_nothing_twice.py`:
- forge/arcanum/medlab/pawn scenes: zero merchandise body lines; every buy/sell/relic option has an icon and a hint containing stat and/or `◈` price.
- medlab rows resolve the six apothecary icons (the pre-028 gap, pinned).
- combat round: note is ≤ 1 sentence; damage numbers appear as `+`/`−` lines; enemy header carries the HP delta.
- death scene: ≤ 1 flavor line + ledger lines; rules fold present on death 1–2, absent on death 3.
- pack card: one row per pack entry, actions match `pack_actions`, popup unchanged.
- sheet card renders for a live player; dict payload unchanged byte-for-byte.
- full-walk budget guard: assertions (a)–(d) from Phase 5 over the scripted walk.
- `to_text` parity sweep over the walk.

## Ship

Standard train: full plugin suite → vendor sync (`worldd/tools/vendor_game.sh`) → worldd suite → dojo pass in a real browser with a live walkthrough written into this folder ("played, not just tested") → bump minor (next free at publish, likely **0.34.0**) → publish, deploy, submodule pointer bump in the parent repo. Straight to `main` per `no-branches.mdc`. Exit: `execution_summary.md` written here, including deviations.

Wire compatibility: no `Scene`/`Option` schema change, no new engine verbs, no worldd change — a 0.33 pane rendering a 0.34 scene sees fewer body lines and more hints, nothing it can't draw.

## Out of scope

- Per-copy wear migration (019 deferral — the pack card *displays* durability; it does not change its shape).
- Combat consumable support for net/whetstone/smoke pot (MUST_BE_DONE_LATER §5).
- Intro-movie skip.
- The walkable 3D hub (`base-mock/`) — different plan, different year.
- Any price, pool, or combat-math change.
