"""Linear Ascent economy — every number derives from vision/economy.md.

Pure functions and data tables only. Content files never carry these
numbers; the loader and engine compute them. Keep the SHAPES when tuning.
"""

from __future__ import annotations

from dataclasses import dataclass

# ── §1 Meters ────────────────────────────────────────────────────────────

ENERGY_REGEN_MIN = 45          # 1 energy per 45 minutes
ENERGY_BASE_CAP = 24

COST_WILDS_FIGHT = 1
COST_WARDEN_ATTEMPT = 3
COST_BOSS_COMMIT = 5
COST_PVP_ATTACK = 3


def energy_cap(level: int, race: str = "") -> int:
    cap = ENERGY_BASE_CAP + level // 10
    if race == "human":
        cap += 1
    return cap


# ── §1b The XP pool (006: aether = crystallized experience) ──────────────
# The mana meter is gone. The ✦ bar is the XP inside the current level:
# earned by fighting, spent on honing / spells / scans. Spending delays the
# next level, never lowers one. All costs are priced in frontier kills so
# they stay a real decision at every level.

ELF_XP_BONUS = 0.05            # elves learn faster (replaces +1 aether cap)


def hone_xp(unlocked_floor: int) -> int:
    """✦ per honing pass: half a frontier kill."""
    return round(0.5 * xp_per_kill(unlocked_floor))


def sleep_xp_cost(floor: int) -> int:
    """✦ to Sleep past a fight: exactly the kill being skipped."""
    return xp_per_kill(floor)


def scan_xp_cost(floor: int) -> int:
    """✦ for a shard scan when no optics charges remain."""
    return round(0.5 * xp_per_kill(floor))


def gear_level_req(tier: int) -> int:
    """Level required to buy tier-T gear: the band's first floor."""
    return band_start(tier)


def floor_level_req(floor: int) -> int:
    """Level required to enter a floor — loose (design level ≈ floor),
    exists so a fresh climber can't ride the world lift to floor 40."""
    return max(1, floor - 10)


# ── §2 Player baseline ───────────────────────────────────────────────────

def player_atk(level: int, weapon_bonus: int) -> int:
    return 3 * level + weapon_bonus


def player_def(level: int, shield_bonus: int, armor_bonus: int,
               race: str = "") -> int:
    armor = armor_bonus
    if race == "dwarf":
        armor = round(armor * 1.05)
    return 2 * level + shield_bonus + armor


def player_max_hp(level: int) -> int:
    return 40 + 12 * level


# ── §3 Monsters, XP, gold ────────────────────────────────────────────────
# 004 retune: monster ATK slope 4.0 → 3.3 keeps at-level wilds fights under
# 40% of the HP pool on every floor once gear honing (below) is in play.

MONSTER_ATK_SLOPE = 3.3
BAND_INCOME_JUMP = 1.2         # gold/kill ×1.2 per gear band (004 §4.5)


def monster_stats(floor: int) -> tuple[int, int, int]:
    """(ATK, DEF, HP) for a regular monster on `floor`."""
    return round(MONSTER_ATK_SLOPE * floor) + 2, 3 * floor, 12 * floor + 25


def xp_per_kill(floor: int) -> int:
    return 12 * floor          # ±25% applied by the roller


def gold_per_kill(floor: int) -> int:
    """Base gold per kill; the same work pays visibly better each band."""
    tier = gear_tier_for_floor(floor)
    return round(8 * floor * BAND_INCOME_JUMP ** (tier - 1))


def daily_income(floor: int) -> int:
    """Design estimate of net gold per day of at-level hunting on `floor`
    (≈30 fights, healer's tent after most of them). Anchors hone prices
    and the tier price ladder — not paid to anyone directly."""
    return round((gold_per_kill(floor) - 2 * floor * 0.8) * 30)


def xp_need(level: int) -> int:
    """XP to go from `level` to `level+1`: 60 · L^1.5."""
    return round(60 * level ** 1.5)


def fade_multiplier(unlocked_floor: int, floor: int) -> float:
    """Farming >5 floors below your own frontier fades rewards (floor
    0.25). 004 §4.2: keyed to floor progress, never to level — being
    over-leveled on your frontier floor always pays in full."""
    gap = unlocked_floor - floor - 5
    if gap <= 0:
        return 1.0
    return max(0.25, 1.0 - 0.1 * gap)


