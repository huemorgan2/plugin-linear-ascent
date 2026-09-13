"""Sequential group battles. Every mutation is inside the shared game engine."""
from __future__ import annotations

from copy import deepcopy
import math
import hashlib

from .. import economy
from ..content import schema
from . import bestiary, collection, combat, state, battle_rules, quiver
from .scene import Option, Scene

DISTANCE = ('Contact', 'Near', 'Far', 'Cover')


def current(p):
    g = p.get('group')
    return g['members'][g['index']] if g else None


def monster_speed(member):
    return max(1, member['speed'] - (collection.catalog()['effectRules']['slow']['speed'] if member.get('slow',0) else 0))


def event(p, kind, text, *, defender='', channel='', damage=0):
    g = p['group']
    g['event_sequence'] += 1
    eid = hashlib.sha256(f"{p['luna_user']}:{g['id']}:{g['event_sequence']}".encode()).hexdigest()[:24]
    row = dict(id=eid, kind=kind, text=text,
               defender=defender, channel=channel, damage=damage)
    g['events'].append(row)
    return row


def open_group(p, *, deep=False, members=None, site=''):
    floor = int(p['floor'])
    if p.get('group'):
        return scene(p)
    if collection.claims(p):
        p['collection_view'] = True
        p['collection_selected'] = collection.claims(p)[0]
        result = collection.scene(p)
        result.refusal = 'Secure your waiting weapon claim before another hunt'
        return result
    key = f'{floor}:{"deep" if deep else "trail"}:{site}'
    offers = p.setdefault('hunt_offers', {})
    if key not in offers:
        sequence = int(p.get('group_sequence', 0)) + 1
        p['group_sequence'] = sequence
        opening = not p.get('groups_cleared') and floor == 1 and not deep and not site
        if members is None:
            fl = schema.get_floor(floor)
            roster = [e for e in fl.encounters if not deep or not {'frail', 'feeble'}.intersection(e.traits)]
            roster = roster or list(fl.encounters)
            low, high = bestiary.size_range(floor)
            count = 2 if opening else state.rng_int(p, low, high)
            members = []
            for i in range(count):
                slug = roster[i % len(roster)].id if opening else state.rng_pick(p, [(e.weight, e.id) for e in roster])
                members.append(bestiary.rolled_member(p, floor, slug, deep=deep, opening=opening))
        gid = f"group:{sequence}"
        for i, member in enumerate(members):
            member['instance'] = f'{gid}:enemy:{i}'
        offers[key] = dict(id=gid, offer=key, floor=floor, deep=deep, site=site,
            members=members, index=0, committed=bool(site), deck=list(p['deck']) if site else [],
            cooldowns={}, haul=dict(gold=0, materials={}, weapons=[]), xp=0, energy=0,
            events=[], event_sequence=0, life_used=False, revision=collection.RULESET,
            combat_revision=2, turn=0)
    p['group'] = deepcopy(offers[key])
    p['location'] = 'group'
    p.pop('group_result', None)
    return scene(p)


def public(p):
    g = p['group']
    keys = ('id','instance','name','image','type','affinity','air','speed','hp','hp_max','atk','defense',
            'power','magic','traits','note','specimen','gap','started','paid','exhausted','killed','effects','rates','bundles','reward_revision','origin_floor','arrival_gap')
    return {k: deepcopy(g[k]) for k in ('id','floor','deep','site','index','committed','deck','cooldowns','haul','xp','energy')} | {
        'members': [{**{k: deepcopy(m[k]) for k in keys if k in m},'base_speed':m['speed'],'speed':monster_speed(m),'slow_phases':m.get('slow',0)} for m in g['members']],
        'events': deepcopy(g['events'])}


