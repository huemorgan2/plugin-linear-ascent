# 034 — a Warden dies once

Three corrections from play, unrelated in code and identical in spirit:
**the game should charge what it says it charges.** A shield that stops a
blow should spend itself on it. A bar that is full should not keep filling.
A Warden that is dead should stay dead.

---

## 1. The shield spends itself on what it stops

**Today.** Every landed blow wears the shield exactly **one use**, no
matter what it turned:

```614:617:plugin-linear-ascent/plugin_linear_ascent/engine/combat.py
    p["hp"] -= dmg
    broke = [note for s in ("shield", "armor") if (note := _wear(p, s))]
    return {"dmg": dmg, "raw": raw, "blocked": raw - dmg, "broke": broke,
            "apple": soaked}
```

A tier-1 shield holds 1300 uses (`durability_pool`), so it survives ~1300
incoming blows — roughly 216 fights, a week of heavy play. The card already
narrates the mitigation by name (`your Scrapwood Buckler blunted 9 of it`)
and then charges the same single point whether it blunted 1 or 90. The
number the player reads and the number the game bills are unrelated.

Worse, **Shield Wall costs the shield nothing at all** — it never reaches
`_monster_hit`, so the one move that is *entirely* the shield turns the
whole blow for free (`combat.py:1678-1700`).

**The rule.** *A shield is spent on damage, not on rounds.* Wear scales
with the share of the blow the shield turned, priced against the shield's
own rating:

```
shield_share  = gear_bonus(shield) / DEF          # how much of the guard is shield
blocked_shield = blocked * shield_share
wear          = max(1, round(SHIELD_WEAR_RATE * blocked_shield
                             / max(1, gear_bonus(shield) / 2)))
```

which reduces to **`wear ≈ SHIELD_WEAR_RATE × blocked / DEF`**. The
`gear_bonus` terms cancel, and that cancellation is the point: the formula
is *tier-stable*. A blow fully absorbed costs a full rate; a blow that
chips straight through costs the floor of 1; and a tier-10 shield facing
tier-10 blows wears at the same pace as tier-1 against tier-1, instead of
4× faster (which naive proportional wear would do, because `blocked` grows
with DEF while the pool grows only 25% a tier).

`SHIELD_WEAR_RATE = 4` — an average fully-met blow costs ~4 uses instead of
1, so a fresh shield lasts ~325 blows (~54 fights) rather than ~1300. Four
times faster, and the repair bench becomes a real gold sink.

**Shield Wall pays too.** It rolls the blow it turned (without applying it
to HP) and wears the shield on the whole thing — the most expensive round
in the game for the shield, which is exactly what "nothing gets through"
should cost.

**Armor stays at one use per hit.** The user asked about shields, and the
asymmetry is honest: armor is what you wear, a shield is what you put in
the way. Changing both would multiply the whole repair economy by four in
one step.

**Touches.** `economy.SHIELD_WEAR_RATE` (new), `combat._monster_hit`
(:615), `combat.shield_wall` handler (:1678), `state.wear_gear` already
takes `n`. Nothing else — pools, prices and `repair_price` are untouched,
so the migration is nil.

---

## 2. The bar is the bar

**Today.** The engine already caps XP on gain (`state.gain_xp` /
`xp_room`), and `ensure_current` clamps legacy saves. Two holes remain:

1. **`guild_train` subtracts instead of resetting** —
   `p["xp"] -= need` (`engine/social.py:614`). Its own docstring says "the
   bar is hard (no overflow to carry)", and then it carries the overflow.
2. **worldd writes XP raw, bypassing the cap entirely** — four sites do
   `doc["xp"] += …` with no `gain_xp`:
   - `_warden_fall` share (`worldd/app/social.py:1227`)
   - milestone boss victory (`_resolve_boss`)
   - PvP bounty
   - flare answer (`FLARE_ANSWER_AETHER`)

   These are the big ones. The floor-10 milestone pays **1,500 XP** into a
   level-10 bar that holds **758**. The overflow lands, the player trains,
   and `-= need` carries 742 XP straight into level 11's bar — a free
   half-level the design never granted.

**The rule.** Below `LEVEL_CAP`, XP behaves exactly like energy: the bar
fills to full and stops, and buying the level empties it.

