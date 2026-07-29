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
    "begin": ("Register at the tower gate: pick a line and a craft, take "
              "your shardmind and ◈ 50, and start hunting floor 1. Every "
              "climber the world has starts exactly here."),

    # ── Roothollow buildings — the priority tips ──
    "forge": ("Weapons, shields and armor by tier. More ATK ends fights "
              "sooner; more DEF keeps HP in your body — together they are "
              "what makes higher floors survivable, and higher floors pay "
              "more gold and XP per hunt. Each tier answers to a level: "
              "train at the Guildhall to wear the next one."),
    "arcanum": ("The mage shop — staves and focuses only a caster can "
                "own, behind a door that reads the hand on it (level 6). "
                "Warriors and archers can buy a stopgap staff off the "
                "rack at triple price; the good glass answers only to "
                "sorcerers."),
    "medlab": ("The shelf that keeps a hunting run going: Medgel +25 HP, "
               "Trauma kit +80 HP, Trollblood tonic full heal usable "
               "MID-fight, Energy cell +5 energy (one a day), Luck charm for "
               "better loot until tomorrow, Scout optics for 3 enemy "
               "scans. Healing on the road means more hunts per day — "
               "and hunts are where gold and XP come from."),
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
                  "or raise a banner, donate to its store, enter the "
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
    "keep": ("The floor's Warden — one shared body for the whole world. "
             "3 energy joins a real fight; every wound you leave stays in "
             "it for the next blade. When its pool empties the floor "
             "opens for EVERYONE and the spoils split by damage dealt. "
             "Fallen Wardens re-fight as echoes at half pay."),
    "sleep": ("◈ 10 × your level for the night: ambush-proof sleep and "
              "+20 HP by dawn. Skip it carrying gold and the fields may "
              "find you."),

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
    "grants": ("Send gold to another climber (they must be level 5+). "
               "The Vault burns 10% of every transfer; your daily cap "
               "is ◈ 150 × level. How veterans pull friends up the "
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
            "count on outrunning the fast."),
    "close_in": ("Cross the open ground to swing steel. Always works, "
                 "costs the round — the monster strikes at HALF power "
                 "while you close. Bows and spellwork don't need this; "
                 "a blade does."),
    "open_distance": ("Break contact and put ground between you — your "
                      "speed against its speed. Costs the round; if no "
                      "gap opens it gets a free half-power hit. At range "
                      "a bow shoots full and its blows land at half."),
    "scout": ("Your shard scans the enemy — exact ATK, DEF and HP. "
              "Free on an optics charge, otherwise it burns XP. Knowing "
              "when to press and when to run saves more than it "
              "costs."),
    "drink_tonic": ("Trollblood tonic — the ONLY heal that works "
                    "mid-fight: full HP, the round keeps going. Carried "
                    "for exactly the moment a Warden has you at the "
                    "edge."),
    "shield_wall": ("Warrior craft: plant the shield and take the round "
                    "on it. You deal nothing, you take nothing — resets "
                    "a fight that started badly without giving up the "
                    "kill."),
    "sleep_spell": ("Sorcerer craft: put the creature under and walk "
                    "past. Costs the fight's XP price and forfeits its "
                    "loot — but spends no HP at all. Cheap when your "
                    "health is worth more than the purse."),
    "treeline_shot": ("Archer craft: one free arrow before the fight is "
                      "joined — damage the enemy never answers. Once "
                      "per encounter; every fight it shortens is HP "
                      "saved."),

    # ── keeps ──
    "strike": ("Join the fight — 3 energy for a FULL fight against the "
               "shared Warden. Kill, flee or fall, everything you cut "
               "away stays cut: every climber's wounds stack on the "
               "same body. When it empties the floor opens for ALL and "
               "the prize splits by damage dealt — fight daily, even a "
               "little claims a share."),
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

# race / class picks read their economy line plus the climb angle.
_RACE_ANGLE = {
    "human": ("+1 energy cap. Energy is the game's clock — one more point "
              "is one more hunt, strike or ambush every single day."),
    "elf": ("+5% XP from kills. Levels come faster, and levels are "
            "gear, floors and power — the compounding pick."),
    "dwarf": ("+5% armor value. Hits land softer, the healer is paid "
              "less, and hunting runs stretch longer per coin."),
}
_CLASS_ANGLE = {
    "warrior": ("Unlocks Shield Wall in fights: take a whole round on "
                "the shield, no damage either way. The durable pick — "
                "fewer healer bills on the way up."),
    "sorcerer": ("Unlocks Sleep Spell: skip any fight for its XP price, "
                 "spending no HP. Trades loot for safety whenever a "
                 "fight looks like a bad deal."),
    "archer": ("Unlocks Treeline Shot: one free strike before every "
               "fight is joined. Shorter fights, less damage taken, "
               "faster grinding."),
}
for _r, _t in _RACE_ANGLE.items():
    _TIPS[_r] = _t