def scene(p):
    g, m = p['group'], current(p)
    if g.get('combat_revision',1) < 2:
        from . import groups_v1
        return groups_v1.scene(p)
    opts = []
    arrow_rows = []
    for iid in p['deck']:
        if not iid:
            continue
        item = p['collection'][iid]
        info, family = collection.stats(item), collection.families()[item['family']]
        reason = 'Broken — repair at the Forge' if item['durability'] <= 0 else (
            'Cannot reach a flying enemy' if info['path'] == 'blade' and m['air'] else
            'Move to contact first' if info['path'] == 'blade' and m['gap'] else '')
        strike_hint = f"{info['path'].title()} strike"
        if info['path'] == 'bow':
            selected = quiver.chosen(p,item)
            ammo = quiver.definitions()[selected]
            stock = quiver.count(p,item['grade'],selected)
            reason = reason or ('Selected arrows empty — choose another payload' if not stock else '')
            strike_hint = f"{ammo['name']} · {ammo['channel']} · {stock} left"
            arrow_rows.append(dict(weapon=iid,name=info['name'],grade=item['grade'],selected=selected,
                arrows=[dict(**a,count=quiver.count(p,item['grade'],a['id']),
                    action=f"load_arrow:{iid}:{a['id']}") for a in quiver.definitions().values()]))
        opts.append(Option('strike:' + iid, info['name'], reason or strike_hint, locked=bool(reason)))
        if family['cooldown']:
            cooldown = g['cooldowns'].get(iid, 0)
            description = family['description']
            if item['family'] == 'hawkeye':
                description = 'Adds 20% at Far (2) or Cover (3). ' + ('Bonus applies here.' if m['gap'] >= 2 else 'No bonus at this distance.')
            why = reason or (f'Ready in {cooldown} enemy phases' if cooldown else description)
            opts.append(Option('skill:' + iid, family['effect'] + ' · ' + info['name'], why,
                               locked=bool(reason or cooldown)))
    if combat.pouch(p) == 'trollblood_tonic':
        opts.append(Option('drink_tonic', 'Drink trollblood tonic', 'Full heal; uses your action'))
    opts.extend([Option('approach', 'Close in', DISTANCE[m['gap']]),
                 Option('withdraw', 'Pull back', 'Speed decides the opening'),
                 Option('guard', 'Guard', 'Stronger shield absorption; some damage gets through'),
                 Option('flee', 'Leave and lose the pending haul' if not m['started'] else 'Try to escape',
                        'Keep earned XP', danger=True)])
    # These legal read-like actions change only the chosen payload. They do not
    # start an enemy or advance any combat clock; all six are visible on cards.
    for row in arrow_rows:
        for a in row['arrows']:
            opts.append(Option(a['action'],f"Load {a['name']} · {row['name']}",
                f"{row['grade']} · {a['count']} left · free selection",locked=not a['count']))
    paid = ('Exhausted: half attack, −2 speed' if m['exhausted'] else 'Energy paid for this enemy') if m['started'] else 'Waiting:1 energy when your first action begins'
    return Scene(eyebrow=f"FLOOR {g['floor']} · {'DEEP HUNT' if g['deep'] else 'HUNT'}",
        headline=f"{m['name']} · enemy {g['index'] + 1} of {len(g['members'])}",
        support='XP after each kill. Secure the gold and items by defeating the whole group.',
        body_lines=[f"{m['affinity']} · {'Air' if m['air'] else 'Ground'} · {DISTANCE[m['gap']]} · {paid}",
                    m['note']] + [e['text'] for e in g['events']], options=opts, meters=combat.meters(p),
        enemy=dict(name=m['name'], hp=m['hp'], hp_max=m['hp_max'], atk=m['atk'],
                   **{'def': m['defense']}, mspd=monster_speed(m)),
        group={**public(p), 'arrows':arrow_rows, 'weapon_reach': [
            dict(name=o.label, available=not o.locked, reason=o.hint)
            for o in opts if o.id.startswith('strike:')]}, combat_events=deepcopy(g['events']))


def refuse(p, text):
    result = scene(p)
    result.refusal = text
    return result


