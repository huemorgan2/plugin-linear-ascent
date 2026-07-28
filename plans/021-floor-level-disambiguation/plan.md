# Plan 021 — Floor is not level: one named conversion, zero behaviour change

Goal: make it **impossible to pass a floor where a level is expected**, so the
level-cap work that follows cannot silently detune the tower. This plan changes
no numbers. Every warden, price and gate must come out byte-identical.

## 1. The question that started it

> "we called floor levels and may have had problems with that."

The tower's 100 levels are **floors**. The player's level is a **separate**
number with its own XP curve. Both are bare `int`, both are frequently in scope
together, and the design deliberately ties them: `_at_level_loadout` defines the
reference player as "**level = floor**, current tier set, honing 2 floors
behind. The reference all tuning points at." (`economy.py:352-355`)

That convention is fine as a tuning idea. The problem is that it leaked into the
code as an *untyped* identity.

## 2. What is actually wrong

Audited every call site of the level-typed functions — `player_atk`,
`player_def`, `player_max_hp`, `xp_need`, `levelup_gold`, `energy_cap`.

**No live bug.** Every runtime call passes `p["level"]` (`state.py:316-335`,
`combat.py:77-79,671-673`, `social.py:256-257,398-399`).

**One conflated call site**, and it is the load-bearing one:

| Fault | Where |
|---|---|
| `per_round = budget * player_max_hp(floor) / rounds` — `player_max_hp` is declared `def player_max_hp(level: int)` and is handed a **floor**. Warden ATK for the whole tower derives from this line. | `economy.py:386` in `warden_stats` |

**Three functions that return a floor and call it a level:**

| Function | Returns | Names it |
|---|---|---|
| `gear_level_req(tier)` → `band_start(tier)`; docstring: "Level required to buy tier-T gear: **the band's first floor**" | a floor | a level |
| `rung_level_req(g)` → `band_start(t) + 5` | a floor | a level |
| `floor_level_req(floor)` — "Level required to enter a floor" | a level | parses two ways |

(`economy.py:55-57`, `742-748`, `60-63`; `band_start` is documented as "First
floor of a gear band", `economy.py:801-803`.)

**And nothing can catch it.** There is no `pyproject.toml`, no mypy or pyright
config in the plugin. Floors and levels are both `int`, so a swapped argument
produces wrong numbers and no error.

## 3. Why this is urgent now, not later

The research note (`research/progression-more-ways-to-earn.md` §13) proposes
capping player level to move long-term progression onto gear. Run that against
`economy.py:386` with a cap of 30:

| Floor | `player_max_hp(floor)` used for tuning | Real capped player HP | Error |
|---|---|---|---|
| 30 | 400 | 400 | none |
| 80 | 1,000 | 400 | **2.5×** |
| 100 | 1,240 | 400 | **3.1×** |

Wardens above the cap would be tuned against a player who **cannot exist**, and
the symptom — "the tower is impossible past floor 50" — points nowhere near the
cause, which is one implicit argument. The same applies to `gear_level_req`:
capping at 30 makes tiers 4–10 unbuyable, because their gate is a *floor* number
being compared against a *level*.

So this refactor is the prerequisite. Doing it first means the cap lands as a
tuning exercise instead of an archaeology exercise.

## 4. The target

### 4.1 One named conversion, in one place

The floor→reference-level conversion becomes explicit and happens exactly once:

```python
def reference_level(floor: int) -> int:
    """The design's at-level player is level == floor (see
    _at_level_loadout). The ONLY place that identity is asserted."""
    return floor


def reference_player_hp(floor: int) -> int:
    """HP of the at-level player used to tune wardens. Deliberately
    NOT player_max_hp(floor) — that reads a floor as a level."""
    return player_max_hp(reference_level(floor))
```

`warden_stats` then calls `reference_player_hp(floor)`. When the level cap
lands, `reference_level` is the one function that changes — and it is named so
the change is obvious.

### 4.2 Renames that make the ambiguity unsayable

| From | To | Why |
|---|---|---|
| `gear_level_req(tier)` | `gear_player_level_req(tier)` | it returns a *player level*, derived from a band's first floor |
| `rung_level_req(g)` | `rung_player_level_req(g)` | same |
| `floor_level_req(floor)` | `floor_entry_player_level(floor)` | "the player level needed to enter this floor" — one reading only |

Each body gains one line stating which quantity it converts from and to. No
formula changes.

### 4.3 A vocabulary note in the module header

Four lines at the top of `economy.py` fixing the two words for good: *floor* =
the tower, 1–100, shared; *level* = the player, personal; and the one place
they are equated on purpose.

## 5. Tests

| Test | Asserts |
|---|---|
| `test_021_floor_is_not_level.py::test_warden_stats_unchanged` | `warden_stats(f)` for **every** floor 1–100 equals a hardcoded golden tuple captured before the refactor |
| `…::test_warden_tuning_reads_the_reference_player` | `warden_stats` derives from `reference_player_hp`, not `player_max_hp` — patch `reference_player_hp`, assert warden ATK moves; patch nothing else |
| `…::test_reference_level_is_the_only_floor_to_level_bridge` | grep-style guard: no module passes a variable named `floor`/`unlocked_floor` into `player_max_hp`, `player_atk`, `player_def`, `xp_need`, `levelup_gold`, `energy_cap` |
| `…::test_gate_and_gear_requirements_unchanged` | the three renamed functions return their pre-rename values for tiers 1–10, rungs, floors 1–100 |

The third one is the durable one: it is what stops the conflation coming back
the next time someone has a floor and a level in the same function.

## 6. Non-goals

- **No level cap.** That is its own plan; this only makes it safe.
- **No tuning changes.** Any diff in a warden, price or gate is a bug in this
  plan.
- **No fix for the shared lift.** `p["unlocked_floor"]` is raised only by your
  own warden kill (`combat.py:720-724`), while the Stone says "The lift opens
  for everyone when a Warden falls" (`core.py:1417`), worldd announces "floor
  N+1 is open for everyone" (`worldd/app/social.py:700`), and
  `floor_level_req`'s docstring describes a "world lift" that does not exist.
  That is a **design decision** — shared unlock or personal? — and it belongs in
  its own plan. Noted here so it is not lost.

## 7. Verification

1. Full plugin suite green, with **no test edited** except the four added above.
   Any existing test needing a change means behaviour moved.
2. `warden_stats` golden values identical for floors 1–100.
3. Re-vendor into worldd (`worldd/tools/vendor_game.sh`) and run the worldd
   suite — `worldd/app/social.py` imports `economy` for `MILESTONES`,
   `world_warden_hp` and `WARDEN_WORLD_REGEN_HOURLY`, so the vendored copy must
   not drift.
4. A browser pass per `.cursor/skills/agent-live-walkthrough`: reach the gate,
   read a floor's level requirement, buy a forge rung, fight a warden. The
   numbers on the cards should be the ones that were there yesterday.

Commit to `main` in both repos (`.cursor/rules/no-branches.mdc`).
