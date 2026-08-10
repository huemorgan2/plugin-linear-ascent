"""046 balance simulator — a headless climb of the whole tower.

Personas play day-by-day against the REAL economy functions (no HTTP,
no engine state machine): energy-budget accounting, Monte-Carlo fights
(the gen_mechanics model), real prices, real XP. Output: one JSONL of
per-floor records per (persona, seed) under plans/046-.../runs/, read
by the balance gates and the conclusions notes.

    python3 tools/sim046.py [--max-floor N] [--personas a,b] [--tag t]

v1 scope (deliberate): warrior/melee vs the floor's common (peer)
monster; hone steps bought with gold (hone_price), XP hone cost
ignored; deaths ignored (win%% stays >= ~85 by design); floors > 30
warden gates are pooled/multiplayer and counted as one scheduling day.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

from plugin_linear_ascent import economy as eco  # noqa: E402

RUNS_DIR = os.path.join(_HERE, "plans", "046-thirty-percent-a-floor",
                        "runs")

FIGHTS_PER_DAY = round(24 * 60 / eco.ENERGY_REGEN_MIN)        # 32
WARDEN_ATTEMPTS_PER_DAY = FIGHTS_PER_DAY // eco.COST_WARDEN_ATTEMPT
MC_SIMS = 200
MAX_ROUNDS = 400
MAX_DAYS_PER_FLOOR = 3650          # runaway guard: file as CRITICAL


# ── the gear ladder the sim can buy (reference shapes, real prices) ──────

def _tier_row(tier: int):
    for t, w, s, a, p in eco._FORGE_ROWS:
        if t == tier:
            return w[2], s[2], a[2], p
    raise KeyError(tier)


def _geo(a: float, b: float, k: float) -> float:
    return a * (b / a) ** k if a > 0 else b * k


def ladder(slot: str):
    """[(rung, bonus, price)] — whole tiers + mid rungs (bonus midpoint,
    price geometric mean), band-1 sub-rungs as tenth-steps (the 025 rung
    ladder: bonus via _step_bonus, price geometric)."""
    si = {"weapon": 0, "shield": 1, "armor": 2}[slot]
    out = []
    w1 = _tier_row(1)
    w2 = _tier_row(2)
    for k in range(0, eco.BAND1_STEPS):          # rung 1.0 … 1.9
        bonus = eco._step_bonus(w1[si], w2[si], k)
        price = round(_geo(w1[3][si], w2[3][si], k / eco.BAND1_STEPS))
        out.append((1 + k / 10, bonus, price))
    for t in range(2, 11):
        lo, hi = _tier_row(t), None
        out.append((float(t), lo[si], lo[3][si]))
        if t < 10:
            hi = _tier_row(t + 1)
            out.append((t + 0.5, eco._gmean_bonus(lo[si], hi[si]),
                        round(_geo(lo[3][si], hi[3][si], 0.5))))
    return out


LADDERS = {}


def next_step(slot: str, rung: float):
    """(new_rung, bonus, price) one rung up, or None at the top."""
    lad = LADDERS[slot]
    for r, b, p in lad:
        if r > rung + 1e-9:
            return r, b, p
    return None


def rung_bonus(slot: str, rung: float) -> int:
    lad = LADDERS[slot]
    best = lad[0][1]
    for r, b, _ in lad:
        if r <= rung + 1e-9:
            best = b
    return best


# ── the fight model (gen_mechanics mirror, melee vs peer) ────────────────

def fight_stats(rng, floor, p_atk, p_def, p_hp):
    """(win%, mean rounds) vs the floor's common peer monster."""
    m_atk, m_def, m_hp0 = eco.creature_stats(floor, ())
    wins = rounds_acc = 0
    for _ in range(MC_SIMS):
        php, mhp = p_hp, m_hp0
        at_range, rounds = True, 0
        while rounds < MAX_ROUNDS:
            rounds += 1
            if at_range:                     # the crossing: halved blow
                at_range = False
                raw = rng.randint(m_atk // 2, m_atk)
                chip = max(1, -(-raw // eco.CHIP_DIVISOR))
                php -= max(chip, raw - p_def // 2) // 2
                if php <= 0:
                    break
                continue
            raw = rng.randint(p_atk // 2, p_atk)
            mhp -= max(1, raw - m_def // 2)
            if mhp <= 0:
                wins += 1
                break
            raw = rng.randint(m_atk // 2, m_atk)
            chip = max(1, -(-raw // eco.CHIP_DIVISOR))
            php -= max(chip, raw - p_def // 2)
            if php <= 0:
                break
        rounds_acc += rounds
    return wins / MC_SIMS, rounds_acc / MC_SIMS


# ── the player ───────────────────────────────────────────────────────────

class Player:
    def __init__(self, persona: str, seed: int):
        self.persona = persona
        self.rng = random.Random(seed)
        self.level, self.xp, self.gold = 1, 0, 0
        self.rung = {"weapon": 1.0, "shield": 1.0, "armor": 1.0}
        self.hone = {"weapon": 0, "shield": 0, "armor": 0}
        self.spent = {"gear": 0, "hone": 0, "training": 0}
        self.earned = {"kills": 0}
        self.race = ""

    def stats(self):
        wb = eco.honed_bonus(rung_bonus("weapon", self.rung["weapon"]),
                             self.hone["weapon"])
        sb = eco.honed_bonus(rung_bonus("shield", self.rung["shield"]),
                             self.hone["shield"])
        ab = eco.honed_bonus(rung_bonus("armor", self.rung["armor"]),
                             self.hone["armor"])
        return (eco.player_atk(self.level, wb),
                eco.player_def(self.level, sb, ab),
                eco.player_max_hp(self.level, ab))

    def energy_share(self):
        return {"optimal": 1.0, "casual": 1 / 3, "skinflint": 1.0,
                "hoarder": 1.0}.get(self.persona, 1.0)


def buy_priority(p: Player, floor: int):
    """The cheapest real power step: next rung per slot, else a hone
    (capped at floors-past-band-start, the forge law)."""
    steps = []
    for slot in ("weapon", "shield", "armor"):
        nxt = next_step(slot, p.rung[slot])
        if nxt:
            steps.append(("rung", slot) + nxt)
    tier = eco.gear_tier_for_floor(floor)
    max_hone = max(0, floor - eco.band_start(tier))
    for slot in ("weapon", "shield", "armor"):
        if p.hone[slot] < max_hone:
            steps.append(("hone", slot, p.hone[slot] + 1, 0,
                          eco.hone_price(floor)))
    steps.sort(key=lambda s: s[4])
    return steps[0] if steps else None


def gate_days(p: Player, floor: int) -> float:
    """Days to open floor `floor`'s gate solo (<=30) — pooled past 30."""
    if floor > eco.WARDEN_SOFT_FLOOR:
        return 1.0                      # coordination is scheduling, not pace
    p_atk, p_def, p_hp = p.stats()
    w_atk, w_def, w_hp = eco.warden_stats(floor)
    pool = eco.world_warden_hp(floor, None)
    p_dmg = max(1, round(0.75 * p_atk) - w_def // 2)
    if floor >= eco.WARDEN_PROFILE_FLOOR:
        p_dmg = max(1, round(p_dmg * eco.TIER_MULT["low"]))
    w_dmg = max(1, round(0.75 * w_atk) - p_def // 2)
    rounds = max(1, (p_hp - 1) // w_dmg)
    per_attempt = rounds * p_dmg
    per_day = WARDEN_ATTEMPTS_PER_DAY * p.energy_share() * per_attempt
    return max(0.1, pool / per_day)


def sim_climb(persona: str, seed: int, max_floor: int, tag: str):
    p = Player(persona, seed)
    rng = p.rng
    recs = []
    for floor in range(1, max_floor + 1):
        days, spend0 = 0.0, dict(p.spent)
        stuck_reason = ""
        win = 0.0
        while days < MAX_DAYS_PER_FLOOR:
            p_atk, p_def, p_hp = p.stats()
            win, _rounds = fight_stats(rng, floor, p_atk, p_def, p_hp)
            # ready to move ON: you can face the NEXT floor's animals
            # (>= 75%, the between-bars band) and pass its level leash
            win_next, _ = fight_stats(rng, min(floor + 1, 100),
                                      p_atk, p_def, p_hp)
            ready = win_next >= 0.75 and (
                p.level >= eco.floor_entry_player_level(floor + 1))
            if ready:
                break
            days += 1
            fights = FIGHTS_PER_DAY * p.energy_share()
            gk = eco.gold_per_kill(floor)
            tent = eco.healer_tent_price(floor) / 3
            p.gold += round(fights * (win * gk - tent))
            p.earned["kills"] += round(fights * win * gk)
            p.xp += round(fights * win * eco.xp_per_kill(floor))
            # train first (levels gate floors), then cheapest gear step
            while (p.level < eco.LEVEL_CAP
                   and p.xp >= eco.xp_need(p.level)
                   and p.gold >= eco.levelup_gold(p.level)):
                p.gold -= eco.levelup_gold(p.level)
                p.spent["training"] += eco.levelup_gold(p.level)
                p.xp -= eco.xp_need(p.level)
                p.level += 1
            if persona != "skinflint" or win < 0.60:
                step = buy_priority(p, floor)
                if step and p.gold >= step[4]:
                    kind, slot, val, bonus, price = step
                    p.gold -= price
                    if kind == "rung":
                        p.rung[slot] = val
                        p.spent["gear"] += price
                    else:
                        p.hone[slot] = val
                        p.spent["hone"] += price
        else:
            stuck_reason = "MAX_DAYS reached — dead end"
        gd = gate_days(p, floor)
        days += gd
        recs.append({
            "floor": floor, "days": round(days, 2),
            "gate_days": round(gd, 2), "win_pct": round(100 * win),
            "level": p.level, "gold": p.gold,
            "rung_w": p.rung["weapon"], "hone_w": p.hone["weapon"],
            "spent_gear": p.spent["gear"] - spend0["gear"],
            "spent_hone": p.spent["hone"] - spend0["hone"],
            "stuck": stuck_reason,
        })
        if stuck_reason:
            break
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, f"{tag}-{persona}-s{seed}.jsonl")
    with open(path, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    return recs, path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-floor", type=int, default=100)
    ap.add_argument("--personas", default="optimal,casual,skinflint")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tag", default="baseline")
    args = ap.parse_args()
    for slot in ("weapon", "shield", "armor"):
        LADDERS[slot] = ladder(slot)
    for persona in args.personas.split(","):
        recs, path = sim_climb(persona, args.seed, args.max_floor,
                               args.tag)
        total = sum(r["days"] for r in recs)
        print(f"\n== {persona} — {total:.0f} days to floor "
              f"{recs[-1]['floor']} -> {path}")
        print("floor days gate win lvl rung_w hone_w")
        for r in recs:
            if r["floor"] % 10 == 0 or r["floor"] <= 3 or r["stuck"]:
                print(f"{r['floor']:>4} {r['days']:>6} {r['gate_days']:>5}"
                      f" {r['win_pct']:>3}% {r['level']:>3}"
                      f" {r['rung_w']:>5} {r['hone_w']:>5}"
                      f" {r['stuck']}")


if __name__ == "__main__":
    main()
