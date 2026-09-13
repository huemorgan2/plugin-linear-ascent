"""Actual core transitions for the sequential encounter contract."""
from copy import deepcopy
import pytest

from plugin_linear_ascent.engine import bestiary, collection, core, groups, state
from plugin_linear_ascent.content import schema
from plugin_linear_ascent import economy

pytestmark = pytest.mark.reel


def climber(monkeypatch, *, energy=10):
    monkeypatch.setenv('ASCENT_RULESET', collection.RULESET)
    p = state.new_player('group-contract')
    p.update(stage='playing',name='Group',race='human',location='gate_town',floor=1,
             training=dict(blade=10,bow=10,staff=10),energy_val=energy)
    core.current_scene(p)
    return p


def fixture_group(p, n=5):
    slug = schema.get_floor(1).encounters[0].id
    monsters = [bestiary.rolled_member(p,1,slug,opening=True) for _ in range(n)]
    for m in monsters:
        m.update(hp=1,hp_max=1,atk=1,defense=0,gap=3)
        m['rewards'] = dict(gold=10,xp=30,materials={'Wood':1},weapon=None)
    groups.open_group(p,members=monsters)
    return p['deck'][1]


def test_five_enemies_two_energy_exhausts_only_the_last_three(monkeypatch):
    p=climber(monkeypatch,energy=2)
    bow=fixture_group(p)
    assert state.energy_now(p)==2
    before_gold=p['gold']
    flags=[]
    for i in range(5):
        scene=core.apply_choice(p,'strike:'+bow)
        if p['group']:
            flags.append(deepcopy(p['group']['members'][i]))
            assert p['gold']==before_gold
            assert p['materials'].get('Wood',0)==0
            assert not groups.current(p)['started']
            assert state.xp_total(p)==30*(i+1)
    assert [(m['paid'],m['exhausted']) for m in flags]==[(True,False),(True,False),(False,True),(False,True)]
    assert state.energy_now(p)==0 and p['group_result']['energy']==2
    assert p['group_result']['won'] and p['gold']==before_gold+50
    assert p['materials']['Wood']==5 and state.xp_total(p)==150
    assert p['xp_reserve']>0


def test_leave_after_two_keeps_three_energy_and_xp_but_loses_haul(monkeypatch):
    p=climber(monkeypatch,energy=5)
    bow=fixture_group(p)
    p['materials']['Wood']=9
    gold=p['gold']
    core.apply_choice(p,'strike:'+bow)
    core.apply_choice(p,'strike:'+bow)
    core.apply_choice(p,'flee')
    assert p['group'] is None and p['group_result']['escaped']
    assert state.energy_now(p)==3 and state.xp_total(p)==60
    assert p['materials']['Wood']==9 and p['gold']==gold


def test_same_unstarted_offer_survives_leaving_and_reload(monkeypatch):
    p=climber(monkeypatch)
    core.apply_choice(p,'hunt')
    offer=deepcopy(p['group'])
    rng=p['rng_counter']
    hp,energy=p['hp'],state.energy_now(p)
    core.current_scene(p)
    core.current_scene(p)
    assert p['group']==offer and p['rng_counter']==rng
    core.apply_choice(p,'flee')
    core.apply_choice(p,'hunt')
    assert p['group']==offer and p['rng_counter']==rng
    assert p['hp']==hp and state.energy_now(p)==energy


def test_invalid_unreachable_and_foreign_actions_spend_nothing(monkeypatch):
    p=climber(monkeypatch)
    fixture_group(p)
    before=deepcopy(p)
    scene=core.apply_choice(p,'strike:'+p['deck'][0])
    assert scene.refusal
    for key in ('gold','energy_val','rng_counter','group','collection'):
        assert p[key]==before[key]
    assert core.apply_choice(p,'strike:not-owned').refusal
    assert not p['group']['committed']