- `guild_train` sets `p["xp"] = 0`.
- Every worldd XP write routes through `pstate.gain_xp(doc, amount)`, which
  already returns what actually landed — so the **ledger row and the
  letter record the XP that landed, not the XP that was offered.** A
  receipt that claims 1,500 into a 758 bar is a lie the ledger would keep
  forever.
- The kill card / letter says so when a share is clipped: `+ 758 XP — your
  share of the kill (your bar took all it holds)`. 027's law: say it in
  the card.

**`LEVEL_CAP` (30) keeps its exception.** At the cap there is no bar — the
Guildhall refuses training and XP becomes pure currency for honing,
repair, spells and scans (`xp_room` returns `None` by design). "You can't
hold more than your bar" is meaningless without a bar, and capping there
would strand level-30 players from the sinks XP exists for. This is the
one place the new rule does not apply, and it is deliberate.

**Touches.** `engine/social.py:614`, four sites in `worldd/app/social.py`,
their ledger/letter lines. No migration: `ensure_current` already clamps
anyone currently over.

---

## 3. A Warden dies once

**Today.** A Warden at the live frontier is genuinely one shared monster
with one shared HP pool and one world-wide death — that part is right.
But *below* the frontier the keep re-arms as an **echo bout**: a full
Warden fight at half pay, repeatable forever.

```2547:2557:plugin-linear-ascent/plugin_linear_ascent/engine/core.py
        # below the frontier: the ECHO bout — a monument that still
        # bites, half pay, no world effect (022/001). Local dev play
        # (no world) keeps the real bout: a world of one.
        s = combat.start_encounter(p, fl, None, "warden")
        if w:
            p["encounter"]["echo"] = True
            s.support = ("An echo of a fallen Warden — half pay, no "
                         "world effect. The real one died long ago.")
```

The card literally says *"the real one died long ago"* and then lets you
fight it. It is a ghost with a loot table: `25×F` XP and `80×F` gold at
half rate, plus a 12% charm roll, repeatable at 3 ⚡ a swing. That is
strictly the best farm in the game on any cleared floor, and it makes the
world's biggest event — a Warden falling — mean nothing an hour later.

**The rule.** *The Warden of a floor below the frontier is dead.* The keep
is a monument, entering is free, and it tells you who killed it and when.

### The memorial

```
FLOOR 3 · THE KEEP
Warden Applewrath fell here
The doors stand open. Nothing has held them since.

Cast down on day 41 — four days ago — by MASTER-CHIEF.
The deepest cut was MASTER-CHIEF's: 559.
The lift above has run free ever since.

[1] Back to the camp
```

- New location `memorial`, reached by the existing `keep` option whenever
  `frontier > floor` (world) or `unlocked_floor > floor` (local dev). The
  gate-town row changes to `The keep where {warden} fell — a monument`
  with **no ⚡ hint**, so the cost is honest before the click.
- **Milestone floors get it too.** Today `keep` routes to `boss_keep`
  whenever `fl.milestone and w`, even long after the boss is resolved —
  so a cleared floor 10 still shows a quorum board. The frontier check
  runs first now.
- Reuses the `warden_fall` banner that 030 Phase 8 already shipped. No new
  art.

### The data: `fallen:{floor}` grows a date

`_warden_fall` writes the slayer roll as a bare JSON string, with no time
at all:

```1208:1211:worldd/app/social.py
    await conn.execute(
        "INSERT INTO ascent_world (key, value) VALUES ($1,$2::jsonb) "
        "ON CONFLICT (key) DO UPDATE SET value=$2::jsonb",
        f"fallen:{floor}", json.dumps(names))
```

It becomes `{"names", "day", "ts", "warden", "top", "top_dmg"}`. Readers
accept **both shapes** — a bare string is `{"names": value}` with no date,
and the memorial degrades to "in the early days of the climb" rather than
inventing one.

**Backfill, additive only.** Production is at frontier 5 with floors 1-4
already fallen (MASTER-CHIEF on 2-4, bob on 4) and no timestamps in
`fallen:*`. A migration fills `day`/`ts` from `ascent_happenings`
(`kind='boss'`, matching `floor`) and falls back to `ascent_stone.created_at`
for the `cast down by` line. It only **adds keys to existing rows** — no
`DROP`, no `DELETE`, no rewrite of the roll. Floors where neither source
survives keep their names and stay dateless.

