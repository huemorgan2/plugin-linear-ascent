# Research: Prior Art for a Text-Based, Multiple-Choice Daily-Turn RPG

## 1. Classic BBS Door Games

### Legend of the Red Dragon (LORD, 1989, Seth Robinson)
The closest ancestor of the proposed concept. Sources: [Wikipedia](https://en.wikipedia.org/wiki/Legend_of_the_Red_Dragon), [Break Into Chat wiki](https://breakintochat.com/wiki/Legend_of_the_Red_Dragon), [CRPG Addict playthrough](http://crpgaddict.blogspot.com/2024/04/game-508-legend-of-red-dragon-1989.html), [Serion BBS LORD page](https://serionbbs.com/lord-info), [Muds wiki](https://muds.fandom.com/wiki/Legend_of_the_Red_Dragon).

- **Core loop:** Log in → village hub (weapon shop, armour shop, healer, Ye Olde Bank, inn, Turgon's Warrior Training, Dark Cloak Tavern) → spend the day's forest fights on random encounters → level up through 12 level masters → at level 12, challenge the Red Dragon.
- **Daily limits:** Sysop-configurable allotment of forest fights per day (commonly ~15; the CRPG Addict's modern board ran ~25 plus a 45-minute daily session cap) and a small separate allotment of player fights per day. Once per day the bard (Seth Able) sings, randomly granting extra forest fights, extra HP, or doubling your bank account — a daily variable-reward pull.
- **Banking:** Ye Olde Bank pays **10% interest per day**. Deposited gold is safe from PvP theft and from death; gold carried on hand is lost.
- **Death penalty:** Lose ~10% experience, all carried gold, and (if killed by a player) your gems; you resurrect the next day back in town. The killer gets half your experience.
- **Offline vulnerability:** Renting an inn room (expensive, priced per level) protects you while offline; players who sleep "in the fields" can be attacked and slaughtered by anyone. This is exactly the lodge mechanic in the new concept.
- **PvP:** Attack online players in real time on multi-node boards, or offline players sleeping in the fields. All kills are broadcast in the Daily Happenings news — public humiliation/glory was the real reward.
- **Social/romance:** Daily flirt system between players (wink → dinner → marriage proposal); NPC romance with Violet (for men) and Seth Able (for women); marriages announced in the news.
- **Endgame:** Killing the Red Dragon posts you to the hall of fame, increments a per-character dragon-kill counter, and resets the character to level 1 — an early prestige/ascension loop.
- **Extensibility:** IGMs (In-Game Modules) — third-party village locations — created an ecosystem of content and gave sysops differentiation.
- **Why sticky:** Robinson's stated design goal was **10–20 minutes per day**, not binging ([Break Into Chat](https://breakintochat.com/wiki/Legend_of_the_Red_Dragon)). Stickiness = daily turn refresh + daily bard lottery + 10%/day bank interest (compounds only if you log in and manage it) + fear of being slaughtered offline + daily news gossip + romance.

### TradeWars 2002 (1986/1991)
Sources: [Break Into Chat](https://breakintochat.com/wiki/TradeWars_2002), [Aaron A. Reed's "50 Years of Text Games"](https://if50.substack.com/p/1991-trade-wars-2002), [Sectorum retrospective](https://sectorum.net/bbs-games-modern.html).

- **Core loop:** Space trading — buy low/sell high across sectors, colonize planets, build up a corporate empire.
- **Daily limit:** Fixed number of turns per day (movement/actions consume turns), forcing strategic prioritization of every warp.
- **PvP:** Corporations (player teams) waged war over sectors and planets; attacking ships and raiding planets while owners were offline was core. Persistent galactic economy meant what you did today changed what the next caller found.
- **Sticky:** Turn economy + persistent shared world + corporation politics; PC World ranked it a top-10 PC game ever and cited EVE Online as its descendant.

### Usurper (1993)
Sources: [Break Into Chat](https://breakintochat.com/wiki/Usurper), [Usurper Reborn](https://usurper-reborn.net/) ([Steam](https://store.steampowered.com/app/4336570/Usurper_Reborn/), [GitHub](https://github.com/binary-knight/usurper-reborn)).

- **Core loop:** Grim-dark town hub + descend 100+ dungeon levels of a mountain; work alone or in small teams; ultimately seize the throne (usurp the king).
- **Offline vulnerability:** The Dormitory — offline characters sleep there and other players can kick them out of bed to duel them or **murder them in their sleep**. Paying for better protection was the counter.
- **PvP:** Real-time multiplayer on multi-node boards, team-vs-team fights, throne control.
- **Note:** Its 2025 remake (Usurper Reborn) markets itself on "60+ autonomous NPCs live, marry, and die 24/7 whether you're playing or not" — the persistent-world-that-moves-without-you fantasy is still a selling point today.

### Barren Realms Elite (BRE, 1992, Mehul Patel)
Sources: [Break Into Chat](https://breakintochat.com/wiki/Barren_Realms_Elite), [GameFAQs strategy guide](https://gamefaqs.gamespot.com/bbs/574618-barren-realms-elite/faqs/1571), [John Dailey Software](https://www.johndaileysoftware.com/products/bbsdoors/barrenrealmselite/).

- **Core loop:** Empire-building: each day the player spends turns on leadership decisions (economy, military, trading) that grow or shrink their nation.
- **Daily limit:** Turn allotment per day; trading available every turn and was the strongest lever.
- **Group model:** Pioneered **inter-BBS leagues** — whole BBSes formed teams, each with a "planetary coordinator" spokesperson; alliances between boards fought for league supremacy, with attack/message data exchanged via mail networks. Board-vs-board identity was a powerful retention driver — you fought for your community, not just yourself.

### Operation: Overkill II (1990)
Sources: [Break Into Chat](https://breakintochat.com/wiki/Operation_Overkill_II), [official site](https://operationoverkill.com/), [CRPG Addict](http://crpgaddict.blogspot.com/2015/04/game-187-operation-overkill-1990.html).

- **Core loop:** Post-apocalyptic survival: explore ANSI maps, find food/water crystals, fight mutants, eventually destroy the Overkill commander.
- **Distinctive:** Timing-based combat (hit spacebar as a gauge scrolls) — an early attempt to make text combat skill-based rather than pure menu choice.
- **Sticky:** Squadrons (player groups), trading water crystals, in-game mail; hailed as one of the deepest BBS CRPGs.

### MajorMUD (1994)
Sources: [Break Into Chat](https://breakintochat.com/wiki/MajorMUD), [majormud.com](http://www.majormud.com/mud-games.html), [MUDCentral](https://www.mudcentral.net/).

- **Core loop:** Real-time MUD on MajorBBS/Worldgroup — no daily turn cap; grind monsters, level, do quests.
- **Group model:** Guilds with quests, PvP, and **guild houses that stored items and could be raided by other guilds** — direct prior art for "group structures that other groups can attack."
- **PvP:** Per-realm settings from PvP-off to full PvP.
- **Sticky:** Scriptable clients let characters grind while you were away — an accidental idle-game layer; per-hour connection billing made it the classic "sticky" MajorBBS revenue engine.

## 2. Modern Successors and Energy-Gated Games

### Kingdom of Loathing (2003)
Sources: [KoL wiki: Adventures](https://wiki.kingdomofloathing.com/Adventures), [official docs](https://www.kingdomofloathing.com/doc.php?topic=adventures), [Daily Activities](https://wiki.kingdomofloathing.com/Daily_Activities).

- **Gate:** **40 Adventures (turns) per day** at rollover; unused adventures bank up to a **200 cap**, softening the punishment for missing a day.
- **Daily-return drivers:** Stomach/liver/spleen capacity resets daily — eating food and drinking booze grants extra adventures, so skipping a day forfeits those extras even if base turns roll over. Long list of once-per-day freebies (Daily Activities). Ascension (prestige reset) is the long-term loop.
- **Lesson:** Cap-with-carryover is the KoL compromise: daily play optimal, missed days not fatal.

### Torn (2004)
Sources: [Torn wiki: Energy](https://wiki.torn.com/wiki/Energy), [Faction](https://wiki.torn.com/wiki/Faction), [Organized Crime 2.0](https://wiki.torn.com/wiki/Organized_Crime_2.0), [mmos.com review](https://mmos.com/review/torn).

- **Gate:** Energy regenerates 5 per 15 min (cap 100) or 5 per 10 min for donators (cap 150) — full bar every 5 hours, so several check-ins per day are optimal. An attack costs 25 energy. Separate "nerve" bar for crimes, "happy" stat modifies gym gains.
- **Offline vulnerability / death:** Losing a fight sends you to the **hospital** for a timed stay (a soft death); attackers can mug (steal cash on hand — banked money safe), hospitalize, or leave you. Flying to other countries makes you unattackable — a paid-time "lodge" analogue.
- **Group model:** Factions run Organized Crimes (multi-member timed heists needing specific roles), hold map Territory that yields daily respect, and fight ranked wars; alliances defend territory.
- **Retention:** Login streaks/awards, weekly "inactivity refills" that lure lapsed players back, real-money donator perks tied to regen rate. 20+ years old and still large — evidence the Torn/LORD formula retains for decades.

### Fallen London (2009)
Sources: [Beginner's Guide](https://fallenlondon.wiki/wiki/Beginner's_Guide), [Failbetter forums on timers](https://community.failbettergames.com/t/actions-and-opportunity-cards-timer-update/14700).

- **Gate:** 1 action per 10 minutes, cap **20** (40 for paying "Exceptional Friends"). Opportunity card deck also refills on a timer. Premium currency (Fate) can refill but the game is explicitly designed not to be binged.
- **Lesson:** Very small caps make each choice feel precious and push multiple short sessions per day; monetization = double the cap, not remove it.

### Tribal Wars / Travian
Sources: [Travian beginner protection](https://support.travian.com/en/support/solutions/articles/7000060689-beginner-s-protection), [Daily Quests](https://support.travian.com/en/support/solutions/articles/7000061163-daily-quests), [Tribal Wars mechanics FAQ](https://support.innogames.com/kb/TribalWars/en_DK/5970), [World Wonder](https://travian.fandom.com/wiki/World_Wonder), [Endgame guide](https://travianlibrary.wordpress.com/2009/03/15/the-complete-guide-to-endgame/).

- **Gate:** Real-time construction/troop timers rather than turns — the building finishes in 4 hours whether you watch or not, so you come back when it's done.
- **Offline protection:** Beginner's protection (3 days–2 weeks, no attacks); the **Cranny** hides a fixed amount of resources from raids; Tribal Wars' night bonus gives defenders +100% during server-defined hours so sleeping players aren't farmed.
- **Retention:** Daily quests (up to 10 tasks/day), login bonuses, and above all the social contract — your tribe expects you online for coordinated attacks.
- **Endgame:** See sections 3 and 5 — the World Wonder.

### Melvor Idle
Source: [Steam discussions](https://steamcommunity.com/app/1267910/discussions/0/598519309481842201).

- Inverts the gate: time itself is the resource; skills train offline and you return to bank the gains and re-queue. Retention comes from "my character is wasting time if I don't redirect it" — the same daily-return psychology as energy bars, achieved without frustration.

### LORD lineage today
- [lord.stabs.org](https://lord.stabs.org/) — play original LORD in the browser.
- **Legend of the Green Dragon (LotGD)** — PHP/MySQL browser remake ([SourceForge](https://sourceforge.net/projects/lotgd/), [GitHub core](https://github.com/lotgd/core), [review](https://jayisgames.com/review/legend-of-the-green-dragon.php)): forest-fight allotment per "game day" (new day every 12 real hours on the flagship server), level 15 → hunt the Green Dragon, clans, opt-out PvP, an "underworld" mini-game while dead. Hundreds of hosted instances in the 2000s prove the formula ports cleanly to the web.
- [Usurper Reborn](https://usurper-reborn.net/) (2025, Steam) — proves there is a present-day audience for revived door games.
- LORD-style chat-bot games exist but no canonical Discord/Telegram LORD port surfaced; the niche appears open ([search found only generic lords-bot tooling](https://help.lords-bot.com/faq/chat-bot/)).

## 3. Aincrad and Shared Linear World-Progression

### SAO's Aincrad structure
Sources: [SAO wiki: Aincrad](https://swordartonline.fandom.com/wiki/Aincrad), [SAO wiki: Boss](https://swordartonline.fandom.com/wiki/Boss).

- 100 stacked floors, each a self-contained world (town + field + labyrinth); the **floor boss guards the stairs to the next floor**, so the entire population's progress is a single shared number: "we are on floor N."
- Bosses at multiples of 25 are spikes; multiples of 10 are the next tier down — rhythm of milestone floors.
- The **Monument of Swordsmen** records up to 7 names per cleared floor — permanent public credit for the clearing party; a small "assault team" clears floors on behalf of everyone, while most players live/craft/trade on lower floors. Two-tier population (frontliners + villagers) is a design feature, not a flaw.

### Games that used shared linear progression
- **SAO: Integral Factor** ([Wikipedia](https://en.wikipedia.org/wiki/Sword_Art_Online:_Integral_Factor)) — MMO that literally implements Aincrad: the whole server advances floor by floor via boss-clear events.
- **Helldivers 2** ([VideoGamer analysis](https://www.videogamer.com/features/helldivers-2-community-wide-orders-build-legacy-mmos/)) — galactic war with community-wide Major Orders; every player's missions add to shared planet-liberation percentages. Widely credited with making "writing history together" mainstream again.
- **Travian World Wonder** ([Travian fandom](https://travian.fandom.com/wiki/End_game)) — first alliance to build a WW to **level 100** wins and ends the server (~280 days on normal speed); each level costs resources far beyond one player, so it is intrinsically a group build project under constant enemy and NPC (Natar) attack.
- **MMO progression servers** (EverQuest TLP, WoW Classic) ([Massively OP](https://massivelyop.com/2018/03/21/perfect-ten-why-mmo-progression-servers-are-a-brilliant-idea/)) — the server community collectively unlocks expansions/content gates; the shared "where are we" state is a proven retention engine. (WoW's classic Ahn'Qiraj gate — a server-wide war-effort resource drive that opened a raid for everyone — is the canonical anecdote of community-unlocked progression.)
- **FFXIV alliance raids** ([wiki](https://ffxiv.consolegameswiki.com/wiki/Raids)) — 24-player content shows the "more players than a party, less than a server" tier for structure-scale fights.

Takeaway: a floor counter that the whole player base shares gives (a) a single legible goal, (b) news ("floor 12 fell last night"), (c) status for clearers (monument), and (d) natural content pacing — exactly what LORD's Daily Happenings did, scaled up.

## 4. Names That State the Goal

Patterns observed ([Catchword on noun+verb game naming](https://catchwordbranding.com/catchthis/8-reasons-mobile-games-are-named-noun-verb-or-how-candy-crush-crushed-bejeweled/), [Game Studies typology of imperative game goals](https://gamestudies.org/2003/articles/debus_zagal_cardonarivera)):

- **Imperative verb + goal-object:** *Slay the Spire* (the entire game is in three words: climb the spire, kill it), *Kill It With Fire*, *Getting Over It*. The Game Studies paper formalizes goals as imperatives ("reach X", "destroy Y", "own Z") — a title in that grammar doubles as the tutorial.
- **The goal-object as legend:** *Legend of the Red Dragon* — the title names the end boss; every player knows from minute one what the game is "about." Same for *Shadow of the Colossus* — the LORD pattern is the relevant one.
- **Destination/escape names:** *Escape from Tarkov*, *Journey*, *Temple Run*, *Subway Surfers* — movement toward/away from a named place.
- **Noun + verb compressions (mobile era):** *Candy Crush*, *Fruit Ninja*, *Trivia Crack* — the action in two words; used because store-front comprehension time is near zero.
- **Structure names for floor games:** the tower itself becomes the brand — *TowerClimb*, *Tower of Babylon*, *The 5-Floor Tower*, *Tower of God* ([itch/Steam survey](https://store.steampowered.com/app/396640/TowerClimb/), [Tower of Babylon](https://devicarus.itch.io/tower-of-babylon)). Aincrad works the same way: the place-name means the challenge.
- **Implication for this game:** the strongest fit is LORD's own pattern or the imperative pattern applied to floors: name the summit/final floor/final boss in the title (e.g. the "*Slay the Spire*" grammar: verb + the structure to be climbed), so the name simultaneously states the linear goal and the shared world.

## 5. Group-vs-Group and Structure-Building in Async Text Games

- **Travian World Wonder** — the archetype of "a structure that requires many players": millions of resources per level, second construction plan needed from an ally past level 50, defended around the clock by the whole alliance while enemies and Natars besiege it ([support article](https://support.travian.com/en/articles/103-world-wonder), [build guide](https://unofficialtravian.com/2025/01/game-secrets-building-a-world-wonder-text-version/)).
- **Torn factions** — persistent group bank, upgrade tree fed by "respect" earned from members' Organized Crimes (role-based multi-player heists on timers), territory blocks that pay daily respect, ranked faction wars ([Faction wiki](https://wiki.torn.com/wiki/Faction), [OC 2.0](https://wiki.torn.com/wiki/Organized_Crime_2.0)).
- **MajorMUD guild houses** — shared item storage that rival guilds could raid; ownership creates both pride and a raid target ([majormud.com](http://www.majormud.com/mud-games.html)).
- **BRE inter-BBS alliances** — whole communities as teams with a named coordinator; cooperation bonuses unavailable in solo mode ([Break Into Chat](https://breakintochat.com/wiki/Barren_Realms_Elite)).
- **LotGD clans, Usurper teams, TW2002 corporations** — small-group tiers in otherwise solo daily loops (sources above).
- **Offline protection catalog:** LORD inn room (pay gold, safe overnight) · Usurper dormitory (default sleeping spot is attackable — protection costs) · Travian cranny (hides a fixed resource amount) + beginner protection (3 days–2 weeks) · Tribal Wars night bonus (+100% defense at night) · Torn hospital/travel states (temporarily untargetable) · KoL/Fallen London have no offline PvP at all. The spectrum runs from "pay to be safe" (LORD — creates a gold sink and a risk decision) to "time-window safety" (night bonus) to "systemic immunity" — LORD's model generates the most drama per player.

## Lessons for Our Game

1. **LORD is the validated template** — village hub, daily fight allotment, 10%/day bank interest that survives death, pay-for-inn-room offline safety, public kill news, level masters, single named end boss, prestige reset after the kill. Deviate knowingly, not accidentally.
2. **Design for 10–20 minutes/day** (Robinson's explicit goal). Energy should run out mid-appetite, and the bank/interest should reward coming back tomorrow rather than grinding today.
3. **Cap with carryover (KoL: 40/day, 200 cap)** forgives a missed day without removing the daily incentive; pair with daily-reset extras (KoL organs, LORD bard song) so full value still requires showing up.
4. **Make the daily gift a lottery, not a fixed stipend** — LORD's bard (random: extra fights / HP / double bank) and modern streak calendars with variable rewards outperform flat bonuses ([retention research](https://maf.ad/en/blog/daily-login-rewards-engagement-retention/)); add a lapsed-player comeback bonus (Torn inactivity refills).
5. **Banked money must survive death and theft; carried money must not.** This one rule creates the whole risk texture of LORD/Torn (mugging, "do I bank before the caves?").
6. **Offline vulnerability + purchasable safety (lodge) is the strongest emotion engine** — but give the poor a partial shelter (cranny/night-bonus analogue) so new players aren't farmed out of the game; use beginner protection for the first days.
7. **Public news feed of kills, marriages, floor clears is free retention** — LORD's Daily Happenings and SAO's monument are the same mechanic: permanent, visible credit and gossip.
8. **Shared floor progression gives the server one legible goal** — Aincrad's "what floor are we on" + Travian's WW race. Let a frontline group clear floors for everyone, engrave their names, and let the milestone floors (every 10th/25th) be community events requiring group-built structures (siege towers, forts) that others can sabotage.
9. **Group tier: shared structure with shared risk** — a clan hall/tower that needs multiple players' daily resources to build, confers benefits (respect trickle, storage), and can be raided (MajorMUD, Torn territory). Group content should consume the same daily energy so it competes with solo grinding.
10. **Name the goal in the title** — use the *Slay the Spire* / *Legend of the Red Dragon* grammar: imperative verb + the tower/summit/boss, so the linear ambition is legible before the first turn is played.
