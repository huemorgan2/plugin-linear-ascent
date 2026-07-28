"""010: margin report for every hard-counter matchup on floors 11-100.

A wall is FELT when it is risky (win <= 0.75) or a drag (rounds >=
1.6x plain prey). Zero failures is necessary but not sufficient for
release: this script also flags matchups that pass within ~0.1 of a
bar (win in (0.65, 0.75] with drag < 1.7x, or drag in [1.6, 1.7) with
win > 0.75) — those are one retune away from flipping and count as
unshipped. Run from the plugin repo root.
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "tests")

from tests.test_017_bestiary import _floor_results, _intended  # noqa: E402
from tests.test_017_damage_types import (_class_mult,  # noqa: E402
                                         _speed_counters)

WIN_BAR = 0.75
DRAG_BAR = 1.6
MARGIN = 0.1

fails, near = [], []
for floor_no in range(11, 101):
    for clazz in ("warrior", "archer", "sorcerer"):
        res = _floor_results(clazz, floor_no)
        plain_candidates = [r for _, (w, r, prof) in res.items()
                            if _intended(clazz, prof)]
        plain = min(plain_candidates) if plain_candidates else None
        for eid, (win, rounds, prof) in res.items():
            if _intended(clazz, prof):
                continue
            if not (_class_mult(clazz, prof) <= 0.5 or prof["bulwark"]
                    or _speed_counters(clazz, prof)):
                continue
            drag = (rounds / plain) if plain else 99.0
            line = (f"floor {floor_no} {clazz} vs {eid}: win {win:.0%}, "
                    f"drag {drag:.2f}x traits={prof}")
            risky = win <= WIN_BAR
            dragged = drag >= DRAG_BAR
            if not (risky or dragged):
                fails.append(line)
            elif ((risky and win > WIN_BAR - MARGIN and not dragged
                   and drag < DRAG_BAR + MARGIN)
                  or (dragged and drag < DRAG_BAR + MARGIN and not risky
                      and win > WIN_BAR - MARGIN)):
                near.append(line)

print(f"FAILING ({len(fails)}):")
for x in fails:
    print(" ", x)
print(f"NEAR-MARGIN, felt by only one bar with <0.1 to spare"
      f" ({len(near)}):")
for x in near:
    print(" ", x)
print("scan done")
