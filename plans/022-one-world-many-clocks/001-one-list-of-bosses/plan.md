# Phase 001 — One list of bosses

Goal: there are 100 wardens in the world, all shared, full stop. The first
climber to fell warden 1 clears the path for everyone, same as warden 71.
The personal-unlock system is deleted. Ships with just enough tuning that
floors 1–30 stay soloable — the full curve lands in 002.

Prerequisite: **plan 021** (floor/level split) merged and vendored.

## Tasks

1. `engine/combat.py`: delete the personal unlock (`_victory` lines
   720-724). The keep fight becomes the shared-warden engagement: full
   12-round fight, and on death/flee/withdraw the damage dealt is emitted
   as a `warden_strike` effect with the fight's total. Pool to zero =
   `_warden_fall` — the floor opens for everyone.
2. `engine/social.py`: retire the single-swing strike (818-832); the keep
   fight is the only way to hurt a warden. Remove the old 3⚡-per-swing UX.
3. worldd `social.py`: `_warden_fall` already bumps `frontier`; new — the
   plugin reads the frontier into `unlocked_floor` on every world sync
   (`max(unlocked_floor, frontier)`), leashed at entry by
   `floor_entry_player_level` (unchanged, `floor − 10`).
4. Wardens exist per floor in worldd for **all** floors 1–100 (today only
   the frontier floor has one; keep it lazy — a warden row materialises
   when its floor is the frontier).
5. Solo-band tuning stopgap: for F ≤ 30, world pool = ~1.5 energy bars of
   at-level fight damage and regen below one player's sustained output;
   for F > 30 keep current numbers (002 re-derives everything).
6. Echo fights: a fallen warden re-fightable at the keep, rewards ×0.5,
   fade rules apply, no world effect, no strike emission.
7. Milestone floors (10, 20 … 90) keep the pledge-quorum path unchanged.
8. Truth pass on the three strings that were lying: Stone
   (`core.py:1417`), worldd announcement (`social.py:700`),
   `floor_entry_player_level` docstring.
9. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Unit: keep-fight damage persists to the pool across two players; pool
  zero opens the floor for a third player who never fought; leash still
  refuses a level-12 climber at floor 40.
- Solo gate: sim — at-level reference player can fell warden 12 in ≤2
  full bars; cannot make net progress on warden 45 alone.
- Echo pays half and never emits a strike.
- Existing saves: a player whose `unlocked_floor` is above the world
  frontier keeps it (no regression for the current world).
- Browser walkthrough: fight a low-floor warden solo to the kill, watch
  the "open for everyone" line arrive as another player.
