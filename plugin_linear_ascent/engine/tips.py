"""014 — the whisper glyphs: one tooltip for every option in the game.

`option_tip(oid)` resolves render-side (no scene-schema change, no
version skew against an older worldd): exact ids first, then prefix
rules for the dynamic ones (buy_/hone_/sell_/floor_/join_/…).
`item_tip(slug)` explains a pack-strip entry.

Voice rule: the game's voice, but unambiguous — numbers included, and
every tip answers "how does this advance the climb?". Unknown ids
return "" and no glyph renders; never a broken [i].
"""

from __future__ import annotations

from .. import economy

# ── static ids ───────────────────────────────────────────────────────────

_TIPS: dict[str, str] = {
    # navigation
    "town": ("Back to Roothollow — the square with the Forge, Vault, "
             "Apothecary, Lodge and Guildhall. Floors stay opened; nothing "
             "is lost by going home to heal, bank and re-gear."),
    "back": "Back to the square — nothing spent, nothing changed.",

    # creation
    "next": ("The story of the Ascent, one scene at a time. Nothing is "
             "spent — watch, then climb."),
    "begin": ("Register at the tower gate: pick a line, take your "
              "shardmind, the gate's Rusted Sword (two ranks of bladework "
              "with it) and ◈ 50, and start hunting floor 1. Every "
              "climber the world has starts exactly here — the School "
              "sells everything else."),

    # ── Roothollow buildings — the priority tips ──
    "forge": ("Weapons, shields and armor by tier. More ATK ends fights "
              "sooner; more DEF keeps HP in your body — together they are "
              "what makes higher floors survivable, and higher floors pay "
              "more gold and XP per hunt. Each tier answers to a level: "
              "train at the Guildhall to wear the next one."),
    "arcanum": ("The staff shop — the full staff line and the glass "
                "focuses, list price to any hand. A staff casts magic "
                "damage past flat DEF; the School trains the rank that "
                "makes it hit true."),
    "medlab": ("The shelf that keeps a hunting run going: Medgel +25 HP, "
               "Trauma kit +80 HP, Trollblood tonic full heal usable "
               "MID-fight, Energy cell +5 energy (one a day), Luck charm "
               "for better loot until tomorrow. Healing on the road means "
               "more hunts per day — and hunts are where gold and XP "
               "come from."),
    "lodge": ("A paid bunk, ◈ 10 × your level: one safe night — fields "
              "ambushes can't touch you, and you wake +20 HP. Sleep here "
              "whenever you carry gold worth stealing. The stew pot "
              "(◈ 2, +5 HP) is the cheap top-up."),
    "vault": ("The bank. Carried gold is LOST when you die; banked gold "
              "survives everything and compounds at 5% a day. Bank your "
              "hunting profit before every risky climb — the interest "
              "alone finances your next tier of steel. The grants desk "
              "sends gold to other climbers."),
    "pawn": ("The broker pays 40% of Forge price for gear in your pack. "
             "Outgrown steel is dead weight — turn it back into gold and "
             "put it toward the next tier."),
    "relay": ("Letters between climbers — free to write. Collect enclosed "
              "gold, coordinate Warden pushes, call for a grant when "
              "you're short. The frontier falls faster when blades "
              "arrive together."),
    "fields": ("PvP. Ambush climbers who skipped the Lodge — 3 energy, twice "
               "a day. Win and you take their carried gold plus an XP "
               "bounty. Fast money, real risk: your banked gold stays "
               "safe either way, and a paid bunk keeps YOU off this "
               "board."),
    "guildhall": ("Training and faction life. A full XP bar plus the fee "
                  "in gold buys your next LEVEL — levels raise ATK, DEF "
                  "and HP and unlock higher gear tiers and higher floors: "
                  "no single thing advances the climb harder. Also: join "
                  "or found a faction, donate to its store, enter the "
                  "week's challenge."),
    "stone": ("The world's record, free to read: where the frontier "
              "stands, which Wardens fell, whose names are cut in the "
              "granite. Tells you where the world is — and where the "
              "glory and the best pay are."),
    "gate": ("The climb itself. Ride the lift to any opened floor and "
             "hunt it — gold and XP scale with the floor, so work the "
             "highest one you survive. A Warden holds every lift up; "
             "when one falls, the next floor opens for EVERYONE."),

    # ── gate towns ──
    "hunt": ("Fight a wild creature of this floor — 1 energy. The bread and "
             "butter of the climb: every kill pays gold and XP, and "
             "deeper floors pay more. This is the steady engine that "
             "buys everything else."),
    "heal": ("The healer's tent: full HP for ◈ 5 × floor. One kill more "
             "than covers it — far cheaper than dying, which takes your "
             "carried gold and breaks your armor and shield."),
    "stew": ("Hunter's stew: ◈ 2 for +5 HP, repeatable. The cheap "
             "top-up when a full heal would waste coin."),
    "school": ("Train your weapon paths — blade, bow, staff — rank 0 to "
               "10 for XP and coin. Higher rank: fewer misses, harder "
               "worst swings. Also sells the CARRY slots that let you "
               "walk in holding two or three weapons."),
    "keep": ("The floor's Warden — one shared body for the whole world. "
             "3 energy joins a real fight; every wound you leave stays in "
             "it for the next blade. When its pool empties the floor "
             "opens for EVERYONE and the spoils split by damage dealt. "
             "Fallen Wardens re-fight as echoes at half pay."),
    # ── 037: active sleep — the fast clock ──
    "sleep_menu": ("Turn in and actively sleep. Awake, energy returns "
                   "every 45 min and wounds wait for dawn; asleep, both "
                   "clocks run faster — ×1.5 in the fields, ×2 at the "
                   "Lodge, and HP mends as you sleep. Wake whenever "
                   "you like."),
    "sleep_lodge": ("Sleep in a Lodge bunk: energy at DOUBLE the waking "
                    "pace and a full HP bar mends in about 2 hours, with "
                    "the palisade keeping ambushers off you. Costs the "
                    "night's bunk price if you haven't paid it yet."),
    "sleep_fields": ("Sleep rough in the fields: free. Energy at ×1.5 "
                     "the waking pace and a full HP bar mends in about "
                     "4 hours — but anyone hunting the fields can still "
                     "find you while you sleep."),
    "lie_down": ("Lie down in your bunk and sleep now — energy at double "
                 "the waking pace and HP mending as you sleep. Pays for "
                 "the night first if you haven't."),
    "wake": ("Get up. Everything the clocks earned while you slept — "
             "energy and mended HP — is already banked."),
    "doze": ("Stay under. The meters refresh so you can watch the "
             "energy and HP climb."),
    # 030: people to talk to — the lodge keeper and the floor's voice
    "talk": ("Talking is free. The locals know this ground — what "
             "hunts it, what the Warden really is, and where the coin "
             "moves. Listening is the cheapest armor sold anywhere."),

    # ── the night slot (022/005) ──
    "night_rest": ("Tonight's ONE night action: rest, and dawn banks "
                   "rested aether — it pays out as +25% bonus XP on "
                   "each kill until the pool runs dry. The pool holds "
                   "at most 3 nights' worth, so rest before hunting "
                   "days, not before town days."),
    "night_work": ("Tonight's ONE night action: take the shift and the "
                   "coin arrives at dawn — about a fifth of a hunting "
                   "day, scaled to your frontier floor. Gold without "
                   "swinging a blade; it never touches the energy "
                   "cell's one-a-day."),

    # ── the long fire (022/008) ──
    "fire_word": ("Say one of five canned words at the long fire — "
                  "free. Everyone lodged tonight reads it; the fire "
                  "keeps the last five lines. The tower's cheapest "
                  "hello."),
    "fire_stew": (f"◈ {economy.FIRE_STEW_GOLD} stands a stew for "
                  "another climber at the fire — their name, your "
                  "name, one warm line everyone sees. Generosity "
                  "with a receipt."),
    "answer_flare": ("Someone on this floor is bleeding and lit a "
                     "flare. First blade to answer gets the fight — "
                     "and the world pays the rescuer gold and aether "
                     "for showing up. The climb remembers who came."),

    # ── the interest stubs (023) ──
    "collect_interest": ("Your banked gold earns 5% a day, dripped in "
                         "1% slices every 24/5 hours — each slice a "
                         "stub on the counter. This stamps the whole "
                         "pile into the bank — collected interest "
                         "compounds, uncollected stubs don't, and the "
                         "clerk keeps only a month of them. Come by "
                         "often and the vault works for you."),

    # ── the strongbox picks (022/005) ──
    "pick_gold": ("The strongbox's sure slot: a lump of gold, about "
                  "half a hunting day at your frontier floor. Always "
                  "on offer — the fallback if you never pick."),
    "pick_aether": ("The strongbox's second slot: a lump of rested "
                    "aether — bonus XP that rides your next kills at "
                    "+25% each. Pick it before a hunting week."),
    "pick_token": ("The strongbox's third slot: a repair token — one "
                   "FREE mend of any worn piece at the Forge. Worth "
                   "the most when your steel is expensive."),
    "pick_relic": ("The strongbox's third slot: a luck charm — better "
                   "loot and present rolls until tomorrow. Crack it "
                   "before a long day."),

    # ── vault desk ──
    "deposit_all": ("Everything into the vault. Banked gold survives "
                    "death and theft and grows 5% a day, compounded — "
                    "the safest advancement there is."),
    "deposit_half": ("Half in, half in hand. Banked gold survives death "
                     "and earns 5%/day; the carried half keeps you "
                     "shopping."),
    "withdraw_all": ("Take it all out. The Forge, Apothecary and "
                     "Guildhall only take carried coin — but only "
                     "carried coin can be lost. Spend it, then bank the "
                     "change."),
    # 036 dropped the receiver gate; 040 fixes the stale copy — any
    # level can receive. The gold rides in a Relay letter, and the
    # letter opens the Relay door for them whatever their level.
    "grants": ("Send gold to another climber — ANY level can receive. "
               "It arrives as a Relay letter with the coin enclosed, "
               "and the letter itself opens their Relay door. The Vault "
               "burns 10% of every transfer; your daily cap is "
               "◈ 150 × level. How veterans pull friends up the "
               "tower."),

    # ── the fight card ──
    "attack": ("Trade blows — your ATK against its DEF, then its ATK "
               "against yours. The straight road to the kill and the "
               "gold and XP it pays."),
    "stand": ("Brace behind your guard: incoming damage this round is "
              "HALVED, and a braced guard can hold a weak blow at "
              "zero. Buys a breath when HP runs low — the fight goes "
              "on until you attack or run."),
    "run": ("Leave the fight. No gold, no XP — but you keep your HP, "
            "your gear and your carried coin. Your speed against its "
            "speed decides the getaway: walk away from the slow, don't "
            "count on outrunning the fast. If it cuts off your line you "
            "take the blow and the fight goes on — and a Warden never "
            "lets you go on better than 3-in-4, however fast you are."),
    "close_in": ("Cross the open ground to swing steel. Always works, "
                 "costs the round — the monster strikes at HALF power "
                 "while you close. Bows and spellwork don't need this; "
                 "a blade does."),
    "open_distance": ("Break contact and put ground between you — only "
                      "possible against something SLOWER than you; equal "
                      "legs never part. Costs the round; if no gap opens "
                      "it gets a free half-power hit. At range a bow "
                      "shoots full and nothing reaches you back — until "
                      "it closes the gap."),
    # 040: the archer's gap ladder wears the same "Open distance" label
    # on the card — one verb for making ground; this tip is the [i].
    "create_distance": ("Give ground on purpose — rank-6 bowwork. It "
                        "ALWAYS works: you step back one length. From "
                        "rank 8 the open gap starts PAYING — ×1.25 at 2 "
                        "lengths, ×1.5 at 3 (the cap); below rank 8 the "
                        "long draw shoots plain ×1.0. The price is "
                        "the monster may rake you once as you pull "
                        "away; faster legs shrink that chance. Costs "
                        "the round."),
    "drink_tonic": ("Trollblood tonic — the ONLY heal that works "
                    "mid-fight: full HP, the round keeps going. Carried "
                    "for exactly the moment a Warden has you at the "
                    "edge."),
    "shield_wall": ("Blade craft, rank 4 — a shield on the arm: plant it "
                    "and take the round "
                    "on it. You deal nothing, you take nothing — resets "
                    "a fight that started badly without giving up the "
                    "kill."),
    "sleep_spell": ("Staff craft, rank 6 — the lullaby: put the creature "
                    "under and walk "
                    "past. Costs the fight's XP price and forfeits its "
                    "loot — but spends no HP at all. Cheap when your "
                    "health is worth more than the purse."),
    "treeline_shot": ("Bow craft, rank 4: one free arrow from the distance, "
                      "before the fight is joined — damage the enemy "
                      "never answers. It is the OPENING move: once you "
                      "attack, the cover is blown and the shot is gone "
                      "for the rest of the fight."),

    # ── keeps ──
    "strike": ("Join the fight — 3 energy for a FULL fight against the "
               "shared Warden. Kill, flee or fall, everything you cut "
               "away stays cut: every climber's wounds stack on the "
               "same body, so withdrawing alive still counts. ONE charge "
               "buys ONE exchange: when you have traded the rounds — or "
               "cut a full fight's worth out of it — its guard closes and "
               "it drives you back, whatever your gear. Nobody takes a "
               "gate in a single standing, and breaking off early is a "
               "gamble: it can follow you out and make you pay for the "
               "turn. The card "
               "says how many full fights are left — the deep ones need "
               "a crowd. Through FLOOR 10 a Warden never heals at all: "
               "chip at it across as many days as you need. Above that, "
               "leave a wound alone for a day and night and it closes "
               "whole (each closing costs it 3% of its body, forever). "
               "When it empties the "
               "floor opens for ALL and the prize splits by damage "
               "dealt — fight daily, even a little claims a share."),
    "boss_commit": ("Pledge your blade to the milestone push — 5 energy. "
                    "When enough blades stand pledged the gate falls "
                    "for everyone, and the pledged split the prize. The "
                    "tower is not climbed alone."),

    # ── guildhall / factions ──
    "guild_train": ("Buy your next level: a full XP bar plus the fee in "
                    "gold. Levels raise ATK, DEF and max HP and unlock "
                    "the next gear tier and deeper floors — the single "
                    "strongest advancement in the game."),
    # found_guild is resolved dynamically in option_tip (020) so the
    # level and fee always read the live constants.
    "donate": ("Move carried gold into the faction store. The store "
               "pays weekly challenge entries — and won challenges pay "
               "minted prizes back to attending members. Gold in the "
               "store also can't die with you."),
    "enter_week": ("Steward's call: pay the entry from the store to "
                   "enter this week's world challenge. Win it and every "
                   "attending, paid-up member shares the prize — the "
                   "faction's whole point."),
    "kick": ("Steward's call: strike a member from the roll. Their dues "
             "stop; so does their share of any prize."),
    "guild_leave": ("Fold your colors and go. Dues stop, prize shares "
                    "stop, the store keeps what it holds. The hall "
                    "always takes you back — for the join fee."),
    "cancel_found": "Back out — nothing charged, nothing signed.",
    "cancel_donate": "Back out — your coin stays in your pocket.",
    "cancel_kick": "Back out — the roll stays as it is.",

    # ── relay ──
    "collect": ("Take the gold enclosed with your letters — it lands "
                "straight in your carried coin."),
}