def test_committed_deck_and_no_remote_town_or_inventory_actions(monkeypatch):
    p=climber(monkeypatch)
    bow=fixture_group(p)
    groups.current(p)['hp']=500
    core.apply_choice(p,'strike:'+bow)
    before=(p['hp'],p['gold'],deepcopy(p['deck']))
    for oid in ('heal','forge','deposit_all','sleep_fields','use_medgel','buy_carry3'):
        assert core.apply_choice(p,oid).refusal
        assert (p['hp'],p['gold'],p['deck'])==before
    core.apply_choice(p,'collection')
    candidate=collection.mint(p,'viper')
    assert core.apply_choice(p,'deck:0:'+candidate['id']).refusal


def test_final_kill_retry_cannot_pay_twice(monkeypatch):
    p=climber(monkeypatch)
    bow=fixture_group(p,n=2)
    core.apply_choice(p,'strike:'+bow)
    observed=core.current_scene(p).scene_id
    core.apply_choice(p,'strike:'+bow,expected_scene=observed)
    after=deepcopy(p)
    assert core.apply_choice(p,'strike:'+bow,expected_scene=observed).refusal
    assert p==after


def test_push_creates_a_real_opening_and_cooldown_survives_next_member(monkeypatch):
    p=climber(monkeypatch)
    item=collection.mint(p,'ramguard')
    collection.set_slot(p,0,item['id'])
    bow=fixture_group(p,n=2)
    m=groups.current(p)
    m.update(hp=100,hp_max=100,gap=0,traits=[])
    hp=p['hp']
    core.apply_choice(p,'skill:'+item['id'])
    assert m['gap']==2 and p['hp']==hp
    cooldown=p['group']['cooldowns'][item['id']]
    m['hp']=1
    core.apply_choice(p,'strike:'+bow)
    assert p['group']['index']==1
    assert p['group']['cooldowns'][item['id']]==cooldown-1
    assert not groups.current(p)['started']


def test_resistance_feedback_reports_the_resolved_channel_and_defender(monkeypatch):
    from plugin_linear_ascent.render import render_scene_fragment
    p=climber(monkeypatch)
    fixture_group(p,n=2)
    m=groups.current(p)
    m.update(hp=500,hp_max=500,magic=.3,affinity='Magic',type='ground-magic')
    s=core.apply_choice(p,'strike:'+p['deck'][2])
    hit=next(e for e in s.combat_events if e['kind']=='resist')
    assert hit['channel']=='Magic' and hit['defender']==m['instance']
    assert hit['damage']==500-m['hp']
    html=render_scene_fragment(s)
    assert 'data-combat-event="'+hit['id']+'"' in html
    assert 'Magic resisted' in html
    assert hit['text'] in s.to_text()


def test_shield_always_leaks_damage_and_wears_when_it_absorbs(monkeypatch):
    p=climber(monkeypatch)
    fixture_group(p)
    m=groups.current(p)
    m.update(hp=500,hp_max=500,atk=100,gap=0)
    p['gear']['shield']=max((g for g in economy.FORGE.values() if g.slot=='shield'),key=lambda g:g.bonus).slug
    p['durability']['shield']=1000
    monkeypatch.setattr(state,'rng_jitter',lambda p,base,pct:base)
    hp=p['hp']
    core.apply_choice(p,'guard')
    assert hp-p['hp']>=25
    assert p['durability']['shield']<1000


def test_candidate_new_character_gets_three_real_starters_once(monkeypatch):
    p=climber(monkeypatch)
    assert len(p['collection'])==3
    assert {collection.stats(p['collection'][i])['path'] for i in p['deck']}=={'blade','bow','staff'}
    before=deepcopy(p['collection'])
    state.ensure_current(p)
    assert p['collection']==before


def test_daily_rescue_second_death_keeps_levels_bank_and_stored_weapons(monkeypatch):
    p=climber(monkeypatch)
    p.update(level=12,gold=1000,bank=77)
    p['materials']['Wood']=23
    paid=collection.mint(p,'viper');paid['level']=7
    stored=collection.mint(p,'thunder');stored['location']='storage'
    for rescue in (True,False):
        p['hp']=1;fixture_group(p,n=2)
        m=groups.current(p);m.update(hp=10000,atk=10000,gap=0)
        beforegold=p['gold']
        # Ensure paid-weapon condition loss; retain actual combat RNG.
        monkeypatch.setattr(state,'roll_ok',lambda *args:True)
        core.apply_choice(p,'guard')
        r=p['group_result']
        assert r['death']['rescued']==rescue and p['gold']<beforegold
        assert p['bank']==77 and p['materials']['Wood']==23
        assert paid['level']==7 and stored['durability']==stored['maximum']
        if rescue:
            assert p['hp']==1 and p['location']=='gate_town'
        else:
            assert p['hp']==state.max_hp(p) and p['location']=='town'
            assert paid['durability']==0
        core.apply_choice(p,'group_return')
        p.update(floor=1,location='gate_town')


