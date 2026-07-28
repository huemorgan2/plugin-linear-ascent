"""009: list every hard-counter matchup on floors 11-100 that is not
FELT at the pinned sim day (the marginal walls the 008 day-seed hid).
Run from the plugin repo root."""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "tests")

from plugin_linear_ascent import economy  # noqa: E402
from tests.test_017_bestiary import _floor_results, _intended  # noqa: E402
from tests.test_017_damage_types import (_class_mult,  # noqa: E402
                                         _speed_counters)

for floor_no in range(11, 101):
    for clazz in ("warrior", "archer", "sorcerer"):
        res = _floor_results(clazz, floor_no)
        plain_candidates = [r for _, (w, r, prof) in res.items()
                            if _intended(clazz, prof)]
        plain = min(plain_candidates) if plain_candidates else None
        for eid, (win, rounds, prof) in res.items():
            if _intended(clazz, prof):
                continue
            if (_class_mult(clazz, prof) <= 0.5 or prof["bulwark"]
                    or _speed_counters(clazz, prof)):
                dragged = plain and rounds >= 1.6 * plain
                if win > 0.75 and not dragged:
                    print(f"floor {floor_no} {clazz} vs {eid}: "
                          f"win {win:.0%}, rounds {rounds:.1f} vs "
                          f"plain {plain:.1f} "
                          f"({rounds / plain:.2f}x) traits={prof}")
print("scan done")
