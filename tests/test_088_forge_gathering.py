"""Real core actions; explicit resource fixtures prove conservation, not pace."""
from copy import deepcopy
import pytest
from plugin_linear_ascent.engine import bestiary,collection,core,gathering,groups,state,workshop
from plugin_linear_ascent.render import render_scene

pytestmark=pytest.mark.reel


def player(monkeypatch):
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    p=state.new_player('forge-gather-laws')
    p.update(stage='playing',name='Gather',race='human',floor=3,location='gate_town',
        unlocked_floor=100,gold=10**15,training=dict(blade=10,bow=10,staff=10))
    core.current_scene(p)
    return p


def action(p,oid):
    s=core.apply_choice(p,oid)
    assert not s.refusal,s.refusal
    return s


def enter(p):
    action(p,'gather_site:drowned-copse')
    action(p,'gather_tool')
    action(p,'gather_begin')


def test_forge_quote_source_condition_upgrade_cost_and_retry(monkeypatch):
    p=player(monkeypatch)
    action(p,'weapon_shop')
    s=action(p,'shop_grade:Legendary')
    assert 'Legendary' in render_scene(s)
    assert 'condition' in s.to_text()
    before=p['gold'];q=workshop.acquisition_quote('viper','Legendary')
    action(p,'forge_buy:viper:Legendary')
    item=p['collection'][p['collection_selected']]
    assert item['level']==6 and item['durability']==item['maximum']
    assert p['gold']==before-q['gold']
    q=collection.upgrade_quote(item)
    p['materials'].update(q['materials'])
    item['durability']=10
    oldmax=item['maximum'];before=p['gold'];scene=core.current_scene(p).scene_id
    action(p,'upgrade:'+item['id'])
    assert item['level']==7 and item['durability']==10+item['maximum']-oldmax
    assert p['gold']==before-q['gold'] and all(p['materials'][k]==0 for k in q['materials'])
    assert core.apply_choice(p,'upgrade:'+item['id'],expected_scene=scene).refusal
    assert item['level']==7


def test_forge_wrong_location_and_missing_materials_never_charge(monkeypatch):
    p=player(monkeypatch);iid=p['deck'][0]
    before=(p['gold'],deepcopy(p['materials']),deepcopy(p['collection']))
    assert core.apply_choice(p,'upgrade:'+iid).refusal
    action(p,'forge_collection')
    assert core.apply_choice(p,'upgrade:'+iid).refusal
    assert (p['gold'],p['materials'],p['collection'])==before
    p['collection'][iid]['level']=20
    assert collection.upgrade_quote(p['collection'][iid]) is None


def test_zero_gold_starter_repair_has_energy_cost(monkeypatch):
    p=player(monkeypatch);iid=p['deck'][0];p['gold']=0
    p['collection'][iid]['durability']=0;collection.project_legacy(p)
    action(p,'forge_collection');action(p,'inspect:'+iid)
    energy=state.energy_now(p)
    action(p,'practice:'+iid)
    assert state.energy_now(p)==energy-1 and p['gold']==0
    assert p['collection'][iid]['durability']==p['collection'][iid]['maximum']


def test_full_pack_claims_are_owned_and_block_hunt_without_loss(monkeypatch):
    p=player(monkeypatch)
    for _ in range(core.pack_cap(p)):
        collection.mint(p,'viper')
    item=collection.mint(p,'thunder',source='drop',receipt='fixture-overflow')
    item['location']='claim'
    assert core.apply_choice(p,'hunt').refusal
    assert core.apply_choice(p,'take:'+item['id']).refusal
    action(p,'forge_collection')
    action(p,'inspect:'+item['id']);action(p,'store:'+item['id'])
    assert not collection.claims(p) and collection.reconcile(p)['ok']
    p.pop('collection_view',None);p.update(floor=3,location='gate_town')
    assert core.apply_choice(p,'deck:0:'+item['id']).refusal


