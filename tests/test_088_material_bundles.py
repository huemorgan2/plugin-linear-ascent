"""Exact material composition and persistence across the opening correction."""
from copy import deepcopy
import pytest
from plugin_linear_ascent.engine import bestiary,collection,core,gathering,groups,state
from plugin_linear_ascent.content import schema

pytestmark=pytest.mark.reel


@pytest.mark.parametrize('member,ratios',[(dict(air=True,affinity='Common'),(3,1)),(dict(air=False,affinity='Magic'),(1,3)),(dict(air=False,affinity='Power'),(2,2))])
@pytest.mark.parametrize('floor', [1,7,25,26,50,51,75,76,100])
def test_grade_carriers_award_both_materials_with_bounded_y(monkeypatch,member,ratios,floor):
    m={**member,'specimen':'common','rates':{'material':dict.fromkeys(collection.GRADES,100),'weapon':dict.fromkeys(collection.GRADES,100)}}
    monkeypatch.setattr(state,'rng_int',lambda *a:1)
    monkeypatch.setattr(state,'rng_pick',lambda p,table:table[0][1])
    reward=bestiary.roll_rewards({},floor,m)
    assert set(reward['materials'])=={v for pair in collection.MATERIALS for v in pair}
    for gi,grade in enumerate(collection.GRADES):
        y=min(5,1+max(0,floor-(1+gi*25))//6)
        expected={name:n*y for name,n in zip(collection.MATERIALS[gi],ratios)}
        assert m['bundles'][grade]==expected
        assert all(reward['materials'][name]==n for name,n in expected.items())
    assert reward['weapon']['grade']=='Common'  # one categorical item, not four


def player(monkeypatch):
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    p=state.new_player('material-persistence')
    p.update(stage='playing',name='Bundle',race='human',floor=3,location='gate_town',unlocked_floor=3,gold=300)
    core.current_scene(p)
    return p


def test_old_rolled_rewards_never_enlarged_on_read_or_settlement(monkeypatch):
    p=player(monkeypatch)
    members=[bestiary.rolled_member(p,3,schema.get_floor(3).encounters[0].id) for _ in range(2)]
    for m in members:
        m.update(hp=1,hp_max=1,defense=0,magic=1)
        m.pop('bundles');m.pop('reward_revision')
        m['rewards']={'gold':1,'xp':1,'materials':{'Wood':1},'weapon':None}
    groups.open_group(p,members=members)
    old=deepcopy(p['group'])
    core.current_scene(p)
    assert p['group']==old
    p['training']['staff']=10
    for _ in members:core.apply_choice(p,'strike:'+p['deck'][2])
    assert p['group_result']['won'] and p['materials']['Wood']==2


def test_existing_expedition_keeps_one_unit_rule_new_trip_gets_two(monkeypatch):
    p=player(monkeypatch)
    for oid in ('gather_site:drowned-copse','gather_tool','gather_begin'):assert not core.apply_choice(p,oid).refusal
    p['expedition'].pop('site_rules')  # persisted before the rules snapshot field
    rolls=iter([1,100,1,100]);monkeypatch.setattr(state,'rng_int',lambda *a:next(rolls))
    core.apply_choice(p,'gather_step')
    assert p['expedition']['haul']['Wood']==1
    core.apply_choice(p,'gather_extract')
    for oid in ('gather_site:drowned-copse','gather_begin','gather_step'):assert not core.apply_choice(p,oid).refusal
    assert p['expedition']['haul']['Wood']==2 and p['materials']['Wood']==1
    core.apply_choice(p,'gather_extract')
    assert p['materials']['Wood']==3
