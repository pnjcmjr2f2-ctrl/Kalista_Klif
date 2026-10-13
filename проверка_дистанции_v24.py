from copy import deepcopy
from unittest.mock import patch
import kalista_engine as e
from kalista_player_model import recalc_player

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d)
 d['enemies']=[dict(id=i,name='Враг',hp=5000,hp_max=5000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=100,attack_type='Физический') for i in (1,2)]
 d=e.migrate(d);d['mana_current']=d['mana_max'];e.start_combat(d);return d

d=fresh();a=d['ally'];attack=next(x for x in a['actions'] if x['kind']=='damage');attack['reach']='Дальняя';attack['hits']=2;attack['effect_kind']='weakness';attack['effect_value']=35;attack['duration']=2
hp=d['enemies'][0]['hp']
with patch.object(e.random,'random',return_value=.1):messages=e.perform_action(d,'ally',attack['id'],['enemy:1'])
assert d['enemies'][0]['hp']==hp and not d['enemies'][0]['effects'] and len(d['turn_actions'])==1
assert sum('промах' in m for m in messages)==2
assert e.preview_action(d,'ally',attack,'enemy:1')['miss']==.5
# Each hit is independent; dodge follows hit check.
d['turn_actions']=[]
with patch.object(e.random,'random',side_effect=[.1,.9,.9]):e.perform_action(d,'ally',attack['id'],['enemy:1'])
assert d['enemies'][0]['hp']==hp-302
attack['reach']='Любая';assert e.ranged_miss_chance(d,'ally',attack,'enemy:1')==0
move=next(x for x in a['actions'] if x.get('rule')=='move_far');d['turn_actions']=[]
e.perform_action(d,'ally',move['id'],['enemy:1'])
assert all(e.distance_between(d,'ally',t)=='Дальняя' for t,_ in e.participants(d) if t!='ally')
assert e.ranged_miss_chance(d,'ally',dict(reach='Дальняя'),'enemy:1')==0
# Friendly proximity does not cause a penalty.
d['distances']['ally|player']='Ближняя';assert e.ranged_miss_chance(d,'ally',dict(reach='Дальняя'),'enemy:1')==0
# A missed soul flame costs mana/action and applies no four statuses or counter.
d=fresh();d['distances']['enemy:1|player']='Ближняя';spell=next(x for x in d['spells'] if x['name']=='Пламя души');hp=d['enemies'][0]['hp'];mp=d['mana_current']
with patch.object(e.random,'random',return_value=.1):e.cast_spell(d,spell,d['enemies'][0])
assert d['enemies'][0]['hp']==hp and not d['enemies'][0]['effects'] and d['mana_current']==mp-spell['mana'] and len(d['turn_actions'])==1
# Melee spells reject distant targets before cost; Any bypasses ranged miss.
d=fresh();spell=d['spells'][0];spell['reach']='Ближняя';before=deepcopy(d)
try:e.cast_spell(d,spell,d['enemies'][0])
except ValueError:pass
else:raise AssertionError('Melee spell hit a distant target')
assert d==before
spell['reach']='Любая';assert e.ranged_miss_chance(d,'player',spell,'enemy:1')==0
# Base armor and worn gear add independently.
a=d['ally'];assert a['armor']==185
p=a['sheet_profile'];item=next(x for x in p['equipment'] if x['name']=='Кираса Ниргхала');item['bonuses']['Броня']=20;recalc_player(a);assert a['armor']==205
item['equipped']=False;recalc_player(a);assert a['armor']==185
print('Passed: per-hit miss, no statuses on miss, costs, friendly exclusion, retreat all, melee spell atomicity, any range, additive armor.')
