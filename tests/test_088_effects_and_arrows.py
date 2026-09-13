"""Small exact combat fixtures verify time, source and paid arrow conservation."""
from copy import deepcopy
import pytest
from plugin_linear_ascent.engine import battle_rules,bestiary,collection,core,groups,quiver,state,workshop
from plugin_linear_ascent.content import schema
from plugin_linear_ascent import economy

pytestmark=pytest.mark.reel


def setup(monkeypatch, family='viper', pathslot=0):
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    p=state.new_player('effect-laws')
    p.update(stage='playing',name='Effects',race='human',location='gate_town',floor=3,unlocked_floor=100,
        energy_val=20,gold=10000,training=dict(blade=10,bow=10,staff=10))
    core.current_scene(p)
    item=collection.mint(p,family)
    collection.set_slot(p,pathslot,item['id'])
    members=[bestiary.rolled_member(p,3,schema.get_floor(3).encounters[0].id) for _ in range(2)]
    for m in members:m.update(hp=1000,hp_max=1000,atk=1,defense=0,power=1,magic=1,air=False,gap=0,traits=[])
    groups.open_group(p,members=members)
    monkeypatch.setattr(state,'rng_int',lambda p,lo,hi:hi)
    monkeypatch.setattr(state,'rng_jitter',lambda p,n,pct:n)
    monkeypatch.setattr(battle_rules,'attack',lambda p,item:100)
    return p,item,groups.current(p)


def act(p,oid):
    s=core.apply_choice(p,oid)
    assert not s.refusal,s.refusal
    return s


@pytest.mark.parametrize('family,kind,tick,phases',[('viper','poison',8,3),('briar','bleed',10,2),('ember','burn',12,2)])
def test_dot_starts_next_action_ticks_exactly_and_snapshots_source(monkeypatch,family,kind,tick,phases):
    p,item,m=setup(monkeypatch,family)
    act(p,'skill:'+item['id'])
    assert m['hp']==900 and m['effects'][0]['remaining']==phases
    before=deepcopy(m['effects'])
    core.current_scene(p);core.current_scene(p)
    assert m['effects']==before
    item['level']=20 # Later changes cannot scale already-applied damage.
    for n in range(phases):
        act(p,'guard');assert m['hp']==900-tick*(n+1)
    assert not m['effects']
    act(p,'guard');assert m['hp']==900-tick*phases


def test_dot_kill_credits_applying_blade_after_a_staff_miss(monkeypatch):
    p,item,m=setup(monkeypatch)
    act(p,'skill:'+item['id']);m['hp']=5
    p['training']['staff']=0
    monkeypatch.setattr(state,'rng_int',lambda p,lo,hi:lo)
    act(p,'strike:'+p['deck'][2])
    assert p['active_weapon']==p['deck'][2]
    assert m['killed'] and m['kill_path']=='blade' and p['group']['index']==1


def test_refresh_ticks_old_snapshot_once_and_keeps_new_duration(monkeypatch):
    p,item,m=setup(monkeypatch)
    act(p,'skill:'+item['id'])
    p['group']['cooldowns'][item['id']]=0
    act(p,'skill:'+item['id'])
    assert m['hp']==792 #100 +100 +one pre-existing8, no new tick
    assert len(m['effects'])==1 and m['effects'][0]['remaining']==3


@pytest.mark.parametrize('family,trait',[('viper','venomproof'),('ember','fireproof'),('briar','bloodless'),('ramguard','steadfast')])
def test_immunity_does_not_become_minimum_one_effect(monkeypatch,family,trait):
    p,item,m=setup(monkeypatch,family);m['traits']=[trait]
    act(p,'skill:'+item['id'])
    assert m['hp']==900 and not m['effects'] and m['gap']==0
    assert any(e['kind']=='immune' for e in p['group']['events'])


def test_fire_impact_and_later_magic_tick_have_separate_resistance(monkeypatch):
    p,item,m=setup(monkeypatch,'hawkeye',1)
    m.update(gap=3,power=.45,magic=1.5)
    p['quiver']['Common']['fire']=2
    act(p,'load_arrow:'+item['id']+':fire')
    act(p,'strike:'+item['id'])
    assert m['hp']==960 and p['quiver']['Common']['fire']==1
    assert [(e['channel'],e['damage']) for e in p['group']['events'] if e['kind']=='resist']==[('Power',40)]
    act(p,'guard');assert m['hp']==944
    assert not [e for e in p['group']['events'] if e['kind']=='resist']


def test_runestring_arcane_bonus_does_not_remove_air_magic_resistance(monkeypatch):
    p,item,m=setup(monkeypatch,'runestring',1)
    p['quiver']['Common']['arcane']=2;m.update(gap=3,air=True,magic=.3)
    act(p,'load_arrow:'+item['id']+':arcane');act(p,'strike:'+item['id'])
    assert m['hp']==962 #125 ×.3 rounds38
    hit=next(e for e in p['group']['events'] if e['kind']=='resist')
    assert hit['channel']=='Magic' and hit['damage']==38


