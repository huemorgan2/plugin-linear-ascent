"""Finite arrow supplies and paid Forge replenishment for collection battles."""
from __future__ import annotations

from copy import deepcopy
import math

from .. import economy
from . import collection, combat, state
from .scene import Option, Scene


def definitions():
    return {a['id']: a for a in collection.catalog()['arrows']}


def ensure(p):
    if not collection.enabled(p) or p.get('quiver_enrollment'):
        return
    p.setdefault('quiver', {})
    # Preserve any imported supplies. The receipt prevents read/reconnect grants.
    stock = p['quiver'].setdefault('Common', {})
    stock['ordinary'] = stock.get('ordinary', 0) + collection.catalog()['quiver']['starter']
    p['quiver_enrollment'] = 'quiver-v1'
    p.setdefault('arrow_choice', {})
    combat._ledger(p, 'quiver_enroll', note='quiver-v1:100:Common:ordinary')


def count(p, grade, arrow):
    return int(p.get('quiver', {}).get(grade, {}).get(arrow, 0))


def used(p):
    return sum(n for stock in p.get('quiver', {}).values() for n in stock.values())


def chosen(p, item):
    return p.get('arrow_choice', {}).get(item['id'], 'ordinary')


def quote(grade, arrow):
    if grade not in collection.GRADES or arrow not in definitions():
        raise ValueError('Choose an arrow and grade from the quiver rack')
    cfg = collection.catalog()['quiver']
    floor = collection.floor_for(grade, 0)
    return dict(grade=grade, arrow=arrow, floor=floor, count=cfg['bundle'],
        gold=math.ceil(cfg['baseGold'] * economy.income_pillar(floor) * definitions()[arrow]['units']))


def select(p, iid, arrow):
    if iid not in p['deck'] or arrow not in definitions():
        raise ValueError('Choose one of the arrows for a selected bow')
    item = p['collection'][iid]
    if collection.stats(item)['path'] != 'bow':
        raise ValueError('Arrows are used by bows')
    if count(p, item['grade'], arrow) <= 0:
        raise ValueError(f"No {item['grade']} {definitions()[arrow]['name']} arrows left")
    p.setdefault('arrow_choice', {})[iid] = arrow


def consume(p, item):
    arrow = chosen(p, item)
    if count(p, item['grade'], arrow) <= 0:
        raise ValueError('No arrows of the selected type and grade remain')
    p['quiver'][item['grade']][arrow] -= 1
    return definitions()[arrow]


def payload(p):
    return dict(stock=deepcopy(p.get('quiver', {})), used=used(p),
        capacity=collection.catalog()['quiver']['capacity'], choices=deepcopy(p.get('arrow_choice', {})))


def scene(p):
    grade = p.get('quiver_grade', 'Common')
    cfg = collection.catalog()['quiver']
    opts = [Option('arrow_grade:' + g, g + ' arrows',
        f"Floor {collection.floor_for(g,0)}", locked=p['unlocked_floor'] < collection.floor_for(g,0))
        for g in collection.GRADES]
    lines = [f"Quiver: {used(p)}/{cfg['capacity']} arrows. Separate from your three weapons.",
             'One arrow per accepted shot, including a miss. Match the arrow grade to the bow.']
    for arrow, definition in definitions().items():
        q = quote(grade, arrow)
        lines.append(f"{definition['name']}: {count(p,grade,arrow)} owned · {definition['channel']} · {definition['effect']}")
        opts.append(Option('arrow_buy:' + grade + ':' + arrow,
            f"Buy {q['count']} {definition['name']} arrows", f"{grade} · {q['gold']:,} gold"))
    opts.append(Option('arrow_practice', 'Make 20 Common Ordinary arrows',
        '1 energy · only below 20 in stock', locked=count(p,'Common','ordinary') >= 20))
    opts.append(Option('arrow_back', 'Back to the Forge'))
    return Scene(eyebrow='ROOTHOLLOW · QUIVER RACK', headline=grade + ' arrows',
        support='Choose your payload before the shot. Its effect and cost are real.',
        body_lines=lines, options=opts, meters=combat.meters(p))


def handle(p, oid):
    if not (oid == 'quiver_shop' or oid.startswith('arrow_')):
        return None
    from .core import _build_scene
    try:
        if collection.locked(p):
            raise ValueError('Finish your group or expedition before replenishing arrows')
        if p['location'] != 'forge':
            raise ValueError('Buy or make arrows at the Forge')
        if oid == 'arrow_back':
            p.pop('quiver_view', None)
            return _build_scene(p)
        if oid == 'quiver_shop':
            p.pop('collection_view', None)
            p.pop('workshop_view', None)
            p['quiver_view'] = True
        elif oid.startswith('arrow_grade:'):
            grade = oid.partition(':')[2]
            if grade not in collection.GRADES or p['unlocked_floor'] < collection.floor_for(grade,0):
                raise ValueError('This arrow grade is not available yet')
            p['quiver_grade'] = grade
        elif oid == 'arrow_practice' or oid.startswith('arrow_buy:'):
            if oid == 'arrow_practice':
                if count(p,'Common','ordinary') >= 20:
                    raise ValueError('Use your remaining Common Ordinary arrows first')
                q = dict(grade='Common',arrow='ordinary',floor=1,count=20,gold=0)
            else:
                parts = oid.split(':')
                if len(parts) != 3:
                    raise ValueError('Choose a current arrow offer')
                q = quote(parts[1], parts[2])
            if p['unlocked_floor'] < q['floor']:
                raise ValueError(f"This arrow grade opens on floor {q['floor']}")
            if used(p) + q['count'] > collection.catalog()['quiver']['capacity']:
                raise ValueError('Your quiver does not have room for this bundle')
            if p['gold'] < q['gold']:
                raise ValueError(f"You need {q['gold']:,} gold")
            if oid == 'arrow_practice' and not state.spend_energy(p,1):
                raise ValueError('One energy is needed at the practice bench')
            p['gold'] -= q['gold']
            stock = p.setdefault('quiver', {}).setdefault(q['grade'], {})
            stock[q['arrow']] = stock.get(q['arrow'],0) + q['count']
            combat._ledger(p, 'arrows', gold=-q['gold'], note=f"{q['grade']}:{q['arrow']}:{q['count']}")
        else:
            raise ValueError('Choose a current quiver action')
        return scene(p)
    except ValueError as exc:
        result = _build_scene(p)
        result.refusal = str(exc)
        return result
