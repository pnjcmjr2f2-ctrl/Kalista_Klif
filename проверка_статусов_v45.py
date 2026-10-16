from copy import deepcopy
from unittest.mock import patch
import kalista_engine as e
from kalista_statuses import on_hit,movement_limit,blind_chance

def target():return dict(name='Цель',hp=1000,hp_max=1000,armor=10000,resists={},effects=[])
def proc(kind,value=30,duration=2):return dict(hit_effect=dict(kind=kind,chance=100,value=value,duration=duration))
t=target()
with patch('kalista_statuses.random.random',return_value=0):
    on_hit(t,proc('bleed',10,3),200)
    assert t['effects'][0]['value']==20
    on_hit(t,proc('bleed',10,3),100)
    assert len(t['effects'])==1 and t['effects'][0]['value']==20
    t['defensive_stance']=True;e.tick_periodic(t)
    assert t['hp']==986 and t['effects'][0]['duration']==2
    t=target();t['race']='Скелет';on_hit(t,proc('bleed'),100);assert not t['effects']
    t=target();on_hit(t,proc('chill'),100);assert movement_limit(t)==21
    on_hit(t,proc('slow',50),100);assert movement_limit(t)==15
    e.tick_periodic(t);assert movement_limit(t)==15
    e.tick_periodic(t);assert movement_limit(t)==30
    on_hit(t,proc('armor_break',20),100);assert e.effective_defense(t,'Физический')==8000
    on_hit(t,proc('blind',30,1),100);assert blind_chance(t)==.3
    on_hit(t,proc('freeze',0,1),100);assert any(x['kind']=='freeze' for x in t['effects'])
    e.apply_damage(t,10,final=True)
    assert not any(x['kind']=='freeze' for x in t['effects']) and t['fear_immunity_turns']==1
    assert e.add_effect(t,dict(kind='fear',name='Страх',value=0,duration=1)) is None
    on_hit(t,proc('freeze',0,1),100);assert not any(x['kind']=='freeze' for x in t['effects'])
    e.tick_periodic(t);on_hit(t,proc('freeze',0,1),100)
    assert any(x['kind']=='freeze' for x in t['effects'])
    e.tick_periodic(t);assert t['fear_immunity_turns']==1
# Movement enforces the same limit the map displays.
d=e.migrate(deepcopy(e.DEFAULT));t=d['ally'];on_hit(t,proc('slow',50),100)
from kalista_map import move
start=d['positions']['ally']
try:move(d,'ally',destination=[start[0]+16,start[1]])
except ValueError:pass
else:raise AssertionError('Slow movement bypassed')
assert d['positions']['ally']==start
# All elemental spells use their own resistance rather than falling back to Darkness.
for school in e.ELEMENTS:
    t=target();t['resists']={school:50}
    sp=dict(name='Проверка',school=school)
    assert e.spell_damage_preview(d,sp,t,100)['incoming']==50
print('Bleed, strongest refresh, bloodless immunity, slow, armor, blind, freeze, shared immunity and all schools: OK')