# race picks read their economy line plus the climb angle.
_RACE_ANGLE = {
    "human": ("+1 energy cap. Energy is the game's clock — one more point "
              "is one more hunt, strike or ambush every single day."),
    "elf": ("+5% XP from kills. Levels come faster, and levels are "
            "gear, floors and power — the compounding pick."),
    "giant": ("+5% armor value. Hits land softer, the healer is paid "
              "less, and hunting runs stretch longer per coin."),
}
for _r, _t in _RACE_ANGLE.items():
    _TIPS[_r] = _t


# ── prefix rules — the dynamic ids ───────────────────────────────────────

def _buy_tip(slug: str) -> str:
    g = economy.FORGE.get(slug)
    if g:
        freq = economy.rung_floor_req(g)
        gate = (f"floor {freq} open" if freq
                else f"level {economy.rung_player_level_req(g)}")
        if g.slot == "shoes":
            return (f"{g.name} — footwear, +{g.speed} speed (wants "
                    f"{gate}). {g.flavor.capitalize()}. Speed "
                    "decides the chase: kiting, fleeing, and the small "
                    "dodge. Expensive on purpose — it buys out of a "
                    "lot of bad matchups.")
        stat = "ATK" if g.slot == "weapon" else "DEF"
        tip = (f"{g.name} — {g.slot}, {stat} +{g.bonus}, rung {g.rung:g} "
               f"(wants {gate}). {g.flavor.capitalize()}. Better "
               f"{stat} is what turns deeper, richer floors from deadly "
               "into farmable; your replaced piece goes to your pack "
               "for the pawn shop.")
        if g.style:
            # 025 §4: a style is the same rung with a different bargain —
            # say which bargain, in uses, before the coin leaves the hand.
            plain = economy.FORGE[g.base]
            tip += (f" Same rung as the {plain.name}: "
                    f"{stat} +{g.bonus} against +{plain.bonus}, "
                    f"{economy.item_pool(g):,} uses against "
                    f"{economy.item_pool(plain):,}, "
                    f"◈ {g.price:,} against ◈ {plain.price:,}.")
        return tip
    i = economy.APOTHECARY.get(slug)
    if i:
        return item_tip(slug)
    r = economy.RELICS.get(slug)
    if r:
        # 006 law, on the glass: one dramatic effect + one hard
        # limitation, both named before the coin leaves your hand.
        pack = f" Sold ×{r.count} to the pack." if r.count > 1 else ""
        return f"{r.name} — {r.effect}. The catch: {r.limit}.{pack}"
    return ""


