"""048 phase 7 — retag 425 monsters' YAML traits to native types.

Mechanical map (assert-counted, atomic per file, sweep_tests.py's
pattern):
  flying                        -> fly
  resist_low/med/high           -> magic_resist   (resist outranks armor)
  armor_low/med/high, armored   -> armoured
  fast, slow                    -> deleted        (speed rides the type)
  bulwark, body, bite           -> kept

Hand flips (the deliberate part — census + pool law, picked by
flavor; the mechanical map runs first, then these override):

  classroom (floors 4-10 owe all three signs; 1-3 keep the 017
  staircase):
    floor 4  lamptree_wight -> armoured  (bark-plate over dead wood;
                               glade_stag stays plain — the stag was
                               floor 4's second measured-farmable blade
                               target, and lamptree_wight is already an
                               above-bar danger fight, so the sign costs
                               no one their pool)
    floor 5  downs_courser  -> fly, drop fierce (a swooping courser;
                               fierce+fly is illegal below sky_hook@6)
    floor 6  vault_weaver   -> armoured  (chitin-plated sentinel spider)
    floor 7  rabid_boar     -> armoured  (tusk-and-hide plate)
    floor 8  greywell_ogre  -> armoured  (crude slab-plates)
    floor 9  shadow_wolf    -> armoured  (line-keepers' scrap-barding,
                               the night_mare precedent; pylon_adder
                               stays plain — armoured at ×0.5 is
                               sub-80% for blade even a bar down, so
                               the sign must ride the floor's at-bar
                               danger fight, which no one farms)

  deep pool rule (every path ≥2 full targets per floor):
    floor 24  marsh_ghoul_crew -> plain  (the stripper, stripped)
    floor 42  mirage_wisp      -> fly    (a heat-ghost floats)
    floor 47  pale_fire        -> fly    (a colorless flame drifts)
    floor 72  night_mare       -> armoured (a stray nightmare in barding)
    floor 74  skirmish_shade   -> armoured (a remnant still in old plate)
    floor 100 crown_regalia    -> armoured (the living regalia IS armour)
    floor 100 kings_shadow     -> fly     (a shadow flits)

  pool rule, second pass (bulwarks don't count toward the pool, and
  each is its band's ONLY bulwark — flip a neighbor to plain instead):
    floor 45  kiln_salamander -> plain  (a mundane fire-lizard)
    floor 57  spray_wolf      -> plain  (ice-crusted coat, not plate)
    floor 62  hold_drake      -> plain  (a wingless hold-lizard)
    floor 75  black_crake     -> plain  (crakes skulk the grass — no
                                         flight to speak of)
"""

import os
import re
import sys

FLOORS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "..", "..", "plugin_linear_ascent",
                      "content", "floors")

TYPE_OF_LEGACY = [    # ordered: flight loudest, resist outranks armor
    (re.compile(r"^flying$"), "fly"),
    (re.compile(r"^resist_(low|med|high)$"), "magic_resist"),
    (re.compile(r"^(armor_(low|med|high)|armored)$"), "armoured"),
]
DROP = {"fast", "slow"}

FLIPS = {   # encounter id -> forced type ("plain" = no type trait)
    "glade_stag": "plain", "lamptree_wight": "armoured",
    "downs_courser": "fly",
    "vault_weaver": "armoured", "rabid_boar": "armoured",
    "greywell_ogre": "armoured", "pylon_adder": "plain",
    "shadow_wolf": "armoured",
    "marsh_ghoul_crew": "plain", "mirage_wisp": "fly",
    "pale_fire": "fly", "night_mare": "armoured",
    "skirmish_shade": "armoured", "crown_regalia": "armoured",
    "kings_shadow": "fly",
    "kiln_salamander": "plain", "spray_wolf": "plain",
    "hold_drake": "plain", "black_crake": "plain",
}
DROP_BITE = {"downs_courser"}          # fierce+fly illegal below floor 6
SOFTEN_BITE = {"courier_hound": ("savage", "fierce")}
# floor 10: blade's only sub-bar plain was banner_wolf — the measured
# ≥2 pool gate needs a second. lean+savage sat AT the bar; lean+fierce
# steps it one down and farmable, for blade and staff both. The danger
# law keeps parade_horse (+1 fierce) and the at-bar guard/wight pair.

TRAIT_LINE = re.compile(r"^(\s*traits: \[)([^\]]*)(\]\s*)$")
ID_LINE = re.compile(r"^\s*- id: (\S+)\s*$")


def retag_line(traits: str, enc_id: str) -> str:
    ts = [t.strip() for t in traits.split(",") if t.strip()]
    kept, natives = [], []
    for t in ts:
        if t in DROP:
            continue
        if t in ("fly", "armoured", "magic_resist"):
            natives.append(t)          # idempotence: re-runs re-decide
            continue
        for pat, native in TYPE_OF_LEGACY:
            if pat.match(t):
                natives.append(native)
                break
        else:
            kept.append(t)
    # precedence mirrors type_from_traits: flight loudest, then resist
    mtype = next((n for n in ("fly", "magic_resist", "armoured")
                  if n in natives), None)
    if enc_id in FLIPS:
        mtype = None if FLIPS[enc_id] == "plain" else FLIPS[enc_id]
    if enc_id in DROP_BITE:
        kept = [t for t in kept if t not in ("feeble", "fierce", "savage")]
    if enc_id in SOFTEN_BITE:
        old, new = SOFTEN_BITE[enc_id]
        kept = [new if t == old else t for t in kept]
    if mtype:
        kept.append(mtype)
    return ", ".join(kept)


def main() -> int:
    n_files = n_traits = n_flips = 0
    for fn in sorted(os.listdir(FLOORS)):
        if not fn.endswith(".yaml"):
            continue
        path = os.path.join(FLOORS, fn)
        src = open(path, encoding="utf-8").read()
        lines = src.split("\n")
        cur_id, changed = None, False
        for i, ln in enumerate(lines):
            m = ID_LINE.match(ln)
            if m:
                cur_id = m.group(1)
                continue
            m = TRAIT_LINE.match(ln)
            if not m:
                continue
            new = retag_line(m.group(2), cur_id)
            if new != m.group(2):
                lines[i] = m.group(1) + new + m.group(3)
                changed = True
                n_traits += 1
                if cur_id in FLIPS:
                    n_flips += 1
        if changed:
            open(path, "w", encoding="utf-8").write("\n".join(lines))
            n_files += 1
    print(f"{n_files} files, {n_traits} trait lines rewritten, "
          f"{n_flips} hand flips applied")
    # re-runs are legal: already-applied flips change no line
    return 0


if __name__ == "__main__":
    sys.exit(main())
