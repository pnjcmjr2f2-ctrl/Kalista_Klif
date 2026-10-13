import sys
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import kalista_engine as e
d=e.migrate(deepcopy(e.DEFAULT));e.recalc(d)
t=dict(name='Цель',hp=1000,hp_max=1000,armor=99999,resists={x:0 for x in e.ELEMENTS},effects=[])
t['resists']['Огонь']=95
assert e.damage_preview(t,100,'Огонь')['incoming']==5
assert e.damage_preview(t,100,'Физический')['incoming']==e.real_dmg(100,99999)
e.add_effect(t,dict(name='Бонус сопротивления',kind='resist',value=100,element='Огонь'))
assert e.damage_preview(t,100,'Огонь')['incoming']==5
t['effects']=[]
soul=next(s for s in d['spells'] if s['name']=='Пламя души')
t['resists']['Огонь']=80;t['resists']['Тьма']=20
assert e.spell_damage_preview(d,soul,t,100)['incoming']==50
shadow=next(s for s in d['spells'] if s['name']=='Теневой укол')
assert shadow['cd_max']==2
assert e.spell_damage_preview(d,shadow,t,100)['incoming']==100
e.add_effect(t,dict(name='Щит',kind='shield',value=40))
assert e.spell_damage_preview(d,shadow,t,100)['hp_loss']==60
assert e.spell_damage_apply(d,shadow,t,100)['hp_loss']==60 and t['hp']==940
# Ash only affects the fire half; racial reduction only affects the dark half.
t['resists']['Огонь']=80;t['resists']['Тьма']=20;d['pepel_empower']=True
assert e.spell_damage_preview(d,soul,t,100)['incoming']==62
t['passives']={'dark_resist':{}}
assert e.spell_damage_preview(d,soul,t,100)['incoming']==58
# Gear and manual corrections cannot exceed 95%; Shadow is included before the same cap.
d['resist_adjustments']['Огонь']=1000;e.recalc(d);assert d['resists']['Огонь']==95
d['ten_resist_boost']=2;assert e.damage_preview(d,100,'Огонь')['incoming']==5
print('Passed: percent resistance, total 95% cap, armor unchanged, 50/50 split, independent fire boost/dark racial reduction, pure damage, shields and cooldown migration.')

from unittest.mock import patch
assert e.shadow_shield_amount(d)==469
# Four independent rolls, exact boundaries and refresh without stacking.
d['pepel_empower']=False;t['hp']=1000;t['effects']=[];t.pop('passives',None)
with patch.object(e.random,'random',side_effect=[0,0,0,0]):e.roll_spell_effects(d,soul,t)
assert {x['name']:x['duration'] for x in t['effects']}=={'Горение':3,'Проклятие':3,'Слабость':2,'Страх':2}
with patch.object(e.random,'random',side_effect=[0,0,0,0]):e.roll_spell_effects(d,soul,t)
assert len(t['effects'])==4
assert e.outgoing_damage(t,100,'Физический')==65 and e.outgoing_damage(t,100,'Огонь')==100
before={x['id']:x['duration'] for x in t['effects']};e.tick_round_effects(t,100)
assert before=={x['id']:x['duration'] for x in t['effects']}
e.tick_periodic(t);assert {x['name']:x['duration'] for x in t['effects']}=={'Горение':2,'Проклятие':2,'Слабость':1,'Страх':1}
e.tick_periodic(t);assert {x['name'] for x in t['effects']}=={'Горение','Проклятие'}
t['effects']=[];t['control_resist']=.5
with patch.object(e.random,'random',side_effect=[.5,.5,.35,.25]):e.roll_spell_effects(d,soul,t)
assert t['effects']==[]
with patch.object(e.random,'random',side_effect=[.99,.99,.99,.249]):e.roll_spell_effects(d,soul,t)
assert [x['name'] for x in t['effects']]==['Страх']
# Fear skips exactly two target turns and does not stop queue progression.
b=e.migrate(deepcopy(e.DEFAULT));e.recalc(b);b['enemies']=[dict(id=1,name='Враг',hp=1000,hp_max=1000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=100,attack_type='Физический')];b['next_enemy_id']=2
foe=b['enemies'][0];e.add_effect(foe,dict(kind='fear',name='Страх',value=0,duration=2))
e.start_combat(b);messages=[]
while b['round']<3:messages+=e.advance_turn(b)
assert sum('пропускает ход' in x for x in messages)==2 and not any(x['kind']=='fear' for x in foe['effects'])
# Weakness is applied after extra dice and before armor for both preview and execution.
b['ally']=e.imported_friend();source=b['ally'];source['actions']=[e.action_template('Удар',amount=100)]
e.add_effect(source,dict(kind='weakness',name='Слабость',value=35,duration=2))
a=source['actions'][0];assert e.preview_action(b,'ally',a,'enemy:1')['hp_min']==65
hp=foe['hp'];e.perform_action(b,'ally',a['id'],['enemy:1']);assert hp-b['enemies'][0]['hp']==65
# Dynamic shield and cast resources/cooldowns persist through validation.
b['mana_current']=b['mana_max'];shield=next(x for x in b['spells'] if x['name']=='Покров тьмы');e.cast_spell(b,shield,b)
assert next(x for x in b['effects'] if x['kind']=='shield')['value']==469
e.migrate(b)
print('Passed: dynamic shield 469, independent status probabilities, refresh/no stacking, personal-turn expiry, control resistance, two feared turn skips, weakness in preview/execution and validated casts.')