def test_free_arrow_selection_and_invalid_shot_do_not_tick_or_charge(monkeypatch):
    p,item,m=setup(monkeypatch,'hawkeye',1)
    p['quiver']['Common']['fire']=2
    before=deepcopy(p['group']);energy=p['energy_val'];rng=p['rng_counter']
    act(p,'load_arrow:'+item['id']+':fire')
    assert p['group']==before and p['energy_val']==energy and p['rng_counter']==rng
    p['quiver']['Common']['fire']=0
    before=deepcopy(p)
    assert core.apply_choice(p,'strike:'+item['id']).refusal
    for k in ('group','collection','quiver','energy_val','rng_counter'):assert p[k]==before[k]
    assert not p['group']['committed']


def test_accepted_miss_uses_one_arrow_and_first_enemy_energy(monkeypatch):
    p,item,m=setup(monkeypatch,'hawkeye',1);p['training']['bow']=0
    monkeypatch.setattr(state,'rng_int',lambda p,lo,hi:lo)
    before=quiver.count(p,'Common','ordinary');energy=state.energy_now(p);dur=item['durability']
    act(p,'strike:'+item['id'])
    assert m['hp']==1000 and quiver.count(p,'Common','ordinary')==before-1
    assert state.energy_now(p)==energy-1 and item['durability']==dur-1


def test_later_enemy_keeps_its_own_arrival_and_no_start_charge(monkeypatch):
    p,item,m=setup(monkeypatch,'hawkeye',1);m['hp']=1
    p['group']['members'][1]['gap']=1
    act(p,'strike:'+item['id'])
    assert groups.current(p)['gap']==1 and not groups.current(p)['started']
    assert p['group']['energy']==1


def test_old_pending_offer_keeps_arrowless_resolver(monkeypatch):
    p,item,m=setup(monkeypatch,'hawkeye',1);p['group'].pop('combat_revision')
    p['quiver']['Common']['ordinary']=0;m['hp']=1
    act(p,'strike:'+item['id'])
    assert m['killed'] and quiver.count(p,'Common','ordinary')==0
    assert groups.current(p)['gap']==3


def test_final_mutual_riposte_death_keeps_xp_forfeits_haul(monkeypatch):
    p,item,m=setup(monkeypatch,'breach');p['mastery']={'blade':True}
    g=p['group'];g['index']=1;m=groups.current(p);m.update(hp=1,atk=100,gap=0)
    p['gear']['shield']=max((g for g in economy.FORGE.values() if g.slot=='shield'),key=lambda g:g.bonus).slug
    p['durability']['shield']=1000;p['hp']=1;gold=p['gold']
    xp=m['rewards']['xp']
    act(p,'guard')
    assert p['group'] is None and not p['group_result']['won']
    assert p['group_result']['xp']==xp and state.xp_total(p)==xp
    assert p['gold']==gold and p['hp']==1 #Level1 daily rescue; no haul.


def test_quiver_purchase_grade_cap_practice_and_enrollment_once(monkeypatch):
    p,item,m=setup(monkeypatch);act(p,'flee');act(p,'forge_collection');act(p,'quiver_shop')
    before=p['gold'];act(p,'arrow_buy:Common:fire')
    assert p['gold']==before-15 and quiver.count(p,'Common','fire')==20
    assert quiver.used(p)==120
    core.current_scene(p);collection.sync(p);assert quiver.used(p)==120
    p['quiver']['Common']['ordinary']=0;energy=state.energy_now(p);gold=p['gold']
    act(p,'arrow_practice');assert quiver.count(p,'Common','ordinary')==20
    assert state.energy_now(p)==energy-1 and p['gold']==gold
    assert core.apply_choice(p,'arrow_practice').refusal
    p['unlocked_floor']=25;gold=p['gold']
    assert core.apply_choice(p,'arrow_buy:Rare:fire').refusal and p['gold']==gold
    p['quiver']['Common']['ordinary']=380
    assert core.apply_choice(p,'arrow_buy:Common:arcane').refusal


def test_quiver_sheet_and_drawer_explain_real_owned_arrows_without_mutation(monkeypatch):
    from plugin_linear_ascent import collection_view
    p,item,m=setup(monkeypatch,'hawkeye',1)
    before=deepcopy(p)
    data=collection.payload(p);q=data['quiver']
    assert q['finite'] and q['miss_consumes_arrow'] and q['arrows_per_accepted_shot']==1
    assert len(q['types'])==6 and all(len(t['offers'])==4 for t in q['types'])
    assert q['bows'][0]['selected']=='ordinary' and q['bows'][0]['remaining']==100
    assert q['choices']=={}
    fire=next(t for t in q['types'] if t['id']=='fire')
    assert fire['offers'][0]==dict(grade='Common',arrow='fire',floor=1,count=20,gold=15,owned=0,unlocked=True)
    html=collection_view.render(data,lambda _:None,lambda _: '<i></i>')
    assert 'Arrows · 100 / 400' in html and 'including a miss' in html
    for arrow in q['types']:assert arrow['name'] in html
    assert p==before
    p['quiver']['Common']['fire']=2;quiver.select(p,item['id'],'fire')
    assert quiver.payload(p)['bows'][0]['selected']=='fire'
    assert quiver.payload(p)['bows'][0]['remaining']==2