def _commit(p):
    g, m = p['group'], current(p)
    if not g['committed']:
        g['deck'] = list(p['deck'])
        g['committed'] = True
    p.setdefault('hunt_offers', {}).pop(g['offer'], None)
    if not m['started']:
        m['started'] = True
        m['paid'] = state.spend_energy(p, 1)
        m['exhausted'] = not m['paid']
        g['energy'] += int(m['paid'])
        combat._ledger(p, 'enemy_start', note=m['instance'] + (':paid' if m['paid'] else ':exhausted'))
        if not m['paid']:
            event(p, 'exhaustion', 'No energy: half outgoing damage and two less speed for this enemy.')


def player_speed(p):
    m = current(p)
    return max(1, economy.player_speed(p) - (2 if m and m['exhausted'] else 0))


def _hurt_monster(p, amount, channel, *, dot=False, source=None):
    m = current(p)
    mult = battle_rules.affinity(m,channel,focus=bool((source or {}).get('focus')))
    defense = m['defense'] * (.8 if m.get('expose', 0) and not dot else 1)
    damage = battle_rules.hp_damage(amount,defense,mult,dot=dot)
    damage = min(m['hp'], damage)
    m['hp'] -= damage
    if damage and source:
        m['last_damage_source'] = deepcopy(source)
    if not dot and m.get('expose', 0):
        m['expose'] -= 1
    text = f'{channel} resisted — {damage} damage' if mult < 1 else f'{damage} {channel} damage'
    event(p, 'resist' if mult < 1 else 'damage', text, defender=m['instance'], channel=channel, damage=damage)
    return damage


def _add_effect(p, kind, source, amount):
    m = current(p)
    rule = collection.catalog()['effectRules'][kind]
    immunity = rule.get('immunity')
    if immunity and immunity in m['traits']:
        event(p, 'immune', f"{m['name']}: {immunity} — {kind} has no effect", defender=m['instance'])
        return
    if kind == 'push':
        m['gap'] = min(3, m['gap'] + rule['steps'])
        m['pushed'] = True
    elif kind == 'stun':
        if m.get('stun_recovery', 0):
            event(p, 'immune', 'Recovering from stun — cannot be stunned again yet', defender=m['instance'])
            return
        m['stunned'] = True
    elif kind == 'slow':
        m['slow'] = rule['phases']
    elif kind == 'expose':
        m['expose'] = rule['hits']
    elif kind in ('poison','burn','bleed'):
        damage = max(1, round(amount * rule['rate'] * (1.5 if kind == 'burn' and 'flammable' in m['traits'] else 1)))
        existing = next((e for e in m['effects'] if e['kind'] == kind and
            (e['source']['id'] == source['id'] or rule['stack']=='strongest')), None)
        entry = dict(kind=kind, source=deepcopy(source), amount=damage, remaining=rule['phases'],
            channel=rule['channel'], applied_turn=p['group']['turn'])
        if existing and rule['stack']=='strongest' and existing['amount'] > damage:
            entry.update(amount=existing['amount'],source=deepcopy(existing['source']))
        if existing:
            existing.update(entry)
        else:
            m['effects'].append(entry)
    event(p, 'effect', f"{kind.title()} applied", defender=m['instance'])


