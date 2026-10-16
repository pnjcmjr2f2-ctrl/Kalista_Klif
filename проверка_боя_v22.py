from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import kalista_engine as e

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d)
 d['enemies']=[dict(id=1,name='Воин',hp=5000,hp_max=5000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=100,attack_type='Физический')];d['next_enemy_id']=2
 d=e.migrate(d);e.start_combat(d);d['current_turn']=next(i for i,x in enumerate(d['turn_order']) if x['kind']=='ally');e.begin_actor_turn(d)
 return d

def ability(d,name):return next(a for a in d['ally']['actions'] if a['name']==name)

d=fresh();names={a['name'] for a in d['ally']['actions']}
assert not {'Когти','Кислотные брызги','Газовое облако','Совершенная контратака'}&names
assert e.evasion_chance(d)==.07 and e.evasion_chance(d['ally'])==.175
assert e.evasion_chance(dict(agility=200))==.5
# Eye uses one action, doubles the remaining hit, and cannot be reactivated in this combat.
e.perform_action(d,'ally',ability(d,'Десница Ока')['id'],['ally']);assert d['ally']['eye_used']
hp=d['enemies'][0]['hp'];e.perform_action(d,'ally',ability(d,'Мощный удар')['id'],['enemy:1'],simulation=True);assert hp-d['enemies'][0]['hp']==906
before=deepcopy(d)
try:e.perform_action(d,'ally',ability(d,'Удар оружием')['id'],['enemy:1'])
except ValueError:pass
else:raise AssertionError('Third action accepted')
assert d==before
e.advance_turn(d);assert not d['ally']['eye_damage_boost']
d['turn_actions']=[]
try:e.perform_action(d,'ally',ability(d,'Десница Ока')['id'],['ally'])
except ValueError:pass
else:raise AssertionError('Eye reused')
e.end_combat(d);e.start_combat(d);assert not d['ally']['eye_used']
# Movement is separate from action budget, once per personal turn; distant melee is rejected atomically.
d=fresh();move=ability(d,'Отступление');e.perform_action(d,'ally',move['id'],['enemy:1'])
assert e.distance_between(d,'ally','enemy:1')=='Дальняя' and not d['turn_actions'][-1]['counts']
before=deepcopy(d)
for name in ('Удар оружием','Сближение'):
 try:e.perform_action(d,'ally',ability(d,name)['id'],['enemy:1'])
 except ValueError:pass
 else:raise AssertionError('Distance or movement restriction ignored')
assert d==before
e.begin_actor_turn(d);e.perform_action(d,'ally',ability(d,'Сближение')['id'],['enemy:1']);assert e.distance_between(d,'ally','enemy:1')=='Ближняя'
# Stance applies exactly once, including magical and pure direct damage, and expires on the next personal start.
d=fresh();e.perform_action(d,'ally',ability(d,'Защитная стойка')['id'],['ally']);assert ability(d,'Защитная стойка')['cooldown_left']==1
ally=d['ally'];ally['resists']['Огонь']=0
fire=next(s for s in d['spells'] if s['school']=='Огонь');preview=e.spell_damage_preview(d,fire,ally,100);hp=ally['hp'];answer=e.spell_damage_apply(d,fire,ally,100)
assert preview['incoming']==answer['incoming']==70 and hp-ally['hp']==70
e.begin_actor_turn(d);assert not d['ally']['defensive_stance'] and ability(d,'Защитная стойка')['cooldown_left']==0
# Physical dodge happens before shields and still provokes a counterattack attempt.
d=fresh();foe=d['enemies'][0];attack=next(a for a in foe['actions'] if a['kind']=='damage');hp=d['ally']['hp'];foe_hp=foe['hp'];e.add_effect(d['ally'],dict(kind='shield',name='Щит',value=200))
with patch.object(e.random,'random',return_value=.1):messages=e.perform_action(d,'enemy:1',attack['id'],['ally'])
assert d['ally']['hp']==hp and d['enemies'][0]['hp']==foe_hp-302 and d['ally']['effects'][0]['value']==200 and any('уклонился' in x for x in messages)
# Successful melee HP loss triggers a normal sword counter, no action charge and no recursion.
d=fresh();foe=d['enemies'][0];foe['counterattack_enabled']=True;attack=next(a for a in foe['actions'] if a['kind']=='damage');hp=d['ally']['hp'];foe_hp=foe['hp']
with patch.object(e.random,'random',side_effect=[.99,.1,.99]):messages=e.perform_action(d,'enemy:1',attack['id'],['ally'])
assert hp-d['ally']['hp']==81 and foe_hp-d['enemies'][0]['hp']==302
assert len([x for x in d['turn_actions'] if x['name']=='Контратака'])==1 and not next(x for x in d['turn_actions'] if x['name']=='Контратака')['counts']
# A shield does not prevent the 65% attempt; a failed roll deals no counter damage. DoT never triggers it.
d=fresh();foe=d['enemies'][0];attack=next(a for a in foe['actions'] if a['kind']=='damage');e.add_effect(d['ally'],dict(kind='shield',name='Щит',value=1000))
with patch.object(e.random,'random',return_value=.99):messages=e.perform_action(d,'enemy:1',attack['id'],['ally'])
assert not any('Контратака:' in x for x in messages) and any('контратака не сработала' in x for x in messages)
d['ally']['effects']=[];e.add_effect(d['ally'],dict(kind='dot',name='Горение',value=100,duration=3,element='Огонь'));hp=d['ally']['hp']
with patch.object(e.random,'random',side_effect=AssertionError('DoT should not roll')):e.tick_periodic(d['ally'])
assert d['ally']['hp']<hp
# Migration preserves current battle resources and all known gear bonuses.
old=deepcopy(e.DEFAULT);old['schema_version']=18;old['ally']=e.imported_friend();hp=old['ally']['hp'];attack=old['ally']['sheet_profile']['attack'];n=e.migrate(old);e.recalc(n)
assert n['ally']['hp']==hp and n['ally']['sheet_profile']['attack']==attack
assert {'Нагрудник','Сапоги'} <= {x['slot'] for x in n['ally']['sheet_profile']['equipment'] if x['equipped']}
print('Passed: warrior migration, eye ×2 once/combat, power strike, 2 actions, separate movement/range, stance once/expiry, physical-only dodge, counter 65%/no recursion, shields and DoT, equipment/resource preservation.')
