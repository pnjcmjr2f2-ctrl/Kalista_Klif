from copy import deepcopy
from unittest.mock import patch
import kalista_engine as e

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d);d['mana_current']=d['mana_max']
 d['enemies']=[dict(id=1,name='Цель',level=21,hp=5000,hp_max=5000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=10,attack_type='Физический')];return e.migrate(d)
d=fresh();a=next(x for x in d['ally']['actions'] if x['name']=='Скорострел')
with patch.object(e.random,'random',side_effect=[.99,.01,.99,.99]):messages=e.perform_action(d,'ally',a['id'],['enemy:1'])
assert d['enemies'][0]['hp']==5000-round(655*.7)-round(302*.7) and sum('КРИТ' in m for m in messages)==1
before=deepcopy(d)
try:e.perform_action(d,'ally',a['id'],['enemy:1'],critical=True)
except ValueError:pass
else:raise AssertionError('Forced weapon crit accepted')
assert before==d
# Proposal validation/preview never rolls; execution determines critical hit.
with patch.object(e.random,'random',side_effect=AssertionError('Preview rolled')):e.perform_action(deepcopy(d),'ally',a['id'],['enemy:1'],simulation=True)
d=fresh();s=d['spells'][0];s.update(base=100,mana=0);d['spell_power']=0
with patch.object(e.random,'random',side_effect=[.01,.99]):messages=e.cast_spell(d,s,d['enemies'][0])
assert d['enemies'][0]['hp']==4850 and any('КРИТ' in m for m in messages)
d=fresh();s=d['spells'][0];before=deepcopy(d)
try:e.cast_spell(d,s,d['enemies'][0],crit=True)
except ValueError:pass
else:raise AssertionError('Forced spell crit accepted')
assert before==d
# Failed ranged hit never triggers a crit roll or any status.
d['combat_active']=True;d['distances']={'enemy:1|player':'Ближняя'}
with patch.object(e.random,'random',side_effect=[.1]):e.cast_spell(d,s,d['enemies'][0])
assert d['enemies'][0]['hp']==5000 and not d['enemies'][0]['effects']
print('Passed: automatic per-hit sword critical, automatic spell critical, rejected forced flags, RNG-free proposal validation and no crit after miss.')