def _strike(p, iid, skill):
    g, m = p['group'], current(p)
    item = p['collection'][iid]
    info, family = collection.stats(item), collection.families()[item['family']]
    p['active_weapon'] = iid
    collection.project_legacy(p)
    rank = int((p.get('training') or {}).get(info['path'], 0))
    attack = battle_rules.attack(p,item)
    source = dict(id=iid,path=info['path'],focus=info['path']=='staff' and bool((p.get('mastery') or {}).get('staff')))
    if m['exhausted']:
        attack *= .5
    arrow = quiver.consume(p,item) if info['path']=='bow' else None
    channel,impact = battle_rules.impact(family,m['gap'],arrow,skill=skill)
    attack *= impact
    if info['path']=='bow' and (p.get('mastery') or {}).get('bow') and m['gap']==3:
        if state.rng_int(p,1,100) <= round(economy.LONG_DRAW_TOP*100):
            attack *= economy.LONG_DRAW_CRIT_MULT
            event(p,'mastery','Long Draw critical',defender=m['instance'])
    item['durability'] = max(0, item['durability'] - 1)
    # Compatibility gear pointers must not restore condition on the next read.
    collection.project_legacy(p)
    if skill:
        g['cooldowns'][iid] = family['cooldown'] + 1
    miss = max(0, 18 - 2 * rank)
    if state.rng_int(p, 1, 100) <= miss:
        event(p, 'miss', info['name'] + ' missed', defender=m['instance'])
        return
    amount = max(1, state.rng_jitter(p, round(attack), .08))
    _hurt_monster(p, amount, channel, source=source)
    if arrow and arrow['status'] and m['hp'] > 0:
        _add_effect(p,arrow['status'],source,amount)
    if skill and m['hp'] > 0:
        effect = family['technique']
        if effect in collection.catalog()['effectRules']:
            _add_effect(p, effect, source, amount)


def _kill(p):
    g, m = p['group'], current(p)
    if m['killed']:
        return
    m['killed'] = True
    reward = m['rewards']
    xp = max(1, round(reward['xp'] * (1.05 if p.get('race') == 'elf' else 1)))
    buff = state.faction_buff_pct(p, 'xp')
    xp = round(xp * (1 + buff / 100))
    got = state.gain_xp(p, xp)
    rested = state.rested_bonus(p, got) if got else 0
    landed = state.gain_xp(p, rested) if rested else 0
    if landed < rested:
        p['rested'] = int(p.get('rested', 0)) + rested - landed
    xp = got + landed
    m['kill_path'] = (m.get('last_damage_source') or {}).get('path','blade')
    g['xp'] += xp
    g['haul']['gold'] += reward['gold']
    for name, count in reward['materials'].items():
        g['haul']['materials'][name] = g['haul']['materials'].get(name, 0) + count
    if reward['weapon']:
        g['haul']['weapons'].append({**reward['weapon'], 'receipt': m['instance']})
    combat._ledger(p, 'kill', xp=xp, note=m['instance'])
    event(p, 'kill', f"{m['name']} defeated. +{xp} XP kept; haul pending.", defender=m['instance'])


def _enemy_phase(p, *, guard=False, prior_effects=()):
    g, m = p['group'], current(p)
    for effect in prior_effects:
        if m['hp'] > 0:
            _hurt_monster(p,effect['amount'],effect['channel'],dot=True,source=effect['source'])
        current_effect = next((e for e in m['effects'] if e['kind']==effect['kind'] and
            e['source']['id']==effect['source']['id']),None)
        if current_effect and current_effect['applied_turn'] < g['turn']:
            current_effect['remaining'] -= 1
    m['effects'] = [e for e in m['effects'] if e['remaining'] > 0]
    g['cooldowns'] = {iid:max(0, n-1) for iid, n in g['cooldowns'].items()}
    if m['hp'] <= 0:
        return
    speed = monster_speed(m)
    if m.get('slow', 0):
        m['slow'] -= 1
    if m.pop('stunned', False):
        m['stun_recovery'] = collection.catalog()['effectRules']['stun']['recovery']
        event(p, 'control', 'Stunned — enemy attack skipped', defender=m['instance'])
        return
    if m.get('stun_recovery', 0):
        m['stun_recovery'] -= 1
    if m.pop('pushed', False):
        event(p, 'control', 'Pushed back — room for your next action', defender=m['instance'])
        return
    if m['gap'] > 0:
        m['gap'] = max(0, m['gap'] - (2 if speed >= player_speed(p) + 3 else 1))
        if m['gap'] > 0:
            event(p, 'move', f"{m['name']} closes to {DISTANCE[m['gap']].lower()}")
            return
    raw = max(1, state.rng_jitter(p, m['atk'], .08))
    armor = state.gear_bonus(p, 'armor')
    if p.get('race')=='giant':
        armor *= 1.05
    shield = 0 if state.is_broken(p,'shield') else state.gear_bonus(p, 'shield')
    hit = battle_rules.incoming(raw,armor,shield,guard=guard)
    damage, absorbed = hit['hp'],hit['shield']
    if absorbed and 'shield' in p.get('durability', {}):
        p['durability']['shield'] = max(0, p['durability']['shield'] - hit['wear'])
    p['hp'] = max(0, p['hp'] - damage)
    event(p, 'incoming', f'{damage} HP lost; shield absorbed {absorbed}', defender='player', damage=damage)
    if (p.get('mastery') or {}).get('blade') and not m['air'] and m['gap']==0 and absorbed+hit['armor'] >= damage:
        blades = [p['collection'][iid] for iid in g['deck'] if iid and
            collection.stats(p['collection'][iid])['path']=='blade' and p['collection'][iid]['durability']>0]
        if blades:
            blade = max(blades,key=battle_rules.contribution)
            amount = battle_rules.attack(p,blade) * economy.RIPOSTE_RETURN * (.5 if m['exhausted'] else 1)
            _hurt_monster(p,amount,'Power',source=dict(id=blade['id'],path='blade',focus=False))
            blade['durability'] = max(0,blade['durability']-1)
            collection.project_legacy(p)
            event(p,'mastery','Blade mastery: Riposte',defender=m['instance'])


