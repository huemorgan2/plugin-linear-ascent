# Dojo plan: guild joining, player presence, warden boards, profiles, looting

Status: draft, not yet anchored to code (Drive mount was unresponsive; re-verify
entity/table/route names against the dojo codebase before implementation).

## 0. Scope

Five features:
1. Guild joining open to all levels, via the Guild Hall.
2. "Players here" presence grid shown in every location.
3. Warden attacker boards (live and dead warden).
4. Player profile page with message / send money / gift item.
5. Looting (PvP theft with retaliation risk).

---

## 1. Guilds — joining

### Rules
- No global level gate: a player of any level may join a guild.
- Each guild may define its own requirements (e.g. min level, min total
  contribution, invite-only flag). A player can join only if they meet the
  guild's own requirements. Default for a new guild: no requirements.
- One guild per player at a time.

### Flow (Guild Hall)
1. Guild Hall menu gains option: **"Join a guild"**.
2. Selecting it opens the **Guild Directory** view:
   - Paginated list, page size 20, hard cap of 100 guilds returned per query.
   - Search box (name substring, case-insensitive); search results also capped
     at 100 with pagination.
   - Each row: guild crest/name, member count, level requirement (if any),
     one-line description, "Join" button.
   - "Join" is disabled with a reason when requirements are unmet
     ("Requires L10", "Invite only", "Full").
3. Joining is immediate when requirements are met; emits a guild event
   ("<player> joined") and updates member count.

### Data
- `guild`: id, name, description, crest, created_at, member_cap,
  requirements JSON (`{min_level?, invite_only?, min_contribution?}`).
- `guild_member`: guild_id, player_id, joined_at, contribution_total,
  contribution_log (or separate `guild_contribution` table:
  member_id, kind [coins|item|warden_damage], amount/item_ref, at).

### API
- `GET /guilds?search=&page=` → max 100 total, 20/page: name, members,
  requirements, joinable-for-me flag.
- `POST /guilds/{id}/join` → 200 or 4xx with reason (level, invite-only, full,
  already in a guild).

---

## 2. "Players here" presence grid (shared component)

### Layout
- Grid of player avatars, **7 per row**, unlimited rows (70 players → 10 rows).
- Each cell: avatar, `Lxx` level tag under it, **Zzz** badge on top of the
  avatar when the player is sleeping.
- Hover (desktop) / long-press (touch): tooltip with coin and energy.
- Click: navigate to that player's profile page (section 4).

### Placement
Rendered **under the location's options** in every location:
- every floor of Rootholow
- the Tavern
- the Vault
- every Warden space

### Data / behavior
- "Here" = players whose current location == this location. Refresh on view
  load; poll or push-update every ~30s while the view is open.
- Sorting: online/awake first, then by level desc.
- If more than ~70 players, keep rendering rows (component itself is not
  capped); virtualize the list if a location exceeds a few hundred.
- Component API: `PlayersHereGrid(location_id)`; reused verbatim everywhere.

### API
- `GET /locations/{id}/players` → [{player_id, avatar, level, sleeping,
  coins, energy}]. Coins/energy may be lazy-loaded on hover instead if the
  payload gets heavy.

---

## 3. Warden boards

### Live warden (being attacked)
In the warden space, under the options, show all players who came to attack
this warden, as an avatar grid (same visual language as the presence grid).
Per player: avatar, Lxx, and **damage taken from the warden** (this fight).
Click → profile.

### Dead warden
Visiting a dead warden space shows all players who helped take it down,
**ranked by damage dealt to the warden** (descending). Per player: rank,
avatar, Lxx, damage dealt. Click → profile.

### Data
- `warden_fight_participant`: warden_id (or fight_id), player_id,
  damage_dealt, damage_taken, joined_at. Persist after the warden dies so the
  dead-warden board is permanent for that kill.

### API
- `GET /wardens/{id}/participants` → live: [{player, damage_taken}],
  dead: [{player, damage_dealt}] sorted desc.

---

## 4. Player profile page

Route: `/players/{id}`. Reached by clicking any avatar anywhere.

