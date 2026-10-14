from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import kalista_engine as e
from kalista_compare import preview_equipment,totals
from kalista_loot import assign_loot,equip_root_reserve
from kalista_player_model import recalc_player
from streamlit.testing.v1 import AppTest

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d);return e.migrate(d)
item=dict(id='loot-staff',name='Проверочный посох',rarity='Легендарный',type='Оружие',qty=1,desc='Для сравнения.',use=None,gear=dict(slot='Оружие 1',root_bonuses=dict(attack=100,int=30,spell_power=15),ally_bonuses={'Атака':100,'Интеллект':30,'Сила заклинаний':15}))
for owner in ('player','ally'):
 d=fresh();before=deepcopy(d);preview=preview_equipment(d,item,owner,loot=True);assert d==before
 assert preview['rows'] and preview['replaces']
 d['loot_batches']=[dict(battle_id='fixture',items=[dict(id='loot-staff',enemy='Враг',item=deepcopy(item),recipient='',discarded=False)])]
 assign_loot(d,'loot-staff',owner)
 if owner=='player':equip_root_reserve(d,'loot-staff:0')
 else:
  p=d['ally']['sheet_profile']
  for x in p['equipment']:
   if x['slot']=='Оружие 1':x['equipped']=x['id']=='loot-staff:0'
  recalc_player(d['ally'])
 after=totals(d,owner)
 assert all(abs(after[label]-value)<1e-8 for label,_,value in preview['rows'])
 # Existing bound items compare at the current owner level, including growth.
 if owner=='player':reserve=next(x for x in d['equipment_reserve'] if x['name']);d['level']+=10;e.recalc(d)
 else:
  reserve=next(x for x in d['ally']['sheet_profile']['equipment'] if not x['equipped'] and x['slot']=='Оружие 1');d['ally']['sheet_profile']['level']+=10;recalc_player(d['ally'])
 unchanged=deepcopy(d);assert preview_equipment(d,reserve,owner)['rows'];assert d==unchanged
# Empty slots, cap-limited resistance, malformed slot and special properties are not guessed.
d=fresh();p=d['ally']['sheet_profile'];ring=dict(id='ring',name='Кольцо',slot='Кольцо 1',rarity='Обычный',bonuses={'Огонь':500},equipped=False,description='')
preview=preview_equipment(d,ring,'ally');assert preview['replaces']==[] and next(x[2] for x in preview['rows'] if x[0]=='Огонь')==95
try:preview_equipment(d,dict(ring,slot='Резерв'),'ally')
except ValueError:pass
else:raise AssertionError('Unknown slot accepted')
with TemporaryDirectory() as directory:
 root=Path(directory);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 for editing in (False,True):
  d=fresh();d['loot_batches']=[dict(battle_id='fixture',items=[dict(id='loot-staff',enemy='Враг',item=deepcopy(item),recipient='',discarded=False)])]
  save.write_text(json.dumps(d,ensure_ascii=False))
  app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['_edit_mode']=editing;app.run();app.radio(key='page').set_value('Бой').run();assert not app.exception
  app.selectbox(key='loot_loot-staff_recipient').set_value('ally').run();assert not app.exception
  assert json.loads(save.read_text())==d,'Preview saved a change'
  if editing:
   app.number_input(key='loot_loot-staff_bonus_Сила заклинаний').set_value(25).run();assert not app.exception
   assert json.loads(save.read_text())==d,'Staged bonus leaked into save'
  app.button(key='loot_loot-staff_assign').click().run();assert not app.exception
  actual=json.loads(save.read_text());record=actual['loot_batches'][0]['items'][0];assert record['recipient']=='ally'
  received=next(x for x in actual['ally']['sheet_profile']['equipment'] if x['id']=='loot-staff:0');assert not received['equipped']
  assert received['bonuses']['Сила заклинаний']==(25 if editing else 15)
  app.run();assert json.loads(save.read_text())==actual,'Rerun duplicated loot'
print('Passed: pure previews match actual equip for both heroes, legendary growth, empty slots, resistance cap, recipient switching, staged edits, reserve assignment, no save writes or duplicate loot.')
