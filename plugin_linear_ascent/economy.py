"""Linear Ascent economy — every number derives from vision/economy.md.

Pure functions and data tables only. Content files never carry these
numbers; the loader and engine compute them. Keep the SHAPES when tuning.

VOCABULARY — two words, never interchangeable:
  floor  = the tower, 1-100, shared by every climber.
  level  = the player, personal, its own XP curve.
They are equated in exactly one place — `reference_level()` — which
asserts the tuning convention "the at-level player is level == floor".
Nothing else may hand a floor to a level-typed function.
"""

from __future__ import annotations

import math

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


def gear_player_level_req(tier: int) -> int:
    """PLAYER LEVEL required to buy tier-T gear. Converts from a floor:
    the band's first floor, read as a level via the reference identity."""
    return band_start(tier)


def floor_entry_player_level(floor: int) -> int:
    """PLAYER LEVEL required to enter a floor. Converts from a floor:
    loose leash (level ≈ floor − 10) so a fresh climber can't ride an
    open frontier to floor 40."""
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
# 008: wilds HP is DERIVED from the at-level player's damage so a common
# kill takes ~2.5 rounds on floor 1, +0.5/floor, capped at ~7 — fights are
# quick clicks early and never drag. Wardens keep the old HP budget
# (they must still feel like bosses; see §5).

MONSTER_ATK_SLOPE = 3.3
BAND_INCOME_JUMP = 1.2         # gold/kill ×1.2 per gear band (004 §4.5)

# 013: armor blunts, it never nullifies. A landed hit always chips at
# least ⌈raw/CHIP_DIVISOR⌉ (min 1) through any DEF — pre-013 the
# max(0, raw − DEF/2) formula let floor-1 animals deal literally zero
# to anyone wearing gear, and HP stopped being a cost at all.
CHIP_DIVISOR = 4

WILDS_ROUNDS_BASE = 2.0        # class-average rounds at floor 1 ≈ 2.5
WILDS_ROUNDS_SLOPE = 0.5
WILDS_ROUNDS_MAX = 7.0


def wilds_rounds(floor: int) -> float:
    """Target rounds-to-kill for a common wilds monster."""
    return min(WILDS_ROUNDS_BASE + WILDS_ROUNDS_SLOPE * floor,
               WILDS_ROUNDS_MAX)


