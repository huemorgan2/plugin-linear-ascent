# Linear Ascent — Game Ideas

How the agent, multiplayer, and pacing come together. Companion to [vision.md](./vision.md) and [research.md](./research.md); world in [world.md](./world.md), numbers in [economy.md](./economy.md).

## 1. The agent as your sidekick

The game is played inside a chat with your Luna agent — so the agent should not just narrate the game, it should be **in** it.

### The agent is a character

- Your agent gets its own in-game character sheet: a small set of stats (insight, courage, luck) and its own inventory slot or two.
- It levels alongside you. Its personality colors how it narrates — the same fight reads differently with a cautious agent than with a reckless one.
- Class complement: whatever class you pick, the agent takes a complementary role (you're the tank, it's the scout; you're the sorcerer, it carries the torch).

### What the sidekick can do mechanically

- **Advise on choices.** Before you pick "stand / attack / run", the agent can whisper an assessment ("that dragon's 7 defense is above your attack — running costs pride, not gold"). Advice accuracy scales with its insight stat, so early on it's sometimes wrong — which is funny and builds attachment.
- **Scout ahead.** Spend agent energy (a separate, smaller pool) to reveal one hidden option or enemy stat before you choose.
- **One save per day.** Once a day the agent can pull you out of a killing blow ("your sidekick drags you into the bushes") — a natural daily-loop hook.
- **Carry loot home.** If you die, anything the agent was carrying survives — a second "bank", but capacity-limited, so it's a real choice what to hand it.
- **Act while you're offline.** The player assigns the agent a night job: guard you (reduces off-line kill chance if you skipped the lodge), work at the blacksmith (small income), listen for rumors (tomorrow's encounter hints). This makes logging off a decision, not an absence.
- **Remember.** The agent genuinely remembers your run history (it's an LLM agent with memory) — it can reference the dragon that killed you last week. No other game can do this natively.

### Agent-native encounters

- Some encounters address the agent directly — a sphinx that only talks to sidekicks, a choice the agent must make for you while "you" are unconscious.
- Social encounters can use the agent's actual conversational ability: persuade the dwarf in free text, and the game judges the attempt. This is the one place free text beats multiple choice — use it sparingly, as a special ability ("Silver Tongue: once per day, talk instead of fight").

## 2. Multiplayer

### Infrastructure

- Shared world state in a **Postgres on Render** (we already run scheduler-service there — same account). Each Luna instance's plugin talks to a small game API service; the plugin never talks to the DB directly.
- Everything is asynchronous. No live sessions needed — the BBS model (LORD) proved async PvP works: you attack the *record* of an offline player.

### Async PvP

- Players who didn't sleep in the lodge appear on the "fields" list — attackable while offline. Lodge is cheap but costs gold, so broke players sleep rough: risk compounds poverty, exactly like LORD.
- Combat vs. offline players is resolved by stats + luck rolls; the victim gets a full story of what happened when they return ("you were ambushed in your sleep by Karl the Red — your sidekick fought them off but lost your boots").
- Bank money is untouchable; carried gold is lootable. This makes the bank/carry decision the core daily risk choice.

### Group play

- **Parties for big targets.** Certain monsters/structures (a fortress, a tower boss) require N players' combined attack within a time window (e.g. 24h). You "commit your attack" and it resolves when the quorum is reached — async raiding.
- **Guilds/clans** own a structure (tower, fortress) that other groups can siege. Owning one gives a passive perk (extra energy regen, bank interest bonus). Sieges are announced, giving defenders a day to rally — which drives return visits.
- **Building.** A player (or guild) can spend resources to build something — a watchtower, a trap on a road, a shrine. Others encounter it: attack it, use it, or join its upkeep. Player-built content becomes other players' encounters.

### Classes, adapted to multiple choice

Full WoW-style action rotations don't fit this interface, but classes work if they **change which options appear**:

- The same dragon encounter shows *stand / attack / run* to everyone, but the tank also sees *shield wall*, the sorcerer sees *sleep spell*, the archer sees *shoot from the treeline*.
- Class = a different option deck, not a different UI. Cheap to build, reads great in text.
- In group fights, each committed class contributes a different modifier (tank soaks the fortress guards, sorcerer lowers the gate, archers add ranged damage) — so mixed parties beat stacked ones.

## 3. Pacing: energy, mana, and the daily return

The design goal is **come back tomorrow**, not **stay for hours**.

- **Two pools:** energy (physical actions: travel, fight) and mana (spells, agent abilities). Both regenerate on a real-time clock; a session naturally drains them in 10–20 minutes.
- **Hard daily rhythm** like LORD's daily turns: N forest fights and 1–3 PvP attacks per day, on top of the energy pools. Simple, legible, proven.
- **Returning is rewarded, luck-flavored:** come back after a day and get presents — a random roll from a gift table (gold, a potion, a rumor, rarely something great). Streaks can gently improve the table, but a break never punishes below baseline — we want forced breaks to feel fine.
- **Bank interest is the quiet retention hook:** daily compounding paid only when you visit the teller. Your money grows while you sleep; you come back to collect.
- **Energy ceiling grows** with level and lodge upgrades, and can be temporarily boosted (potions, presents) — sessions get a bit richer over time without becoming binges.
- **No paid skip-the-wait**, at least initially: the wait *is* the game. Everyone lives on the same clock, which keeps the shared world fair.
- The agent softens the wall: out of energy doesn't mean silence — you can still talk to your sidekick, plan tomorrow, check the fields list, read the rumor it heard. Zero-energy states are social, not dead.

## 4. Story and structure: the linear goal

Borrowing the Aincrad idea (SAO): the world is a **stack of floors** — each floor a self-contained world (village + wilds + boss). The community advances floor by floor; clearing a floor boss is a server-wide event that opens the next floor for everyone. This gives:

- A **shared linear goal** the whole player base pushes toward — the name of the game can literally state it.
- Natural content cadence for us: we author one floor at a time.
- Floor bosses as the flagship group-quorum fights.
- Old floors stay open — new players catch up in cleared floors while veterans push the frontier.

## 5. Name candidates

The name should carry the main goal (linear ascent, floor by floor). Candidates:

- **Nextfloor** / **Floor by Floor** — literal, states the loop.
- **The Climb** / **Ascent** / **Upward** — the goal as a verb.
- **Spire** / **The Spire** — the world is the name; "what floor are you on?" becomes the player question.
- **One Hundred Floors** — states the finish line, SAO-style.
- **Sidequest** — keep it if we want the general/ironic frame: you and your agent, the "sidekick", on a side quest that turns out to be the main one. Works with the story: the agent's quest is *you*.

**Decided 2026-07-23: Linear Ascent.** The tower is "the Ascent" in-world ([story.md](./story.md)) — the name is the goal, the place, and the progression model at once.

## 6. Open questions

- Does PvP corpse-looting need an opt-out (protected mode) for casual players, or is lodge-cost the only shield?
- Agent energy: shared pool with the player or separate? (Separate proposed above.)
- One shared world for all Luna tenants, or shards? One world is the dream; needs abuse controls.
- Who resolves timed group fights when no player is online — Render cron on the game service (we already have scheduler infrastructure there).