def _finish(p, won=False, escaped=False):
    g = p['group']
    result = dict(id=g['id'], won=won, escaped=escaped, floor=g['floor'], kills=sum(m['killed'] for m in g['members']),
                  count=len(g['members']), xp=g['xp'], energy=g['energy'], exhausted=sum(m['exhausted'] for m in g['members']), haul=deepcopy(g['haul']), events=deepcopy(g['events']))
    if won:
        if g['site']:
            expedition = p['expedition']
            expedition['gold'] += g['haul']['gold']
            for name, n in g['haul']['materials'].items():
                expedition['haul'][name] = expedition['haul'].get(name, 0) + n
            expedition['weapons'].extend(g['haul']['weapons'])
            from .gathering import _site
            target = _site(p)['material']
            expedition['haul'][target] = expedition['haul'].get(target, 0) + len(g['members'])
            expedition['message'] = f"Ambush cleared. +{len(g['members'])} {target}; extract to secure your haul."
        else:
            p['gold'] += g['haul']['gold']
            for name, n in g['haul']['materials'].items():
                p['materials'][name] = p['materials'].get(name, 0) + n
            for drop in g['haul']['weapons']:
                from .core import pack_used, pack_cap
                full = pack_used(p) >= pack_cap(p)
                item = collection.mint(p, drop['family'], drop['grade'], 'drop', receipt=drop['receipt'])
                if full:
                    item['location'] = 'claim'
        from . import contracts, weekly
        for member in g['members']:
            contracts.note_kill(p, dict(id=member['id'], floor=g['floor']),
                {'blade':'melee', 'bow':'ranged', 'staff':'magic'}[member.get('kill_path','blade')])
            weekly.note(p, 'kills')
            if p.get('_world') is not None:
                p.setdefault('_effects', []).append(dict(kind='kill_note',floor=g['floor'],slug=member['id']))
        p['groups_cleared'] = int(p.get('groups_cleared', 0)) + 1
        combat._ledger(p, 'group_clear', gold=g['haul']['gold'] if not g['site'] else 0, note=g['id'])
    else:
        combat._ledger(p, 'group_escape' if escaped else 'group_defeat', note=g['id'])
        if g['site']:
            p['expedition'] = None
    p.setdefault('hunt_offers', {}).pop(g['offer'], None)
    p['group'] = None
    p['group_result'] = result
    p['location'] = 'gathering' if p.get('expedition') else 'gate_town'
    return result_scene(p)