def monster_stats(floor: int) -> tuple[int, int, int]:
    """(ATK, DEF, HP) for a common wilds monster on `floor`."""
    atk = round(MONSTER_ATK_SLOPE * floor) + 2
    dfs = 3 * floor
    p_atk, _ = _at_level_loadout(floor)
    p_dmg = max(1, round(0.75 * p_atk) - dfs // 2)
    return atk, dfs, round(p_dmg * wilds_rounds(floor))


# 008: per-encounter specimen roll — same averages, real variance.
# Hard specimens pay more; the tag is visible on the encounter card so
# running from an alpha is an informed choice. Expectations of hp and
# gold multipliers are within a few % of 1.0 (sim gate asserts it).
SPECIMENS: dict[str, dict] = {
    "runt":   {"weight": 25, "hp": 0.55, "atk": 1.0, "gold": 0.45,
               "tag": "gaunt and limping — an easy kill, thin pickings"},
    "common": {"weight": 50, "hp": 1.0, "atk": 1.0, "gold": 1.0, "tag": ""},
    "tough":  {"weight": 20, "hp": 1.4, "atk": 1.0, "gold": 1.4,
               "tag": "scarred and heavy-set — dangerous, but it will pay"},
    "alpha":  {"weight": 5, "hp": 2.0, "atk": 1.2, "gold": 2.3,
               "tag": "an alpha, twice the size — worth a fortune or a "
                      "funeral"},
}


# ── 017 §2: damage types & defense profiles ──────────────────────────────
# Three professions, three damage types. Every monster carries a defense
# profile derived from qualitative content traits — content never carries
# numbers. Tier multipliers cut the FINAL damage of the affected type.

DAMAGE_TYPE = {"warrior": "melee", "archer": "ranged", "sorcerer": "magic"}

TIER_MULT = {"none": 1.0, "low": 0.75, "med": 0.50, "high": 0.25}
TIER_LABEL = {"none": "None", "low": "Low", "med": "Medium", "high": "High"}
_TIER_ORDER = ("none", "low", "med", "high")

# gold bumps: a hard profile pays for the diagnosis it demands
PROFILE_GOLD = {"low": 1.1, "med": 1.25, "high": 1.4}
FLYING_GOLD_MULT = 1.2
BULWARK_GOLD_MULT = 1.5
BULWARK_HP_MULT = 2.2          # the outlast-you enemy

# speed scale (1–10) — priced by the chase model (phase 002); authorable
# and displayed from 001 so content and cards never need a second pass.
SPEED_SLOW = 3
SPEED_NORMAL = 5
SPEED_FAST = 7

WARDEN_PROFILE_FLOOR = 21      # band 3+: wardens get low/low tiers

# ── 017 §2.4: speed and the two-state range model (phase 002) ─────────────
# Fights open at range. Bows and spells carry; steel must close. Every
# probability below is a pure function of the two speeds, so the [i] card
# can show the whole chase without a single hidden number.

PLAYER_BASE_SPEED = 5
ALPHA_SPEED_BONUS = 1          # alphas run +1 on the 1–10 scale
BOW_CLOSE_MULT = 0.6           # bow damage in close quarters
DODGE_CAP_PCT = 12             # speed never becomes the main defense

# Shoes ship in 004 (the Forge ladder). The speed hook lands with the
# chase model so 004 only adds catalog rows here.
SHOE_SPEED: dict[str, int] = {}


def player_speed(p: dict) -> int:
    shoes = (p.get("gear") or {}).get("shoes") or ""
    bonus = SHOE_SPEED.get(shoes, 0)
    # 005: broken boots drag — half the spring until the Forge sees them.
    dur = (p.get("durability") or {}).get("shoes")
    if bonus and dur is not None and dur <= 0:
        bonus //= 2
    return PLAYER_BASE_SPEED + bonus


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def p_close(mspd: int, pspd: int) -> float:
    """End of an at-range round: the monster tries to close the gap."""
    return _clamp(0.25 + 0.15 * (mspd - pspd), 0.05, 0.95)


def p_open(pspd: int, mspd: int) -> float:
    """Open distance from close quarters — the archer's bread and butter."""
    return _clamp(0.50 + 0.15 * (pspd - mspd), 0.05, 0.90)


def p_flee(pspd: int, mspd: int) -> float:
    """Leave the fight. You can walk away from the slow; you cannot
    outrun the wolf without shoes."""
    return _clamp(0.60 + 0.12 * (pspd - mspd), 0.10, 0.95)


def dodge_pct(pspd: int, mspd: int) -> int:
    """Log-decay dodge from speed ADVANTAGE only — capped so armor and
    resist stay the primary defenses by construction."""
    a = max(0, pspd - mspd)
    return min(DODGE_CAP_PCT, round(7 * math.log2(1 + a)))


def tier_up(tier: str) -> str:
    return _TIER_ORDER[min(len(_TIER_ORDER) - 1,
                           _TIER_ORDER.index(tier) + 1)]


def profile_from_traits(traits) -> dict:
    """Defense profile from content traits. Legacy 'armored' → armor_med."""
    prof = {"armor": "none", "resist": "none", "flying": False,
            "bulwark": False, "speed": SPEED_NORMAL}
    for t in traits or ():
        if t.startswith("armor_"):
            prof["armor"] = t[len("armor_"):]
        elif t.startswith("resist_"):
            prof["resist"] = t[len("resist_"):]
        elif t == "armored":               # legacy content, pre-017 tiers
            prof["armor"] = "med"
        elif t == "flying":
            prof["flying"] = True
        elif t == "bulwark":
            prof["bulwark"] = True
        elif t == "slow":
            prof["speed"] = SPEED_SLOW
        elif t == "fast":
            prof["speed"] = SPEED_FAST
    if prof["bulwark"]:
        prof["armor"] = tier_up(prof["armor"])
    return prof


def profile_gold_mult(prof: dict) -> float:
    m = 1.0
    m *= PROFILE_GOLD.get(prof.get("armor", "none"), 1.0)
    m *= PROFILE_GOLD.get(prof.get("resist", "none"), 1.0)
    if prof.get("flying"):
        m *= FLYING_GOLD_MULT
    if prof.get("bulwark"):
        m *= BULWARK_GOLD_MULT
    return m


def typed_damage(dtype: str, raw: int, monster_def: int, prof: dict) -> int:
    """Player damage through a defense profile. Magic ignores flat DEF but
    eats the resist tier; melee/ranged keep raw−DEF/2 and eat the armor
    tier. Anything that CAN hit chips ≥1 (the 013 lesson). The single
    legal zero: melee vs flying — the blade cannot reach."""
    if dtype == "melee" and prof.get("flying"):
        return 0
    if dtype == "magic":
        base = raw
        mult = TIER_MULT[prof.get("resist", "none")]
    else:
        base = raw - monster_def // 2
        mult = TIER_MULT[prof.get("armor", "none")]
    return max(1, round(max(1, base) * mult))


def warden_profile(floor: int) -> dict:
    """Wardens join the system gently: nothing below floor 21, low/low
    tiers after, med/med on milestone bosses (damage checks, not walls)."""
    if floor % 10 == 0:
        return profile_from_traits(("armor_med", "resist_med"))
    if floor >= WARDEN_PROFILE_FLOOR:
        return profile_from_traits(("armor_low", "resist_low"))
    return profile_from_traits(())


def xp_per_kill(floor: int) -> int:
    """012: XP is scarce — always below the kill's gold (8·floor and up)."""
    return 4 * floor           # ±25% applied by the roller


def gold_per_kill(floor: int) -> int:
    """Base gold per kill; the same work pays visibly better each band."""
    tier = gear_tier_for_floor(floor)
    return round(8 * floor * BAND_INCOME_JUMP ** (tier - 1))


def daily_income(floor: int) -> int:
    """Design estimate of net gold per day of at-level hunting on `floor`
    (≈30 fights, a ◈5×floor tent visit every ~3 fights now that chip
    damage is real). Anchors hone prices and the tier price ladder —
    not paid to anyone directly."""
    return round((gold_per_kill(floor) - HEALER_TENT_PER_FLOOR * floor / 3)
                 * 30)


def xp_need(level: int) -> int:
    """XP to go from `level` to `level+1`: 60 · L^1.5."""
    return round(60 * level ** 1.5)


# ── §4b Guild training (012) ─────────────────────────────────────────────
# Levels are bought, never granted: a full XP bar is the license to train,
# the gold fee is the price. One day of at-level income per level — the
# same growth curve everything else is priced in (linear × 1.2 per band).

LEVELUP_BASE_GOLD = 200        # the first level-up, by design


def levelup_gold(level: int) -> int:
    """Gold fee to train from `level` to `level+1` at the Guildhall."""
    return max(LEVELUP_BASE_GOLD, round(daily_income(level) / 10) * 10)


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


def reference_level(floor: int) -> int:
    """The design's at-level player is level == floor (see
    _at_level_loadout). The ONLY place that identity is asserted."""
    return floor


def reference_player_hp(floor: int) -> int:
    """HP of the at-level player used to tune wardens. Deliberately
    NOT player_max_hp(floor) — that reads a floor as a level."""
    return player_max_hp(reference_level(floor))


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
    lvl = reference_level(floor)
    return (player_atk(lvl, 8 * tier + hone),
            player_def(lvl, 5 * tier, 7 * tier + 2 * hone))


def _boss_hp_base(floor: int) -> int:
    """Pre-008 wilds HP curve. Wardens keep this budget so the 008
    fast-kill retune never shrinks a boss — a Warden must still take
    ~12+ rounds while a wilds animal takes 2.5–7."""
    return 12 * floor + 25


def warden_stats(floor: int) -> tuple[int, int, int]:
    """Regular Warden (floors not ending in 0), soloable at-level."""
    p_atk, p_def = _at_level_loadout(floor)
    m_def = 3 * floor
    hp = round(_boss_hp_base(floor) * WARDEN_HP_MULT)
    if floor > WARDEN_SOFT_FLOOR:
        hp = round(hp * (1 + (floor - WARDEN_SOFT_FLOOR) / WARDEN_HP_RAMP))
    p_dmg = max(1, round(0.75 * p_atk) - m_def // 2)
    if floor >= WARDEN_PROFILE_FLOOR:
        # 017: band-3+ wardens carry low tiers (both axes, so every class
        # feels it equally) — the reference damage drops ×0.75 and the
        # rounds/ATK budget below re-tunes itself by construction.
        p_dmg = max(1, round(p_dmg * TIER_MULT["low"]))
    rounds = max(3, hp // p_dmg)
    # floors 1–5 ramp in gently: fresh climbers reach these gates with
    # partial kits (the first with the bare shiv), and the first hour
    # must never be a coin flip.
    budget = WARDEN_DMG_BUDGET * min(1.0, 0.5 + 0.1 * floor)
    per_round = budget * reference_player_hp(floor) / rounds
    atk = round((per_round + p_def // 2) / 0.75)
    if floor > WARDEN_SOFT_FLOOR:
        atk = round(atk * (1 + (floor - WARDEN_SOFT_FLOOR) / WARDEN_ATK_RAMP))
    return atk, m_def, hp


def warden_xp(floor: int) -> int:
    return 25 * floor          # 012: below warden_gold — XP is scarce


def warden_gold(floor: int) -> int:
    return 80 * floor


# ── §5b The shared Warden (007 §3, rebuilt by 022 §001) ──────────────────
# ALL 100 Wardens are shared — one list of bosses for the whole world.
# The keep fight is a REAL fight: every wound you leave persists in the
# world HP pool; pool at zero opens the floor for everyone. Floors 1–30
# are tuned so one strong at-level player can finish the job alone
# (small pool, regen below one blade's output); deeper floors take a
# rally. 022/002 re-derives both curves from the coordination model —
# the two functions below are the 001 stopgap.

WARDEN_WORLD_HP_MULT = 4            # pool = solo-fight HP × this (F > 30)
WARDEN_WORLD_HP_MULT_SOLO = 1.5     # …× this inside the solo band (F ≤ 30)
WARDEN_WORLD_REGEN_HOURLY = 0.08    # of max HP, back per hour (F > 30)
WARDEN_WORLD_REGEN_SOLO = 0.03      # …inside the solo band (F ≤ 30)


def world_warden_hp_mult(floor: int) -> float:
    return (WARDEN_WORLD_HP_MULT_SOLO if floor <= WARDEN_SOFT_FLOOR
            else WARDEN_WORLD_HP_MULT)


def world_warden_regen_hourly(floor: int) -> float:
    return (WARDEN_WORLD_REGEN_SOLO if floor <= WARDEN_SOFT_FLOOR
            else WARDEN_WORLD_REGEN_HOURLY)


def world_warden_hp(floor: int) -> int:
    return round(warden_stats(floor)[2] * world_warden_hp_mult(floor))


# the reward pool scales with the HP pool and splits by damage dealt,
# so the payout per energy matches the solo-tuned warden.
def world_warden_reward_mult(floor: int) -> float:
    return world_warden_hp_mult(floor)


# 022/001: a fallen Warden can be re-fought at its keep as an ECHO —
# half pay, no world effect, pure training and story.
WARDEN_ECHO_MULT = 0.5


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


# 012: milestone XP = 0.3 × gold — XP scarcer than gold, in all places.
MILESTONES: dict[int, MilestoneBoss] = {m.floor: m for m in [
    MilestoneBoss(10, "Gnarl, the Goblin King", 60, 50, 900, 2, 1_500, 5_000),
    MilestoneBoss(20, "Warlord Skarn", 120, 100, 1_800, 3, 3_000, 10_000),
    MilestoneBoss(30, "The Barrow King", 180, 150, 2_700, 4, 4_500, 15_000),
    MilestoneBoss(40, "Matriarch Vyx", 240, 200, 3_600, 5, 6_000, 20_000),
    MilestoneBoss(50, "Cindermaw the Wyrm", 300, 250, 4_500, 6, 7_500, 25_000),
    MilestoneBoss(60, "Jarl Hrimgar", 360, 300, 5_400, 7, 9_000, 30_000),
    MilestoneBoss(70, "Zephyra, the Storm Queen", 420, 350, 6_300, 8, 10_500, 35_000),
    MilestoneBoss(80, "The Pale Huntsman", 480, 400, 7_200, 9, 12_000, 40_000),
    MilestoneBoss(90, "Malgrim, Herald of the King", 540, 450, 8_100, 10, 13_500, 45_000),
    MilestoneBoss(100, "Vharuk, the Demon King", 650, 550, 12_000, 12, 15_000, 50_000),
]}


def is_milestone(floor: int) -> bool:
    return floor % 10 == 0


# ── §6 Forge catalog ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class GearItem:
    slug: str
    name: str
    flavor: str
    slot: str          # weapon | shield | armor | shoes
    tier: int
    bonus: int
    price: int
    # 017/004: the buying game — three class weapon lines, mid rungs,
    # the shoes ladder, and the Arcanum's focuses.
    line: str = ""     # weapon/focus owner class ("" = shared gear)
    rung: float = 0.0  # 1, 1.5, 2 … (0 = starter / pre-004 semantics)
    speed: int = 0     # shoes: +speed on the 1–10 scale
    level: int = 0     # explicit level gate override (shoes ladder)


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


# ── 004 §3.1: the mid rungs and the three weapon lines ──────────────────
# Between every tier T and T+1 a rung T.5: bonus = midpoint, price =
# geometric mean (rounded to ◈10) — days-to-afford stays smooth. Archer
# and sorcerer lines mirror the warrior numbers rung for rung; only the
# names differ. Names below; numbers all derive from _FORGE_ROWS.

_WARRIOR_MIDS = {
    1.5: ("Iron Sword", "honest forge-iron, honest weight"),
    2.5: ("Bloodgroove Falchion", "the channel drinks so the edge doesn't"),
    3.5: ("Seared Cleaver", "quench-burnt edge, still warm"),
    4.5: ("Moonwake Saber", "elven mono-edge, second polish"),
    5.5: ("Bannerbreak Blade", "knight steel that outlived its knight"),
    6.5: ("Ironstorm Maul", "half thunder, all weight"),
    7.5: ("Tempest Edge", "storm-cell steel, twice charged"),
    8.5: ("Night-Iron Glaive", "phase-etched — light won't hold it"),
    9.5: ("Kingsguard Razor", "demon-steel, palace-forged"),
}

_ARCHER_WEAPONS = {
    1: ("Ashwood Bow", "straight-grain ash, dependable"),
    1.5: ("Sinew-Backed Bow", "backed for the longer throw"),
    2: ("Wolfsight Recurve", "shock-tip recurve, keen at distance"),
    2.5: ("Horncore Bow", "horn core under tension"),
    3: ("Emberflight Longbow", "dwarf-lathed, plasma nock"),
    3.5: ("Cinderfletch", "burns as it leaves the string"),
    4: ("Thornstring", "elven mono-fiber string"),
    4.5: ("Silverlimb", "silverthread limbs, no creak"),
    5: ("Oathstring", "knight's arc-bow"),
    5.5: ("Drakespine Recurve", "ribbed with wyrm bone"),
    6: ("Grimflight", "a giant-slaying ballista in one hand"),
    6.5: ("Frosthawk Bow", "cold-field nock, quiet release"),
    7: ("Starshot", "storm-cell compound bow"),
    7.5: ("Stormnock", "twice-charged limbs"),
    8: ("Duskwhisper", "phase-etched — the string makes no sound"),
    8.5: ("Gloamreach", "cloak-field limbs"),
    9: ("Kingspiercer", "demon-steel railbow"),
    9.5: ("Hellbarb Bow", "barbed for what won't die"),
    10: ("Dawnstring", "fusion-core bow — the last light, bent double"),
}

_SORCERER_WEAPONS = {
    1: ("Tallowwood Staff", "candle-soft wood that holds a spark"),
    1.5: ("Coalglass Staff", "coalglass core, banked heat"),
    2: ("Stormtwig Staff", "green wood that remembers lightning"),
    2.5: ("Embervein Staff", "ember veins under the bark"),
    3: ("Ashspire Staff", "dwarf-kilned, draws like a chimney"),
    3.5: ("Cinderheart Staff", "the knot at its heart still burns"),
    4: ("Thornweave Staff", "elven mono-fiber wrap"),
    4.5: ("Silverbough Staff", "silverthread graft, cold light"),
    5: ("Oathflame Staff", "knight's arc-focus"),
    5.5: ("Wyrmtongue Staff", "speaks fire back"),
    6: ("Grimspark Staff", "giant-slaying thunder rod"),
    6.5: ("Frostbrand Staff", "a cold-field emitter on a stave"),
    7: ("Starcaller Staff", "storm-cell core"),
    7.5: ("Stormcrown Staff", "twice-charged crown"),
    8: ("Duskbinder Staff", "phase-etched heartwood"),
    8.5: ("Nightwell Staff", "draws from somewhere dark"),
    9: ("Kingscourge Staff", "demon-steel core"),
    9.5: ("Hellrune Staff", "runes that shouldn't hold — and do"),
    10: ("Dawncaller Staff", "fusion-core staff — the last light answers"),
}

_SHIELD_MIDS = {
    1.5: ("Banded Kite", "iron bands over ashwood"),
    2.5: ("Boarhide Aspis", "boiled hide on a boss of iron"),
    3.5: ("Kilnplate Round", "kiln-fired ceramic facing"),
    4.5: ("Moonglass Targe", "light bends around the rim"),
    5.5: ("Wyvernbone Wall", "ribbed like the thing it stopped"),
    6.5: ("Frostrim Tower", "the rim sweats cold"),
    7.5: ("Tempest Aegis", "a deflector wound twice"),
    8.5: ("Gloamguard", "the cloak-field hums"),
    9.5: ("Hellgrate Shield", "grated demon-steel, still warm"),
}

_ARMOR_MIDS = {
    1.5: ("Studded Jack", "canvas and rivets, better than luck"),
    2.5: ("Boiled Cuirass", "leather boiled to plank"),
    3.5: ("Kilnforged Scale", "ceramic scale, kiln-set"),
    4.5: ("Moonthread Weave", "silverthread, double weave"),
    5.5: ("Drakehide Plate", "hide over plate over hide"),
    6.5: ("Frostbound Carapace", "powerplate with a cold heart"),
    7.5: ("Tempestweave", "storm-cell mesh"),
    8.5: ("Gloamshroud Mail", "nightweave, second shadow"),
    9.5: ("Hellforged Panoply", "demonbone, re-forged and obedient"),
}

# The Arcanum's focuses: the sorcerer's shield-slot. Whole tiers only —
# the Arcanum stocks ten rungs and no mids (§3.4).
_FOCUS_NAMES = {
    1: ("Glass Bead Focus", "a bead that bends the spark"),
    2: ("Ironglass Prism", "smoked prism in an iron claw"),
    3: ("Kilnfire Lens", "dwarf-kilned, drinks the flare"),
    4: ("Moonwater Orb", "elven glass, always cool"),
    5: ("Oathlight Prism", "knight-cut, holds a vow of light"),
    6: ("Grimlight Core", "a thunder rod's stolen heart"),
    7: ("Starwell Lens", "storm-cell condenser"),
    8: ("Duskmirror Orb", "phase-etched — it reflects later"),
    9: ("Kingseye Prism", "demon-steel setting, unblinking"),
    10: ("Dawnprism", "the last light, folded"),
}

# 004 §3.3: the shoes ladder — explicit level gates (3/11/21/41/61), paid
# gear, wears per chase action once 005 lands. Speed feeds §2.4 directly.
_SHOE_ROWS = [
    (1, "Cobbled Boots", "resoled twice, they'll hold", 1, 500, 3),
    (2, "Wayfarer's Treads", "road-sworn leather, spring in the heel",
     2, 3_500, 11),
    (3, "Chasewind Boots", "elven soles — the ground agrees to help",
     3, 24_000, 21),
    (4, "Skyline Striders", "storm-cell arches, half a jump each step",
     4, 120_000, 41),
    (5, "Stormstep Greaves", "the thunder arrives after you do",
     5, 400_000, 61),
]


def _slugify(name: str) -> str:
    return name.lower().replace("'", "").replace(" ", "_").replace(
        "—", "").replace(",", "").replace("-", "_")


def _gmean_price(a: int, b: int) -> int:
    return round(math.sqrt(a * b) / 10) * 10


def _build_forge() -> dict[str, GearItem]:
    items: dict[str, GearItem] = {}

    def put(name: str, flavor: str, slot: str, rung: float, bonus: int,
            price: int, line: str = "", speed: int = 0, level: int = 0):
        slug = _slugify(name)
        assert slug not in items, f"forge slug collision: {slug}"
        items[slug] = GearItem(slug, name, flavor, slot, int(rung), bonus,
                               price, line=line, rung=float(rung),
                               speed=speed, level=level)

    rows = {t: (w, s, a, p) for t, w, s, a, p in _FORGE_ROWS}
    for tier, (w, s, a, (pw, ps, pa)) in rows.items():
        put(w[0], w[1], "weapon", tier, w[2], pw, line="warrior")
        put(s[0], s[1], "shield", tier, s[2], ps)
        put(a[0], a[1], "armor", tier, a[2], pa)
    for t in range(1, 10):
        w1, s1, a1, (pw1, ps1, pa1) = rows[t]
        w2, s2, a2, (pw2, ps2, pa2) = rows[t + 1]
        r = t + 0.5
        n, f = _WARRIOR_MIDS[r]
        put(n, f, "weapon", r, (w1[2] + w2[2]) // 2,
            _gmean_price(pw1, pw2), line="warrior")
        n, f = _SHIELD_MIDS[r]
        put(n, f, "shield", r, (s1[2] + s2[2]) // 2, _gmean_price(ps1, ps2))
        n, f = _ARMOR_MIDS[r]
        put(n, f, "armor", r, (a1[2] + a2[2]) // 2, _gmean_price(pa1, pa2))

    # the other two weapon lines mirror the warrior numbers rung for rung
    warrior = {g.rung: g for g in items.values()
               if g.slot == "weapon" and g.line == "warrior"}
    for line, table in (("archer", _ARCHER_WEAPONS),
                        ("sorcerer", _SORCERER_WEAPONS)):
        for r, (n, f) in table.items():
            ref = warrior[float(r)]
            put(n, f, "weapon", float(r), ref.bonus, ref.price, line=line)

    shields = {g.rung: g for g in items.values()
               if g.slot == "shield" and g.rung == int(g.rung)}
    for t, (n, f) in _FOCUS_NAMES.items():
        ref = shields[float(t)]
        put(n, f, "shield", float(t), ref.bonus, ref.price, line="sorcerer")

    for t, n, f, spd, price, lvl in _SHOE_ROWS:
        put(n, f, "shoes", float(t), 0, price, speed=spd, level=lvl)
    return items


FORGE: dict[str, GearItem] = _build_forge()

SHOE_SPEED.update({g.slug: g.speed for g in FORGE.values()
                   if g.slot == "shoes"})

# Tier-0 gate issue, free at creation. Bare-handed ATK at level 1 is 3 vs
# floor-1 monsters at DEF 3 / HP 37 — ~1 damage a round, unwinnable. The
# basic weapon makes floor 1 hard-but-fair while keeping the ◈250 tier-1
# purchase a real first goal. Never sold (forge_tier lists tiers ≥ 1).
# 017 §1: the basic weapon is a floor, not a phase — one per class, it
# never degrades, never runs out, is never lost. rusted_shiv stays as the
# pre-class / legacy-doc slug (same stats as the warrior sword).
STARTER_WEAPON = GearItem(
    "rusted_shiv", "Rusted Shiv",
    "gate-issue salvage steel — barely better than teeth",
    "weapon", 0, 5, 0)
FORGE[STARTER_WEAPON.slug] = STARTER_WEAPON

CLASS_STARTERS: dict[str, GearItem] = {
    "warrior": GearItem(
        "rusted_sword", "Rusted Sword",
        "gate-issue salvage steel, honest weight — it will never leave you",
        "weapon", 0, 5, 0, line="warrior"),
    "archer": GearItem(
        "basic_bow", "Basic Bow",
        "gate-issue laminate bow — the quiver of plain arrows never empties",
        "weapon", 0, 5, 0, line="archer"),
    "sorcerer": GearItem(
        "worn_staff", "Worn Wooden Staff",
        "gate-issue focus wood, thumb-polished — the spark answers you, always",
        "weapon", 0, 5, 0, line="sorcerer"),
}
for _g in CLASS_STARTERS.values():
    FORGE[_g.slug] = _g


def class_starter(clazz: str) -> GearItem:
    return CLASS_STARTERS.get(clazz or "", STARTER_WEAPON)

PAWN_BUYBACK = 0.40    # pre-006 flat rate; 006 makes it the band centre


def pawn_rate(day: int) -> float:
    """006 §3.8: the broker's mood — deterministic from the world day,
    uniform 25–55%. Everyone sees the same rate; patience is a trade."""
    x = (day * 2654435761) % 2 ** 32
    return 0.25 + 0.30 * (x / 2 ** 32)


def forge_tier(tier: int) -> list[GearItem]:
    return [g for g in FORGE.values() if g.tier == tier]


def gear_rungs(slot: str, line: str = "") -> list[GearItem]:
    """All PAID rungs of a slot (and weapon/focus line), rung-sorted."""
    return sorted((g for g in FORGE.values()
                   if g.slot == slot and g.line == line and g.rung >= 1),
                  key=lambda g: g.rung)


def weapon_line(line: str) -> list[GearItem]:
    return gear_rungs("weapon", line)


def rung_player_level_req(g: GearItem) -> int:
    """PLAYER LEVEL gate for a forge rung. Converts from a floor:
    rung T at band_start(T), T.5 at band_start(T)+5 — the shoes ladder
    carries explicit gates instead."""
    if g.level:
        return g.level
    t = int(g.rung)
    return band_start(t) + (5 if g.rung != t else 0)


# ── 004 §3.2: off-class stopgap gear ─────────────────────────────────────
# Any class can buy the previous-rung weapon of another line: ×3 price,
# ×0.5 damage, a 25% miss that eats the round, never hones, and a bow in
# off-class hands burns bought arrows. A tool for breaking a hard
# counter, priced so it can never be a build.

OFF_CLASS_PRICE_MULT = 3
OFF_CLASS_DMG_MULT = 0.5
OFF_CLASS_MISS = 0.25
ARROW_PACK_SIZE = 10
ARROW_PACK_PRICE = 120

ARCANUM_LEVEL = 6              # 004 §3.4: the mage shop's unlock level

# 007 town readability: every not-day-1 door reads its level from the
# square. Relay opens once a name means something (letters, grants at
# 5 anyway); the fields once a climber can afford to lose a scrap.
RELAY_LEVEL = 3
FIELDS_LEVEL = 5


def off_class_price(g: GearItem) -> int:
    return g.price * OFF_CLASS_PRICE_MULT


def line_twin(g: GearItem, line: str) -> GearItem | None:
    """The same rung of another weapon line. The three lines mirror each
    other rung for rung — same bonus, same price — so trading a piece for
    its twin costs its holder nothing."""
    if g.slot != "weapon" or g.rung < 1 or not line or g.line == line:
        return None
    for other in weapon_line(line):
        if other.rung == g.rung:
            return other
    return None


def off_class_offer(line: str, level: int) -> GearItem | None:
    """The one off-class weapon on the rack: the rung BELOW the highest
    this level unlocks in `line` (the first rung when nothing is below)."""
    unlocked = [g for g in weapon_line(line) if rung_player_level_req(g) <= level]
    if not unlocked:
        return None
    return unlocked[-2] if len(unlocked) >= 2 else unlocked[0]


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


# ── §6d Durability (005 §3.5) ────────────────────────────────────────────
# Power is a running cost, not a plateau. Every PAID piece carries a
# use pool sized so a fresh piece lasts ROUGHLY a week of at-level
# hunting (≈30 fights × ~6 rounds a day — the same model daily_income
# anchors on). Pools GROW with tier but repair scales with price, so
# the gold-per-use climbs anyway: the running-cost tax rises smoothly
# from ~8% of daily income at T1 to ~12% at T10 and never breaks a
# piece inside one day. (The pre-plan's "better gear wears faster"
# pool CURVE failed the ≤20%-of-income gate by up to 14× at T10 —
# the tax keeps the intent, the pool direction had to flip.)
# Basic (tier-0) gear never wears; broken means half strength, never
# helpless.

DURABILITY_BASE = 1300
DURABILITY_GROWTH = 0.25
REPAIR_PRICE_PCT = 0.20        # of item price × missing fraction
DURABILITY_SLOTS = ("weapon", "shield", "armor", "shoes")


def durability_pool(tier: float) -> int:
    """Uses in a fresh piece of this tier (mids sit between wholes)."""
    t = max(1.0, float(tier))
    return round(DURABILITY_BASE * (1 + DURABILITY_GROWTH * (t - 1)))


def item_pool(item: GearItem) -> int:
    """Pool for a specific piece — mid-rungs (rung 1.5, 2.5…) wear a
    touch faster than the whole tier below them, so the rung is the
    truth when the item carries one."""
    return durability_pool(item.rung or item.tier)


def repair_price(item: GearItem, missing_frac: float) -> int:
    """The Forge mends for a fraction of what the smith charged."""
    return max(1, round(REPAIR_PRICE_PCT * item.price
                        * max(0.0, min(1.0, missing_frac))))


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

# ── 006 §3.7: the relic catalog v1 ───────────────────────────────────────
# Law: one dramatic effect + one hard limitation; no permanent stats.
# Prices anchor to daily_income(player frontier) — a relic always costs
# the same fraction of your hunting day, wherever you are on the tower.

@dataclass(frozen=True)
class Relic:
    slug: str
    name: str
    effect: str            # the one dramatic thing it does (shown verbatim)
    limit: str             # the one hard limitation (shown verbatim)
    di: float              # price = pretty(di × daily_income(frontier))
    floor: int             # appears in stock from this unlocked floor
    shop: str              # "forge" | "arcanum" | "apothecary"
    count: int = 1         # units per purchase (arrow packs, net packs)
    clazz: str = ""        # class-locked purchase ("" = anyone)
    hold1: bool = False    # own at most one at a time
    group: str = ""        # per-fight exclusivity ("life")


RELICS: dict[str, Relic] = {r.slug: r for r in [
    # 010 retune (2026-07-28): quivers 0.3→0.2 DI, piercing 0.5→0.35.
    # The stacked-drain gate charges each class one wall-push a day
    # (~3 special arrows); at the old prices the push stacked repairs
    # + the death line past the 40%-of-daily-income ceiling.
    Relic("poison_arrows", "Poisoned Arrows",
          "true damage for 3 rounds — seeps past any plate",
          "no stacking; Wardens and venomproof things shrug it off",
          0.2, 6, "forge", count=5),
    Relic("slowing_arrows", "Slowing Arrows",
          "the target drops 2 speed for the fight — the kiting answer",
          "wears off with the fight; wasted on anything already slow",
          0.2, 8, "forge", count=5),
    Relic("piercing_arrows", "Piercing Arrows",
          "the shot ignores armor tiers entirely",
          "five to a quiver, archer hands only",
          0.35, 11, "forge", count=5, clazz="archer"),
    Relic("fire_arrows", "Fire Arrows",
          "+50% burst on the shot; burns regeneration out",
          "plate still turns fire-tipped shafts like any arrow",
          0.2, 11, "forge", count=5),
    Relic("weapon_oil", "Weapon Oil",
          "your next 10 strikes hit +25% — steel or string, always works",
          "ten strikes, then the flask is gone",
          0.2, 6, "forge"),
    Relic("entangling_net", "Entangling Net",
          "the monster loses its round tangled — it cannot close or flee",
          "three to a pack; a Warden tears through it instantly",
          0.25, 11, "forge", count=3, clazz="warrior"),
    Relic("sky_hook", "Sky-Hook",
          "your steel reaches the airborne for this whole fight",
          "five uses a hook, one burned per fight",
          0.4, 11, "forge", count=5, clazz="warrior"),
    # 010 retune (2026-07-28): vials 0.3→0.1 DI. One vial is one FIGHT,
    # so at 0.3 the mage's wall-push cost 3.6× the warrior's net and
    # broke the stacked-drain ceiling at every band; 0.1 puts all three
    # classes' per-push cost in the same 0.08–0.12 DI lane.
    Relic("strip_potion", "Resistance-Strip Potion",
          "dissolves the target's spellguard for the fight",
          "one fight, one vial",
          0.1, 6, "arcanum", clazz="sorcerer"),
    Relic("curse_scroll", "Curse Scroll",
          "halves the target's plate for the fight",
          "one fight, one scroll",
          0.1, 6, "arcanum", clazz="sorcerer"),
    Relic("polymorph_dust", "Polymorph Dust",
          "the monster becomes a harmless critter — the fight simply ends",
          "no loot, no XP, never works on Wardens; one pinch",
          1.2, 21, "arcanum", clazz="sorcerer"),
    Relic("veil_draught", "Veil Draught",
          "nothing can touch you until your first attack lands",
          "one fight; only one life-guard works per fight",
          0.5, 21, "apothecary", group="life"),
    Relic("golden_apple", "Golden Apple",
          "an overshield of twice your health, and all damage halved",
          "one fight, the shield rots as the rounds pass; one life-guard "
          "per fight",
          0.8, 21, "apothecary", group="life"),
    Relic("reincarnation_spell", "Weapon Reincarnation Spell",
          "death takes NOTHING — and every weapon and armor piece "
          "repairs to full",
          "consumed by the death it cancels; each SPARE spell you hoard "
          "rolls 50% lost",
          # 0.5 DI: EV-positive against an unprotected death from band 2
          # on (the intended buy) — while the spare-spell leak keeps
          # hoarding 3+ strictly worse than banking the gold.
          0.5, 11, "apothecary"),
    Relic("stone_of_undying", "Stone of Undying",
          "cancels the death itself — you stand back up mid-fight",
          "revive at 30% health; hold exactly one; consumed",
          1.5, 21, "apothecary", hold1=True, group="life"),
    Relic("severing_word", "Severing Word",
          "speak it and any non-Warden monster simply ends",
          "one use; hold exactly one",
          8.0, 31, "arcanum", hold1=True),
]}

QUIVER_SLUGS = ("poison_arrows", "slowing_arrows", "piercing_arrows",
                "fire_arrows")
LIFE_GROUP = tuple(r.slug for r in RELICS.values() if r.group == "life")

OIL_STRIKES = 10
OIL_MULT = 1.25
FIRE_ARROW_MULT = 1.5
POISON_ROUNDS = 3
SLOW_ARROW_DELTA = 2
STONE_REVIVE_PCT = 0.30
APPLE_SHIELD_MULT = 2.0
APPLE_DECAY = 0.20             # the overshield rots 20% of itself a round

# 006 §3.6 death economy (level > BEGINNER_MERCY_MAX_LEVEL, unprotected)
DEATH_GOLD_MIN = 0.40
DEATH_GOLD_MAX = 0.60
DEATH_WEAPON_LOSS = 0.20       # each paid weapon rolls: gone for good
DEATH_DURABILITY_HIT = 0.50    # armor/shield/shoes lose half a pool
SPARE_SPELL_LEAK = 0.50        # each spare Reincarnation Spell on a
                               # protected death

# 006 §3.8 faucet cuts — bought relics need the free charms scarce.
# Gate: ≤ 1/3 of the pre-006 rates (alpha was 30%, warden 40%).
ALPHA_CHARM_PCT = 10
WARDEN_CHARM_PCT = 12


def _pretty(n: float) -> int:
    """Shop-window rounding: two leading digits, zeros after."""
    n = max(1, round(n))
    if n < 100:
        return int(round(n / 5) * 5) or n
    step = 10 ** (len(str(n)) - 2)
    return int(round(n / step) * step)


def relic_price(slug: str, frontier: int) -> int:
    r = RELICS[slug]
    return _pretty(r.di * daily_income(max(1, frontier)))


def relic_stock(shop: str, frontier: int, clazz: str) -> list[Relic]:
    """What this shop shows this player, catalog order."""
    return [r for r in RELICS.values()
            if r.shop == shop and frontier >= r.floor
            and (not r.clazz or r.clazz == clazz)]


# ── §6c Healing (008, repriced by 013) ───────────────────────────────────
# The ladder: stew (2g, +5 HP, repeatable) → healer's tent (5×floor,
# full — still below one kill's gold, but a real bite of it now that
# armor chips instead of nullifying) → a Lodge night (+20 HP at dawn)
# → potions for mid-fight emergencies. HP is meant to be the scarcer
# currency: gold flows every kill, health only trickles back.

STEW_PRICE = 2
STEW_HEAL_HP = 5
LODGE_NIGHT_HEAL_HP = 20
HEALER_TENT_PER_FLOOR = 5      # full heal: ◈ 5 × floor (was 2 pre-013)

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

# 009: three lines climb the Ascent — the halfling listing is retired
# (doc v4 re-registers existing halflings as human).
RACES = {
    "human": "Adaptable: +1 energy cap. Port-town survivors.",
    "elf": "Keen: +5% experience from kills. Their bio-lit forest is floor 23.",
    "dwarf": "Stubborn: +5% armor value. The fusion-halls are floors 11-20.",
}

CLASSES = {
    "warrior": "Extra combat option: Shield Wall (soak a round).",
    "sorcerer": "Extra combat option: Sleep Spell (skip a fight for its "
                "experience price).",
    "archer": "Extra combat option: Treeline Shot (first strike).",
}