_HONE_STAT = {"weapon": "ATK", "shield": "DEF", "armor": "DEF"}

# 006: fight-option id → relic slug (the ids stay short on the card)
_FIGHT_RELIC = {
    "use_oil": "weapon_oil", "throw_net": "entangling_net",
    "use_hook": "sky_hook", "use_strip": "strip_potion",
    "use_curse": "curse_scroll", "use_polymorph": "polymorph_dust",
    "use_veil": "veil_draught", "use_apple": "golden_apple",
    "use_severing": "severing_word",
}


def option_tip(oid: str) -> str:
    """The tooltip for an option id, or "" (→ no glyph)."""
    t = _TIPS.get(oid)
    if t:
        return t
    if oid == "found_guild":
        from . import social
        return (f"Found your own faction — level {social.FOUND_MIN_LEVEL} "
                f"and ◈ {social.GUILD_FOUND_FEE}. You set the join fee "
                "and the weekly dues, steward the store, enter the "
                "world's weekly challenges and share their minted "
                "prizes with your members.")
    if oid.startswith("buy_"):
        return _buy_tip(oid.removeprefix("buy_"))
    if oid.startswith("wear_"):
        slug = oid.removeprefix("wear_")
        g = economy.FORGE.get(slug)
        name = g.name if g else "it"
        return (f"Take {name} out of your pack and wear it — free, on "
                "the spot; whatever it replaces goes to the pack. "
                "Honing stays with the bench, not the swap.")
    if oid.startswith("hone_"):
        slot = oid.removeprefix("hone_")
        stat = _HONE_STAT.get(slot, "its stat")
        return (f"Spend XP and gold to push this {slot} one notch "
                f"further (+1 {stat} per hone). The bonus lives on the "
                "item — replace it and the honing goes with it — so "
                "hone the piece you'll keep wearing. Spending XP delays "
                "training but never lowers your level.")
    if oid.startswith("repair_"):
        slot = oid.removeprefix("repair_")
        return (f"Paid gear wears with use — every swing, blow taken or "
                f"sprint spends a little of it. At zero it's broken, "
                f"not gone: half strength until mended. This restores "
                f"the {slot} to full for a fraction of its price plus "
                "a few XP.")
    if oid.startswith("donate_"):
        slug = oid.removeprefix("donate_")
        g = economy.FORGE.get(slug)
        name = g.name if g else "it"
        return (f"Hang {name} on your faction's armory racks — no coin "
                "changes hands, and its wear travels with it exactly as "
                "it is. Any member can take one piece a day at the "
                "Guildhall. Generosity, not a market.")
    if oid.startswith("take_arm_"):
        return ("Lift this piece off the faction racks into your pack — "
                "free, wear included, exactly as the donor left it. One "
                "take per day, members only. Wear or pawn it like "
                "anything else you own.")
    if oid.startswith("sell_"):
        slug = oid.removeprefix("sell_")
        g = economy.FORGE.get(slug)
        r = economy.RELICS.get(slug)
        a = economy.APOTHECARY.get(slug)
        name = (g.name if g else r.name if r else a.name if a
                else "the repair token" if slug == "repair_token" else "it")
        return (f"The broker pays a daily rate (25–55%, same for "
                f"everyone) for {name}, times its wear if it's gear. "
                "Outgrown things back into gold — gold into the next "
                "tier. A patient seller checks the rate tomorrow.")
    if oid.startswith("claim_"):
        return (f"Collect this finished job — the gold and XP land now, "
                f"minus the broker's ◈ {economy.BOARD_PRICE} stamp. "
                "Jobs die at dawn, collected or not: never sleep on a "
                "finished line.")
    if oid.startswith("token_"):
        slot = oid.removeprefix("token_")
        return (f"Spend an armor-repair token: this {slot} back to "
                "full — no gold, no XP, the smith asks nothing else. "
                "Tokens come from presents, contract bonuses and the "
                "weekly strongbox; spend them on your priciest steel.")
    if oid.startswith("floor_"):
        n = oid.removeprefix("floor_")
        return (f"Ride the lift to floor {n}. Gold and XP scale with "
                "the floor, so hunt the highest one you survive — "
                "level ≈ floor is the safe line, and the frontier is "
                "where Warden glory waits.")
    if oid.startswith("nock_"):
        return item_tip(oid.removeprefix("nock_")) + \
            " Nocking is free — the switch doesn't spend your round."
    if oid.startswith("use_") or oid == "throw_net":
        # 006 fight options carry short ids; map back to the relic.
        slug = _FIGHT_RELIC.get(oid, oid.removeprefix("use_"))
        t = item_tip(slug)
        if t:
            return t
        return item_tip(oid.removeprefix("use_"))
    if oid.startswith("write_"):
        who = oid.removeprefix("write_")
        return (f"Write to {who} — free. Coordinate a Warden push, ask "
                "for a grant, share what a floor is hiding. Allies "
                "make the tower shorter.")
    if oid.startswith("grantto_"):
        who = oid.removeprefix("grantto_")
        return (f"Send carried gold to {who}. The Vault burns 10% of "
                "every transfer — generosity has a tithe.")
    if oid.startswith("grantamt_"):
        try:
            amt = int(oid.removeprefix("grantamt_"))
        except ValueError:
            return ""
        burn = int(amt * economy.GRANT_BURN_PCT)
        return (f"Grant ◈ {amt:,} — ◈ {burn:,} of it burns as the "
                f"Vault's tithe; the rest arrives as carried gold.")
    if oid.startswith("join_"):
        name = oid.removeprefix("join_")
        return (f"Swear to {name}: the join fee moves into their store "
                "and weekly dues follow. In return — a share of every "
                "challenge prize the faction wins, and a hall that "
                "fights beside you.")
    if oid.startswith("sig_"):
        return ("Fly this sigil as the faction's banner — it heads the "
                "roll, the board and every prize note.")
    if oid.startswith("kick_"):
        who = oid.removeprefix("kick_")
        return (f"Strike {who} from the roll. Their dues stop; so does "
                "their share of any prize.")
    if oid.startswith("attack_"):
        who = oid.removeprefix("attack_")
        return (f"Ambush {who} in the fields — 3 energy, two a day. Win and "
                "you take their carried gold plus an XP bounty; lose "
                "and you limp home lighter. Banked gold is safe on "
                "both sides.")
    # 020: any registry-backed row gets its tip from the registry, so a
    # locked row and the ladder can never disagree — and coverage of
    # new gates is automatic.
    from .. import unlocks
    u = unlocks.for_option(oid)
    if u is not None:
        gate = "level" if u.gate == "level" else "floor"
        cost = f" Costs {u.cost}." if u.cost else ""
        return (f"{u.title.capitalize()} — {u.why}."
                f"{cost} Opens at {gate} {u.at}.")
    return ""


