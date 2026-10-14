from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from unittest.mock import patch
import json
import kalista_engine as e
import kalista_interactive_map as board
from streamlit.testing.v1 import AppTest

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d['distance_mode']='meters';e.recalc(d)
 d['enemies']=[dict(id=i,name='Враг '+str(i),hp=2000,hp_max=2000,armor=0,resists={x:0 for x in e.ELEMENTS},initiative=1,effects=[],attack_damage=30,attack_type='Физический') for i in (1,2)]
 d=e.migrate(d);d['positions']={'player':[0.,0.],'ally':[0.,5.],'enemy:1':[40.,0.],'enemy:2':[45.,0.]}
 s=next(s for s in d['spells'] if s['name']=='Огненный шар');s.update(range_m=80.,area_radius_m=10.)
 return d,s
with TemporaryDirectory() as folder:
 root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 for role in ('gm','player'):
  d,s=fresh();save.write_text(json.dumps(d,ensure_ascii=False));app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.run();page='page' if role=='gm' else 'player_section';app.radio(key=page).set_value('Бой').run();assert not app.exception
  key='turn_target_player' if role=='gm' else 'player_battle_target'
  def click_target(**kwargs):return {'epoch':kwargs['epoch'],'target':'enemy:2'}
  with patch.object(board,'_component',side_effect=click_target):app.run()
  assert not app.exception and app.selectbox(key=key).value=='enemy:2'
  assert json.loads(save.read_text())==d,'Selecting target mutated save'
  if role=='gm':
   with patch.object(board,'_component',side_effect=lambda **k:{'epoch':k['epoch'],'ability':s['id']}):app.run()
   assert not app.exception and app.selectbox(key='battle_spell').value==s['id']
   calls=[]
   def area(**kwargs):calls.append(kwargs);return {'epoch':kwargs['epoch'],'point':[40.,0.]}
   with patch.object(board,'_component',side_effect=area):app.selectbox(key='battle_spell').set_value(s['id']).run()
   assert not app.exception
   assert len(calls)==1 and calls[0]['mode']=='area' and calls[0]['radius']==10,'Area rendered a second map'
   assert any('Враг 1' in x.value and 'Враг 2' in x.value for x in app.caption)
   assert json.loads(save.read_text())==d
  else:
   with patch.object(board,'_component',side_effect=lambda **k:{'epoch':k['epoch'],'point':[20.,5.]}):
    app.radio(key='board_mode_ally').set_value('Перемещение').run();assert not app.exception
    app.button(key='map_apply_ally').click().run();assert not app.exception
   actual=json.loads(save.read_text());assert actual['positions']==d['positions']
   assert actual['player_requests'][-1]['destination']==[20.,5.]
print('Passed: map clicks select targets in both roles; no viewing writes; one shared area map; player movement only proposes and retains authoritative positions.')
# Wrong-turn availability is explained before proposal submission.
with TemporaryDirectory() as folder:
 root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json';d,s=fresh();e.start_combat(d);save.write_text(json.dumps(d,ensure_ascii=False))
 app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='player';app.run();app.radio(key='player_section').set_value('Бой').run()
 assert not app.exception
 assert any('Сейчас ход другого участника' in x.value for x in app.caption)
 assert all(x.disabled for x in app.button if x.key and x.key.startswith('perform_ally_'))
print('Passed: wrong-turn proposals disabled with clear explanation.')
