"""Candidate monster profiles and drops, shared by play, wiki and simulations."""
from __future__ import annotations

from functools import lru_cache
import math

from .. import economy
from ..content import schema
from . import collection, state

AIR_MAGIC = frozenset({'ledger_wisp', 'rod_wisp', 'cairn_wisp', 'bell_wisp', 'vigil_light',
    'charge_wisp', 'sac_light', 'mirage_wisp', 'pale_fire', 'chime_sprite',
    'charge_harpy', 'smoke_haunt', 'light_leak', 'pollen_shade', 'banner_wraith',
    'kings_shadow', 'arc_moth', 'mirror_moth'})
AIR_POWER = frozenset({'ash_wyrmling', 'road_wyrmling', 'nest_wyrmling', 'young_drake',
    'link_drake', 'column_drake', 'mast_drake', 'aerie_drake', 'court_champion',
    'wall_sentinel', 'rookery_warden_harpy'})
BODY = {'frail': .65, 'lean': .9, 'sturdy': 1.15, 'hulking': 1.45}
BITE = {'feeble': .65, 'fierce': 1.2, 'savage': 1.5}


def type_id(enc) -> str:
    old = economy.type_of(enc.traits)
    if old == 'fly':
        return 'air-' + ('magic' if enc.id in AIR_MAGIC else 'power' if enc.id in AIR_POWER else 'common')
    return 'ground-' + {'armoured': 'power', 'magic_resist': 'magic', 'plain': 'common'}[old]


def interpolate(knots, floor):
    for a, b in zip(knots, knots[1:]):
        if a[0] <= floor <= b[0]:
            ratio = (floor - a[0]) / (b[0] - a[0])
            return [x + (y - x) * ratio for x, y in zip(a[1:], b[1:])]
    return list(knots[0 if floor < knots[0][0] else -1][1:])


def drop_rates(floor: int, traits=(), *, specimen='common', deep=False) -> dict:
    loot = collection.catalog()['loot']
    mult = loot['specimen'][specimen]
    for trait in traits:
        mult *= loot['body'].get(trait, loot['bite'].get(trait, 1))
    material = interpolate(loot['materialKnots'], floor)
    weapon = interpolate(loot['weaponKnots'], floor)
    material = [min(loot['materialCapPct'], x * mult * (loot['deepMaterial'][i] if deep else 1))
                for i, x in enumerate(material)]
    weapon = [x * mult * (loot['deepWeapon'][i] if deep else 1) for i, x in enumerate(weapon)]
    if floor < loot['legendaryDiscoveryFloor']:
        material[3] = weapon[3] = 0
    scale = min(1, loot['weaponTotalCapPct'] / max(sum(weapon), .000001))
    return dict(material=dict(zip(collection.GRADES, material)),
                weapon=dict(zip(collection.GRADES, [x * scale for x in weapon])))


@lru_cache(maxsize=512)
def profile(floor: int, creature_id: str) -> dict:
    enc = next(e for e in schema.get_floor(floor).encounters if e.id == creature_id)
    t = next(t for t in collection.catalog()['types'] if t['id'] == type_id(enc))
    body = math.prod(BODY.get(x, 1) for x in enc.traits)
    bite = math.prod(BITE.get(x, 1) for x in enc.traits)
    # Direct anchors avoid the old opening attack jump6→21→54 caused by
    # deriving ordinary attacks from a reference shield the player lacks.
    hp = round(18 * economy.pillar(floor) * body)
    attack = round(6 * economy.pillar(floor) * bite)
    defense = round(economy.pillar(floor) * (1.3 if t['affinity'] == 'Power' else .7))
    traits = list(enc.traits)
    tokens = creature_id.split('_')
    if any(x in tokens for x in ('wisp', 'wraith', 'haunt', 'shade', 'sentinel', 'golem')):
        traits += ['bloodless', 'venomproof']
    if any(x in tokens for x in ('wood', 'bark', 'moth')):
        traits += ['flammable']
    if 'bulwark' in traits:
        hp = round(hp * 1.35)
        traits.append('steadfast')
    return dict(id=enc.id, name=enc.name, floor=floor, image=f'creatures/{enc.id}_320x112.png',
        type=t['id'], affinity=t['affinity'], air=t['air'], speed=t['speed'],
        hp=max(1, hp), hp_max=max(1, hp), atk=max(1, attack), defense=max(0, defense),
        power=t['power'], magic=t['magic'], traits=traits, note=t['note'],
        lore=enc.lore or enc.prose, weight=enc.weight)


def rolled_member(p: dict, floor: int, creature_id: str, *, deep=False, opening=False) -> dict:
    from copy import deepcopy
    m = deepcopy(profile(floor, creature_id))
    table = economy.DEEP_SPECIMENS if deep else economy.specimen_table(floor)
    specimen = 'common' if opening else state.rng_pick(p, [(v['weight'], k) for k, v in table.items()])
    spec = economy.SPECIMENS[specimen]
    m.update(specimen=specimen, hp=max(1, round(m['hp'] * spec['hp'])),
             atk=max(1, round(m['atk'] * spec['atk'] * (1.2 if deep else 1))),
             speed=m['speed'] + (1 if specimen == 'alpha' else 0) + int(deep))
    m['hp_max'] = m['hp']
    m['rates'] = drop_rates(floor, m['traits'], specimen=specimen, deep=deep)
    m.update(started=False, paid=False, exhausted=False, killed=False, gap=3 if opening else state.rng_int(p, 1, 3),
             effects=[], stun_recovery=0)
    m['rewards'] = roll_rewards(p, floor, m, deep=deep)
    return m


def roll_rewards(p, floor, m, *, deep=False):
    rates = m['rates']
    specimen = m['specimen']
    reward_mult = (1.4 if deep else 1) * {'runt': .7, 'common': 1, 'tough': 1.2, 'alpha': 1.6}[specimen]
    materials = {}
    carrier = 'A' if m['air'] else 'B' if m['affinity'] == 'Magic' else 'mixed'
    ratios = collection.catalog()['loot']['carrierRatios'][carrier]
    for gi, grade in enumerate(collection.GRADES):
        if state.rng_int(p, 1, 100000000) <= round(rates['material'][grade] * 1000000):
            index = 0 if state.rng_int(p, 1, sum(ratios)) <= ratios[0] else 1
            name = collection.MATERIALS[gi][index]
            materials[name] = max(1, 1 + (floor - 1 - gi * 25) // 5)
    drop = None
    roll, threshold = state.rng_int(p, 1, 100000000), 0
    for grade in collection.GRADES:
        threshold += round(rates['weapon'][grade] * 1000000)
        if roll <= threshold:
            favored = 'bow' if m['air'] else 'blade' if m['affinity'] == 'Magic' else 'staff' if m['affinity'] == 'Power' else ''
            family = state.rng_pick(p, [(3 if w['path'].lower() == favored else 1, w['id'])
                                       for w in collection.families().values()])
            drop = dict(family=family, grade=grade)
            break
    return dict(gold=max(1, round(economy.gold_per_kill(floor) * reward_mult)),
        xp=max(1, round(economy.xp_per_kill(floor) * reward_mult)), materials=materials, weapon=drop)


def size_range(floor: int) -> tuple[int, int]:
    for limit, count in ((3, (2, 2)), (10, (2, 3)), (25, (2, 4)),
                         (50, (3, 4)), (75, (3, 5)), (100, (3, 6))):
        if floor <= limit:
            return count
    raise ValueError('Floor must be1–100')