# ── pack-strip items ─────────────────────────────────────────────────────

_ITEM_TIPS: dict[str, str] = {
    # 027: where a thing COMES FROM belongs in its tip — a pack that keeps
    # filling up with something is a question the game should answer.
    "medgel": ("Medgel — +25 HP. Click it here to use it, anywhere out of "
               "a fight. They pile up because nine alpha kills in ten "
               "leave one behind (and presents carry them too): the pack "
               "is your health bar between fights, so spend them."),
    "trauma_kit": ("Trauma kit — +80 HP, used from the pack out of a "
                   "fight. The deep patch for deep floors, where one bad "
                   "round costs more than the kit did."),
    "trollblood_tonic": ("Trollblood tonic — full heal, drinkable "
                         "MID-fight, the only one that is. Carried for "
                         "the round a Warden has you at the edge."),
    "energy_cell": ("Energy cell — +5 energy on the spot, one a day. Energy "
                    "is the day's clock: a cell is five extra hunts' "
                    "worth of climbing."),
    "luck_charm": ("Luck charm — fortune leans your way until tomorrow: "
                   "better loot and present rolls. Click it to crack one "
                   "(once a day is all it does); alphas and Wardens drop "
                   "them about one time in ten."),
    "arrows": ("Bought arrows from the old armory ledger — bows no "
               "longer burn them; a trained hand's quiver looks after "
               "itself. A keepsake of a stricter era."),
    "repair_token": ("Armor-repair token — the Forge honors it as one "
                     "FREE mend, any worn piece, no gold, no XP. Best "
                     "spent on your priciest steel; the pawn shop buys "
                     "it if you'd rather have coin."),
}


