from copy import deepcopy
from unittest.mock import patch
import kalista_engine as e

d=e.migrate(deepcopy(e.DEFAULT));e.recalc(d)
t=dict(name='Цель',hp=10000,hp_max=10000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[])
soul=next(s for s in d['spells'] if s['name']=='Пламя души')
assert e.kalista_dot_damage(d,'burn')==28 and e.kalista_dot_damage(d,'curse')==19
with patch.object(e.random,'random',return_value=0):e.roll_spell_effects(d,soul,t)
assert [x['value'] for x in t['effects'] if x['kind']=='dot']==[28,19]
e.tick_periodic(t)
d['spell_power']=0
with patch.object(e.random,'random',return_value=0):e.roll_spell_effects(d,soul,t)
assert [x['value'] for x in t['effects'] if x['kind']=='dot']==[28,19]
assert all(x['duration']==3 for x in t['effects'] if x['kind']=='dot')
d['spell_power']=1
with patch.object(e.random,'random',return_value=0):e.roll_spell_effects(d,soul,t)
assert [x['value'] for x in t['effects'] if x['kind']=='dot']==[35,24]
d['spell_power']=10;hp=t['hp'];e.tick_periodic(t);assert hp-t['hp']==59
e.tick_periodic(t);assert t['fear_immunity_turns']==1
with patch.object(e.random,'random',return_value=0):messages=e.roll_spell_effects(d,soul,t)
assert not any(x['kind']=='fear' for x in t['effects']) and any('иммунитет' in x for x in messages)
assert e.add_effect(t,dict(kind='fear',name='Другой страх',value=0,duration=2)) is None
e.tick_periodic(t);assert t['fear_immunity_turns']==0
with patch.object(e.random,'random',return_value=0):e.roll_spell_effects(d,soul,t)
assert any(x['kind']=='fear' for x in t['effects'])
assert e.migrate(d)['schema_version']>=20
print('Passed: scaling, snapshot, stronger refresh, growth, fixed ticks, fear immunity and expiry.')