### Balance fallout (all of it)

Removing the echo removes a faucet. Every consequence, and what happens
to it:

| Loses | Consequence | Answer |
|---|---|---|
| Echo XP/gold on cleared floors | The best sub-frontier farm goes | Intended. The wilds (1 ⚡) stay, and the live frontier Warden is where Warden money should come from. |
| 12% charm / trollblood roll per echo kill | Charm supply drops | Accept — charms were never meant to be farmable. |
| `weekly.note(p, "wardens")` on fight open | Strongbox activity counter loses a source | Now only the live frontier keep and milestone pledges count it. Correct: it was counting ghosts. |
| Contract board `note_warden` job | "Answer a keep's horn" becomes uncompletable for anyone who can't reach the frontier | **Must fix**: only offer the warden job when the player can actually enter the frontier floor (`unlocked_floor` and `floor_entry_player_level`). Otherwise the board hands out a job that cannot be done. |
| Re-fighting a Warden statline for practice | No boss-shaped fight below frontier | Accept. The frontier Warden is always available and is the real thing. |

`WARDEN_ECHO_MULT` and the `echo` encounter flag are deleted, along with
the half-pay branch in `_victory` (`combat.py:922-926`). A doc caught
mid-echo-fight when this ships resolves normally — the flag just stops
being read.

---

## Phases

1. **Shield wear** — `economy.SHIELD_WEAR_RATE`, `_monster_hit`,
   `shield_wall`. Unit tests: a fully-blocked blow wears ~4× a chipped
   one; a tier-1 and a tier-10 shield burn the same fraction of pool
   against their own band's blows; Shield Wall wears more than standing;
   a shield with no durability entry (free starter) still no-ops.
2. **The bar** — `guild_train` reset; four worldd sites through
   `gain_xp`; ledger and letters record what landed. Tests: train at
   exactly-full and at over-full leaves 0; a floor-10 milestone into a
   level-10 bar lands 758 and ledgers 758, not 1,500.
3. **The Warden dies once** — `fallen:{floor}` payload + additive
   backfill migration; `_memorial_scene`; `keep` dispatch; milestone
   check ordering; echo deletion; contract-board fix. Tests: below the
   frontier `keep` never starts an encounter and never spends ⚡; the
   memorial names slayer and day; a legacy bare-string `fallen:` row
   renders dateless without raising; milestone floor below frontier shows
   the memorial, not the quorum board.
4. **Ship** — full plugin + worldd suites, vendor sync into
   `worldd/vendor/plugin_linear_ascent`, version bump, publish, commit
   and push both repos. Per `.cursor/rules/no-branches.mdc` this goes
   straight to `main` in both — no branch.

## Decisions taken

- **Armor is not touched.** Only the shield changes units.
- **`LEVEL_CAP` keeps uncapped XP.** No bar, no cap; XP is currency there.
- **Ledger records what landed, never what was offered.** A clipped share
  is a smaller ledger row and a line in the card saying why.
- **The memorial is free to enter.** It is a story, not an encounter; the
  ⚡ hint leaves the row.
- **No new art.** `warden_fall` from 030 Phase 8 carries it.
- **Backfill is additive.** Existing `fallen:*` rows keep their names
  whatever else is missing.

## Risks

- **Shield wear is a 4× economy change.** Repair gold and bench XP demand
  rise for every shield-carrying build at once. Pin the pace with a test
  (`uses per average blow` at three tiers) so a later retune is a
  one-constant change.
- **Clipped XP shares change payouts people already expect.** The
  milestone bosses are the visible case; the letter must say the bar was
  full or it reads as theft.
- **Echo removal touches the contract board.** If the warden job keeps
  being offered to players below the frontier, the board becomes a dead
  end — this is the one place the change can silently break a daily loop.
- **`fallen:` shape change is read by the floor movie** (030 Phase 8's
  broken-keep beat). Both readers must accept the string form or old
  floors lose their slayer names.

Exit: all green, published, worldd synced, `execution_summary.md`.
