from copy import deepcopy
from random import Random
import kalista_engine as e
from kalista_loot import settings,generate_item,roll_battle_loot,assign_loot,equip_root_reserve
from kalista_player_model import sheet_snapshot,edit_player_sheet

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d)
 d['enemies']=[dict(id=i,name='Враг',level=21,hp=10,hp_max=100,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=10,attack_type='Физический') for i in range(1,6)]
 return e.migrate(d)
d=fresh();config=settings(d);config['chances']={k:100 for k in config['chances']};d['loot_settings']=config;e.start_combat(d)
for x in d['enemies']:x['hp']=0
retry=deepcopy(d);e.end_combat(d);e.end_combat(retry);assert d['loot_batches']==retry['loot_batches']
assert len(d['loot_batches'][0]['items'])==5
before=deepcopy(d['loot_batches']);e.end_combat(d);assert d['loot_batches']==before
# Explicit generation fixture exercises gear receipt and atomic swap without default bonuses leaking.
gear=None
for seed in range(100):
 item=generate_item(Random(seed),21,'Редкий','fixture')
 if item.get('gear'):gear=item;break
assert gear
record=dict(id='fixture',enemy='Тест',item=gear,recipient='',discarded=False);d['loot_batches'].append(dict(battle_id='test',items=[record]));beforearmor=d['ally']['armor']
assign_loot(d,'fixture','ally');assert d['ally']['armor']==beforearmor
received=next(x for x in d['ally']['sheet_profile']['equipment'] if x['id']=='fixture:0');assert not received['equipped'] and received['rarity']=='Редкий'
before=deepcopy(d)
try:assign_loot(d,'fixture','ally')
except ValueError:pass
else:raise AssertionError('Duplicate loot assigned')
assert d==before
# Root reserve receives zero-filled equipment on equip, so old slot properties cannot leak.
d['loot_batches'].append(dict(battle_id='root',items=[dict(id='root-fixture',enemy='Тест',item=deepcopy(gear),recipient='',discarded=False)]))
assign_loot(d,'root-fixture','player');item=d['equipment_reserve'][0];slot=item['slot'];slot='Оружие 1 (посох)' if slot=='Оружие 1' else slot
old=deepcopy(d['equipment'][slot]);equip_root_reserve(d,item['id']);assert d['equipment'][slot]['rarity']=='Редкий'
for field in ('int','wis','spi','fire','dark'):assert d['equipment'][slot][field]==gear['gear']['root_bonuses'].get(field,0)
assert any(x['name']==old['name'] for x in d['equipment_reserve'])
# Consumables go to inventory once; rejection does not transfer anything.
potion=generate_item(Random(2),21,'Обычный','potion')
for seed in range(100):
 potion=generate_item(Random(seed),21,'Обычный','potion')
 if not potion.get('gear'):break
d['loot_batches'].append(dict(battle_id='consumable',items=[dict(id='potion',enemy='Тест',item=potion,recipient='',discarded=False)]));n=len(d['inventory']);assign_loot(d,'potion','player');assert len(d['inventory'])==n+1
record=next(x for x in d['loot_batches'][0]['items'] if not x['recipient']);assign_loot(d,record['id'],'discard');assert next(x for x in d['loot_batches'][0]['items'] if x['id']==record['id'])['discarded']
# Zero chances give an empty, fixed batch.
d=fresh();conf=settings(d);conf['chances']={k:0 for k in conf['chances']};d['loot_settings']=conf;e.start_combat(d)
for x in d['enemies']:x['hp']=0
e.end_combat(d);assert d['loot_batches'][0]['items']==[]
print('Passed: seeded no-reroll loot, drop chances, five items, explicit assignment, no duplicate claim, gear reserve, equip swap, zero-filled stats, consumables and discard.')
# Full UI: pending loot can be assigned in view mode without enabling rule editing.
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from streamlit.testing.v1 import AppTest
from kalista_storage import read_state
with TemporaryDirectory() as directory:
 root=Path(directory);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text())
 d=fresh();conf=settings(d);conf['chances']={k:100 for k in conf['chances']};d['loot_settings']=conf;e.start_combat(d)
 for x in d['enemies']:x['hp']=0
 e.end_combat(d);rid=d['loot_batches'][0]['items'][0]['id'];save=root/'kalista_save.json';save.write_text(json.dumps(d,ensure_ascii=False))
 app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['page']='Бой';app.run();assert not app.exception
 next(b for b in app.button if b.label=='Выдать предмет').click().run();assert not app.exception
 actual,_=read_state(save);assert next(x for x in actual['loot_batches'][0]['items'] if x['id']==rid)['recipient']=='player'
print('Passed: GM view-mode loot assignment through form and persisted recipient.')