# ── §5 Wardens ───────────────────────────────────────────────────────────
# 004 §4.1: wardens are derived from the at-level player model (current
# tier set + full hone) so "soloable at-level" holds by construction:
# win 65–85% through floor 30, then HP/ATK ramps fade solo odds smoothly
# toward "bring friends" (<10% well before floor 50).

WARDEN_HP_MULT = 1.9           # × monster HP → a real boss fight (~12 rounds)
WARDEN_DMG_BUDGET = 1.07       # expected damage dealt ÷ player pool
WARDEN_SOFT_FLOOR = 30         # last floor tuned for solo play
WARDEN_HP_RAMP = 40            # HP ×(1+(F−30)/40) past the soft floor
WARDEN_ATK_RAMP = 100          # ATK ×(1+(F−30)/100) past the soft floor


REFERENCE_HONE_LAG = 2         # honing trails the climb by ~2 floors


def reference_hone(floor: int) -> int:
    """Hone level of the design's at-level player: honing trails the
    climb slightly (income funds it with a lag, and fresh climbers in
    band 1 are still finding the bench)."""
    return max(0, floor - band_start(gear_tier_for_floor(floor))
               - REFERENCE_HONE_LAG)


def _at_level_loadout(floor: int) -> tuple[int, int]:
    """(ATK, DEF) of the design's at-level player: level = floor, current
    tier set, honing 2 floors behind. The reference all tuning points at."""
    tier = gear_tier_for_floor(floor)
    hone = reference_hone(floor)
    return (3 * floor + 8 * tier + hone,
            2 * floor + 5 * tier + 7 * tier + 2 * hone)