def item_tip(slug: str, equipped: bool = False,
             bonus: int | None = None) -> str:
    """`bonus` is the LIVE stat when the caller knows it (the honed
    number on worn steel) — without it the tip quotes fresh-forge base
    and a honed sword reads weaker than it hits."""
    t = _ITEM_TIPS.get(slug)
    if t:
        return t
    r = economy.RELICS.get(slug)
    if r:
        return f"{r.name} — {r.effect}. The catch: {r.limit}."
    g = economy.FORGE.get(slug)
    if g:
        stat = "ATK" if g.slot == "weapon" else "DEF"
        shown = g.bonus if bonus is None else bonus
        # 045: durability on the tip — fresh-piece endurance; the pack
        # cell's hover carries the live left/total.
        end = (f", durability {economy.endurance(g):,}"
               if economy.wears(g) else "")
        if equipped:
            doing = ("every blow you land rides it"
                     if g.slot == "weapon"
                     else "it blunts every blow that lands on you")
            return (f"{g.name} — your worn {g.slot}, {stat} +{shown}"
                    f"{end}: {doing}. The Forge sells the next tier; "
                    "honing pushes this one further.")
        return (f"{g.name} — {g.slot}, {stat} +{shown}{end}, riding "
                "in your pack. Click it to put it on, or let the pawn "
                "shop pay the day's rate (25–55%) toward your next "
                "tier.")
    return ("Something the climb put in your pack. The pawn shop will "
            "tell you what it's worth.")
