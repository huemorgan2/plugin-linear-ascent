"""Named resource expeditions; settlement stays in the shared game engine."""
from __future__ import annotations
from copy import deepcopy

from . import bestiary, collection, combat, groups, state
from .scene import Scene, Option
from ..content import schema

SITES = {
    'drowned-copse': dict(name='Drowned Copse',floor=3,material='Wood',tool='wood-axe',
        tool_name='Wood axe',price=35,yield_pct=58,yield_amount=2,ambush_pct=5,condition=100,
        preferred='bow',description='Cut driftwood beneath the drowned canopy. Wings stir overhead.'),
    'bog-iron-field': dict(name='Bog-Iron Field',floor=3,material='Raw Metal',tool='pickaxe',
        tool_name='Iron pickaxe',price=45,yield_pct=47,yield_amount=2,ambush_pct=4,condition=120,
        preferred='blade',description='Break iron from the wet earth. Arcane creatures guard the exposed seams.'),
}


def directory(p):
    """Discoverable travel facts, including unopened sites; no route mutation."""
    return [dict(key=key, **site, available=site['floor'] <= p.get('unlocked_floor',1),
                 entry_action='gather_site:'+key,tool_sold_here=True,entry_requires_tool=False,gather_requires_tool=True,
                 route=f"Tower gate → floor {site['floor']} camp → {site['name']}")
            for key,site in SITES.items()]


def sites_at(floor):
    return {key:site for key,site in SITES.items() if site['floor']==floor}


def _site(p):
    exp=p.get('expedition')
    if exp:
        # Pre-bundle expeditions retain their accepted one-unit collection rule.
        return exp.get('site_rules') or {**SITES[exp['site']], 'yield_amount':1}
    return SITES[p['gathering_site']]


def scene(p):
    site=_site(p)
    key=(p.get('expedition') or {}).get('site') or p['gathering_site']
    tool=p.get('utility_tools',{}).get(site['tool'])
    expedition=p.get('expedition')
    opts=[]
    if not tool:
        opts.append(Option('gather_tool','Buy '+site['tool_name'],f"{site['price']} gold · utility tool, outside your three weapons"))
    elif not expedition:
        if tool['condition']<site['condition']:
            opts.append(Option('gather_mend','Repair '+site['tool_name'],f"{tool_repair_price(site,tool)} gold"))
        opts.append(Option('gather_begin','Begin expedition','Your three weapons stay fixed until you extract',locked=not tool['condition']))
    else:
        opts.append(Option('gather_step','Collect '+site['material'],
            f"1 energy · {site['yield_pct']}% yield · {site['ambush_pct']}% ambush",
            locked=state.energy_now(p)<1 or not tool['condition']))
        opts.append(Option('gather_extract','Extract with your haul','Secure all gathered materials and won loot'))
    if not expedition:
        opts.append(Option('gather_back','Return to camp'))
    lines=[site['description'],f"Target: {site['material']} · strong choice: {site['preferred'].title()}",
        f"Each attempt: {site['yield_pct']}% for {site['yield_amount']} {site['material']}; {site['ambush_pct']}% for an ambush.",
        'An ambush costs one additional energy per enemy when it begins. Defeat or retreat loses this expedition’s entire haul.']
    if tool:
        lines.append(f"{site['tool_name']}: {tool['condition']}/{site['condition']} condition")
    if expedition:
        lines += [f"Unbanked: {expedition['gold']} gold · " + (', '.join(f'{k} ×{v}' for k,v in expedition['haul'].items()) or 'no materials yet'),
                  expedition.get('message','Choose how long to stay; extract before the next risk.')]
    image=schema.get_floor(site['floor']).encounters[0].id
    return Scene(eyebrow=f"FLOOR {site['floor']} · GATHERING",headline=site['name'],body_lines=lines,
        support='Bring the right tool and weapons. Your haul is secured only when you extract.',
        options=opts,meters=combat.meters(p),banner=schema.get_floor(site['floor']).banner,
        expedition=dict(site=key,**site,active=bool(expedition),tool_state=deepcopy(tool),
            haul=deepcopy(expedition['haul']) if expedition else {},image=f'creatures/{image}_320x112.png'))


def tool_repair_price(site,tool):
    import math
    return max(1,math.ceil(site['price']*.25*(1-tool['condition']/site['condition'])))