def warden_stats(floor: int) -> tuple[int, int, int]:
    """Regular Warden (floors not ending in 0), soloable at-level."""
    p_atk, p_def = _at_level_loadout(floor)
    _, m_def, m_hp = monster_stats(floor)
    hp = round(m_hp * WARDEN_HP_MULT)
    if floor > WARDEN_SOFT_FLOOR:
        hp = round(hp * (1 + (floor - WARDEN_SOFT_FLOOR) / WARDEN_HP_RAMP))
    p_dmg = max(1, round(0.75 * p_atk) - m_def // 2)
    rounds = max(3, hp // p_dmg)
    # floors 1–5 ramp in gently: fresh climbers reach these gates with
    # partial kits (the first with the bare shiv), and the first hour
    # must never be a coin flip.
    budget = WARDEN_DMG_BUDGET * min(1.0, 0.5 + 0.1 * floor)
    per_round = budget * player_max_hp(floor) / rounds
    atk = round((per_round + p_def // 2) / 0.75)
    if floor > WARDEN_SOFT_FLOOR:
        atk = round(atk * (1 + (floor - WARDEN_SOFT_FLOOR) / WARDEN_ATK_RAMP))
    return atk, m_def, hp


def warden_xp(floor: int) -> int:
    return 60 * floor


def warden_gold(floor: int) -> int:
    return 80 * floor


@dataclass(frozen=True)
class MilestoneBoss:
    floor: int
    name: str
    atk: int
    dfs: int
    hp: int
    quorum: int
    xp: int
    gold: int


MILESTONES: dict[int, MilestoneBoss] = {m.floor: m for m in [
    MilestoneBoss(10, "Gnarl, the Goblin King", 60, 50, 900, 2, 4_000, 5_000),
    MilestoneBoss(20, "Warlord Skarn", 120, 100, 1_800, 3, 8_000, 10_000),
    MilestoneBoss(30, "The Barrow King", 180, 150, 2_700, 4, 12_000, 15_000),
    MilestoneBoss(40, "Matriarch Vyx", 240, 200, 3_600, 5, 16_000, 20_000),
    MilestoneBoss(50, "Cindermaw the Wyrm", 300, 250, 4_500, 6, 20_000, 25_000),
    MilestoneBoss(60, "Jarl Hrimgar", 360, 300, 5_400, 7, 24_000, 30_000),
    MilestoneBoss(70, "Zephyra, the Storm Queen", 420, 350, 6_300, 8, 28_000, 35_000),
    MilestoneBoss(80, "The Pale Huntsman", 480, 400, 7_200, 9, 32_000, 40_000),
    MilestoneBoss(90, "Malgrim, Herald of the King", 540, 450, 8_100, 10, 36_000, 45_000),
    MilestoneBoss(100, "Vharuk, the Demon King", 650, 550, 12_000, 12, 40_000, 50_000),
]}


def is_milestone(floor: int) -> bool:
    return floor % 10 == 0


# ── §6 Forge catalog ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class GearItem:
    slug: str
    name: str
    flavor: str
    slot: str          # weapon | shield | armor
    tier: int
    bonus: int
    price: int


# 004 §4.4 reprice: tiers 3–10 follow the quadratic ladder
# set(T) ≈ 2·(T−1) days of mid-band tier-(T−1) income, so days-in-tier
# (set + honing) lands on the 6→24 line without requiring the bank meta.
_FORGE_ROWS = [
    # tier, weapon(name, flavor, +ATK), shield, armor, prices (w, s, a)
    (1, ("Pigsticker", "scrap-steel shiv", 8),
        ("Scrapwood Buckler", "", 5), ("Padded Jerkin", "", 7),
        (250, 100, 200)),
    (2, ("Wolfbite", "shock-tip hunting spear", 16),
        ("Ironbound Targe", "", 10), ("Riveted Leather", "", 14),
        (800, 320, 640)),
    (3, ("Emberfang", "dwarf-forged plasma axe", 24),
        ("Dwarven Wall", "powered tower shield", 15), ("Chain Hauberk", "", 21),
        (6_500, 2_600, 5_200)),
    (4, ("Thornsong", "elven mono-edge blade", 32),
        ("Elfmirror", "light-bending", 20), ("Silverthread Mail", "", 28),
        (20_000, 8_000, 16_500)),
    (5, ("Oathkeeper", "knight's arc-blade", 40),
        ("Drakescale Barrier", "", 25), ("Wyrmhide Coat", "", 35),
        (47_000, 18_500, 37_500)),
    (6, ("Grimcleaver", "giant-slaying thunder maul", 48),
        ("Frostguard", "cold-field emitter", 30), ("Dwarven Powerplate", "", 42),
        (92_000, 36_500, 74_000)),
    (7, ("Starfall", "storm-cell saber", 56),
        ("Stormwarden's Aegis", "deflector", 35), ("Stormforged Plate", "", 49),
        (165_000, 65_000, 132_000)),
    (8, ("Duskrender", "phase-etched glaive", 64),
        ("Gloomturner", "cloak-field", 40), ("Nightweave Harness", "", 56),
        (277_000, 110_000, 222_000)),
    (9, ("Kingsbane", "demon-steel railblade", 72),
        ("Hellgate Bulwark", "", 45), ("Demonbone Panoply", "", 63),
        (443_000, 175_000, 356_000)),
    (10, ("Dawnbreaker", "fusion-core blade — the last light of Aldervale", 80),
         ("The Unbroken", "", 50), ("Aegis of the Vale", "", 70),
         (685_000, 271_000, 550_000)),
]


def _build_forge() -> dict[str, GearItem]:
    items: dict[str, GearItem] = {}
    for tier, weapon, shield, armor, (pw, ps, pa) in _FORGE_ROWS:
        for (name, flavor, bonus), slot, price in (
                (weapon, "weapon", pw), (shield, "shield", ps),
                (armor, "armor", pa)):
            slug = name.lower().replace("'", "").replace(" ", "_").replace(
                "—", "").replace(",", "")
            items[slug] = GearItem(slug, name, flavor, slot, tier, bonus, price)
    return items


FORGE: dict[str, GearItem] = _build_forge()

# Tier-0 gate issue, free at creation. Bare-handed ATK at level 1 is 3 vs
# floor-1 monsters at DEF 3 / HP 37 — ~1 damage a round, unwinnable. The
# shiv makes floor 1 hard-but-fair while keeping the ◈250 Pigsticker a
# real first goal. Never sold (forge_tier lists tiers ≥ 1).
STARTER_WEAPON = GearItem(
    "rusted_shiv", "Rusted Shiv",
    "gate-issue salvage steel — barely better than teeth",
    "weapon", 0, 5, 0)
FORGE[STARTER_WEAPON.slug] = STARTER_WEAPON

PAWN_BUYBACK = 0.40


def forge_tier(tier: int) -> list[GearItem]:
    return [g for g in FORGE.values() if g.tier == tier]


def gear_tier_for_floor(floor: int) -> int:
    return min(10, (floor - 1) // 10 + 1)


def band_start(tier: int) -> int:
    """First floor of a gear band: tier 1 → 1, tier 2 → 11, …"""
    return (tier - 1) * 10 + 1


# ── §6b Gear honing (004 §4.3) ───────────────────────────────────────────
# The Forge hones each equipped piece +1 per unlocked floor past the band
# start — turning the +8 tier step into small per-floor steps and adding a
# linear gold sink. Hone levels live on the equipped item (reset on buy).

HONE_SLOTS = ("weapon", "shield", "armor")
HONE_PRICE_PCT = 0.15          # of a frontier day's income, per hone


def max_hone(unlocked_floor: int) -> int:
    """Hone cap: +1 per unlocked floor past the current band's start."""
    return max(0, unlocked_floor - band_start(
        gear_tier_for_floor(unlocked_floor)))


def hone_price(unlocked_floor: int) -> int:
    return max(5, round(HONE_PRICE_PCT * daily_income(unlocked_floor)))


# ── §6 Apothecary & Medlab ───────────────────────────────────────────────

@dataclass(frozen=True)
class ShopItem:
    slug: str
    name: str
    price: int
    effect: str
    note: str = ""


APOTHECARY: dict[str, ShopItem] = {i.slug: i for i in [
    ShopItem("medgel", "Medgel", 25, "heal_25"),
    ShopItem("trauma_kit", "Trauma kit", 120, "heal_80"),
    ShopItem("trollblood_tonic", "Trollblood tonic", 600, "heal_full",
             "usable mid-fight"),
    ShopItem("energy_cell", "Energy cell", 200, "energy_5", "max 1/day"),
    ShopItem("luck_charm", "Luck charm", 300, "luck_today",
             "better loot & present rolls until tomorrow"),
    ShopItem("scout_optics", "Scout optics", 100, "scout_3",
             "sidekick reveals enemy stats, 3 charges"),
]}

# ── §7 Bank, death, lodge, presents ──────────────────────────────────────

BANK_INTEREST_RATE = 0.05           # 5%/day compound, credited on visit
LODGE_PRICE_PER_LEVEL = 10          # gold per night
PVP_ATTACKS_PER_DAY = 2
PVP_XP_BOUNTY_PCT = 0.05            # of victim's level XP need
BEGINNER_PROTECTION_MAX_LEVEL = 5
BEGINNER_MERCY_MAX_LEVEL = 3        # 004 §A.2: PvE death keeps armor,
VAULT_APOLOGY_GOLD = 100            #   takes half gold at levels 1–3
PRESENT_AWAY_HOURS = 20

# present table: (weight, kind)
PRESENT_TABLE = [
    (40, "gold"),          # 50 × level
    (25, "potion"),
    (15, "full_energy"),
    (10, "rumor"),
    (8, "repair_token"),
    (2, "jackpot"),        # rare item or bank doubling capped 1000×level
]

# ── §8 Social economy ────────────────────────────────────────────────────

GRANT_BURN_PCT = 0.10
GRANT_DAILY_CAP_PER_LEVEL = 150
GRANT_MIN_RECEIVER_LEVEL = 5
LETTER_PRICE = 0        # 004 §C.1: talking is free if collaboration is the game
BOARD_PRICE = 10


# ── Races & classes ──────────────────────────────────────────────────────

RACES = {
    "human": "Adaptable: +1 energy cap. Port-town survivors.",
    "elf": "Keen: +5% experience from kills. Their bio-lit forest is floor 23.",
    "dwarf": "Stubborn: +5% armor value. The fusion-halls are floors 11-20.",
    "halfling": "Lucky: better present and loot rolls.",
}

CLASSES = {
    "warrior": "Extra combat option: Shield Wall (soak a round).",
    "sorcerer": "Extra combat option: Sleep Spell (skip a fight for its "
                "experience price).",
    "archer": "Extra combat option: Treeline Shot (first strike).",
}
