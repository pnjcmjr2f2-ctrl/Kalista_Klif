from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import math,json
import kalista_engine as e
from kalista_shapes import in_cone,shape_targets,check_area_aim
from kalista_area import cast_area_spell
from streamlit.testing.v1 import AppTest

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d['distance_mode']='meters';e.recalc(d);d['mana_current']=d['mana_max'];d['hp_current']=d['hp_max']
 d['enemies']=[dict(id=i,name='Цель '+str(i),hp=2000,hp_max=2000,armor=0,resists={x:0 for x in e.ELEMENTS},initiative=1,effects=[],attack_damage=10,attack_type='Физический') for i in range(1,6)]
 d=e.migrate(d);d['positions']={'player':[0.,0.],'ally':[6.,0.],'enemy:1':[10.,0.],'enemy:2':[10*math.cos(math.pi/6),5.],'enemy:3':[10.001,0.],'enemy:4':[8.,8.],'enemy:5':[-1.,0.]}
 s=next(x for x in d['spells'] if x['name']=='Адское дыхание');s.update(area_shape='cone',cone_length_m=10.,cone_angle_deg=60.,range_m=1.,area_radius_m=999.,reach='Любая')
 return d,s

d,s=fresh();assert shape_targets(d,'player',s,[1,0])==['ally','enemy:1','enemy:2']
assert shape_targets(d,'player',s,[100000,0])==shape_targets(d,'player',s,[1,0])
assert 'player' not in shape_targets(d,'player',s,[1,0]);assert in_cone([5,-20],[5,0],[5,-10],10,60)
assert not in_cone([0,0],[1,0],[10*math.cos(math.pi/6+.0001),10*math.sin(math.pi/6+.0001)],10,60)
for point in ([0,0],[float('nan'),0]):
 before=deepcopy(d)
 try:cast_area_spell(d,s,point)
 except ValueError:pass
 else:raise AssertionError('Bad direction accepted')
 assert d==before
before=deepcopy(d);du,so=e.spell_bonuses(d,s);raw=e.spell_raw(s['base'],d['spell_power'],du,so);expected={t:e.spell_damage_preview(d,s,e.participant(d,t),raw)['hp_loss'] for t in shape_targets(d,'player',s,[1,0])}
with patch.object(e.random,'random',return_value=.99):cast_area_spell(d,s,[100000,0])
assert d['hp_current']==before['hp_current']
assert d['mana_current']==before['mana_current']-s['mana'] and next(x for x in d['spells'] if x['id']==s['id'])['cd_left']==s['cd_max']
assert sum(x['counts'] for x in d['turn_actions'])==1
for token,loss in expected.items():assert e.participant(before,token)[e.hp_fields(e.participant(before,token))[0]]-e.participant(d,token)[e.hp_fields(e.participant(d,token))[0]]==loss
for i in (3,4,5):assert d['enemies'][i-1]['hp']==2000
# The generic participant pipeline also takes the complete authoritative cone target set.
d,s=fresh();a=e.action_template('Конус меча',amount=100,damage_type='Физический',reach='Любая',hits=2);a.update(area_shape='cone',cone_length_m=10.,cone_angle_deg=60.,cooldown=2);d['ally']['actions'].append(a);d=e.migrate(d);victims=shape_targets(d,'ally',a,[1000,0]);before=deepcopy(d)
try:e.perform_action(d,'ally',a['id'],victims[:-1],area_center=[1000,0])
except ValueError:pass
else:raise AssertionError('Forged area target set accepted')
assert d==before
with patch.object(e.random,'random',return_value=.99):e.perform_action(d,'ally',a['id'],victims,area_center=[1000,0])
assert sum(x['counts'] for x in d['turn_actions'])==1
for token in victims:assert e.participant(d,token)['hp']==e.participant(before,token)['hp']-200
# UI: cone fields are visible only in developer mode; incomplete root form does not poison the save.
with TemporaryDirectory() as folder:
 root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 for role in ('gm','player'):
  for editing in (False,True):
   d,s=fresh();save.write_text(json.dumps(d,ensure_ascii=False));app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.session_state['_edit_mode']=editing;app.run()
   app.radio(key='page' if role=='gm' else 'player_section').set_value('Заклинания' if role=='gm' else 'Заклинания и способности').run();assert not app.exception
   assert any(x.label=='Форма области' for x in app.selectbox)==editing
   app.radio(key='page' if role=='gm' else 'player_section').set_value('Бой').run();assert not app.exception
   if role=='gm':
    app.selectbox(key='battle_spell').set_value(s['id']).run();assert not app.exception
    assert any('Конус' in x.value and '10' in x.value for x in app.caption)
   assert json.loads(save.read_text())==d,'Viewing cone changed save'
print('Passed: radial/angular boundaries, rotation, aim distance independence, caster excluded, allies hit, independent full damage, one mana/action/CD, invalid directions and forged targets atomic, both pipelines and roles, developer-only settings.')

with TemporaryDirectory() as folder:
 root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json';d,s=fresh();save.write_text(json.dumps(d,ensure_ascii=False))
 app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['_edit_mode']=True;app.run();app.radio(key='page').set_value('Заклинания').run()
 other=next(x for x in d['spells'] if x['area_shape']=='circle');prefix='spell_shape_'+str(other['id'])
 app.selectbox(key=prefix+'_shape').set_value('cone')
 button=app.button(key=prefix+'_save')
 button.click().run();assert not app.exception and any('больше 0' in x.value for x in app.error);assert json.loads(save.read_text())==d
 app.selectbox(key=prefix+'_shape').set_value('cone');app.number_input(key=prefix+'_length').set_value(20.);button=app.button(key=prefix+'_save');button.click().run();assert not app.exception
 actual=json.loads(save.read_text());changed=next(x for x in actual['spells'] if x['id']==other['id']);assert changed['area_shape']=='cone' and changed['cone_length_m']==20
print('Passed: incomplete cone form stays editable and never writes invalid shape; valid form persists.')