def result_scene(p):
    r = p['group_result']
    won = r['won']
    return Scene(eyebrow=f"FLOOR {r['floor']} · GROUP RESULT",
        headline='Group defeated' if won else 'You escaped' if r['escaped'] else 'The group held its ground',
        support=f"{r['kills']}/{r['count']} defeated · {r['xp']} XP kept · {r['energy']} energy spent",
        body_lines=[f"{r['haul']['gold']} gold {'awaiting extraction' if won and p.get('expedition') else 'secured' if won else 'left behind'}",
                    ' · '.join(f'{k} ×{v}' for k,v in r['haul']['materials'].items()) or 'No materials in this haul'] + ([f"Carried gold lost: {r['death']['gold_lost']}. Bank and secured materials kept.", 'Your shardmind rescued you to camp.' if r['death']['rescued'] else 'You wake in Roothollow. Inspect your equipment for damage.'] if r.get('death') else []),
        options=[Option('group_return','Return to the expedition' if p.get('expedition') else 'Return to Roothollow' if p['location']=='town' else 'Return to camp')],
        meters=combat.meters(p), combat_events=deepcopy(r['events']))


def handle(p, oid):
    if not p.get('group'):
        if p.get('group_result') and oid == 'group_return':
            p.pop('group_result', None)
            from .core import _build_scene
            return _build_scene(p)
        return None
    g, m = p['group'], current(p)
    if g.get('combat_revision',1) < 2:
        from . import groups_v1
        return groups_v1.handle(p,oid)
    if oid.startswith('load_arrow:'):
        try:
            parts = oid.split(':')
            if len(parts)!=3:
                raise ValueError('Choose a current arrow payload')
            quiver.select(p,parts[1],parts[2])
            return scene(p)
        except ValueError as exc:
            return refuse(p,str(exc))
    if oid == 'flee' and not m['started']:
        if not g['committed']:
            p['group'] = None
            p['location'] = 'gate_town'
            from .core import _build_scene
            return _build_scene(p)
        return _finish(p, escaped=True)
    parts = oid.split(':')
    skill = parts[0] == 'skill'
    if parts[0] in ('strike','skill') and len(parts) == 2:
        iid = parts[1]
        if iid not in p['deck'] or iid not in p['collection']:
            return refuse(p, 'Choose one of your three selected weapons')
        item = p['collection'][iid]
        info = collection.stats(item)
        if item['durability'] <= 0:
            return refuse(p, 'This weapon is broken. Escape and repair it at the Forge.')
        if info['path'] == 'blade' and (m['air'] or m['gap']):
            return refuse(p, 'A blade cannot reach a flyer' if m['air'] else 'Close to contact first')
        if info['path']=='bow' and not quiver.count(p,item['grade'],quiver.chosen(p,item)):
            return refuse(p,'No arrows of the selected type remain. Select another payload or weapon.')
        if skill and (not collection.families()[item['family']]['cooldown'] or g['cooldowns'].get(iid, 0)):
            return refuse(p, 'That technique is not ready')
    elif oid == 'drink_tonic' and combat.pouch(p) != 'trollblood_tonic':
        return refuse(p, 'A trollblood tonic must be in your charm pouch')
    elif oid not in ('approach','withdraw','guard','flee','drink_tonic'):
        return refuse(p, 'Finish this group or escape before doing that')
    else:
        iid = None
    if not any(p['collection'][i]['durability'] > 0 for i in p['deck'] if i) and not g['committed']:
        return refuse(p, 'Select a usable weapon in your collection before beginning')
    p.pop('collection_view', None)
    g['events'] = []
    prior_effects = deepcopy(m['effects'])
    g['turn'] += 1
    _commit(p)
    if oid == 'flee':
        chance = max(.1, min(.95, .2 + .15*m['gap'] + .03*(player_speed(p) - monster_speed(m))))
        if state.rng_int(p, 1, 10000) <= round(chance * 10000):
            return _finish(p, escaped=True)
        event(p, 'escape', 'Escape blocked — the enemy catches you')
    elif oid == 'drink_tonic':
        combat.spend_pouch(p)
        p['hp'] = state.max_hp(p)
        event(p, 'heal', 'Trollblood restores your health')
    elif iid:
        _strike(p, iid, skill)
    elif oid == 'approach':
        m['gap'] = max(0, m['gap'] - 1)
    elif oid == 'withdraw':
        m['gap'] = min(3, m['gap'] + (2 if player_speed(p) > monster_speed(m) else 1))
    _enemy_phase(p,guard=oid=='guard',prior_effects=prior_effects)
    if m['hp'] <= 0:
        _kill(p)
    if p['hp'] <= 0:
        if p.get('daily', {}).get('death_save') and combat.pouch(p) == 'stone_of_undying' and not g['life_used']:
            combat.spend_pouch(p)
            g['life_used'] = True
            p['hp'] = max(1, round(state.max_hp(p) * economy.STONE_REVIVE_PCT))
            event(p, 'revive', 'The Stone of Undying burns. Same fight, same committed weapons.')
            if m['hp'] > 0:
                return scene(p)
    if p['hp'] <= 0:
        daily_save = not p.setdefault('daily', {}).get('death_save')
        p['daily']['death_save'] = True
        loss = _death_cost(p, daily_save)
        combat._ledger(p, 'death', gold=-loss, note=g['id'])
        if p.get('_world') is not None:
            p.setdefault('_effects', []).append(dict(kind='happening',floor=g['floor'],tag='kill',
                line=f"{p.get('name') or 'A climber'} fell to {m['name']} on floor {g['floor']}"))
        _finish(p)
        p['group_result']['death'] = dict(rescued=daily_save,gold_lost=loss)
        if daily_save:
            p['hp'] = 1
        else:
            p.update(location='town',floor=0,hp=state.max_hp(p))
        return result_scene(p)
    if m['hp'] <= 0:
        if g['index'] == len(g['members']) - 1:
            return _finish(p, won=True)
        g['index'] += 1
    return scene(p)