for _c, _t in _CLASS_ANGLE.items():
    _TIPS[_c] = _t


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
        return (f"{g.name} — {g.slot}, {stat} +{g.bonus}, rung {g.rung:g} "
                f"(wants {gate}). {g.flavor.capitalize()}. Better "
                f"{stat} is what turns deeper, richer floors from deadly "
                "into farmable; your replaced piece goes to your pack "
                "for the pawn shop.")
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
        return (f"Raise your own banner — level {social.FOUND_MIN_LEVEL} "
                f"and ◈ {social.GUILD_FOUND_FEE}. You set the join fee "
                "and the weekly dues, steward the store, enter the "
                "world's weekly challenges and share their minted "
                "prizes with your members.")
    if oid == "buy_arrow_pack":
        return (f"A pack of {economy.ARROW_PACK_SIZE} arrows for a bow "
                "in off-class hands — an archer's basic quiver never "
                "empties, everyone else's does. When the pack runs dry "
                "mid-fight your own weapon comes back out on its own.")
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
        name = g.name if g else (r.name if r else "it")
        return (f"The broker pays a daily rate (25–55%, same for "
                f"everyone) for {name}, times its wear if it's gear. "
                "Outgrown things back into gold — gold into the next "
                "tier. A patient seller checks the rate tomorrow.")
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
                "challenge prize the banner wins, and a hall that "
                "fights beside you.")
    if oid.startswith("sig_"):
        return ("Fly this sigil as the banner's mark — it heads the "
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
    "medgel": ("Medgel — +25 HP, used at a gate camp between fights. "
               "Keeps a hunting run going without the walk home: more "
               "hunts per day, more gold and XP."),
    "trauma_kit": ("Trauma kit — +80 HP at a gate camp. The deep patch "
                   "for deep floors, where one bad round costs more "
                   "than the kit did."),
    "trollblood_tonic": ("Trollblood tonic — full heal, drinkable "
                         "MID-fight, the only one that is. Carried for "
                         "the round a Warden has you at the edge."),
    "energy_cell": ("Energy cell — +5 energy on the spot, one a day. Energy "
                    "is the day's clock: a cell is five extra hunts' "
                    "worth of climbing."),
    "luck_charm": ("Luck charm — fortune leans your way until "
                   "tomorrow: better loot and present rolls. Crack it "
                   "before a long hunting day."),
    "scout_optics": ("Scout optics — 3 shard scans: exact enemy ATK, "
                     "DEF and HP before you commit. Fights you can "
                     "read are fights you don't lose."),
    "arrows": ("Bought arrows — every off-class bow shot burns one. "
               "When they run out mid-fight your own weapon comes "
               "back out. Archers never need these; their basic "
               "quiver refills itself."),
    "repair_token": ("Armor-repair token — the Forge honors it as one "
                     "FREE mend, any worn piece, no gold, no XP. Best "
                     "spent on your priciest steel; the pawn shop buys "
                     "it if you'd rather have coin."),
}


def item_tip(slug: str, equipped: bool = False) -> str:
    t = _ITEM_TIPS.get(slug)
    if t:
        return t
    r = economy.RELICS.get(slug)
    if r:
        return f"{r.name} — {r.effect}. The catch: {r.limit}."
    g = economy.FORGE.get(slug)
    if g:
        stat = "ATK" if g.slot == "weapon" else "DEF"
        if equipped:
            doing = ("every blow you land rides it"
                     if g.slot == "weapon"
                     else "it blunts every blow that lands on you")
            return (f"{g.name} — your worn {g.slot}, {stat} +{g.bonus}: "
                    f"{doing}. The Forge sells the next tier; honing "
                    "pushes this one further.")
        return (f"{g.name} — {g.slot}, {stat} +{g.bonus}, riding in "
                f"your pack since you outgrew it. Dead weight: the "
                "pawn shop pays the day's rate (25–55%) toward your "
                "next tier — worth checking on a good day.")
    return ("Something the climb put in your pack. The pawn shop will "
            "tell you what it's worth.")
