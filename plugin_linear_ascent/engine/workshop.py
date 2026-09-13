"""Weapon purchase, crafting, upgrades and repairs at the actual Forge."""
from __future__ import annotations
import math

from .. import economy
from . import collection, combat, state
from .scene import Scene, Option

SHOP_FLOORS = (1, 28, 57, 84)


def acquisition_quote(family, grade, source='shop'):
    f=collection.families()[family]
    gi=collection.GRADES.index(grade)
    level=f['acquisition'][grade][source+'Level']
    floor=collection.floor_for(grade, level)
    materials={} if source=='shop' else {name:q*ratio for name,ratio in zip(collection.MATERIALS[gi], f['recipe']) for q in ((1,3,8,20)[gi],)}
    gold=math.ceil((200 if source=='shop' else 50) * economy.pillar(floor) * f['cost'])
    return dict(family=family,grade=grade,source=source,level=level,
                floor=SHOP_FLOORS[gi] if source=='shop' else collection.floor_for(grade,0),
                gold=gold,materials=materials)


def repair_quote(item):
    info=collection.stats(item)
    fraction=max(0,1-item['durability']/item['maximum'])
    return max(1, math.ceil(12 * economy.income_pillar(info['floor']) * fraction)) if fraction else 0


def _pay(p, quote):
    if p['unlocked_floor']<quote['floor']:
        raise ValueError(f"This work opens on floor {quote['floor']}")
    if p['gold']<quote['gold']:
        raise ValueError(f"You need {quote['gold']:,} gold")
    if any(p['materials'].get(k,0)<n for k,n in quote['materials'].items()):
        raise ValueError('Gather both required materials before upgrading')
    p['gold']-=quote['gold']
    for name,n in quote['materials'].items():
        p['materials'][name]-=n


def buy(p, family, grade, source):
    from .core import pack_used,pack_cap
    if pack_used(p)>=pack_cap(p):
        raise ValueError('Make room in your pack or use town storage first')
    quote=acquisition_quote(family,grade,source)
    _pay(p,quote)
    item=collection.mint(p,family,grade,source,receipt=f"forge:{p.get('act_seq',0)}")
    combat._ledger(p,'craft' if source=='craft' else 'buy',gold=-quote['gold'],note=item['id'])
    p.update(collection_view=True,collection_selected=item['id'])
    return collection.scene(p)


def upgrade(p, iid):
    item=p['collection'].get(iid)
    if item is None:
        raise ValueError('Choose a weapon you own')
    quote=collection.upgrade_quote(item)
    if quote is None:
        raise ValueError('This weapon cannot take another upgrade')
    _pay(p,quote)
    old_max=item['maximum']
    item['level']=quote['level']
    item['maximum']=collection.stats(item)['maximum']
    item['durability']=min(item['maximum'], item['durability'] + max(0,item['maximum']-old_max)) if item['durability'] else 0
    collection.project_legacy(p)
    combat._ledger(p,'upgrade',gold=-quote['gold'],note=f"{iid}:+{item['level']}")
    return collection.scene(p)


def repair(p, iid, *, recovery=False):
    item=p['collection'].get(iid)
    if not item:
        raise ValueError('Choose a weapon you own')
    price=repair_quote(item)
    if not price:
        raise ValueError('This weapon is already fully repaired')
    if recovery:
        if item['source']!='starter' or item['grade']!='Common':
            raise ValueError('The practice bench repairs Common starter weapons only')
        if not state.spend_energy(p,1):
            raise ValueError('One energy for the practice bench; rest in the fields to recover')
        price=0
    elif p['gold']<price:
        raise ValueError(f"You need {price:,} gold for this repair")
    p['gold']-=price
    item['durability']=item['maximum']
    collection.project_legacy(p)
    combat._ledger(p,'repair',gold=-price,note=iid+(':practice' if recovery else ''))
    return collection.scene(p)


def scene(p):
    grade=p.get('shop_grade','Common')
    opts=[Option('shop_grade:'+g,g,'Weapon grade',locked=False) for g in collection.GRADES]
    items=[]
    for f in collection.families().values():
        quote=acquisition_quote(f['id'],grade)
        fake=dict(id='shop:'+f['id'],family=f['id'],grade=grade,level=quote['level'],source='shop',durability=0,maximum=1)
        info=collection.stats(fake)
        fake['maximum']=fake['durability']=info['maximum']
        item=collection.card(p,fake)
        item['purchase']=quote
        items.append(item)
        opts.append(Option('forge_buy:'+f['id']+':'+grade,f['name']+f" +{quote['level']}",
                           f"{quote['gold']:,} gold · floor {quote['floor']}",locked=p['unlocked_floor']<quote['floor']))
        craft=acquisition_quote(f['id'],grade,'craft')
        opts.append(Option('forge_craft:'+f['id']+':'+grade,'Craft '+f['name']+' +0',
            f"{craft['gold']:,} gold · " + ', '.join(f'{k} ×{v}' for k,v in craft['materials'].items()),
            locked=p['unlocked_floor']<craft['floor']))
    opts.append(Option('shop_back','Back to the Forge'))
    return Scene(eyebrow='ROOTHOLLOW · THE FORGE',headline='Choose a weapon for your next fight',
        support='Each grade has its own drawing. Bought weapons arrive fully repaired; crafted weapons begin at +0.',
        options=opts,meters=combat.meters(p),workshop=dict(grade=grade,items=items))


def handle(p, oid):
    if not collection.enabled(p):
        return None
    recognized=oid in ('weapon_shop','forge_collection','shop_back') or oid.startswith(('shop_grade:','forge_buy:','forge_craft:','upgrade:','mend:','practice:'))
    if not recognized:
        return None
    from .core import _build_scene
    if collection.locked(p):
        result=_build_scene(p)
        result.refusal='Finish the fight or expedition before visiting the Forge'
        return result
    p.pop('quiver_view',None)
    if oid=='forge_collection':
        p.pop('workshop_view',None)
        p.update(location='forge',floor=0,collection_view=True)
        return collection.scene(p)
    if oid=='weapon_shop':
        p.update(location='forge',floor=0,workshop_view=True)
        p.pop('collection_view',None)
        return scene(p)
    if p['location']!='forge':
        result=_build_scene(p)
        result.refusal='Weapon upgrades and purchases happen at the Forge'
        return result
    try:
        if oid=='shop_back':
            p.pop('workshop_view',None)
            return _build_scene(p)
        if oid.startswith('shop_grade:'):
            grade=oid.partition(':')[2]
            if grade not in collection.GRADES:
                raise ValueError('Choose Common, Rare, Epic or Legendary')
            p['shop_grade']=grade
            return scene(p)
        if oid.startswith(('forge_buy:','forge_craft:')):
            _,family,grade=oid.split(':')
            if family not in collection.families() or grade not in collection.GRADES:
                raise ValueError('Choose a weapon from the Forge catalog')
            return buy(p,family,grade,'craft' if oid.startswith('forge_craft:') else 'shop')
        iid=oid.partition(':')[2]
        if oid.startswith('upgrade:'):
            return upgrade(p,iid)
        return repair(p,iid,recovery=oid.startswith('practice:'))
    except ValueError as exc:
        result=_build_scene(p)
        result.refusal=str(exc)
        return result
