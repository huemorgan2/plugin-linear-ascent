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

ENERGY_REGEN_MIN = 45          # 1 energy per 45 minutes — the WAKING pace
ENERGY_BASE_CAP = 24

# ── 037: active sleep — the fast clock ───────────────────────────────────
# Awake, the bar ticks at ENERGY_REGEN_MIN and wounds wait for dawn.
# Sleeping runs the clock faster — and it is the ONLY daytime healing
# (the 022/004 dawn law stands for the waking). The Lodge bunk is paid
# and exactly DOUBLE the waking pace; a hollow in the fields is free,
# slower, and anyone hunting the fields can still find you.
SLEEP_ENERGY_MULT = {"fields": 1.5, "lodge": 2.0}
# minutes of sleep to mend one FULL HP bar, whatever the bar's size
SLEEP_HP_FULL_MIN = {"fields": 240, "lodge": 120}

COST_WILDS_FIGHT = 1
COST_WARDEN_ATTEMPT = 3
# every swing at a Warden — flat across floors, on top of the join cost,
# so the keep drains the energy bar instead of being a free grind.
COST_WARDEN_STRIKE = 3
COST_BOSS_COMMIT = 5
COST_PVP_ATTACK = 3

# 022/002: the level cap. Levels carry the first weeks; gear carries the
# climb. Everything priced "per level" beyond 30 is priced per gear band
# or per floor instead.
LEVEL_CAP = 30

# ── 046: the pillar — one growth law for the whole tower ─────────────────
# Every power number in the game is its floor-1 anchor carried up ONE
# exponential: ×PILLAR per floor. Two derived exponents hang off it:
# income rides PILLAR/PACE_DISCOUNT, so each floor pays slightly less
# than its costs grow and days-per-floor stretches ×PACE_DISCOUNT — the
# climb slows exponentially; warden HP rides PILLAR×WARDEN_RISE, so the
# gates outgrow their own floor's monsters 2%/floor compounding.
# Floor 1 is byte-identical to the pre-046 game: only the SLOPE changed,
# never the anchor.
#
# The cost law that makes the wedge real: CAPITAL (gear, hones,
# training) rides the FULL pillar; RUNNING costs (the healer's tent,
# repairs, consumables) ride the income curve — priced on the pillar
# they would outgrow the income that pays for them.
PILLAR = 1.3
PACE_DISCOUNT = 1.04           # income exponent = PILLAR / PACE_DISCOUNT
WARDEN_RISE = 1.02             # warden HP exponent = PILLAR × WARDEN_RISE


def pillar(b: float) -> float:
    """The master curve: ×PILLAR per floor (or level), 1.0 at floor 1."""
    return PILLAR ** (max(1, b) - 1)


def income_pillar(b: float) -> float:
    """What a floor PAYS: the pillar minus the pace discount."""
    return (PILLAR / PACE_DISCOUNT) ** (max(1, b) - 1)


def pace_wedge(b: float) -> float:
    """How many floor-1 days one of floor B's days is worth — the gap
    between what B costs (pillar) and what B pays (income_pillar)."""
    return PACE_DISCOUNT ** (max(1, b) - 1)

# 030 Phase 9: how deep the tuning work has actually gone. Slow sim
# suites cover floors ≤ this cap on every run; the full tower runs only
# under ASCENT_FULL_SIMS=1 (the pre-ship ritual, not the inner loop).
# Whole-tower arithmetic gates (smoothness, pace, art coverage) ignore
# this — they are quick and always on.
TUNED_FLOOR_CAP = 10


def energy_cap(gear_tier: int, race: str = "") -> int:
    """022/002: the cap is keyed off the GEAR BAND (tier of the best
    equipped paid piece), never the level — the level stops at 30, the
    steel does not."""
    cap = ENERGY_BASE_CAP + max(0, min(10, gear_tier) - 1)
    if race == "human":
        cap += 1
    return cap


# ── §1b The XP pool (006: aether = crystallized experience) ──────────────
# The mana meter is gone. The ✦ bar is the XP inside the current level:
# earned by fighting, spent on honing / spells / mending. Spending delays the
# next level, never lowers one. All costs are priced in frontier kills so
# they stay a real decision at every level.

ELF_XP_BONUS = 0.05            # elves learn faster (replaces +1 aether cap)


def hone_xp(unlocked_floor: int) -> int:
    """✦ per honing pass: half a frontier kill."""
    return round(0.5 * xp_per_kill(unlocked_floor))


def sleep_xp_cost(floor: int) -> int:
    """✦ to Sleep past a fight: exactly the kill being skipped."""
    return xp_per_kill(floor)


def gear_player_level_req(tier: int) -> int:
    """PLAYER LEVEL required to buy tier-T gear — capped: the level cap
    can never strand a tier. Tiers whose band starts past the cap add a
    FLOOR gate instead (gear_floor_req)."""
    return min(band_start(tier), LEVEL_CAP)


def gear_floor_req(tier: int) -> int:
    """UNLOCKED FLOOR required for tiers whose band starts past the
    level cap (4–10): the world must have climbed there. 0 = no floor
    gate (the level gate suffices)."""
    fl = band_start(tier)
    return fl if fl > LEVEL_CAP else 0


def floor_entry_player_level(floor: int) -> int:
    """PLAYER LEVEL required to enter a floor. Converts from a floor:
    loose leash (level ≈ floor − 10) so a fresh climber can't ride an
    open frontier to floor 40 — capped so the cap never seals the
    tower (a level-30 body passes every leash)."""
    return max(1, min(floor - 10, LEVEL_CAP))


# ── §2 Player baseline ───────────────────────────────────────────────────
# 022/002: the level's share stops at the cap; gear carries the rest.
# The armor piece feeds max HP (GEAR_HP_PER_ARMOR × its bonus) so the
# health pool keeps climbing past level 30 the same way ATK/DEF do.

# 4 is measured, not guessed: monster chip damage (raw/4) ignores DEF,
# so deep-floor survival is bought with HP alone — at 3 the true prey
# win rate for warriors sags to 78% by floor 93; at 4 the whole 80-100
# band holds 86-95% and the first hour barely moves (+7 max HP at T1).
GEAR_HP_PER_ARMOR = 4          # max-HP points per point of armor bonus


def player_atk(level: int, weapon_bonus: int) -> int:
    """046: the level's share rides the pillar (anchor 3 at level 1)."""
    return round(3 * pillar(min(level, LEVEL_CAP))) + weapon_bonus


def player_def(level: int, shield_bonus: int, armor_bonus: int,
               race: str = "") -> int:
    armor = armor_bonus
    if race == "giant":
        armor = round(armor * 1.05)
    return round(2 * pillar(min(level, LEVEL_CAP))) + shield_bonus + armor


def player_max_hp(level: int, armor_bonus: int = 0) -> int:
    """046: the old 40 + 12·L line is one pillar-riding anchor now —
    52 at level 1 (identical kitted floor-1 pool: 52 + 4·7 = 80)."""
    return (round(52 * pillar(min(level, LEVEL_CAP)))
            + GEAR_HP_PER_ARMOR * armor_bonus)


# ── §3 Monsters, XP, gold ────────────────────────────────────────────────
# 004 retune: monster ATK slope 4.0 → 3.3 keeps at-level wilds fights under
# 40% of the HP pool on every floor once gear honing (below) is in play.
# 008: wilds HP is DERIVED from the at-level player's damage so a common
# kill takes ~2.5 rounds on floor 1, +0.5/floor, capped at ~7 — fights are
# quick clicks early and never drag. Wardens keep the old HP budget
# (they must still feel like bosses; see §5).