def test_broken_upgrade_stays_broken_and_full_attack_is_inspectable(monkeypatch):
    p,item,m=setup(monkeypatch);act(p,'flee');act(p,'forge_collection')
    item['durability']=0;q=collection.upgrade_quote(item);p['materials'].update(q['materials'])
    act(p,'upgrade:'+item['id']);assert item['level']==1 and item['durability']==0
    assert battle_rules.contribution(item)==0
    act(p,'mend:'+item['id']);assert battle_rules.contribution(item)==collection.stats(item)['attack']
    item['durability']=round(item['maximum']*.1)
    assert battle_rules.contribution(item)<collection.stats(item)['attack']*.3


def test_all_eight_sites_have_local_real_weighted_enemies_and_atomic_tools(monkeypatch):
    from plugin_linear_ascent.engine import gathering
    assert len(gathering.SITES)==8
    assert sorted(site['floor'] for site in gathering.SITES.values())==[3,3,18,25,45,55,70,80]
    original_rng=state.rng_int
    for key,site in gathering.SITES.items():
        monkeypatch.setattr(state,'rng_int',original_rng)
        p,item,m=setup(monkeypatch);act(p,'flee')
        p.update(floor=site['floor'],location='gate_town',gold=10**15)
        act(p,'gather_site:'+key);before=p['gold'];pack=core.pack_used(p)
        act(p,'gather_tool');assert p['gold']==before-site['price'] and core.pack_used(p)==pack
        act(p,'gather_begin');assert p['expedition']['site_rules']==site
        # Force a successful collection and no ambush. Combat itself is tested separately.
        rolls=iter([1,100]);monkeypatch.setattr(state,'rng_int',lambda *a:next(rolls))
        act(p,'gather_step');assert p['expedition']['haul'][site['material']]==site['yield_amount']
        assert p['materials'].get(site['material'],0)==0
        act(p,'gather_extract');assert p['materials'][site['material']]==site['yield_amount']
        assert not p['expedition']
        roster=site.get('roster',[])
        if roster:
            choices=[]
            for row in roster:
                assert abs(row['floor']-site['floor'])<=2
                profile=bestiary.profile(row['floor'],row['id'])
                favored=profile['air'] if site['preferred']=='bow' else not profile['air'] and profile['affinity']=='Magic'
                choices.append((row['weight'],favored))
            assert sum(w for w,fit in choices if fit)>sum(w for w,fit in choices if not fit)>0


def test_mastery_and_condition_use_current_shared_attack_and_focus(monkeypatch):
    # No forced attack stub: this test checks earned studies and current condition.
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    p=state.new_player('mastery-calculation');p.update(stage='playing',race='human',name='Mastery')
    core.current_scene(p);item=p['collection'][p['deck'][2]]
    base=battle_rules.attack(p,item)
    p['mastery']={'blade':True,'bow':True,'staff':True}
    assert battle_rules.attack(p,item)==pytest.approx(base*1.3)
    assert battle_rules.affinity(dict(air=False,magic=.45),'Magic',focus=True)==.75
    assert battle_rules.affinity(dict(air=True,magic=.35),'Magic',focus=True)==.35
    assert battle_rules.affinity(dict(air=True,magic=.3),'Magic',focus=True)==.3
    item['durability']=1
    assert 0<battle_rules.contribution(item)<collection.stats(item)['attack']
    assert battle_rules.contribution(item)>=round(collection.stats(item)['attack']*.5)


def test_stun_recovery_prevents_two_weapons_from_permanent_lock(monkeypatch):
    p,item,m=setup(monkeypatch,'thunder')
    second=collection.mint(p,'stormbell');collection.set_slot(p,2,second['id'])
    act(p,'skill:'+item['id'])
    assert m['stun_recovery']==2
    hp=p['hp'];act(p,'skill:'+second['id'])
    assert p['hp']<hp and m['stun_recovery']==1
    assert any(e['kind']=='immune' for e in p['group']['events'])


def test_only_one_strongest_bleed_wound_can_be_refreshed(monkeypatch):
    p,item,m=setup(monkeypatch,'briar')
    other=collection.mint(p,'briar');collection.set_slot(p,1,other['id'])
    act(p,'skill:'+item['id'])
    monkeypatch.setattr(battle_rules,'attack',lambda p,item:50)
    act(p,'skill:'+other['id'])
    assert len(m['effects'])==1 and m['effects'][0]['amount']==10
    assert m['effects'][0]['source']['id']==item['id']
    assert m['effects'][0]['remaining']==2
    assert m['hp']==840 #100 +50 +old10; no extra fresh10