### Shows (everything, read-only)
- Avatar, name, level, sleeping state.
- Money (coins), energy.
- Full inventory (equipment + items).
- Guild: name + **total contribution and its breakdown** (what they gave:
  coins, items, warden damage — from `guild_contribution`).

### Actions (on another player's profile)
1. **Send private message** — text message, lands in the target's inbox/chat.
2. **Send money** — routed **through the Vault**: amount is withdrawn from
   sender, transferred via a vault transaction record, credited to target.
   Vault takes its standard fee if one exists (verify in code).
3. **Gift item** — pick an item from your inventory; it moves to the target's
   inventory. Confirmation step; blocked if target inventory is full.
4. **Loot** — see section 5. Shown with a danger treatment and the eligibility
   state ("active recently — high risk").

### API
- `GET /players/{id}/profile`
- `POST /players/{id}/message` {text}
- `POST /players/{id}/send-money` {amount} (vault transaction)
- `POST /players/{id}/gift` {item_id}
- `POST /players/{id}/loot`

---

## 5. Looting

### Eligibility
- A player can be **successfully looted only if they made no action in the
  last 1 hour** (track `last_action_at` on every meaningful action).
- Anyone can *attempt* a loot on anyone.

### Resolution
Let A = attacker, D = defender/target.

**Case 1 — D active within the last hour:**
- The loot fails outright (nothing is taken).
- A takes retaliation damage equal to **200% of D's attack power**.

**Case 2 — D inactive ≥ 1 hour (lootable):**
- D auto-defends at **25% of their attack power**: A takes damage equal to
  25% of D's attack power (mitigated by A's defense the same way normal
  combat mitigates damage).
- Loot success chance and haul scale with the power gap
  (level + abilities + equipment):
  - A much stronger than D → succeeds, takes ~no effective damage
    (25% of a weak player's attack is negligible after mitigation).
  - A much weaker than D → likely gets hurt badly for a small/no haul.
  - Equals → each attempt costs real HP; over repeated attempts against
    equals the expected value is negative (by design).
- Haul on success: a percentage of D's carried (non-vaulted) coins and a
  chance at one equipped/inventory item. Exact percentages to tune; suggest
  starting at 10–20% of carried coins, 5–10% item chance, both scaled by
  power gap. Vault-stored money is never lootable (makes the vault matter).

**Counter-loot exposure:** looting is itself an action (updates A's
`last_action_at` — so A is *not* lootable for the next hour by the inactivity
rule), but D (and others) can loot A back later under the same rules; combat
log notifies D they were looted and by whom.

### Damage/death interaction
- Retaliation damage uses the normal damage pipeline (can knock A out / kill
  per existing dojo death rules — protected/unprotected, revive stones, etc.).

### Data
- `player.last_action_at` (indexed).
- `loot_attempt`: attacker_id, target_id, at, outcome
  (failed_active | success | failed_roll), damage_to_attacker, coins_taken,
  item_taken.
- Notification/event to the target on any attempt.

### Anti-abuse
- Cooldown: one loot attempt per attacker per target per hour.
- No looting guildmates (suggest; confirm with Roy).
- All attempts logged and visible in the target's combat log.

---

## 6. Build order

1. `last_action_at` tracking + presence data (`current_location`) — everything
   else reads these.
2. `PlayersHereGrid` component + `GET /locations/{id}/players`; mount in
   Rootholow floors, Tavern, Vault, Warden spaces.
3. Profile page (read-only) + click-through from every avatar.
4. Warden participant tracking + live/dead boards.
5. Guild directory (search, pagination, cap 100) + join flow with per-guild
   requirements; contribution breakdown on profile.
6. Message / send-money-via-vault / gift actions.
7. Looting (mechanics, log, notifications, cooldowns), then tuning pass on
   haul percentages and damage numbers.

## 7. Open items (need code access or Roy's call)

- Exact table/route naming conventions in the dojo codebase.
- Whether a "sleeping" state already exists or is derived from inactivity.
- Vault fee on player-to-player transfers.
- Loot haul percentages and success-roll formula constants.
- Guildmate-looting ban yes/no.