MONSTER_ATK_SLOPE = 3.3
BAND_INCOME_JUMP = 1.2         # RETIRED by 046 (income rides the income
                               # pillar now); kept for old imports

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
    atk = round(MONSTER_ATK_SLOPE * pillar(floor)) + 2
    dfs = round(3 * pillar(floor))
    p_atk, _ = _at_level_loadout(floor)
    p_dmg = max(1, round(0.75 * p_atk) - dfs // 2)
    return atk, dfs, round(p_dmg * wilds_rounds(floor))


# ── 025 §1: the stat archetype — a floor is a RANGE of animals ───────────
# Before 025 every encounter on a floor shared one stat line: content may
# author no numbers, and the only per-creature variation was the defense
# axis (banned on floor 1 by the intro staircase) plus the specimen roll.
# Four animals in four costumes, all two hits, all paying the same.
#
# So the archetype joins the trait vocabulary: qualitative words in the
# YAML, numbers here, content still numberless. Two independent axes:
#
#   BODY  (frail/lean/sturdy/hulking) — how long the fight runs. A
#         multiplier on the calibrated rounds-to-kill, hard-capped so no
#         creature is ever a slog.
#   BITE  (feeble/fierce/savage) — what the fight COSTS, expressed as a
#         share of the at-level player's HP pool, exactly the way
#         WARDEN_DMG_BUDGET is. ATK is then solved backwards out of the
#         damage rule.
#
# The bite must be derived, not multiplied. The damage rule is
# max(chip, raw − DEF/2) with chip = ceil(raw/4), so on floor 1 an ATK of
# 5 against a kitted DEF of 14 can only ever land the 1-point chip: a
# plain multiplier does nothing at the bottom of the tower. Multipliers
# big enough to be felt on floor 1 (×4) then land ATK 140 on floor 10 and
# kill an at-level player in two rounds. A pool share is right at both
# ends by construction, and it stays right for floors 11-100 when their
# archetypes get assigned.
#
# The PEER (no bite word) is left exactly as calibrated in 004/008/022 —
# 025 adds the range around it, it does not re-tune the middle.

# 043: the body stretches or shrinks the fight around the anchor; the
# spread narrowed (was 0.45–2.4) because length no longer carries threat
# — the bar does. Values shape texture, never difficulty.
BODY_ROUNDS = {"frail": 0.6, "lean": 0.8, "sturdy": 1.35, "hulking": 1.7}
# 043: the bite is a MULTIPLIER on the bar's calibrated lethality κ —
# a feeble thing at its bar is a slightly kind fight, a savage one
# slightly cruel, both inside the ±5% win tolerance. Which BAR a
# creature stands on (the real difficulty) is BITE_OFFSET/BODY_OFFSET
# below; pre-043 these values were absolute pool shares (0.05–1.0) and
# feeble prey stayed harmless on every floor forever.
BITE_COST = {"feeble": 0.85, "fierce": 1.0, "savage": 1.1}

WILDS_ROUNDS_HARD_MAX = 11.0    # the longest any wilds body may run
# No wilds creature may take more than this share of the pool in ONE
# round: death must always be preceded by a round you could have run in.
WILDS_ROUND_CAP = 0.45


def _archetype(traits) -> tuple[str, str]:
    """(body word, bite word) — "" for either axis the content left out."""
    body = bite = ""
    for t in traits or ():
        if t in BODY_ROUNDS:
            body = t
        elif t in BITE_COST:
            bite = t
    return body, bite


# ── 043: the bar — one difficulty ladder for a hundred floors ────────────
# Bar B = the design's reference loadout of floor B (level min(B, 30),
# reference rung + hone of floor B). Below 30 it climbs mostly by
# levels; above, entirely by steel. Every creature is anchored to a
# target bar T = floor + offset, offset read off the archetype and
# clamped to [−2, +1]: the floor's easiest kill rises with the floor
# (the 043 minimum bar), and something always stands one bar above you.
# "Anchored" is a measurement, not a metaphor: the bar-T reference
# player beats the creature ~90% of the time in the /mechanics
# Monte-Carlo; κ below is calibrated against that sim, not on paper.

BAR_MAX = 101                  # bar 101 = floor-101 steel, the ceiling

BODY_OFFSET = {"frail": -1, "lean": -1, "sturdy": 0, "hulking": 1}
BITE_OFFSET = {"feeble": -1, "fierce": 0, "savage": 1}
BAR_OFFSET_MIN, BAR_OFFSET_MAX = -2, 1

# κ: total damage a creature deals across its whole fight, as a share
# of its BAR's reference HP pool — the knob that puts the at-bar win at
# ~90%. Interpolated by bar: short low-bar fights are high-variance and
# need a lower share for the same win rate. CALIBRATED (tools/
# calibrate_bars.py), warrior model, plain profile.
_KAPPA_TABLE: dict[int, float] = {
    1: 0.732, 5: 0.781, 10: 0.806, 20: 0.795, 40: 0.778, 70: 0.780,
    101: 0.762,
}


def _kappa(bar: int) -> float:
    """Lethality share for `bar`, linear between calibration probes."""
    pts = sorted(_KAPPA_TABLE.items())
    if bar <= pts[0][0]:
        return pts[0][1]
    for (b0, k0), (b1, k1) in zip(pts, pts[1:]):
        if bar <= b1:
            return k0 + (k1 - k0) * (bar - b0) / (b1 - b0)
    return pts[-1][1]


def bar_offset(traits) -> int:
    """How far from its floor this archetype stands, in bars."""
    body, bite = _archetype(traits)
    off = BODY_OFFSET.get(body, 0) + BITE_OFFSET.get(bite, 0)
    return max(BAR_OFFSET_MIN, min(BAR_OFFSET_MAX, off))


def creature_bar(floor: int, traits) -> int:
    """The bar this creature is anchored to — stats AND pay key off it."""
    return max(1, min(BAR_MAX, floor + bar_offset(traits)))

# What the opener says about a shape you must read BEFORE committing —
# running is only a real choice if the card tells you what walked in.
BODY_TAG = {
    "frail": "small and slight",
    "lean": "lean and quick-ribbed",
    "sturdy": "thick through the shoulders",
    "hulking": "enormous — it fills the path",
}
BITE_TAG = {
    "feeble": "half-starved and slow with it",
    "fierce": "and it comes in hard",
    "savage": "and something in it has gone wrong",
}


def archetype_note(traits) -> str:
    """One clause naming this animal's body and bite, or "" for a peer."""
    parts = [d[t] for d in (BODY_TAG, BITE_TAG)
             for t in (traits or ()) if t in d]
    return ", ".join(parts)


def creature_rounds(floor: int, traits) -> float:
    """Rounds-to-kill for THIS creature at its own bar — the bar's
    calibrated target stretched by its body, capped: never a slog."""
    body, _ = _archetype(traits)
    return min(WILDS_ROUNDS_HARD_MAX,
               wilds_rounds(creature_bar(floor, traits))
               * BODY_ROUNDS.get(body, 1.0))


# 043.1: the gentle start. κ concentrated a low bar's whole kill budget
# into 2–3 rounds, so a floor-1 rat swung for a third of a fresh body's
# pool per blow — correct on the ladder, unplayable at the gate. These
# caps bound the FELT blow instead: per-round damage may not exceed this
# share of the bar's reference pool, ramping to the standard
# WILDS_ROUND_CAP by bar 5. At bars 1–2 the cap binds almost always, so
# the early fights cost less total than κ asks — that discount IS the
# on-ramp (it replaces the old WILDS_BAR1_SOFT). Bars 5+ are the honest
# ladder, untouched.
WILDS_LOW_BAR_CAPS = {1: 0.08, 2: 0.14, 3: 0.22, 4: 0.33}


def wilds_round_cap(bar: int) -> float:
    """Per-round damage ceiling for `bar`, as a share of its pool."""
    return WILDS_LOW_BAR_CAPS.get(bar, WILDS_ROUND_CAP)


# 043.2: the tutorial floors. The first hour must be EASY, not merely
# survivable — a flat FLOOR-keyed division of the final ATK, applied on
# top of the bar math: floor 1 bites at a third, floor 2 at two thirds,
# floor 3+ is the honest game. Keyed by floor (not bar) on purpose:
# the same bar-2 shape hits full on floor 3 and soft on floor 1.
FLOOR_ATK_SOFT = {1: 1 / 3, 2: 2 / 3}

# Death is free until you have anything to lose: a player still on
# level 1 keeps every coin through every death path — the tower does
# not tax the first stumble.
DEATH_FREE_MAX_LEVEL = 1


def creature_stats(floor: int, traits) -> tuple[int, int, int]:
    """(ATK, DEF, HP) for THIS creature on `floor` — 043: everything is
    derived from its BAR, not its floor. DEF stays flat per bar; the
    defense axis (armor/resist tiers) remains the class-matchup layer on
    top and is deliberately NOT bar-neutralized."""
    bar = creature_bar(floor, traits)
    body, bite = _archetype(traits)
    dfs = round(3 * pillar(bar))
    # HP: what the bar's reference player grinds through in `rounds`.
    p_atk, p_def = _at_level_loadout(bar)
    p_dmg = max(1, round(0.75 * p_atk) - dfs // 2)
    rounds = creature_rounds(floor, traits)
    hp = max(1, round(p_dmg * rounds))
    # ATK: across the whole fight the creature deals κ(bar) — nudged by
    # its bite — of the bar's reference pool. Short bodies spend it in
    # fewer rounds and hit harder per round: the glass cannon, at equal
    # anchored lethality.
    pool = reference_player_hp(bar)
    cost = _kappa(bar) * BITE_COST.get(bite, 1.0) * pool
    per_round = min(cost / rounds, wilds_round_cap(bar) * pool)
    # Invert the damage rule, BOTH branches: a landed blow deals
    # max(raw/CHIP_DIVISOR, raw − DEF/2), so the raw roll that lands
    # exactly `per_round` is the smaller of the two solutions.
    raw = min(CHIP_DIVISOR * per_round, per_round + p_def // 2)
    atk = max(1, round(raw / 0.75))
    atk = max(1, round(atk * FLOOR_ATK_SOFT.get(floor, 1.0)))
    # 048 N1: the type weighs the body — flyers land many weak cuts,
    # the armoured land rare heavy ones. On top of the bar, like the
    # tiers were: the type layer is deliberately NOT bar-neutralized.
    mtype = type_of(traits)
    atk = max(1, round(atk * TYPE_ATK[mtype]))
    hp = max(1, round(hp * TYPE_HP[mtype]))
    return atk, dfs, hp


# 043: danger pays THROUGH THE BAR now. xp_per_kill/gold_per_kill take
# the creature's bar, so a floor's terror out-pays its snack from the
# same one formula — the 025/039 threat-multiplier stack (BITE_PAY ×
# BODY_ROUNDS, floor-capped) is retired with its caps.

# 025 §5: the rubber band. A draw the player would probably not survive
# keeps a FIFTH of its weight — an 80% cut, never a ban. The tower must
# still be able to put something in front of you that you have to run
# from; that is the whole point of the archetypes, and the opener names
# the shape before you commit.
RUBBER_BAND_CUT = 0.20
LETHAL_SHARE = 0.90       # a fight costing this much of your CURRENT HP

# ── 039: the floor shapes the draw ───────────────────────────────────────
# Flat knobs made floor 6 feel like floor 1 with different costumes: the
# same prey share, the same runt odds, the same 80% mercy on lethal
# draws, the same reward ceiling. From floor 4 the tower stops being
# polite — prey thins out, the rubber band loosens, and the ceiling on
# what a hard kill may pay climbs.

PREY_FADE_START = 3        # last floor with the full prey share
PREY_FADE_SLOPE = 0.15     # weight lost per floor past the start
PREY_FADE_FLOOR = 0.25     # the moths never vanish — lore still walks


def prey_weight_mult(floor: int) -> float:
    """039 §1: prey (feeble-bite) draw weight fades with altitude —
    1.0 through floor 3, then −0.15/floor to 0.25 at floor 8+."""
    if floor <= PREY_FADE_START:
        return 1.0
    return max(PREY_FADE_FLOOR,
               1.0 - PREY_FADE_SLOPE * (floor - PREY_FADE_START))


def rubber_band_cut(floor: int) -> float:
    """039 §3: the mercy ladder. Low floors keep 025's 80% cut on
    probably-lethal draws; the band loosens as the tower stops
    apologizing — 0.35 on floors 4–6, half weight kept from floor 7."""
    if floor <= 3:
        return RUBBER_BAND_CUT
    return 0.35 if floor <= 6 else 0.50


# (043: reward_mult_cap / kill_reward_mult lived here — retired. A
# creature's pay now comes from gold_per_kill(bar)/xp_per_kill(bar); the
# bar offset is clamped to [−2, +1], so the cap's job — one lucky draw
# never outpaying the Warden — is structural.)


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

# 039 §2: the runt fade. Specimen WEIGHTS become floor-shaped (stat/gold
# multipliers and tags never move): runts thin out from floor 4 and the
# freed weight goes to the paying end. The 008 "expectation ≈ 1.0"
# promise is deliberately relaxed at altitude — the roll's gold
# expectation climbs 1.00 → 1.20 by floor 8, which IS part of "higher
# floors pay more"; specimen_gold_expectation() states the designed
# curve so the sim asserts drift against design, not against 1.0.
_SPECIMEN_LADDER = {
    4: {"runt": 22, "common": 51, "tough": 21, "alpha": 6},
    5: {"runt": 18, "common": 53, "tough": 22, "alpha": 7},
    6: {"runt": 15, "common": 52, "tough": 24, "alpha": 9},
    7: {"runt": 11, "common": 54, "tough": 25, "alpha": 10},
    8: {"runt": 8,  "common": 55, "tough": 26, "alpha": 11},
}


def specimen_table(floor: int) -> dict[str, dict]:
    """The specimen roll for THIS floor — SPECIMENS with floor-shaped
    weights. Floors 1–3 are exactly the 008 table."""
    if floor <= 3:
        return SPECIMENS
    w = _SPECIMEN_LADDER[min(floor, 8)]
    return {k: {**s, "weight": w[k]} for k, s in SPECIMENS.items()}


def specimen_gold_expectation(floor: int) -> float:
    """The designed gold expectation of the specimen roll at `floor`."""
    t = specimen_table(floor)
    total = sum(s["weight"] for s in t.values())
    return sum(s["weight"] * s["gold"] for s in t.values()) / total


# ── 039 §2: the deep hunt — ⚡2, floor 4+ ────────────────────────────────
# An informed opt-in to the dangerous end of the roster: opponents
# harder in ATK and SPEED, NEVER in HP — the fight gets scarier, not
# longer. No prey, no runts, no rubber band (choosing this IS the
# consent), and a clear per-energy premium on the way out.
COST_WILDS_DEEP = 2
DEEP_HUNT_MIN_FLOOR = 4
DEEP_ATK_MULT = 1.2
DEEP_SPEED_BONUS = 1       # on the 1–10 scale; stacks with alpha's +1

# The premium tracks the blood. Deep-roster brutality is CONTENT — floor
# 4 is stag country (avg threat 1.8, deep death ~2%), floor 9 is the
# night floor (avg threat 2.6, deep death ~25%) — so a flat premium
# made deep a strictly bad deal exactly where it is scariest. Ladder
# sim-fitted (plans/039-the-climb-pays/sim039.py) so deep EV/⚡ lands
# ≈1.2–1.5× the same-floor normal hunt on every floor. Gold AND xp.
_DEEP_REWARD_LADDER = {4: 1.3, 5: 1.6, 6: 1.9, 7: 2.8, 8: 2.8,
                       9: 3.0, 10: 3.4}


def deep_reward_mult(floor: int) -> float:
    return _DEEP_REWARD_LADDER.get(min(max(floor, 4), 10), 3.4)

_DEEP_WEIGHTS = {"runt": 0, "common": 45, "tough": 35, "alpha": 20}
DEEP_SPECIMENS = {k: {**s, "weight": _DEEP_WEIGHTS[k]}
                  for k, s in SPECIMENS.items()}


# ── 017 §2: damage types & defense profiles ──────────────────────────────
# Three professions, three damage types. Every monster carries a defense
# profile derived from qualitative content traits — content never carries
# numbers. Tier multipliers cut the FINAL damage of the affected type.

DAMAGE_TYPE = {"warrior": "melee", "archer": "ranged", "sorcerer": "magic"}

# 048 phase 5: the tier system died here — one TYPE per monster now
# bundles sign, speed, weight, and the triangle (tables below). The
# warden reference-damage cut keeps the old low-tier number until the
# phase-6 bake re-anchors the band.
WARDEN_REF_CUT = 0.75
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
BOW_CLOSE_MULT = 0.5           # bow damage in close quarters (036: 0.6 →
                               # 0.5 — the gap ladder pays it back)
DODGE_CAP_PCT = 12             # speed never becomes the main defense

# ── 036: the gap ladder — an archer's fight has a THIRD axis ─────────────
# "close" is gap 0; a fight opens at gap 1 (the old "at_range"). An archer
# can keep giving ground: every length of gap is draw-time, and draw-time
# is power. The price of making ground is a parting blow whose CHANCE is
# what speed buys — faster legs, cleaner break.
GAP_MAX = 3
BOW_GAP_MULT = {1: 1.0, 2: 1.25, 3: 1.5}


def bow_gap_mult(gap: int) -> float:
    """Bow damage by gap. Close quarters cramp the draw; a long field
    lets the archer use the whole arc of the shot."""
    if gap <= 0:
        return BOW_CLOSE_MULT
    return BOW_GAP_MULT.get(min(int(gap), GAP_MAX), 1.0)


def p_gap_hit(pspd: int, mspd: int) -> float:
    """Chance the monster lands its parting blow while you make ground.
    Every point of speed advantage is a cleaner break; a faster monster
    almost always collects."""
    return _clamp(0.65 - 0.12 * (pspd - mspd), 0.05, 0.95)

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


def type_of(traits) -> str:
    """048 phase 7: content speaks types natively — at most one type
    trait per monster (none = plain). The legacy bridge is
    type_from_traits, kept for doc-migration tests only."""
    ts = set(traits or ())
    if "fly" in ts:
        return "fly"
    if "magic_resist" in ts:
        return "magic_resist"
    if "armoured" in ts:
        return "armoured"
    return "plain"


def profile_from_traits(traits) -> dict:
    """048: the defense profile IS the type. One type per monster —
    sign, speed, and the triangle answer all hang off it. `bulwark`
    stays orthogonal (an elite wall, never a weapon-answer)."""
    t = type_of(traits or ())
    return {"type": t, "flying": t == "fly",
            "bulwark": "bulwark" in set(traits or ()),
            "speed": TYPE_SPEED[t]}


def profile_gold_mult(prof: dict) -> float:
    """A signed monster pays for the diagnosis it demands."""
    m = TYPE_GOLD.get(prof.get("type", "plain"), 1.0)
    if prof.get("bulwark"):
        m *= BULWARK_GOLD_MULT
    return m


# ── 048: one type per monster — sign, speed, weight, and the triangle ──
# (phase 1: tables + mapping only; combat still runs the tier system.)

TYPE_SPEED = {"fly": 7, "armoured": 3, "magic_resist": 3, "plain": 5}
TYPE_ATK = {"fly": 0.6, "armoured": 1.4, "magic_resist": 1.4, "plain": 1.0}
TYPE_HP = {"fly": 0.9, "armoured": 1.2, "magic_resist": 1.0, "plain": 1.0}
TYPE_GOLD = {"fly": 1.2, "armoured": 1.3, "magic_resist": 1.3, "plain": 1.0}

TYPE_MULT = {
    "fly":          {"blade": 0.0, "bow": 1.0, "staff": 0.6},
    "armoured":     {"blade": 0.5, "bow": 0.15, "staff": 1.0},
    "magic_resist": {"blade": 1.0, "bow": 0.5, "staff": 0.15},
    "plain":        {"blade": 1.0, "bow": 1.0, "staff": 1.0},
}

TYPE_SIGN = {"fly": "⚡", "armoured": "⛨", "magic_resist": "✧",
             "plain": ""}
TYPE_NAME = {"fly": "fly", "armoured": "armoured",
             "magic_resist": "magic-resistant", "plain": "plain"}
PATH_WEAPON_WORD = {"blade": "steel", "bow": "arrows", "staff": "magic"}


def answer_word(mult: float) -> str:
    """The triangle cell as a spoken answer — the card's vocabulary."""
    if mult <= 0:
        return "can't reach"
    if mult <= 0.2:
        return "glance"
    if mult < 1.0:
        return "half"
    return "full"


def type_line(mtype: str) -> str:
    """S3: the one line under the numbers — what each weapon does to
    this type. Plain monsters say so in words."""
    if mtype == "plain":
        return "no sign — every weapon bites full"
    sign = TYPE_SIGN[mtype]
    bits = " · ".join(
        f"{PATH_WEAPON_WORD[path]}: {answer_word(TYPE_MULT[mtype][path])}"
        for path in ("blade", "bow", "staff"))
    return f"{sign} {TYPE_NAME[mtype]} — {bits}"


def speed_word(spd: int) -> str:
    if spd >= SPEED_FAST:
        return " (fast)"
    if spd <= SPEED_SLOW:
        return " (slow)"
    return ""


# 048 N4: the mastery studies' teeth (phase 5) — riposte, long draw,
# focus. Sold at the School (MASTERY_XP); recorded in p["mastery"].
RIPOSTE_RETURN = 0.25          # blocked blow answers 25% of mean swing
LONG_DRAW_CRIT_MULT = 1.5      # gap-3 top-roll crit
LONG_DRAW_TOP = 0.10           # the top 10% of the roll band crits
FOCUS_MULT = 0.75              # staff's half-answers cast at ×0.75
MASTERY_ATK_BONUS = 0.10       # each studied mastery: +10% on EVERY swing


def legacy_rank(unlocked_floor: int) -> int:
    """048 migration: the honored rank scales with the climb — rank 6
    (the old on-class feel) as the floor of it, +1 per ten floors
    opened, capped one step under the master's studies."""
    return min(9, 6 + max(0, int(unlocked_floor)) // 10)


PATH_OF_LINE = {"warrior": "blade", "archer": "bow", "sorcerer": "staff"}

# 048 N3: trained rank 0–10 per path — the player's skill, never the
# weapon's. Rank buys consistency: the miss fades, the worst swing rises.
TRAIN_XP_ANCHOR = 20
TRAIN_GOLD_ANCHOR = 8


def TRAIN_MISS_PCT(rank: int) -> int:
    """Chance (whole %) an attack goes wide: 25% untrained → 0% at 10."""
    return max(0, round(25 - 2.5 * rank))


def TRAIN_ROLL_FLOOR(rank: int) -> float:
    """The worst swing as a share of full power: 30% → 70% at rank 10.
    Rank 5 reproduces today's [ATK/2, ATK] band."""
    return (30 + 4 * rank) / 100


def train_xp(rank: int) -> int:
    """XP the School asks for RANK (each costs more than the last).
    One path 0→10 = 2,854 XP ≈ body levels 1→10."""
    return round(TRAIN_XP_ANCHOR * rank ** 1.5)


def train_gold(rank: int, frontier: int) -> int:
    """The instructor's fee — rides the pillar so it never trivializes."""
    return round(TRAIN_GOLD_ANCHOR * pillar(frontier) * rank)


# 048 N4/N5: mastery studies and the CARRY skill — School merchandise.
# A master pays 80% on the OTHER paths' first five ranks (the hands
# already know discipline); the discount never reaches rank 6+.
# N7: fight options answer to trained rank, not class — the gate table.
TREELINE_RANK = 4     # bow — the shot from cover
GAP_OPEN_RANK = 6     # bow — give ground on purpose
GAP_DRAW_RANK = 8     # bow — the open gap starts paying ×1.25/×1.5
WALL_RANK = 4         # blade — shield wall (a shield on the arm too)
SLEEP_RANK = 6        # staff — the lullaby

MASTERY_XP = round(train_xp(10) * 1.5)          # 948
MASTERY_DISCOUNT = 0.8
MASTERY_DISCOUNT_MAX_RANK = 5
CARRY2_XP, CARRY2_GOLD = 60, 30                 # 2nd slot — level 1
# 049.2: the level-8 gate is back — and this time it LOOKS locked.
# 049.1 removed it because a plain "needs level 8" line next to a
# buyable row read as a bug; the real fix is a dimmed row that says
# what opens it, not an open row nobody below level 8 can pay anyway
# (the XP bar can't hold 500 before then).
CARRY3_LEVEL = 8
CARRY3_XP, CARRY3_GOLD_ANCHOR = 500, 200        # 3rd slot


def carry3_gold(frontier: int) -> int:
    return round(CARRY3_GOLD_ANCHOR * pillar(frontier))


def train_xp_cost(rank: int, discounted: bool = False) -> int:
    xp = train_xp(rank)
    if discounted and rank <= MASTERY_DISCOUNT_MAX_RANK:
        xp = round(xp * MASTERY_DISCOUNT)
    return xp


def type_from_traits(traits) -> str:
    """Legacy trait sets → the one 048 type. Flight is the loudest fact;
    resist outranks armor (a warded thing reads as warded); bulwark is
    orthogonal and never a type."""
    ts = set(traits)
    if "flying" in ts:
        return "fly"
    if any(t.startswith("resist_") for t in ts):
        return "magic_resist"
    if any(t.startswith("armor_") for t in ts):
        return "armoured"
    return "plain"


def typed_damage_048(path: str, raw: int, monster_def: int,
                     mtype: str, focus: bool = False) -> int:
    """Damage of weapon path P against monster type T. Staff ignores flat
    DEF; blade and bow eat raw−DEF/2. Anything that CAN hit chips ≥1 —
    the single legal zero stays blade-vs-fly. `focus` is the staff
    mastery study: its ×0.5/×0.6 answers cast at ×0.75 (the glance
    stays a mistake)."""
    if path == "blade" and mtype == "fly":
        return 0
    mult = TYPE_MULT[mtype][path]
    if focus and path == "staff" and 0.5 <= mult < 0.75:
        mult = FOCUS_MULT
    base = raw if path == "staff" else raw - monster_def // 2
    return max(1, round(max(1, base) * mult))


def warden_profile(floor: int) -> dict:
    """048: a Warden is a damage RACE, not a triangle question — every
    weapon bites it full. The milestone damage-check story returns with
    the phase-6 band re-anchor."""
    return profile_from_traits(())


XP_PER_KILL_SLOPE = 3.0        # 048: was 2.4 — +25% funds the School
                               # sink so the one-path climber keeps the
                               # level≈floor pace while training


def xp_per_kill(bar: int) -> int:
    """012: XP is scarce — always below the kill's gold. 043: takes the
    creature's BAR (== floor for a common at-floor kill). 046: derived
    from the level≈floor sync law — xp_need(L)=24·L^1.5 must be earned
    in days(L)=d₀·PACE^(L−1) at ~30 kills/day, so xp/kill carries L^1.5
    over the pace wedge; past the cap the ✦ pool keeps the shape."""
    return max(1, round(XP_PER_KILL_SLOPE * bar ** 1.5 / pace_wedge(bar)))


GOLD_PER_KILL_ANCHOR = 8       # the floor-1 kill, unchanged since 004


EARLY_COIN_FLOORS = 10


def early_coin_mult(floor: int) -> float:
    """048 N8: the young-tower bounty — ×2.0 at floor 1 fading to ×1.1
    at 10, gone at 11. The first ten floors are the classroom: the
    bounty funds both basic weapons and the first ranks of every path.
    Labeled on the kill card so the fade never reads as a nerf."""
    return 2.0 - 0.1 * (floor - 1) if floor <= EARLY_COIN_FLOORS else 1.0


def gold_per_kill(bar: int) -> int:
    """Base gold per kill. 043: takes the creature's BAR — coin follows
    toughness. 046: the anchor rides the INCOME pillar; the old
    linear × band-jump ladder is retired (BAND_INCOME_JUMP with it).
    048: the young-tower bounty rides IN the paycheck."""
    return max(1, round(GOLD_PER_KILL_ANCHOR * income_pillar(bar)
                        * early_coin_mult(bar)))


def base_gold_per_kill(bar: int) -> int:
    """The un-bountied paycheck — the basis for every price and fee
    ladder. 048: the young-tower bounty is pocket coin, a gift to the
    young climber; if fees and prices rode it, the gift would tax
    itself away. Ladders anchor here; the paycheck pays gold_per_kill."""
    return max(1, round(GOLD_PER_KILL_ANCHOR * income_pillar(bar)))


def healer_tent_price(floor: int) -> int:
    """Full heal at the tent. 046: a RUNNING cost — it rides the income
    curve (◈5 anchor), the same slice of a hunting day on every floor;
    the old 5×floor line outgrows deep-floor income and flips it
    negative."""
    return max(1, round(HEALER_TENT_PER_FLOOR * income_pillar(floor)))


def daily_income(floor: int) -> int:
    """Design estimate of net gold per day of at-level hunting on `floor`
    (≈30 fights, a tent visit every ~3 fights now that chip damage is
    real). Anchors hone prices and the tier price ladder — not paid to
    anyone directly."""
    return round((base_gold_per_kill(floor) - healer_tent_price(floor) / 3)
                 * 30)   # 048: un-bountied — prices/fees must not ride the gift


XP_NEED_BASE = 24              # 022/002: was 60 — the cap arrives in the
                               # first weeks, then XP is pure currency


def xp_need(level: int) -> int:
    """XP to go from `level` to `level+1`: 24 · L^1.5. Below LEVEL_CAP the
    bar is hard — surplus from a kill is discarded. At LEVEL_CAP the
    Guildhall refuses training and the ✦ pool becomes pure currency
    (honing, spells, mending — the sinks that already exist)."""
    return round(XP_NEED_BASE * level ** 1.5)


# ── §4b Guild training (012) ─────────────────────────────────────────────
# Levels are bought, never granted: a full XP bar is the license to train,
# the gold fee is the price. One day of at-level income per level — the
# same growth curve everything else is priced in (linear × 1.2 per band).

LEVELUP_BASE_GOLD = 60         # the first level-up, by design (047)
TRAIN_SOFT_LEVELS = 8          # the ramp reaches the full fee here
# 8, not 5: the climber trains ~2–3 levels ahead of the floor, so the
# fees paid ON floors 1–5 are levels 1–8's.


def _train_soft(level: int) -> float:
    """047 tutorial ramp: the first levels charge a fraction of the
    one-day law (×0.25 at level 1, linear to ×1.0 at TRAIN_SOFT_LEVELS)
    — the bottom of the tower advances on kills, not a savings plan."""
    if level >= TRAIN_SOFT_LEVELS:
        return 1.0
    return 0.25 + 0.75 * (level - 1) / (TRAIN_SOFT_LEVELS - 1)


def levelup_gold(level: int) -> int:
    """Gold fee to train from `level` to `level+1` at the Guildhall.
    046: training is CAPITAL — the fee rides the full pillar (one
    floor-1 day at the anchor, ×pace_wedge in day terms per level).
    047: the first ten levels ride the tutorial ramp."""
    return max(LEVELUP_BASE_GOLD,
               round(daily_income(level) * pace_wedge(level)
                     * _train_soft(level) / 10) * 10)


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
# 022/002: 0.82 is MEASURED against the real fight sim, not derived on
# paper — at the old 1.07 the mean fight dealt 107% of the player's
# pool and the true at-level win rate had drifted to 0–36% (nothing
# gated it; the chip rule and range crossing moved reality away from
# the formula). 0.82 lands floors 5–29 at 59–88% wins, averaging 76%.
WARDEN_DMG_BUDGET = 0.82       # expected damage dealt ÷ player pool
WARDEN_SOFT_FLOOR = 30         # last floor tuned for solo play
# (046: WARDEN_HP_RAMP / WARDEN_ATK_RAMP retired — WARDEN_RISE compounds
# the gap into the HP exponent itself; ATK stays share-based so strikes
# remain survivable at every depth.)


REFERENCE_HONE_LAG = 2         # honing trails the climb by ~2 floors

# 022/002: additive honing weight per step — RETIRED by 046 (kept for
# old imports). A flat +3 can never keep a band that grows ×1.3 a
# floor; honed_bonus() below is the law now.
HONE_WEIGHT = {"weapon": 3, "shield": 2, "armor": 2}


def honed_bonus(base: int, hone: int) -> int:
    """046: a hone step multiplies its piece by the PILLAR — one step is
    one floor's growth on that slot, so honing IS the within-band climb
    and the reference (hone = floors-past-band-start − LAG) lands on
    anchor × pillar(floor − LAG) by construction."""
    return round(base * PILLAR ** max(0, hone))


def reference_level(floor: int) -> int:
    """The design's at-level player is level == floor UP TO THE CAP
    (see _at_level_loadout). The ONLY place that identity is asserted;
    past floor 30 the reference body is a capped body in deeper steel."""
    return min(floor, LEVEL_CAP)


def reference_rung(floor: int) -> float:
    """The rung the at-level player is standing on. 025: band 1 sells a
    rung per level, and the player buys them — before 025 the reference
    read the WHOLE tier (bonus 8) while a level-6 player could already
    own rung 1.5 (bonus 23), so floors 6–10 were tuned against a
    climber who no longer existed. That understatement is most of why
    the first ten floors played flat. Bands 2+ keep the whole-tier
    reference until their sub-rungs exist (MUST_BE_DONE_LATER §4)."""
    tier = gear_tier_for_floor(floor)
    if tier != 1:
        return float(tier)
    return 1 + (min(floor, BAND1_STEPS) - 1) / BAND1_STEPS


def _reference_bonus(floor: int, slot: str) -> int:
    """Base bonus of the reference player's piece in `slot`, honing
    excluded — read off the ladder the shops actually stock."""
    by_tier = {"weapon": _WEAPON_ATK_BY_TIER, "shield": _SHIELD_DEF_BY_TIER,
               "armor": _ARMOR_DEF_BY_TIER}[slot]
    rung = reference_rung(floor)
    t = int(rung)
    if rung == t:
        return by_tier[t]
    k = round((rung - t) * BAND1_STEPS)
    return _step_bonus(by_tier[t], by_tier[t + 1], k)


def reference_armor_bonus(floor: int) -> int:
    """Armor bonus of the at-level player (base × pillar-hone) — the
    piece that also feeds max HP."""
    return honed_bonus(_reference_bonus(floor, "armor"),
                       reference_hone(floor))


def reference_player_hp(floor: int) -> int:
    """HP of the at-level player used to tune wardens. Deliberately
    NOT player_max_hp(floor) — that reads a floor as a level."""
    return player_max_hp(reference_level(floor), reference_armor_bonus(floor))


def reference_hone(floor: int) -> int:
    """Hone level of the design's at-level player: honing trails the
    climb slightly (income funds it with a lag).

    025: zero through band 1. The within-band growth there is now the
    rung ladder itself (a step per level), and counting both would put
    the reference at floor 10 ABOVE the reference at floor 11 — a cliff
    where the tower is supposed to be a straight line. Honing stays what
    it always was in band 1: the diligent climber's edge over the
    reference, not the reference. Bands 2+ have no sub-rungs yet, so
    honing still carries them (MUST_BE_DONE_LATER §4)."""
    tier = gear_tier_for_floor(floor)
    if tier == 1:
        return 0
    return max(0, floor - band_start(tier) - REFERENCE_HONE_LAG)


def _at_level_loadout(floor: int) -> tuple[int, int]:
    """(ATK, DEF) of the design's at-level player: level = min(floor,
    cap), current tier set, honing 2 floors behind. The reference all
    tuning points at."""
    hone = reference_hone(floor)
    lvl = reference_level(floor)
    return (player_atk(lvl, honed_bonus(
                _reference_bonus(floor, "weapon"), hone)),
            player_def(lvl,
                       honed_bonus(_reference_bonus(floor, "shield"), hone),
                       reference_armor_bonus(floor)))


def _boss_hp_base(floor: int) -> int:
    """046: the boss pool rides pillar × WARDEN_RISE — a warden outgrows
    its own floor's monsters 2%/floor, compounding to ~7× the monster
    gap by floor 100. Anchor 37 = the old 12·1+25 at floor 1."""
    return round(37 * pillar(floor) * WARDEN_RISE ** (floor - 1))


def warden_stats(floor: int) -> tuple[int, int, int]:
    """Regular Warden (floors not ending in 0), soloable at-level
    through the soft floor. 046: the rise lives in HP only — ATK stays
    share-based (WARDEN_DMG_BUDGET), so a strike is survivable at every
    depth and the wall is the POOL, not the blow."""
    p_atk, p_def = _at_level_loadout(floor)
    m_def = round(3 * pillar(floor))
    hp = round(_boss_hp_base(floor) * WARDEN_HP_MULT)
    p_dmg = max(1, round(0.75 * p_atk) - m_def // 2)
    if floor >= WARDEN_PROFILE_FLOOR:
        # 017: band-3+ wardens carry low tiers (both axes, so every class
        # feels it equally) — the reference damage drops ×0.75 and the
        # rounds/ATK budget below re-tunes itself by construction.
        p_dmg = max(1, round(p_dmg * WARDEN_REF_CUT))
    rounds = max(3, hp // p_dmg)
    # floors 1–5 ramp in gently: fresh climbers reach these gates with
    # partial kits (the first with the bare shiv), and the first hour
    # must never be a coin flip.
    budget = WARDEN_DMG_BUDGET * min(1.0, 0.5 + 0.1 * floor)
    per_round = budget * reference_player_hp(floor) / rounds
    atk = round((per_round + p_def // 2) / 0.75)
    return atk, m_def, hp


def warden_xp(floor: int) -> int:
    """012: below warden_gold — XP is scarce. 046: the old 15·floor
    carries the same xp_per_kill sync shape (anchor 15 at floor 1)."""
    return max(1, round(15 * floor ** 1.5 / pace_wedge(floor)))


def warden_gold(floor: int) -> int:
    """046: ten frontier kills' worth, plus the warden rise — the gate's
    bounty outgrows the floor's grind the way its HP does. Anchor: ◈80
    at floor 1, exactly the old 80·floor there."""
    return max(1, round(10 * gold_per_kill(floor)
                        * WARDEN_RISE ** (floor - 1)))


# ── §5b The shared Warden — the coordination curve (022 §002) ────────────
# ALL 100 Wardens are shared — one list of bosses for the whole world.
# The keep fight is a REAL fight: every wound you leave persists in the
# world HP pool; pool at zero opens the floor for everyone.
#
# The curve, from research/one-tower-for-everyone.md §4:
#   A     = active players (the census; REFERENCE_ACTIVE when dark)
#   R100  = max(min(50, 0.5·A), 0.10·A)      # strikers the finale needs
#   N(F)  = 1 for F ≤ 30, else ceil(R100^((F−30)/70))
#   pool  = N(F) × 8 strike-fights            # one full bar per striker
#   regen = breakeven at N(F)/2 sustained strikers — a constant fraction
#           of the pool by algebra, every floor
#   W(F)  = the silence window (F > 30): no strike for W hours and the
#           wound closes fully — "coordinated" means same DAY, not same
#           minute
#   pity  = each fully-closed wound takes 3% off the max, forever — a
#           world can always eventually win; a siege can still fail.
#
# The unit everything is measured in: one honest strike-fight — the
# at-level player fights the pool until one round from death, then
# withdraws. Sizing pools in this unit closes the banked-bar burst
# (one bar ≈ 9 fights can never out-damage an N ≥ 2 pool of 16+).

REFERENCE_ACTIVE = 200         # sizing fallback when no census exists
WARDEN_POOL_FIGHTS = 8         # pool per required striker ≈ one full bar
# 024 set this to 2 to rescue a floor-1 gate that read 1,032 HP. 025
# raises it 60%: on the siege floors the wound never closes, so the wall
# is allowed to be a wall. Raising the ANCHOR rather than multiplying the
# siege band keeps the ramp one straight line — a ×1.6 on floors 1-10
# alone put a 6.2 → 4.1 cliff at floor 11, which is the exact dip 024
# exists to prevent.
WARDEN_POOL_FIGHTS_MIN = 3.2
WARDEN_SILENCE_MIN_H = 6.0     # silence window at floor 31…
WARDEN_SILENCE_MAX_H = 30.0    # …stretching to this by floor 90+
WARDEN_SILENCE_SOLO_H = 30.0   # 024: a day and a night, inside the band
WARDEN_PITY_PCT = 0.03         # off max HP per fully-closed wound, forever
WARDEN_POOL_TUNE = 3           # 024/025: bump to resize live pools on read

# ── 025 §3: the siege floors ─────────────────────────────────────────────
# "The first bosses up to stage 10 can not rejuvenate — so they can have a
# large energy but even a single player can have at them over time."
#
# 024 gave the solo band a 30-hour silence window, which is generous but
# still a clock: forget the gate for a day and a night and the wound is
# gone. Below the siege floor there is no clock at all. A wound never
# closes, no regen ever runs, and no pity is ever paid — so the pool is
# allowed to be a wall (see WARDEN_POOL_FIGHTS_MIN), because every blow
# anyone lands on it is permanent.
WARDEN_SIEGE_FLOOR = 10

# a player spending every ⚡ on the keep: fights per hour, sustained
SUSTAINED_FIGHTS_PER_HOUR = (60 / ENERGY_REGEN_MIN) / COST_WARDEN_ATTEMPT

# ── 026: a Warden is a war machine, not a rat ────────────────────────────
# The keep fight has exactly one end condition — you withdraw or you die —
# and 3 ⚡ is charged once, when you join. That is only a limit while the
# Warden can actually hurt you. A climber whose DEF had outgrown the gate
# took the 1-POINT chip every round, so the fight had no end at all: one
# charge bought unlimited swings, and a failed getaway cost nothing worth
# the word "chase".
#
# Two laws close it, and neither touches the damage arithmetic — measured
# attempts to fix this by making a Warden's blow heavier (a per-round
# floor at the mean bite; halving the chip divisor) either deleted the
# lower half of the roll distribution or, at depth where Warden ATK is
# huge, collapsed the whole coordination band from ~60% at-level wins to
# ~20%. The damage table is load-bearing; the EXCHANGE was not bounded.
#
# 1. One charge buys one exchange. 3 ⚡ was always sold as "a full
#    fight", and the pool is literally measured in those fights
#    (strike_fight_damage: "fight until one round from death, then
#    withdraw"). Now the Warden's guard closes when that many rounds are
#    spent and drives you back — wounds kept, ⚡ spent, come again.
# 2. A gate never lets you walk. The getaway roll is capped, and the
#    blow that catches you cannot be filed down to the chip.
WARDEN_FLEE_MAX = 0.75         # a Warden always has a chance to follow
WARDEN_GRAB_SHARE = 0.06       # the least a caught getaway costs you


def warden_exchange_rounds(floor: int) -> int:
    """Rounds ONE 3 ⚡ charge buys against a shared Warden — the same
    near-death fight the pool is measured in (see strike_fight_damage).
    Nothing enforced this before, so a climber whose DEF had outgrown the
    gate could stand in the keep and swing until the pool was empty."""
    _p_atk, p_def = _at_level_loadout(floor)
    w_atk, _w_def, _w_hp = warden_stats(floor)
    w_dmg = max(1, round(0.75 * w_atk) - p_def // 2)
    return max(1, (reference_player_hp(floor) - 1) // w_dmg)


def warden_grab_damage(pool: int) -> int:
    """A Warden that cuts off your line lands a real blow, not a chip."""
    return max(1, round(WARDEN_GRAB_SHARE * max(1, int(pool))))


def required_strikers_100(active: int) -> float:
    """R100 — the scaled-minimum small-world rule."""
    a = max(1, int(active))
    return max(min(50.0, 0.5 * a), 0.10 * a)


def required_strikers(floor: int, active: int | None = None) -> int:
    """N(F): 1 inside the solo band, exponential to R100 at the top."""
    if floor <= WARDEN_SOFT_FLOOR:
        return 1
    r100 = required_strikers_100(
        REFERENCE_ACTIVE if active is None else active)
    return max(2, math.ceil(r100 ** ((min(floor, 100) - 30) / 70)))


def strike_fight_damage(floor: int) -> int:
    """Damage ONE at-level strike-fight leaves in the pool: fight until
    one round from death, then withdraw. The pool's measuring unit."""
    p_atk, p_def = _at_level_loadout(floor)
    w_atk, w_def, _hp = warden_stats(floor)
    p_dmg = max(1, round(0.75 * p_atk) - w_def // 2)
    if floor >= WARDEN_PROFILE_FLOOR:
        p_dmg = max(1, round(p_dmg * WARDEN_REF_CUT))
    # 026: the round count is the exchange the keep now actually grants
    # (warden_exchange_rounds) — one function, so the unit the pool is
    # measured in and the fight the player is sold can never drift.
    return max(1, warden_exchange_rounds(floor) * p_dmg)


def warden_pool_fights(floor: int) -> float:
    """024: strike-fights one striker's share of the pool is worth. The
    flat 8 was written for the coordination floors and then applied to
    the whole tower, so floor 1 — the first gate anyone meets, and one a
    lone climber has to open alone — asked the same eight near-death
    fights as floor 30. Ramp it: two at the bottom (two, not one, so the
    mechanic teaches itself — you come back and find your own wound
    still open), a straight line to the coordination band's 8 at the
    soft floor.

    Fractional on purpose. Rounding this to whole fights put +35–40%
    cliffs on floors 14, 17, 21 and 25 — the effort curve is what the
    climber feels, and it must rise one honest step per floor."""
    if floor >= WARDEN_SOFT_FLOOR:
        return float(WARDEN_POOL_FIGHTS)
    return WARDEN_POOL_FIGHTS_MIN + (
        WARDEN_POOL_FIGHTS - WARDEN_POOL_FIGHTS_MIN) * (
            floor - 1) / (WARDEN_SOFT_FLOOR - 1)


def pool_unit(floor: int) -> int:
    """The fight-unit pools are measured in, made monotone inside the
    solo band. 024: strike_fight_damage rides integer round counts, so
    it can DIP a floor (floor 3's unit came out under floor 2's, which
    handed floor 3 a weaker Warden than the floor below it). A climbing
    tower may never step backwards; deep floors keep the raw unit, where
    every pool is an order of magnitude clear of its neighbours."""
    if floor > WARDEN_SOFT_FLOOR:
        return strike_fight_damage(floor)
    return max(strike_fight_damage(f) for f in range(1, max(1, floor) + 1))


def world_warden_hp(floor: int, active: int | None = None) -> int:
    """The world pool: N(F) × warden_pool_fights(F) honest strike-fights.
    046: deep pools pass 2^53, where a float product silently loses the
    low bits — keep the arithmetic in integers whenever the factors are
    whole (they are, past the soft floor)."""
    n = required_strikers(floor, active)
    fights = warden_pool_fights(floor)
    if float(n).is_integer() and float(fights).is_integer():
        return max(1, int(n) * int(fights) * pool_unit(floor))
    return max(1, round(n * fights * pool_unit(floor)))


def world_warden_regen_hourly(floor: int) -> float:
    """Fraction of max HP healed per hour. Derived so exactly N(F)/2
    sustained strikers break even — fewer visibly lose ground.

    024: zero inside the solo band. A climber's body heals at dawn and
    nowhere else, so his honest cadence is one strike a day — a trickle
    of 2.78%/h restored ~25 fights' worth of body between his visits and
    made the band unwinnable alone. There, silence is the only healer."""
    if floor <= WARDEN_SOFT_FLOOR:
        return 0.0
    return SUSTAINED_FIGHTS_PER_HOUR / (2 * warden_pool_fights(floor))


def warden_silence_hours(floor: int) -> float | None:
    """W(F): hours of silence that close the wound fully — or None on the
    siege floors, where it never closes at all. 024 gave the solo band a
    day and a night, so a wound outlived the dawn a climber needs; 025
    takes the clock off the first ten gates entirely, because a wall you
    can only chip at is only fair if the chips stay."""
    if floor <= WARDEN_SIEGE_FLOOR:
        return None
    if floor <= WARDEN_SOFT_FLOOR:
        return WARDEN_SILENCE_SOLO_H
    t = min(1.0, max(0.0, (floor - 31) / 59))    # 31 → 90+
    return WARDEN_SILENCE_MIN_H + t * (WARDEN_SILENCE_MAX_H
                                       - WARDEN_SILENCE_MIN_H)


def world_warden_reward_mult(floor: int, active: int | None = None) -> float:
    """The reward pool in units of warden_xp/warden_gold. One pool =
    N × warden_pool_fights(F) fight-equivalents of damage, and one solo
    warden fight pays warden_gold for the same 3⚡ — so paying that many
    pools keeps the payout per energy at parity with the solo-tuned
    warden. 024: it reads the ramp, never the flat 8, or a two-fight
    gate would pay for eight."""
    return float(required_strikers(floor, active)
                 * warden_pool_fights(floor))


def milestone_quorum(floor: int, active: int | None = None) -> int:
    """022/002: milestone war parties sit on the same N(F) curve —
    never below the hand-set floor from the table."""
    ms = MILESTONES.get(floor)
    base = ms.quorum if ms else 2
    return max(base, required_strikers(floor, active))


# 034 §3: WARDEN_ECHO_MULT is gone. 022/001 let a fallen Warden be
# re-fought at its keep as an ECHO at half pay — a card that said in as
# many words that the real one died long ago, and then paid out for
# killing it again, forever. A Warden dies once; its keep is a memorial
# afterwards (engine/core._memorial_scene).


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


# 046: the hand-set stat table is gone — a linear boss row is dust
# against pillar-grown climbers by floor 40. The table keeps only the
# NAMES and war-party quorums; every stat rides the warden law
# (_build_milestones, after the forge tables it depends on). 012 rule
# preserved: milestone XP scarcer than its gold, in all places.
_MILESTONE_NAMES: dict[int, tuple[str, int]] = {
    10: ("Gnarl, the Goblin King", 2),
    20: ("Warlord Skarn", 3),
    30: ("The Barrow King", 4),
    40: ("Matriarch Vyx", 5),
    50: ("Cindermaw the Wyrm", 6),
    60: ("Jarl Hrimgar", 7),
    70: ("Zephyra, the Storm Queen", 8),
    80: ("The Pale Huntsman", 9),
    90: ("Malgrim, Herald of the King", 10),
    100: ("Vharuk, the Demon King", 12),
}

MILESTONE_HP_MULT = 1.6        # a milestone outguns its decade's warden
MILESTONE_ATK_MULT = 1.15
MILESTONE_FINALE_HP = 1.5      # Vharuk: the last door is the heaviest
MILESTONE_XP_MULT = 3          # × warden_xp — scarcer than the gold
MILESTONE_GOLD_MULT = 6        # × warden_gold

MILESTONES: dict[int, MilestoneBoss] = {}   # filled below the forge tables


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
    style: str = ""    # 025: "" plain | keen | warded (same rung, a choice)
    base: str = ""     # style variants: the plain slug they are cut from


# 004 §4.4 reprice: tiers 3–10 follow the quadratic ladder
# set(T) ≈ 2·(T−1) days of mid-band tier-(T−1) income, so days-in-tier
# (set + honing) lands on the 6→24 line without requiring the bank meta.
# 022/002 rescale: gear carries the growth past the level cap. Bonus
# ladders (anchored at the old tier-1 values so the first hour is
# untouched): weapon 30·T − 22, shield 10·T − 5, armor 16·T − 9.
_FORGE_ROWS = [
    # tier, weapon(name, flavor, +ATK), shield, armor, prices (w, s, a)
    # 049.1: was "Pigsticker" — a name with no weapon in it read as a
    # mystery on the attack row. Every blade says what it is now.
    (1, ("Scrap Dagger", "scrap-steel, but it's yours", 8),
        ("Scrapwood Buckler", "", 5), ("Padded Jerkin", "", 7),
        (250, 100, 200)),
    (2, ("Wolfbite", "shock-tip hunting spear", 38),
        ("Ironbound Targe", "", 15), ("Riveted Leather", "", 23),
        (800, 320, 640)),
    (3, ("Emberfang", "dwarf-forged plasma axe", 68),
        ("Dwarven Wall", "powered tower shield", 25), ("Chain Hauberk", "", 39),
        (6_500, 2_600, 5_200)),
    (4, ("Thornsong", "elven mono-edge blade", 98),
        ("Elfmirror", "light-bending", 35), ("Silverthread Mail", "", 55),
        (20_000, 8_000, 16_500)),
    (5, ("Oathkeeper", "knight's arc-blade", 128),
        ("Drakescale Barrier", "", 45), ("Wyrmhide Coat", "", 71),
        (47_000, 18_500, 37_500)),
    (6, ("Grimcleaver", "giant-slaying thunder maul", 158),
        ("Frostguard", "cold-field emitter", 55), ("Dwarven Powerplate", "", 87),
        (92_000, 36_500, 74_000)),
    (7, ("Starfall", "storm-cell saber", 188),
        ("Stormwarden's Aegis", "deflector", 65), ("Stormforged Plate", "", 103),
        (165_000, 65_000, 132_000)),
    (8, ("Duskrender", "phase-etched glaive", 218),
        ("Gloomturner", "cloak-field", 75), ("Nightweave Harness", "", 119),
        (277_000, 110_000, 222_000)),
    (9, ("Kingsbane", "demon-steel railblade", 248),
        ("Hellgate Bulwark", "", 85), ("Demonbone Panoply", "", 135),
        (443_000, 175_000, 356_000)),
    (10, ("Dawnbreaker", "fusion-core blade — the last light of Aldervale", 278),
         ("The Unbroken", "", 95), ("Aegis of the Vale", "", 151),
         (685_000, 271_000, 550_000)),
]

# 046: the table above keeps the NAMES and flavors; every bonus and
# price is overwritten here — the tier-1 anchors carried up the pillar
# to each band's first floor. Prices ride the FULL pillar (capital law):
# against income riding pillar/PACE, days-to-afford a band grows
# ×pace_wedge — that ratio IS the exponential climb time.
_GEAR_ANCHORS = ((8, 250), (5, 150), (7, 200))    # (bonus, ◈) w/s/a


def _round_price(n: float) -> int:
    """Prices keep 3 leading digits — readable at ◈10¹³."""
    n = max(10.0, n)
    step = 10 ** max(1, len(str(round(n))) - 3)
    return int(round(n / step) * step)


_EARLY_WEAPON_DISCOUNT = 0.8   # 047: first-five-floors weapons cheaper.
# Applies to the tier-1 sticker; sub-rungs fade it linearly to nothing
# by rung 1.5 (floor 5), so the price law is untouched from mid-band up.
_EARLY_WEAPON_FADE_RUNGS = 5

_FORGE_ROWS = [
    (t,
     (w[0], w[1], round(_GEAR_ANCHORS[0][0] * pillar((t - 1) * 10 + 1))),
     (s[0], s[1], round(_GEAR_ANCHORS[1][0] * pillar((t - 1) * 10 + 1))),
     (a[0], a[1], round(_GEAR_ANCHORS[2][0] * pillar((t - 1) * 10 + 1))),
     tuple(_round_price(anchor * pillar((t - 1) * 10 + 1)
                        * (_EARLY_WEAPON_DISCOUNT
                           if t == 1 and i == 0 else 1.0))
           for i, (_b, anchor) in enumerate(_GEAR_ANCHORS)))
    for t, w, s, a, _p in _FORGE_ROWS
]

# tier → bonus lookups for the reference model (single source: the rows)
_WEAPON_ATK_BY_TIER = {t: w[2] for t, w, _s, _a, _p in _FORGE_ROWS}
_SHIELD_DEF_BY_TIER = {t: s[2] for t, _w, s, _a, _p in _FORGE_ROWS}
_ARMOR_DEF_BY_TIER = {t: a[2] for t, _w, _s, a, _p in _FORGE_ROWS}


def _build_milestones() -> dict[int, MilestoneBoss]:
    """046: milestone stats ride the warden law (× the mults above).
    Called at the END of the module — the warden model reaches through
    the whole reference chain (forge tables, band math)."""
    out = {}
    for f, (name, quorum) in _MILESTONE_NAMES.items():
        w_atk, w_def, w_hp = warden_stats(f)
        hp = round(w_hp * MILESTONE_HP_MULT
                   * (MILESTONE_FINALE_HP if f == 100 else 1.0))
        out[f] = MilestoneBoss(
            f, name, round(w_atk * MILESTONE_ATK_MULT), w_def, hp, quorum,
            max(1, MILESTONE_XP_MULT * warden_xp(f)),
            max(1, MILESTONE_GOLD_MULT * warden_gold(f)))
    return out


# ── 004 §3.1: the mid rungs and the three weapon lines ──────────────────
# Between every tier T and T+1 a rung T.5: bonus = midpoint, price =
# geometric mean (rounded to ◈10) — days-to-afford stays smooth. Archer
# and sorcerer lines mirror the warrior numbers rung for rung; only the
# names differ. Names below; numbers all derive from _FORGE_ROWS.

_WARRIOR_MIDS = {
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

# 046: shoes reprice on the same capital law — the tier-1 anchor carried
# up the pillar from its own gate to each deeper gate.
_SHOE_ANCHOR = (500, 3)        # tier-1 boots: ◈, gate level
_SHOE_ROWS = [
    (t, n, f, spd,
     _round_price(_SHOE_ANCHOR[0] * pillar(lvl) / pillar(_SHOE_ANCHOR[1])),
     lvl)
    for t, n, f, spd, _price, lvl in _SHOE_ROWS
]


# ── 025 §4: band 1 sells something at every level ───────────────────────
# The complaint that opened 025: "I worked 3 days to advance a level only
# to find … I have no more things to buy at level 4." Band 1 had three
# gate moments across ten levels (rung 1 at level 1, the shoes at 3, the
# 1.5 mids at 6). It now has ten: rung 1.k opens at level 1+k.
#
# Numbers are not authored — they interpolate between the tier-1 and
# tier-2 rows: bonus linearly, price geometrically. At k=5 that IS the
# old mid (its bonus was the midpoint, its price the geometric mean), so
# every pre-025 piece keeps its exact power and price and the 1.5 names
# simply move into this table. Bands 2–10 keep the single mid until the
# 1–10 tuning settles (MUST_BE_DONE_LATER §4).
BAND1_STEPS = 10

_BAND1_LADDER = {
    "warrior": {
        1: ("Notched Cleaver", "a butcher's tool that changed trades"),
        2: ("Ratcatcher's Dirk", "thin, quick, and it knows the dark"),
        3: ("Boarspine Shortsword", "ground from a tusk that gored its owner"),
        4: ("Gatewatch Gladius", "surplus, stamped, sharpened by someone who "
            "cared"),
        5: ("Iron Sword", "honest forge-iron, honest weight"),
        6: ("Wolfsteel Broadsword", "quenched in the hide it took"),
        7: ("Goblin-Iron Falchion", "captured, straightened, resentful"),
        8: ("Warden's Cast-Off", "a keep blade, rehilted for smaller hands"),
        9: ("Emberquench Blade", "the last of the low forge's heat"),
    },
    "archer": {
        1: ("Green Hazel Bow", "cut this season, still learning"),
        2: ("Ratgut Shortbow", "the string is exactly what you fear it is"),
        3: ("Boarhorn Shortbow", "horn-tipped and boar-stubborn"),
        4: ("Gatewatch Shortbow", "surplus, stamped, honest"),
        5: ("Sinew-Backed Bow", "backed for the longer throw"),
        6: ("Wolfsinew Bow", "wolf tendon draws harder than hemp"),
        7: ("Goblin-Notch Bow", "taken off a straggler who missed"),
        8: ("Warden's Castbow", "a keep bow with the crest filed away"),
        9: ("Emberflight Shortbow", "nocks scorched black at the low forge"),
    },
    "sorcerer": {
        1: ("Kindling Rod", "it barely holds a spark — but it holds"),
        2: ("Ratbone Wand", "small bones, quick current"),
        3: ("Boarhide Stave", "wrapped in hide that took a beating first"),
        4: ("Gatewatch Baton", "issued to whoever could read"),
        5: ("Coalglass Staff", "coalglass core, banked heat"),
        6: ("Wolfsong Staff", "it howls a half-beat before you do"),
        7: ("Goblin-Fetish Staff", "someone else's god, borrowed"),
        8: ("Warden's Broken Rod", "cracked at the keep, mended in town"),
        9: ("Emberquench Staff", "banked low-forge heat in a walking stick"),
    },
    "shield": {
        1: ("Plank Shield", "a door that lost its house"),
        2: ("Ratskin Round", "cheap, light, faintly awful"),
        3: ("Boarhide Buckler", "hide over a boss of iron"),
        4: ("Gatewatch Round", "surplus, dented, dependable"),
        5: ("Banded Kite", "iron bands over ashwood"),
        6: ("Wolfhide Targe", "the pelt still turns a claw"),
        7: ("Goblin-Plate Buckler", "riveted from a dozen dead things"),
        8: ("Warden's Cast-Off Guard", "keep-issue, crest filed off"),
        9: ("Emberband Round", "banded hot, cooled slow"),
    },
    "armor": {
        1: ("Ratskin Vest", "it smells of the drain it came out of"),
        2: ("Quilted Rags", "layers, and layers, and layers"),
        3: ("Boarhide Jack", "thick exactly where it matters"),
        4: ("Gatewatch Surplus", "issued, returned, reissued"),
        5: ("Studded Jack", "canvas and rivets, better than luck"),
        6: ("Wolfpelt Coat", "warm, and it remembers hunting"),
        7: ("Goblin-Scrap Brigandine", "plates off a dozen dead things"),
        8: ("Warden's Cast Mail", "keep mail, resized badly"),
        9: ("Emberforge Scale", "scales set in the low forge"),
    },
    "focus": {
        1: ("Chipped Lens", "a spectacle lens with a change of career"),
        2: ("Ratbone Charm", "it rattles when the spell lands"),
        3: ("Boartooth Fetish", "a tusk, a thong, a stubborn spark"),
        4: ("Gatewatch Signet", "issued to whoever could read"),
        5: ("Sootglass Bead", "soot trapped in glass, and it glows"),
        6: ("Wolfeye Stone", "it looks back"),
        7: ("Goblin Idol-Shard", "a chip of someone else's altar"),
        8: ("Warden's Cracked Prism", "cracked, and the crack focuses"),
        9: ("Emberglass Lens", "low-forge glass, still faintly warm"),
    },
}

# ── 025 §4: styles — the same steel, three temperaments ─────────────────
# "we can have the same icon in different colours". A style is a real
# choice on the rung you can already afford, not a fourth rung: keen buys
# power with upkeep, warded buys upkeep with nothing. Same glyph, three
# tints (render.py), three prices.
#   (bonus ×, price ×, durability pool ×)
GEAR_STYLES: dict[str, tuple[float, float, float]] = {
    "keen": (1.15, 1.40, 0.65),
    "warded": (1.00, 1.20, 1.75),
}
STYLE_FLAVOR = {
    "keen": "ember-tempered — keener than it should be, and it knows it",
    "warded": "frost-warded — no keener, and it outlasts three of these",
}
STYLE_WORD = {"": "plain", "keen": "keen", "warded": "warded"}
# 025: styles exist through band 1 while the 1–10 climb is being tuned.
STYLE_MAX_RUNG = 2.0


def _slugify(name: str) -> str:
    return name.lower().replace("'", "").replace(" ", "_").replace(
        "—", "").replace(",", "").replace("-", "_")


def _gmean_price(a: int, b: int) -> int:
    return round(math.sqrt(a * b) / 10) * 10


def _gmean_bonus(a: int, b: int) -> int:
    """046: mid-rung bonuses are geometric means — an even % step on an
    exponential ladder (the arithmetic midpoint made the lower half of
    every band a cliff and the upper half a freebie)."""
    return round(math.sqrt(max(1, a) * max(1, b)))


def _step_bonus(base: int, top: int, k: int) -> int:
    """Bonus of sub-rung k between two whole tiers — 046: GEOMETRIC, so
    every band-1 rung is one pillar step (×1.3, matching the floor it
    unlocks on) and k=10 lands exactly on the next tier."""
    if k <= 0 or base <= 0:
        return base
    return round(base * (top / base) ** (k / BAND1_STEPS))


def _step_price(base: int, top: int, k: int) -> int:
    """Price of sub-rung k — geometric, so days-to-afford is even and
    k=5 lands exactly on the pre-025 mid's geometric mean."""
    return round(base * (top / base) ** (k / BAND1_STEPS) / 10) * 10


def _build_forge() -> dict[str, GearItem]:
    items: dict[str, GearItem] = {}

    def put(name: str, flavor: str, slot: str, rung: float, bonus: int,
            price: int, line: str = "", speed: int = 0, level: int = 0,
            style: str = "", base: str = ""):
        slug = _slugify(name)
        assert slug not in items, f"forge slug collision: {slug}"
        items[slug] = GearItem(slug, name, flavor, slot, int(rung), bonus,
                               price, line=line, rung=float(rung),
                               speed=speed, level=level, style=style,
                               base=base)
        return items[slug]

    rows = {t: (w, s, a, p) for t, w, s, a, p in _FORGE_ROWS}
    for tier, (w, s, a, (pw, ps, pa)) in rows.items():
        put(w[0], w[1], "weapon", tier, w[2], pw, line="warrior")
        put(s[0], s[1], "shield", tier, s[2], ps)
        put(a[0], a[1], "armor", tier, a[2], pa)

    # band 1: a rung per level, interpolated between T1 and T2
    (bw, bs, ba, (bpw, bps, bpa)) = rows[1]
    (tw, ts, ta, (tpw, tps, tpa)) = rows[2]
    for k in range(1, BAND1_STEPS):
        r = 1 + k / BAND1_STEPS
        n, f = _BAND1_LADDER["warrior"][k]
        # 047: the early discount fades out of the sub-rung stickers by
        # _EARLY_WEAPON_FADE_RUNGS; the ladder is priced off the full
        # (undiscounted) anchor so rung 1.5 up is byte-identical to 046.
        full_bpw = round(bpw / _EARLY_WEAPON_DISCOUNT)
        fade = (_EARLY_WEAPON_DISCOUNT
                + (1 - _EARLY_WEAPON_DISCOUNT)
                * min(k, _EARLY_WEAPON_FADE_RUNGS) / _EARLY_WEAPON_FADE_RUNGS)
        put(n, f, "weapon", r, _step_bonus(bw[2], tw[2], k),
            round(_step_price(full_bpw, tpw, k) * fade / 10) * 10,
            line="warrior")
        n, f = _BAND1_LADDER["shield"][k]
        put(n, f, "shield", r, _step_bonus(bs[2], ts[2], k),
            _step_price(bps, tps, k))
        n, f = _BAND1_LADDER["armor"][k]
        put(n, f, "armor", r, _step_bonus(ba[2], ta[2], k),
            _step_price(bpa, tpa, k))
        n, f = _BAND1_LADDER["focus"][k]
        put(n, f, "shield", r, _step_bonus(bs[2], ts[2], k),
            _step_price(bps, tps, k), line="sorcerer")

    for t in range(2, 10):
        w1, s1, a1, (pw1, ps1, pa1) = rows[t]
        w2, s2, a2, (pw2, ps2, pa2) = rows[t + 1]
        r = t + 0.5
        n, f = _WARRIOR_MIDS[r]
        put(n, f, "weapon", r, _gmean_bonus(w1[2], w2[2]),
            _gmean_price(pw1, pw2), line="warrior")
        n, f = _SHIELD_MIDS[r]
        put(n, f, "shield", r, _gmean_bonus(s1[2], s2[2]),
            _gmean_price(ps1, ps2))
        n, f = _ARMOR_MIDS[r]
        put(n, f, "armor", r, _gmean_bonus(a1[2], a2[2]),
            _gmean_price(pa1, pa2))

    # the other two weapon lines mirror the warrior numbers rung for rung
    warrior = {g.rung: g for g in items.values()
               if g.slot == "weapon" and g.line == "warrior"}
    for line, table in (("archer", _ARCHER_WEAPONS),
                        ("sorcerer", _SORCERER_WEAPONS)):
        rungs = dict(table)
        rungs.update({1 + k / BAND1_STEPS: nf
                      for k, nf in _BAND1_LADDER[line].items()})
        for r, (n, f) in rungs.items():
            ref = warrior[float(r)]
            put(n, f, "weapon", float(r), ref.bonus, ref.price, line=line)

    shields = {g.rung: g for g in items.values()
               if g.slot == "shield" and g.rung == int(g.rung)
               and not g.line}
    for t, (n, f) in _FOCUS_NAMES.items():
        ref = shields[float(t)]
        put(n, f, "shield", float(t), ref.bonus, ref.price, line="sorcerer")

    for t, n, f, spd, price, lvl in _SHOE_ROWS:
        put(n, f, "shoes", float(t), 0, price, speed=spd, level=lvl)

    # 025 §4: keen and warded cuts of every band-1 rung. Same rung, same
    # gate, same glyph in another tint — a decision at the counter rather
    # than a queue.
    plain = [g for g in list(items.values())
             if g.slot in ("weapon", "shield", "armor")
             and 1 <= g.rung < STYLE_MAX_RUNG]
    for g in plain:
        for style, (bm, pm, _pool) in GEAR_STYLES.items():
            bonus = (g.bonus if bm == 1.0
                     else max(g.bonus + 1, round(g.bonus * bm)))
            put(f"{style.title()} {g.name}", STYLE_FLAVOR[style], g.slot,
                g.rung, bonus, round(g.price * pm / 10) * 10,
                line=g.line, style=style, base=g.slug)
    return items


FORGE: dict[str, GearItem] = _build_forge()

SHOE_SPEED.update({g.slug: g.speed for g in FORGE.values()
                   if g.slot == "shoes"})

# Tier-0 gate issue, free at creation. Bare-handed ATK at level 1 is 3 vs
# floor-1 monsters at DEF 3 / HP 37 — ~1 damage a round, unwinnable. The
# basic weapon makes floor 1 hard-but-fair while keeping the ◈250 tier-1
# purchase a real first goal. Never sold (forge_tier lists tiers ≥ 1).
# 017 §1 / 049: the basic weapon is a floor, not a phase — one per class.
# It WEARS now (a plain tier-1 pool, 049) but is still never LOST: a
# replaced basic rides to the pack, death never takes it, and broken
# means half strength until the Forge mends it for pocket change.
# rusted_shiv stays as the pre-class / legacy-doc slug (same stats as
# the warrior sword).
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

# 049: the basic weapons — gate steel that wears but is never lost.
BASIC_WEAPONS = frozenset({STARTER_WEAPON.slug}
                          | {g.slug for g in CLASS_STARTERS.values()})


def wears(item: GearItem) -> bool:
    """049: does this piece spend a durability pool? All paid gear, plus
    the basic weapons — they carry a plain tier-1 pool now. The gate
    guard kit (buckler, jerkin) stays wear-free."""
    return item.price > 0 or item.slug in BASIC_WEAPONS

# 043: the gate issues the whole kit, not just the blade. Bar 1 is
# defined as "level 1 in the floor's reference gear" — so a fresh
# climber must BE bar 1, or floor 1's animals (tuned against that
# reference) would eat every newcomer before their first coin. The
# pieces match the rung-1.0 forge bonuses (shield 5, armor 7), tier 0:
# never sold, never wear, worth nothing at the pawn desk.
GATE_SHIELD = GearItem(
    "gate_buckler", "Gate-Issue Buckler",
    "armory plank, scuffed by a hundred hands before yours",
    "shield", 0, 5, 0)
GATE_ARMOR = GearItem(
    "gate_jerkin", "Gate-Issue Jerkin",
    "quilted in the standard cut — it has met wolves before",
    "armor", 0, 7, 0)
FORGE[GATE_SHIELD.slug] = GATE_SHIELD
FORGE[GATE_ARMOR.slug] = GATE_ARMOR


PAWN_BUYBACK = 0.40    # pre-006 flat rate; 006 makes it the band centre


def pawn_rate(day: int) -> float:
    """006 §3.8: the broker's mood — deterministic from the world day,
    uniform 25–55%. Everyone sees the same rate; patience is a trade."""
    x = (day * 2654435761) % 2 ** 32
    return 0.25 + 0.30 * (x / 2 ** 32)


def forge_tier(tier: int) -> list[GearItem]:
    return [g for g in FORGE.values() if g.tier == tier]


def gear_rungs(slot: str, line: str = "") -> list[GearItem]:
    """All PAID rungs of a slot (and weapon/focus line), rung-sorted —
    025: plain steel only. Style cuts hang off their plain rung
    (`gear_styles`) so a ladder stays a ladder."""
    return sorted((g for g in FORGE.values()
                   if g.slot == slot and g.line == line and g.rung >= 1
                   and not g.style),
                  key=lambda g: g.rung)


def gear_styles(g: GearItem) -> list[GearItem]:
    """The keen/warded cuts of a plain rung, in table order."""
    return [FORGE[s] for s in
            (_slugify(f"{st.title()} {g.name}") for st in GEAR_STYLES)
            if s in FORGE]


def style_of(slug: str) -> str:
    g = FORGE.get(slug)
    return g.style if g else ""


def weapon_line(line: str) -> list[GearItem]:
    return gear_rungs("weapon", line)


def _rung_gate_raw(g: GearItem) -> int:
    """The rung's natural threshold (a floor number): rung T.k opens k
    steps into its band, so T at band_start(T) and T.5 at band_start+5
    exactly as before 025 — band 1's nine sub-rungs land one per level.
    The shoes ladder carries explicit gates instead."""
    if g.level:
        return g.level
    t = int(g.rung)
    return band_start(t) + round((g.rung - t) * BAND1_STEPS)


def rung_player_level_req(g: GearItem) -> int:
    """PLAYER LEVEL gate for a forge rung — capped: past the cap the
    gate converts to a floor (rung_floor_req)."""
    return min(_rung_gate_raw(g), LEVEL_CAP)


def rung_floor_req(g: GearItem) -> int:
    """UNLOCKED FLOOR gate for rungs whose threshold sits past the
    level cap. 0 = level gate suffices."""
    r = _rung_gate_raw(g)
    return r if r > LEVEL_CAP else 0


# ── 048: the armory sells every line to everyone at list price ───────────
# The off-class system (×3 price, ×0.5 damage, 25% miss, arrow burn)
# died with the classes — the trained rank is the only tax on a weapon
# in the wrong hands now. The gate-issue basics of the other two lines
# sell for a flat coin so ANY climber can start a second path.

BASIC_WEAPON_PRICE = 60        # basic_bow / worn_staff off the wall —
                               # wears (049), never lost, never sold back
ARROW_PACK_SIZE = 10           # legacy — old packs still hold arrows
ARROW_PACK_PRICE = 120

ARCANUM_LEVEL = 3              # 0.29.1: was 6 — the shop arrives when
                               # class identity lands, not four levels on

# 007 town readability: every not-day-1 door reads its level from the
# square. 0.29.1 re-gate: gates exist for PROTECTION (mercy, pvp) or
# pacing a confusing system — never as a reward for persistence. The
# daily-texture doors (relay, board, night slot) open at 2 in one
# "the town wakes up for you" beat; the fields stay post-mercy.
RELAY_LEVEL = 2                # was 3
FIELDS_LEVEL = 5


def line_twin(g: GearItem, line: str) -> GearItem | None:
    """The same rung of another weapon line. The three lines mirror each
    other rung for rung — same bonus, same price — so trading a piece for
    its twin costs its holder nothing."""
    if g.slot != "weapon" or g.rung < 1 or not line or g.line == line:
        return None
    for other in FORGE.values():
        if (other.slot == "weapon" and other.line == line
                and other.rung == g.rung and other.style == g.style):
            return other
    return None


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
    """046: honing is CAPITAL — 15% of a floor-1 day at the anchor,
    riding the full pillar (×pace_wedge in day terms), because a hone
    step now IS a floor's worth of power on that piece."""
    return max(5, round(HONE_PRICE_PCT * daily_income(unlocked_floor)
                        * pace_wedge(unlocked_floor)))


# ── §6d Durability (005 §3.5) ────────────────────────────────────────────
# Power is a running cost, not a plateau. Every PAID piece carries a
# use pool sized against a day of at-level hunting (≈30 fights × ~6
# rounds — the same model daily_income anchors on): a blade or a pair of
# boots runs about a week, a guard piece about 2.4 days, and nothing
# breaks inside a single day at any band. Pools GROW with tier but
# repair scales with price, so the gold-per-use climbs anyway: the
# running-cost tax rises smoothly from ~11% of daily income at T1 to
# ~16% at T10. (The pre-plan's "better gear wears faster" pool CURVE
# failed the ≤20%-of-income gate by up to 14× at T10 — the tax keeps the
# intent, the pool direction had to flip.)
# 049: the basic WEAPONS carry a plain tier-1 pool too (repair is
# pocket change — price 0 floors the bill at ◈1); the gate guard kit
# stays wear-free. Broken means half strength, never helpless.

DURABILITY_BASE = 1300
DURABILITY_GROWTH = 0.25
DURABILITY_SLOTS = ("weapon", "shield", "armor", "shoes")

# 035: 0.20 → 0.13. Both guard slots now spend themselves on damage rather
# than on rounds, which triples their event count; the repair-tax gate
# (≤20% of daily income, no step-function between bands) is linear in that
# count, so the price per point has to come down to meet it. 0.13 puts the
# daily bill on exactly the 034 ceiling (0.161 of income at the worst band)
# and improves the band step. Same gold a day, a bench visit that is
# cheaper and far more frequent — which is the point: the bar has to move
# where the player can see it.
REPAIR_PRICE_PCT = 0.13        # of item price × missing fraction

# 034 §1 / 035: a guard piece is spent on DAMAGE, not on rounds. Weapon and
# boots still tick one use per swing and per stride; the shield and the
# plate pay for what they actually turned, so the number the card narrates
# and the number the bench bills are finally the same thing.
# 3, not 4: 4 tips the band 1→2 step over the cliff tolerance even at the
# lowered repair price. 3 burns a guard ~3× faster than the flat point it
# replaces — ~2.4 hunting days out of a tier-1 buckler or jerkin.
ARMOR_WEAR_RATE = 3            # 035: the plate meets every blow — bill it

# A bought shield turns 50× its own block, then breaks. The flat rate it
# replaces read as ~217× block at tier 1 and ran past 700× at depth —
# a pool nobody would ever see the bottom of. The rate scales with the
# piece's own pool so END is 50·block on every rung; the sticker anchor
# pays for the endurance (100 → 150, the 30×-floor price plus two thirds).
SHIELD_END_PER_BLOCK = 50


def shield_wear_rate(rung: float) -> float:
    """Uses per evenly-met blow for a shield of this rung — sized so the
    fresh pool empties after exactly `SHIELD_END_PER_BLOCK × block` of
    turned damage (2·50 even blows, whatever the tier)."""
    return durability_pool(rung) / (2 * SHIELD_END_PER_BLOCK)


def durability_pool(tier: float) -> int:
    """Uses in a fresh piece of this tier (mids sit between wholes)."""
    t = max(1.0, float(tier))
    return round(DURABILITY_BASE * (1 + DURABILITY_GROWTH * (t - 1)))


def guard_wear(blocked: int, bonus: int, total_def: int,
               rate: float) -> int:
    """034 §1 / 035: uses spent by a guard piece that turned `blocked`.

    The piece's share of the guard is `bonus / DEF`, and that share is
    priced against the piece's own rating (`bonus / 2`, what a fresh rung
    turns on an even blow) — the two cancel, which is the point: the pace
    is the same at tier 1 and tier 10 instead of running hotter at depth,
    where `blocked` grows with DEF but the pool grows only 25% a tier.
    The cancellation also means shield and plate spend the same on the
    same blow, which is the honest reading — they met it together.

    A blow that chips straight through costs the floor of one use; a blow
    fully met costs `rate`.
    """
    if blocked <= 0 or bonus <= 0 or total_def <= 0:
        return 1
    blocked_by_piece = blocked * bonus / total_def
    even_blow = bonus / 2
    return max(1, round(rate * blocked_by_piece / even_blow))


def shield_wear(blocked: int, shield_bonus: int, total_def: int,
                rung: float = 1.0) -> int:
    return guard_wear(blocked, shield_bonus, total_def,
                      shield_wear_rate(rung))


def armor_wear(blocked: int, armor_bonus: int, total_def: int) -> int:
    return guard_wear(blocked, armor_bonus, total_def, ARMOR_WEAR_RATE)


def item_pool(item: GearItem) -> int:
    """Pool for a specific piece — mid-rungs (rung 1.5, 2.5…) wear a
    touch faster than the whole tier below them, so the rung is the
    truth when the item carries one. 025: the style is the other half of
    the truth — keen steel is spent steel, warded steel is patient."""
    pool = durability_pool(item.rung or item.tier)
    if item.style:
        pool = round(pool * GEAR_STYLES[item.style][2])
    return pool


def endurance(item: GearItem, left: int | None = None) -> int:
    """045: the END number on the card — one honest unit per slot.

    Guard pieces (shield/armor) show the DAMAGE the piece can still turn:
    wear per blow is `rate · blocked_by_piece / (bonus/2)` pool-uses, so
    `pool · bonus / (2·rate)` is damage — the number falls by what the
    piece absorbs, which is how a player reads "endurance 100, blows of
    54+36+10, broken". Weapons/shoes already wear one use per
    swing/stride, so their pool IS the count.
    """
    pool = item_pool(item) if left is None else max(0, left)
    if item.slot == "shield":
        return round(pool * item.bonus
                     / (2 * shield_wear_rate(item.rung or item.tier)))
    if item.slot == "armor":
        return round(pool * item.bonus / (2 * ARMOR_WEAR_RATE))
    return pool


def gear_card_stats(item: GearItem, left: int | None = None) -> str:
    """011: a pack piece's numbers as one hint fragment — the stat it
    grants, the durability it carries (a worn piece says what's left of
    full, in the same units `endurance` puts on every shop card), and
    its style word. Reused by every card that shows a piece leaving the
    pack: the chest's PUT wall, the pawn shop's donate rows."""
    stat = ("+{} spd".format(item.speed) if item.slot == "shoes"
            else ("+{} ATK".format(item.bonus) if item.slot == "weapon"
                  else "+{} DEF".format(item.bonus)))
    if left is not None and left < item_pool(item):
        dur = (f"durability {endurance(item, left):,} "
               f"of {endurance(item):,}")
    else:
        dur = f"durability {endurance(item):,}"
    parts = [stat, dur]
    if item.style:
        parts.append(STYLE_WORD[item.style])
    return " · ".join(parts)


def repair_price(item: GearItem, missing_frac: float) -> int:
    """The Forge mends for a fraction of what the smith charged.
    046: repair is a RUNNING cost — the pillar-riding sticker price is
    discounted back to the income curve (÷pace_wedge at the piece's own
    gate), so the daily repair tax stays the same share of a hunting
    day at every band instead of eating the whole income at depth."""
    running = item.price / pace_wedge(_rung_gate_raw(item))
    return max(1, round(REPAIR_PRICE_PCT * running
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
    line: str = ""         # weapon-line-locked purchase ("" = anyone;
                           # 048: sold to whoever HOLDS that line)
    hold1: bool = False    # own at most one at a time
    group: str = ""        # per-fight exclusivity ("life")


# 025 §4: the tactical shelf comes down to meet the archetypes. Before
# 025 the counters (curse, strip, hook, quivers) mostly sat at floor 11
# while the traits they answer appear from floor 2 — so the first ten
# floors sold a climber nothing but steel, and a walled matchup was a
# wall rather than a shopping list. Each counter now lands one floor
# after the trait it answers arrives (TRAIT_INTRO_FLOOR), which is also
# the "upgrades buy access, not comfort" rule with a price tag on it.
RELICS: dict[str, Relic] = {r.slug: r for r in [
    # 010 retune (2026-07-28): quivers 0.3→0.2 DI, piercing 0.5→0.35.
    # The stacked-drain gate charges each class one wall-push a day
    # (~3 special arrows); at the old prices the push stacked repairs
    # + the death line past the 40%-of-daily-income ceiling.
    Relic("poison_arrows", "Poisoned Arrows",
          "true damage for 3 rounds — seeps past any plate",
          "no stacking; Wardens and venomproof things shrug it off",
          0.2, 4, "forge", count=5),
    Relic("slowing_arrows", "Slowing Arrows",
          "the target drops 2 speed for the fight — the kiting answer",
          "wears off with the fight; wasted on anything already slow",
          0.2, 5, "forge", count=5),
    Relic("piercing_arrows", "Piercing Arrows",
          "the shot ignores armor tiers entirely",
          "five to a quiver, archer hands only",
          0.35, 8, "forge", count=5, line="archer"),
    Relic("fire_arrows", "Fire Arrows",
          "+50% burst on the shot; burns regeneration out",
          "plate still turns fire-tipped shafts like any arrow",
          0.2, 8, "forge", count=5),
    Relic("weapon_oil", "Weapon Oil",
          "your next 10 strikes hit +25% — steel or string, always works",
          "ten strikes, then the flask is gone",
          0.2, 2, "forge"),
    Relic("entangling_net", "Entangling Net",
          "the monster loses its round tangled — it cannot close or flee",
          "three to a pack; a Warden tears through it instantly",
          0.25, 5, "forge", count=3, line="warrior"),
    Relic("sky_hook", "Sky-Hook",
          "your steel reaches the airborne for this whole fight",
          "five uses a hook, one burned per fight",
          0.4, 6, "forge", count=5, line="warrior"),
    # 010 retune (2026-07-28): vials 0.3→0.1 DI. One vial is one FIGHT,
    # so at 0.3 the mage's wall-push cost 3.6× the warrior's net and
    # broke the stacked-drain ceiling at every band; 0.1 puts all three
    # classes' per-push cost in the same 0.08–0.12 DI lane.
    Relic("strip_potion", "Resistance-Strip Potion",
          "dissolves the target's spellguard for the fight",
          "one fight, one vial",
          0.1, 4, "arcanum", line="sorcerer"),
    Relic("curse_scroll", "Curse Scroll",
          "halves the target's plate for the fight",
          "one fight, one scroll",
          0.1, 3, "arcanum", line="sorcerer"),
    Relic("polymorph_dust", "Polymorph Dust",
          "the monster becomes a harmless critter — the fight simply ends",
          "no loot, no XP, never works on Wardens; one pinch",
          1.2, 21, "arcanum", line="sorcerer"),
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
# 031 §8: death is taxed at EVERY level — even the daily shard save takes
# half the carried coin. Past DEATH_NO_PARDON_LEVEL there is no pardon:
# 90% of carried coin and one random pack stack go with you.
DEATH_GOLD_MIN = 0.50
DEATH_GOLD_MAX = 0.60
DEATH_NO_PARDON_LEVEL = 6      # = BEGINNER_PROTECTION_MAX_LEVEL + 1
DEATH_GOLD_NO_PARDON = 0.90
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


def relic_stock(shop: str, frontier: int, lines) -> list[Relic]:
    """What this shop shows this player, catalog order. `lines` is the
    set of weapon lines in the player's hands (048: the weapon decides
    who a line-locked relic sells to)."""
    return [r for r in RELICS.values()
            if r.shop == shop and frontier >= r.floor
            and (not r.line or r.line in lines)]


# ── §6c Healing (008, repriced by 013, dawn law by 022/004) ─────────────
# The law: dawn closes every wound — HP restores to FULL at the world-day
# boundary and ONLY there. No daytime trickle, so mid-session healing
# still costs gold and still buys time: stew (2g, +5 HP, repeatable) →
# healer's tent (5×floor, full) → potions for mid-fight emergencies.
# The Lodge's old +20-at-dawn special case is retired — the Lodge sells
# a SAFE night (nobody finds you), never health.

STEW_PRICE = 2
STEW_HEAL_HP = 5
HEALER_TENT_PER_FLOOR = 5      # full heal: ◈ 5 × floor (was 2 pre-013)

# ── §7 Bank, death, lodge, presents ──────────────────────────────────────

REPAIR_TOKEN_VALUE = 60             # the broker's basis for a repair
                                    # token — roughly one mid-band mend
BANK_INTEREST_RATE = 0.05           # 5%/day, dripped as slice STUBS (023/041)
BANK_INTEREST_TICKS = 5             # slices per day — 1% every 24/5 hours
INTEREST_STUB_CAP = 150             # the clerk keeps a month of slices —
                                    # no infinite rewards for the absent
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
    (8, "repair_token"),   # redeemed at the Forge (one free mend) or
                           # pawned at REPAIR_TOKEN_VALUE × the day's rate
    (2, "jackpot"),        # rare item or bank doubling capped 1000×level
]

# ── §8 Social economy ────────────────────────────────────────────────────

GRANT_BURN_PCT = 0.10
GRANT_DAILY_CAP_PER_LEVEL = 150
# 036: the receiver level gate is gone — any climber can be granted gold.
# The burn and the sender's daily cap remain the anti-funnel valves.
LETTER_PRICE = 0        # 004 §C.1: talking is free if collaboration is the game
BOARD_PRICE = 10        # 022/004: the broker's stamp — off the top of payouts

# ── §8b The contract board (022 §004) ────────────────────────────────────
# Three jobs a world day, seeded from the DAY like the pawn broker's
# mood — the whole tower reads one board and can talk about it. Payouts
# are a BONUS on work you'd hunt anyway (a cull pays ~80% of the kills'
# raw gold on top of the kills themselves), never a wage that replaces
# the grind. XP rides at half weight — XP stays scarce (012).

BOARD_LEVEL = 2                  # 0.29.1: was 4 — the board is the day's
                                 # texture; pay is reach-capped (contracts
                                 # .pay_for), so early hands earn early gold
BOARD_JOBS_PER_DAY = 3
CONTRACT_CULL_GOLD_MULT = 0.8    # × N kills' base gold on the named floor
CONTRACT_CULL_XP_MULT = 0.5      # × N kills' base XP
CONTRACT_PATH_GOLD_MULT = 0.5    # weapon-path jobs price off mid-tower
CONTRACT_PATH_XP_MULT = 0.5
CONTRACT_WARDEN_MULT = 0.5       # × warden pay at the frontier
CONTRACT_TOKEN_CHANCE = 0.25     # a job carries a repair token sometimes

# ── §8c Nights & weeks (022 §005) ────────────────────────────────────────
# The night slot: ONE action per night at the Lodge — rest (bank rested
# aether, paid out as bonus XP on kills only) or work (gold at dawn).
# Deliberately shallow; professions with ranks stay deferred and this
# slot is their future socket. Rested is modest ON PURPOSE — XP is the
# scarce resource (012) and the climb is the game, so a night banks 4%
# of the current level bar, capped at 3 nights' accrual, drawn down at
# +25% per kill. Work pays 20% of a hunting day and never touches the
# Energy cell's 1/day ceiling (the cell cap is the whole safety
# mechanism for offline gold).

NIGHT_SLOT_LEVEL = 2           # 0.29.1: was 6 — going to bed with a plan
                               # IS the early hook; income scales with
                               # floor, not level, so it can't be abused
NIGHT_WORK_INCOME_PCT = 0.20
NIGHT_REST_PCT_OF_BAR = 0.04
RESTED_XP_BONUS_PCT = 0.25
RESTED_POOL_CAP_NIGHTS = 3
NIGHT_SHIFTS = ("the forge shift", "the bar shift", "the palisade watch")


def night_work_gold(floor: int) -> int:
    return max(1, round(NIGHT_WORK_INCOME_PCT * daily_income(floor)))


def night_rest_aether(level: int) -> int:
    return max(1, round(NIGHT_REST_PCT_OF_BAR * xp_need(level)))


def rested_pool_cap(level: int) -> int:
    return RESTED_POOL_CAP_NIGHTS * night_rest_aether(level)


# The weekly strongbox (Vault, level 10): three counters the game
# already tracks — kills, warden engagements, floors gained — sum to
# activity points; thresholds open 1/2/3 reward slots; at the weekly
# tick the player picks EXACTLY ONE reward. Unpicked weeks fall back
# to the lowest slot, never to nothing.

STRONGBOX_LEVEL = 6            # 0.29.1: was 10 — the weekly rhythm
                               # arrives once the daily one is habit
STRONGBOX_THRESHOLDS = (2, 4, 6)      # points → slots 1 / 2 / 3
STRONGBOX_GOLD_PCT_OF_DAY = 0.5       # slot 1: half a hunting day
STRONGBOX_AETHER_PCT_OF_BAR = 0.10    # slot 2: a tenth of the level bar


def strongbox_gold(floor: int) -> int:
    return max(1, round(STRONGBOX_GOLD_PCT_OF_DAY * daily_income(floor)))


def strongbox_aether(level: int) -> int:
    return max(1, round(STRONGBOX_AETHER_PCT_OF_BAR * xp_need(level)))


# §8d — 022/008: together — the flare, assist strikes, the long fire.
# 80% of "fighting side by side" without synchronous combat: a dying
# climber can call the floor, an answerer is paid and remembered, and
# two blades on the same prey inside minutes link their logs.
FLARE_HP_PCT = 0.25            # the flare option appears below this bar
FLARE_AETHER = 10              # XP burned to send it — a cry costs
FLARE_TTL_MIN = 30             # a flare gutters out after this (server law)
FLARE_ANSWER_GOLD_MULT = 0.5   # × gold_per_kill(floor), paid to the answerer
FLARE_ANSWER_AETHER = 10       # XP paid to the answerer
ASSIST_WINDOW_MIN = 15         # linked-log window on the same prey
ASSIST_BONUS_PCT = 0.25        # × the kill's gold — the finisher's bonus
FIRE_STEW_GOLD = 5             # stand a stranger a stew at the long fire
FIRE_WORDS = (                 # canned only — no free chat, no moderation
    "Long day. Good fire.",
    "The tower creaked twice tonight. Count it.",
    "Whoever left stew in the pot — thank you.",
    "Sharpen before you sleep. Dawn forgets nothing.",
    "Heard a flare answered on the high floors. Good.",
)


def flare_answer_gold(floor: int) -> int:
    return max(1, round(FLARE_ANSWER_GOLD_MULT * gold_per_kill(floor)))


# ── Races & classes ──────────────────────────────────────────────────────

# 009: three lines climb the Ascent — the halfling listing is retired
# (doc v4 re-registers existing halflings as human). 052: the dwarf
# line is re-carved GIANT (doc v10) — same Stubborn perk, a frame two
# heads taller; the fusion-halls stay theirs.
RACES = {
    "human": "Adaptable: +1 energy cap. Port-town survivors.",
    "elf": "Keen: +5% experience from kills. Their bio-lit forest is floor 23.",
    "giant": "Stubborn: +5% armor value. The fusion-halls are floors 11-20.",
}

# 046: last — the milestone stats read the whole model above.
MILESTONES.update(_build_milestones())