def test_gather_gate_tools_energy_and_no_duplicate_extract(monkeypatch):
    p=player(monkeypatch)
    assert 'gather_site:drowned-copse' in [o.id for o in core.current_scene(p).options]
    action(p,'gather_site:drowned-copse')
    assert core.apply_choice(p,'gather_begin').refusal
    deck=deepcopy(p['deck']);used=core.pack_used(p)
    action(p,'gather_tool');action(p,'gather_begin')
    assert core.pack_used(p)==used and p['deck']==deck
    # One yield and no ambush; only environmental chance is forced here.
    rolls=iter([1,100]);monkeypatch.setattr(state,'rng_int',lambda *args:next(rolls))
    energy=state.energy_now(p);before=p['materials'].get('Wood',0)
    action(p,'gather_step')
    assert state.energy_now(p)==energy-1 and p['materials'].get('Wood',0)==before
    assert p['expedition']['haul']['Wood']==1
    assert p['utility_tools']['wood-axe']['condition']==99
    action(p,'gather_extract');assert p['materials']['Wood']==before+1
    assert core.apply_choice(p,'gather_extract').refusal
    assert p['materials']['Wood']==before+1


def test_ambush_retreat_loses_entire_expedition_not_owned_resources(monkeypatch):
    p=player(monkeypatch);p['materials']['Wood']=17
    enter(p);p['expedition']['haul']['Wood']=8
    def ambush(p,site):
        ms=[bestiary.rolled_member(p,3,__import__('plugin_linear_ascent.content.schema',fromlist=['get_floor']).get_floor(3).encounters[0].id) for _ in range(2)]
        for m in ms:m.update(hp=1,hp_max=1,defense=0,gap=3)
        return ms
    monkeypatch.setattr(gathering,'ambush_members',ambush)
    # Force ambush but leave combat RNG intact after the gather roll.
    real=state.rng_int;rolls=[1,1]
    monkeypatch.setattr(state,'rng_int',lambda *a:rolls.pop(0) if rolls else real(*a))
    energy=state.energy_now(p);action(p,'gather_step')
    assert state.energy_now(p)==energy-1 and p['group']['committed']
    action(p,'strike:'+p['deck'][1])
    assert state.energy_now(p)==energy-2
    action(p,'flee')
    assert p['expedition'] is None and p['materials']['Wood']==17
    assert p['group_result']['xp']>0


def test_ambush_win_returns_to_expedition_and_target_bonus_waits_for_extract(monkeypatch):
    p=player(monkeypatch);enter(p)
    from plugin_linear_ascent.content import schema
    ms=[bestiary.rolled_member(p,3,schema.get_floor(3).encounters[0].id) for _ in range(2)]
    for m in ms:
        m.update(hp=1,hp_max=1,defense=0,gap=3)
        m['rewards']=dict(gold=10,xp=3,materials={},weapon=None)
    groups.open_group(p,members=ms,site='drowned-copse')
    gold=p['gold'];before=p['materials'].get('Wood',0)
    for _ in range(2):action(p,'strike:'+p['deck'][1])
    assert p['gold']==gold and p['materials'].get('Wood',0)==before
    assert p['expedition']['haul']['Wood']==2
    assert 'awaiting extraction' in core.current_scene(p).to_text()
    action(p,'group_return');action(p,'gather_extract')
    assert p['gold']==gold+20 and p['materials']['Wood']==before+2


def test_expedition_blocks_healing_regear_and_can_extract_when_broken_and_empty(monkeypatch):
    p=player(monkeypatch);enter(p)
    before=(p['gold'],p['hp'],deepcopy(p['deck']))
    for oid in ('heal','town','forge_collection','deposit_all','sleep_fields','gather_tool'):
        assert core.apply_choice(p,oid).refusal
        assert (p['gold'],p['hp'],p['deck'])==before
    p['energy_val']=0;p['utility_tools']['wood-axe']['condition']=0
    assert core.apply_choice(p,'gather_step').refusal
    action(p,'gather_extract')
    assert p['expedition'] is None
