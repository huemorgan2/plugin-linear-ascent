# 017 phase 011 — the off-class amnesty (doc v5)

## The bug, as a player met it

A level-3 elf **archer** stood at the Forge and read:

```
[4]  Pigsticker            ◈ 750 · off-class
[5]  Repair Pigsticker     ◈ 1 + 2 XP
PACK  Pigsticker · Scrapwood Buckler · Luck charm ×2
```

The shop was calling their own equipped weapon "not your class" while
charging them to repair it. They reasonably concluded the game had lost
track of what they were.

It hadn't. `clazz` read `archer` the whole time. The weapon was wrong.

## Root cause

Before 017, the Forge sold one weapon ladder and weapons had no class.
017 §4 split that ladder into three lines and stamped every existing
Forge weapon `line="warrior"` — Pigsticker, Wolfbite, Emberfang, all of
them. Nothing re-examined the weapons players were already holding.

Doc v2 (`ensure_current`) handled only the climbers still carrying the
free generic shiv. Its guard was explicit:

```python
if (p.get("stage") == "playing" and clazz in economy.CLASS_STARTERS
        and p["gear"].get("weapon") == economy.STARTER_WEAPON.slug):
```

…and a test locked the omission in as intended behavior:

```python
def test_v1_doc_with_bought_weapon_is_untouched():
    p["gear"]["weapon"] = "pigsticker"       # earned gear stays
```

"Earned gear stays" was the right instinct aimed at the wrong risk. It
was guarding against *demoting* a paid weapon to the free starter. What
it actually did was strand every non-warrior who had ever bought one:

- ×0.5 damage and a 25% miss that eats the round
- the weapon can never be honed
- ×3 price to replace it
- and no class basic weapon either, since v2 only issued one to shiv-holders

A retroactive penalty for a purchase that was correct when it was made.

Two smaller gaps from the same guard:

- `stage == "playing"` skipped anyone who picked a class and walked away
  mid-creation — they kept the generic shiv permanently.
- A weapon sitting in the *pack* was never considered at all.

## The fix — doc v5

For any doc with a class, `ensure_current` now:

1. Swaps a generic shiv (or another class's starter) for the holder's own
   class basic weapon — silently, at any stage. Closes the v2 stage gap.
2. Re-forges any off-class **bought** weapon, worn or packed, into the
   same rung of the holder's own line via `economy.line_twin`.
3. Sends one letter naming each trade, only to docs already `playing`.

The three lines mirror each other rung for rung — same bonus, same price
— so the trade is exact. Durability lives on the slot and honing lives on
the slot, so both carry across untouched. Pack items merge counts and
keep the better pool.

This is a **one-time amnesty, not a rule change.** Buying off-class on
purpose still carries the full 017 §4 penalty, and the off-class rack
still stands. Only gear bought before the lines existed is forgiven.

## Verification

| Gate | Result |
|---|---|
| `tests/test_017_offclass_migration.py` | 20 new tests |
| Full plugin suite | 432 passed |
| `rehearse.py` over a dump of all 8 live docs | 8 migrated, 0 left off-class, all idempotent |
| `worldd_check.py` — real DB, real `game.run_scene` | 8 docs at v5 on disk, none off-class |
| Forge scene re-render for the reporting player | `✓ Ashwood Bow — worn`, `Repair Ashwood Bow` |

`test_v1_doc_with_bought_weapon_is_untouched` was rewritten to assert its
real intent — a paid weapon is never demoted to the free starter — rather
than the literal slug it happened to produce.

## Production rollout

Shipped as plugin v0.27.3, vendored to worldd in `85523dc`. Render's
auto-deploy did not fire on the push and the deploy had to be triggered
by hand — worth checking after any future push.

The reporting player healed on their own next turn, before the write-back
ran: `pigsticker → ashwood_bow`, doc v4 → v5. `writeback.py --apply` then
brought the remaining seven forward.

Final audit — all 8 live documents:

| player | class | weapon | v |
|---|---|---|---|
| MASTER-CHIEF | elf archer | Ashwood Bow | 5 |
| huemorgan | elf archer | Basic Bow | 5 |
| Sir Akselrod | human sorcerer | Worn Wooden Staff | 5 |
| Torvald ×2, Roydric, Chipprod, (unnamed dwarf) | warrior | Rusted Sword | 5 |

Every stored document was then re-derived from the pre-migration backup
and compared field by field: 0 unexpected mismatches. The only deltas on
MASTER-CHIEF are `gold`, `xp`, `floor`, `location` and `durability` —
they moved because the player kept playing.

## Scripts

All three live in this folder.

```bash
psql "$PROD_DB" -At -c "SELECT json_build_object('tenant',tenant,
    'player',player,'doc',doc)::text FROM ascent_players" > docs.jsonl

python rehearse.py docs.jsonl                        # dry run
DATABASE_URL=... python worldd_check.py docs.jsonl   # real worldd turn
PROD_DB=... python writeback.py [--apply]            # heal live docs now
```

`writeback.py` is only an accelerator — `ensure_current` heals every
document on load anyway. It guards each UPDATE on the document it read,
so a turn played mid-run is never clobbered.

> The first cut of `writeback.py` built SQL by string interpolation and
> misparsed `RETURNING`, so it reported "skipped" for rows it had in fact
> written. It was rewritten on asyncpg with bound parameters. If you write
> another one-off against production: **bind your parameters**, and verify
> against the data rather than trusting the script's own summary.
