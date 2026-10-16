from copy import deepcopy
from unittest.mock import patch
import kalista_engine as e

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d)
 foe=dict(id=1,name='Атакующий',level=21,hp=10000,hp_max=10000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=20,attack_type='Физический')
 d['enemies']=[foe];d=e.migrate(d);d['distance_mode']='meters';d['positions']['ally']=[0.,0.];d['positions']['enemy:1']=[1.,0.];d['positions']['player']=[-1.,0.];return d

def attack(d,**kw):
 a=e.action_template('Проверочная атака',amount=20,**kw);d['enemies'][0]['actions']=[a];e.validate_action_state(d);return a
for dtype in ('Физический','Огонь'):
 d=fresh();e.add_effect(d['ally'],dict(kind='shield',name='Щит',value=10000,duration=2));a=attack(d,damage_type=dtype,reach='Ближняя');hp=d['ally']['hp']
 with patch.object(e.random,'random',return_value=.1):messages=e.perform_action(d,'enemy:1',a['id'],['ally'])
 assert d['ally']['hp']==hp and any(m.startswith('Контратака:') for m in messages)
# Dodge is an attack attempt, not a reason to skip the reaction.
d=fresh();d['ally']['sheet_profile']['stats']['Ловкость']=100;a=attack(d)
with patch.object(e.random,'random',side_effect=[0.,0.,.99]):messages=e.perform_action(d,'enemy:1',a['id'],['ally'])
assert any('уклонился' in m for m in messages) and any(m.startswith('Контратака:') for m in messages)
# Ranged magic cast at close range misses and still triggers the reaction.
d=fresh();d['combat_active']=True;a=attack(d,damage_type='Огонь',reach='Дальняя')
with patch.object(e.random,'random',side_effect=[.1,.1,.99]):messages=e.perform_action(d,'enemy:1',a['id'],['ally'])
assert any('промах' in m for m in messages) and any(m.startswith('Контратака:') for m in messages)
# Two attacks blocked by a shield give two independent attempts.
d=fresh();a=attack(d,hits=2);e.add_effect(d['ally'],dict(kind='shield',name='Щит',value=10000,duration=2))
with patch.object(e.random,'random',return_value=.1):messages=e.perform_action(d,'enemy:1',a['id'],['ally'])
assert sum(m.startswith('Контратака:') for m in messages)==2
# Far attacks and simulation cannot provoke counters or consume RNG.
d=fresh();d['positions']['enemy:1']=[6.,0.]
with patch.object(e.random,'random',side_effect=AssertionError('Invalid roll')):assert e.counterattack(d,'enemy:1','ally',{'hp_loss':0})==[]
d=fresh();a=attack(d)
with patch.object(e.random,'random',side_effect=AssertionError('Preview rolled')):e.perform_action(d,'enemy:1',a['id'],['ally'],simulation=True)
# Ordinary Kalista spell misses in close range, too.
d=fresh();d['combat_active']=True;spell=d['spells'][0];spell['mana']=0
with patch.object(e.random,'random',side_effect=[.1,.1,.99]):messages=e.cast_spell(d,spell,d['ally'])
assert any(m.startswith('Контратака:') for m in messages)
print('65% counters on close physical/magic attempts: shield, dodge, miss, multi-hit; no far/preview triggers: OK')
