"""008 — tune encounter WEIGHTS on floors 11-100 so the smoothness
gates pass.

Traits set the texture (what each floor is made of); weights set the
mix (how often you meet each thing).  The smoothness gate measures the
weighted mix, so weights are the right knob: no trait, pool or spread
rule can be broken by re-weighting, and the linter proves it after.

Uses the EXACT math from tests/test_smoothness.py (imported, not
copied) to precompute per-encounter metrics, then runs a greedy local
search over integer weights 1-4 (bulwarks capped at 2 — elites stay
rare) minimising gate violations plus a small drift penalty that keeps
weights close to the authored ones.  Floors 1-10 are 001-tuned and
frozen.  Writes `weight:` lines back into the YAML in place.
"""

import importlib.util
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from plugin_linear_ascent import economy              # noqa: E402
from plugin_linear_ascent.content import schema       # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "smoothness", ROOT / "tests" / "test_smoothness.py")
sm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sm)

FLOORS = list(range(1, 101))
TUNABLE = set(range(11, 101))
CLASSES = list(economy.DAMAGE_TYPE)


# ---- precompute per-encounter metrics (weights are the only variable)

class Enc:
    __slots__ = ("id", "weight", "orig", "bulwark", "gold_mult",
                 "per_class")

    def __init__(self, floor, e):
        profile = economy.profile_from_traits(e.traits)
        self.id = e.id
        self.weight = e.weight
        self.orig = e.weight
        self.bulwark = profile["bulwark"]
        self.gold_mult = economy.profile_gold_mult(profile)
        self.per_class = {}
        _, _, m_hp = economy.monster_stats(floor)
        for clazz in CLASSES:
            if not sm._is_intended(clazz, profile):
                self.per_class[clazz] = None
                continue
            dmg = sm._expected_player_damage(clazz, floor, profile)
            kill_rounds = m_hp / max(1, dmg)
            total, taken = sm._chase_adjusted(clazz, kill_rounds, profile)
            self.per_class[clazz] = (total, taken)


MODEL = {f: [Enc(f, e) for e in schema.get_floor(f).encounters]
         for f in FLOORS}
RISK_SCALE = {f: sm._expected_monster_damage(f) / economy.player_max_hp(f)
              for f in FLOORS}
GPK = {f: economy.gold_per_kill(f) for f in FLOORS}


def _series(clazz):
    rounds, risk, income = [], [], []
    for f in FLOORS:
        encs = MODEL[f]
        rw = kw = ww = gw = gt = 0.0
        for e in encs:
            gw += e.weight * e.gold_mult
            gt += e.weight
            pc = e.per_class[clazz]
            if pc is None:
                continue
            rw += e.weight * pc[0]
            kw += e.weight * pc[1]
            ww += e.weight
        rounds.append(rw / ww)
        risk.append(kw / ww * RISK_SCALE[f])
        income.append(GPK[f] * gw / gt)
    return rounds, risk, income


def _loss():
    """Sum of gate-cap overshoots across every gate in the test file,
    plus a whisper of drift so weights stay near the authored mix."""
    bad = 0.0
    for clazz in CLASSES:
        rounds, risk, income = _series(clazz)
        for name, values in (("rounds", rounds), ("risk", risk)):
            base = sm.BASE_FLOOR[name]
            for a, b in zip(values, values[1:]):
                bad += max(0.0, abs(b - a) / max(a, base)
                           - sm.ADJACENT_CAP)
            avg = sm._moving_average(values)
            for a, b in zip(avg, avg[1:]):
                bad += max(0.0, abs(b - a) / max(a, base) - sm.TREND_CAP)
        for a, b in zip(income, income[1:]):
            bad += max(0.0, 0.90 - b / a)
        avg = sm._moving_average(income)
        for a, b in zip(avg, avg[1:]):
            bad += max(0.0, 0.98 - b / a)
    drift = sum(abs(e.weight - e.orig)
                for f in TUNABLE for e in MODEL[f])
    return bad * 1000 + drift * 0.01


def tune(seed=17, iters=40000):
    rng = random.Random(seed)
    tunable = [(f, e) for f in TUNABLE for e in MODEL[f]]
    best = _loss()
    print(f"start loss {best:.2f}")
    stall = 0
    while iters and best >= 0.01 * len(tunable):  # drift-only = done
        iters -= 1
        f, e = tunable[rng.randrange(len(tunable))]
        cap = 2 if e.bulwark else 4
        old = e.weight
        e.weight = rng.randint(1, cap)
        if e.weight == old:
            continue
        now = _loss()
        if now < best:
            best, stall = now, 0
        else:
            e.weight = old
            stall += 1
        if stall > 8000:
            break
    print(f"end loss {best:.2f}")
    return best


def write_back():
    changed = 0
    for f in sorted(TUNABLE):
        path = (ROOT / "plugin_linear_ascent" / "content" / "floors"
                / f"floor_{f:03d}.yaml")
        text = path.read_text()
        for e in MODEL[f]:
            if e.weight == e.orig:
                continue
            pat = (rf"(- id: {e.id}\n(?:.*\n)*?\s*weight:) {e.orig}\b")
            new, n = re.subn(pat, rf"\g<1> {e.weight}", text, count=1)
            assert n == 1, f"floor {f}: could not rewrite {e.id}"
            text = new
            changed += 1
            print(f"floor {f:3d} {e.id}: {e.orig} -> {e.weight}")
        path.write_text(text)
    print(f"{changed} weights rewritten")


if __name__ == "__main__":
    tune()
    write_back()