def ambush_members(p,site):
    floor=site['floor']
    # Use neighboring floor art with its true identity/type. Numbers scale to
    # this site's floor, so an image choice cannot secretly multiply danger.
    candidates=[]
    for source_floor in range(max(1,floor-2),floor+3):
        for enc in schema.get_floor(source_floor).encounters:
            profile=bestiary.profile(source_floor,enc.id)
            fit=profile['air'] if site['preferred']=='bow' else not profile['air'] and profile['affinity']=='Magic'
            candidates.append((5 if fit else 1,(source_floor,enc.id)))
    members=[]
    from .. import economy
    for _ in range(2):
        origin,slug=state.rng_pick(p,candidates)
        member=bestiary.rolled_member(p,origin,slug)
        ratio=economy.pillar(floor)/economy.pillar(origin)
        for stat in ('hp','hp_max','atk','defense'):
            member[stat]=max(1,round(member[stat]*ratio))
        member['floor']=floor
        # Site rewards use site-floor odds, never the art's original floor.
        member['rates']=bestiary.drop_rates(floor,member['traits'],specimen=member['specimen'])
        member['rewards']=bestiary.roll_rewards(p,floor,member)
        members.append(member)
    return members


def _extract(p):
    exp=p['expedition']
    p['gold']+=exp['gold']
    for name,n in exp['haul'].items():
        p['materials'][name]=p['materials'].get(name,0)+n
    from .core import pack_used,pack_cap
    for drop in exp['weapons']:
        full=pack_used(p)>=pack_cap(p)
        item=collection.mint(p,drop['family'],drop['grade'],'drop',receipt=drop['receipt'])
        if full:
            item['location']='claim'
    combat._ledger(p,'gather_extract',gold=exp['gold'],note=exp['id'])
    p['gathering_result']=deepcopy(exp)
    p['expedition']=None
    p['location']='gate_town'
    from .core import _build_scene
    result=_build_scene(p)
    result.support='Extracted: '+(', '.join(f'{k} ×{v}' for k,v in exp['haul'].items()) or 'no materials')+f" · {exp['gold']} gold. Your haul is secured."
    return result


def handle(p,oid):
    if not collection.enabled(p):
        return None
    exp=p.get('expedition')
    if not (oid.startswith('gather') or exp):
        return None
    from .core import _build_scene
    try:
        if oid.startswith('gather_site:'):
            key=oid.partition(':')[2]
            if exp or p.get('group') or p['location']!='gate_town' or key not in sites_at(p['floor']):
                raise ValueError('Visit this resource site from its floor camp')
            if collection.claims(p):
                raise ValueError('Secure your waiting weapon claim before starting an expedition')
            p.update(gathering_site=key,location='gathering')
            return scene(p)
        if p['location']!='gathering':
            raise ValueError('Choose a resource site from its floor camp')
        site=_site(p)
        tool=p.setdefault('utility_tools',{}).get(site['tool'])
        if exp:
            if oid=='gather_extract':
                return _extract(p)
            if oid!='gather_step':
                raise ValueError('Extract first; your weapons and haul remain committed to this expedition')
            if not tool or tool['condition']<=0:
                raise ValueError('Your tool needs repair. Extract your haul first')
            if not state.spend_energy(p,1):
                raise ValueError('No energy left. You can still extract your haul')
            tool['condition']-=1
            exp['attempts']+=1
            found=state.rng_int(p,1,100)<=site['yield_pct']
            if found:
                exp['haul'][site['material']]=exp['haul'].get(site['material'],0)+site['yield_amount']
            exp['message']=(f"Found {site['yield_amount']} "+site['material']) if found else 'Nothing recovered this attempt.'
            combat._ledger(p,'gather',note=exp['id']+':'+str(exp['attempts'])+(':yield' if found else ':empty'))
            if state.rng_int(p,1,100)<=site['ambush_pct']:
                return groups.open_group(p,members=ambush_members(p,site),site=exp['site'])
            return scene(p)
        if oid=='gather_back':
            p['location']='gate_town'
            return _build_scene(p)
        if oid in ('gather_tool','gather_mend'):
            if oid=='gather_tool' and tool:
                raise ValueError('You already own this tool')
            if oid=='gather_mend' and not tool:
                raise ValueError('Buy the tool first')
            price=site['price'] if not tool else tool_repair_price(site,tool)
            if p['gold']<price:
                raise ValueError(f'You need {price} gold')
            p['gold']-=price
            p['utility_tools'][site['tool']]=dict(condition=site['condition'])
            combat._ledger(p,'gather_tool',gold=-price,note=site['tool'])
            return scene(p)
        if oid=='gather_begin' and tool and tool['condition']:
            seq=p.get('expedition_sequence',0)+1
            p['expedition_sequence']=seq
            p['expedition']=dict(id=f'expedition:{seq}',site=p['gathering_site'],deck=list(p['deck']),
                haul={},gold=0,weapons=[],attempts=0,site_rules=deepcopy(site))
            return scene(p)
        raise ValueError('Choose a current gathering action')
    except ValueError as exc:
        result=_build_scene(p)
        result.refusal=str(exc)
        return result