def _death_cost(p, daily_save):
    if p['level'] <= economy.DEATH_FREE_MAX_LEVEL:
        fraction = 0
    elif daily_save or p['level'] <= economy.BEGINNER_MERCY_MAX_LEVEL:
        fraction = .5
    elif p['level'] >= economy.DEATH_NO_PARDON_LEVEL:
        fraction = economy.DEATH_GOLD_NO_PARDON
    else:
        fraction = state.rng_int(p,round(economy.DEATH_GOLD_MIN*100),round(economy.DEATH_GOLD_MAX*100))/100
    loss = p['gold'] - p['gold']//2 if fraction == .5 else round(p['gold']*fraction)
    p['gold'] -= loss
    if not daily_save and p['level'] > economy.BEGINNER_MERCY_MAX_LEVEL:
        for item in p['collection'].values():
            if item.get('location','carried') == 'carried' and item['source'] != 'starter':
                if state.roll_ok(p,economy.DEATH_WEAPON_LOSS):
                    item['durability'] = 0
        for slot in ('armor','shield','shoes'):
            gear = economy.FORGE.get(p['gear'].get(slot) or '')
            if gear and gear.price > 0 and slot in p.get('durability',{}):
                p['durability'][slot] = max(0,p['durability'][slot]-round(economy.item_pool(gear)*economy.DEATH_DURABILITY_HIT))
        if p['level'] >= economy.DEATH_NO_PARDON_LEVEL:
            stacks=sorted(slug for slug,n in p.get('inventory',{}).items() if n>0 and slug not in economy.BASIC_WEAPONS)
            if stacks:
                slug=stacks[state.rng_int(p,0,len(stacks)-1)]
                p['inventory'].pop(slug)
                p.get('durability_pack',{}).pop(slug,None)
        collection.project_legacy(p)
    return loss
