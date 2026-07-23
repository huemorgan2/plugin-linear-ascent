"""Linear Ascent economy — every number derives from vision/economy.md.

Pure functions and data tables only. Content files never carry these
numbers; the loader and engine compute them. Keep the SHAPES when tuning.
"""

from __future__ import annotations

from dataclasses import dataclass

# ── §1 Meters ────────────────────────────────────────────────────────────

ENERGY_REGEN_MIN = 45          # 1 energy per 45 minutes
MANA_REGEN_MIN = 90            # 1 mana per 90 minutes
ENERGY_BASE_CAP = 24
MANA_BASE_CAP = 10

COST_WILDS_FIGHT = 1
COST_WARDEN_ATTEMPT = 3
COST_BOSS_COMMIT = 5
COST_PVP_ATTACK = 3
COST_SIDEKICK_SCOUT_MANA = 2


def energy_cap(level: int, race: str = "") -> int:
    cap = ENERGY_BASE_CAP + level // 10
    if race == "human":
        cap += 1
    return cap


def mana_cap(level: int, race: str = "") -> int:
    cap = MANA_BASE_CAP + level // 20
    if race == "elf":
        cap += 1
    return cap


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

def monster_stats(floor: int) -> tuple[int, int, int]:
    """(ATK, DEF, HP) for a regular monster on `floor`."""
    return 4 * floor + 2, 3 * floor, 12 * floor + 25


def xp_per_kill(floor: int) -> int:
    return 12 * floor          # ±25% applied by the roller


def gold_per_kill(floor: int) -> int:
    return 8 * floor           # ±50% applied by the roller


def xp_need(level: int) -> int:
    """XP to go from `level` to `level+1`: 60 · L^1.5."""
    return round(60 * level ** 1.5)


def fade_multiplier(level: int, floor: int) -> float:
    """Fighting >5 floors below level fades rewards, floor 0.25."""
    gap = level - floor - 5
    if gap <= 0:
        return 1.0
    return max(0.25, 1.0 - 0.1 * gap)


# ── §5 Wardens ───────────────────────────────────────────────────────────

def warden_stats(floor: int) -> tuple[int, int, int]:
    """Regular Warden (floors ending 1–9), soloable at-level."""
    return 5 * floor, 4 * floor, 60 * floor


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
        (2_500, 1_000, 2_000)),
    (4, ("Thornsong", "elven mono-edge blade", 32),
        ("Elfmirror", "light-bending", 20), ("Silverthread Mail", "", 28),
        (7_500, 3_000, 6_000)),
    (5, ("Oathkeeper", "knight's arc-blade", 40),
        ("Drakescale Barrier", "", 25), ("Wyrmhide Coat", "", 35),
        (22_000, 9_000, 18_000)),
    (6, ("Grimcleaver", "giant-slaying thunder maul", 48),
        ("Frostguard", "cold-field emitter", 30), ("Dwarven Powerplate", "", 42),
        (60_000, 24_000, 48_000)),
    (7, ("Starfall", "storm-cell saber", 56),
        ("Stormwarden's Aegis", "deflector", 35), ("Stormforged Plate", "", 49),
        (160_000, 64_000, 130_000)),
    (8, ("Duskrender", "phase-etched glaive", 64),
        ("Gloomturner", "cloak-field", 40), ("Nightweave Harness", "", 56),
        (420_000, 170_000, 340_000)),
    (9, ("Kingsbane", "demon-steel railblade", 72),
        ("Hellgate Bulwark", "", 45), ("Demonbone Panoply", "", 63),
        (1_100_000, 440_000, 880_000)),
    (10, ("Dawnbreaker", "fusion-core blade — the last light of Aldervale", 80),
         ("The Unbroken", "", 50), ("Aegis of the Vale", "", 70),
         (2_800_000, 1_100_000, 2_200_000)),
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
PAWN_BUYBACK = 0.40


def forge_tier(tier: int) -> list[GearItem]:
    return [g for g in FORGE.values() if g.tier == tier]


def gear_tier_for_floor(floor: int) -> int:
    return min(10, (floor - 1) // 10 + 1)


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
    ShopItem("aether_philtre", "Aether philtre", 150, "mana_3", "max 1/day"),
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
LETTER_PRICE = 5
BOARD_PRICE = 25


# ── Races & classes ──────────────────────────────────────────────────────

RACES = {
    "human": "Adaptable: +1 energy cap. Port-town survivors.",
    "elf": "Keen: +1 aether cap. Their bio-lit forest is floor 23.",
    "dwarf": "Stubborn: +5% armor value. The fusion-halls are floors 11-20.",
    "halfling": "Lucky: better present and loot rolls.",
}

CLASSES = {
    "warrior": "Extra combat option: Shield Wall (soak a round).",
    "sorcerer": "Extra combat option: Sleep Spell (2 aether, skip a fight).",
    "archer": "Extra combat option: Treeline Shot (first strike).",
}