def test_stone_revives_once_without_unlocking_deck_or_settling_haul(monkeypatch):
    p=climber(monkeypatch);p['daily']['death_save']=True
    p['hp']=1
    # Pouch API is unrelated to group settlement; this tests consuming its
    # actual spend function with the documented legacy pouch representation.
    p['gear']['charm']='stone_of_undying'
    fixture_group(p,n=2)
    m=groups.current(p);m.update(hp=10000,atk=10000,gap=0)
    assert __import__('plugin_linear_ascent.engine.combat',fromlist=['pouch']).pouch(p)=='stone_of_undying'
    core.apply_choice(p,'guard')
    assert p['group']['life_used'] and p['hp']>0 and collection.locked(p)
    assert not p.get('group_result')
    p['hp']=1;core.apply_choice(p,'guard')
    assert p['group'] is None and p['group_result']['death']


def test_contract_and_weekly_credits_require_full_group(monkeypatch):
    from plugin_linear_ascent.engine import contracts,weekly
    p=climber(monkeypatch);bow=fixture_group(p,n=2)
    calls=[]
    monkeypatch.setattr(contracts,'note_kill',lambda p,e,d:calls.append(('contract',e,d)))
    monkeypatch.setattr(weekly,'note',lambda p,k:calls.append(('weekly',k)))
    core.apply_choice(p,'strike:'+bow)
    assert not calls
    core.apply_choice(p,'flee');assert not calls
    core.apply_choice(p,'group_return');bow=fixture_group(p,n=2)
    core.apply_choice(p,'strike:'+bow);core.apply_choice(p,'strike:'+bow)
    assert len(calls)==4 and calls[0][2]=='ranged'


def test_group_roster_and_xp_rules_reach_the_text_and_map_surfaces(monkeypatch):
    from plugin_linear_ascent import render
    p=climber(monkeypatch)
    camp=core.current_scene(p)
    hunt=next(marker for marker in camp.map['markers'] if marker['opt']=='hunt')
    assert 'enemy' in hunt['cost'] and 'free' in hunt['tip']
    html=render.render_scene(camp)
    assert 'surplus goes nowhere' not in html
    assert 'beyond the level bar is saved' in html
    scene=core.apply_choice(p,'hunt')
    text=scene.to_text()
    assert 'Group roster' in text and 'gold pending until full clear' in text
    for m in p['group']['members']:
        assert m['name'] in text and m['affinity'] in text
    before=deepcopy(p)
    # Simulate PostgreSQL returning object keys in a different order.
    p['collection']=dict(reversed(list(p['collection'].items())))
    assert [i['id'] for i in collection.payload(p)['items']][:3]==p['deck']
    assert p==before


def test_luna_advice_receives_actual_reach_and_technique_bonus(monkeypatch):
    import json
    from plugin_linear_ascent import plugin
    p=climber(monkeypatch)
    core.apply_choice(p,'hunt')
    scene=core.current_scene(p)
    text=json.loads(plugin.build_payload(scene))
    rendered=str(text)
    assert 'Current distance: Cover' in rendered
    assert 'Blades require Ground and Contact' in rendered
    cover=next(o for o in scene.options if o.label.startswith('Cover shot'))
    assert '20%' in cover.hint and 'distance 2–3' in cover.hint
    assert next(o for o in scene.options if o.id=='strike:'+p['deck'][0]).locked
    assert 'cover-shot double' not in plugin._GUIDE_RULES
    assert 'first level ◈ 200' not in plugin._SHARED_RULES
