#!/usr/bin/env python3
"""048 phase 4 — the test sweep.

~30 test files carry a local copy of the creation walk that answers the
dead class question. This script rewrites each local helper so the
file's MEANING survives the classless era:

- the class-choice step (`choose(p, clazz)` and friends) is deleted;
- before the helper's `return p`, the old class feel is restored by
  hand: the clazz param maps to its path trained to rank 6 and that
  line's basic weapon in the hand (exactly what the class pick used to
  grant via the transitional phase-2/3 gates).

`tests/test_017_offclass_migration.py` is deleted outright — the T1
migration in state.py covers those docs now, and the off-class system
it tested no longer exists. Expected-text fixes are done by hand from
the failure list (see execution_summary.md).

Run from the plugin-linear-ascent repo root:
    python plans/048-the-weapon-decides/phase-4/sweep_tests.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
TESTS = ROOT / "tests"

# the class-choice line inside a creation helper, any local dialect:
#   choose(p, clazz) | core.apply_choice(p, clazz) | choose(p, "warrior")
CLASS_CHOOSE = re.compile(
    r"^\s+(?:core\.)?(?:apply_)?choose?(?:_choice)?\("
    r"p,\s*(?:clazz|\"(?:warrior|archer|sorcerer)\")\s*(?:,\s*\"\")?\)\s*$")

KIT = """\
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {{"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}}[{clazz}]
    _slug = {{"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}}[{clazz}]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p"""


def sweep_file(path: pathlib.Path) -> bool:
    src = path.read_text()
    lines = src.splitlines()
    out, changed = [], False
    in_helper = False
    helper_has_clazz = False
    for line in lines:
        m = re.match(r"def (create_character|make_character|_character)\(", line)
        if m:
            in_helper = True
            helper_has_clazz = "clazz" in line
            out.append(line)
            continue
        if in_helper and CLASS_CHOOSE.match(line):
            changed = True     # the dead question, asked no more
            continue
        if in_helper and re.match(r"^    return p\s*$", line):
            clazz = "clazz" if helper_has_clazz else '"warrior"'
            out.append(KIT.format(clazz=clazz))
            in_helper = False
            changed = True
            continue
        if in_helper and re.match(r"^def ", line):
            in_helper = False
        out.append(line)
    if changed:
        path.write_text("\n".join(out) + ("\n" if src.endswith("\n") else ""))
    return changed


def main():
    gone = TESTS / "test_017_offclass_migration.py"
    if gone.exists():
        gone.unlink()
        print(f"deleted  {gone.name}")
    touched = []
    for path in sorted(TESTS.glob("*.py")):
        if sweep_file(path):
            touched.append(path.name)
    print(f"rewrote  {len(touched)} files:")
    for name in touched:
        print(f"  {name}")


if __name__ == "__main__":
    sys.exit(main())
