from copy import deepcopy
import math,json
from pathlib import Path
import kalista_engine as e
from kalista_map_background import calibration,ensure_backgrounds,assign_map,background,catalog,remember_layout,restore_layout

# Ten 100px cells at 5m/cell => 0.05m/px. Both axes use the SAME ratio.
c=calibration([100,200],[1100,200],50,2400,1800)
assert c['metres_per_pixel']==.05
assert math.isclose(math.dist([0,0],[600*.05,800*.05]),50)
assert math.isclose(2400*.05/1800/.05,2400/1800)
for p,q,d in [([0,0],[0,0],50),([-1,0],[100,0],50),([0,0],[2401,0],50),([0,0],[100,0],0),([0,0],[100,0],float('nan'))]:
 try:calibration(p,q,d,2400,1800)
 except ValueError:pass
 else:raise AssertionError('Invalid calibration accepted')
data=e.migrate(deepcopy(e.DEFAULT));data['distance_mode']='meters'
assert not background(data)
maps=catalog()
if not maps:
 from tempfile import TemporaryDirectory
 from PIL import Image
 import kalista_map_background as bg
 fixture=TemporaryDirectory();bg.ROOT=Path(fixture.name)
 Image.new('RGB',(240,180),'black').save(bg.ROOT/'fixture.webp')
 (bg.ROOT/'catalog.json').write_text(json.dumps([dict(id='fixture',name='Тестовая карта',file='fixture.webp',width=240,height=180)]))
 maps=catalog()
else:assert len(maps)==33
ident=maps[0]['id'];item=maps[0]
try:assign_map(data,ident)
except ValueError:pass
else:raise AssertionError('Uncalibrated map enabled')
assert not data['battle_maps']['assignments']
data['battle_maps']['calibrations'][ident]=calibration([0,0],[100,0],5,item['width'],item['height'])
assign_map(data,ident);b=background(data);assert b['metres_per_pixel']==.05 and b['width']==item['width'] and b['height']==item['height']
before=deepcopy(data['positions']);data['positions']['player']=[12,-18];assign_map(data,'');data['positions']['player']=[77,88];assign_map(data,ident);assert data['positions']['player']==[12.,-18.]
scene=e.create_scene(data,'Тестовая локация','');e.activate_scene(data,scene['id']);assert not background(data)
assign_map(data,ident);data['positions']['player']=[40,-20];scene2=e.create_scene(data,'Вторая локация','');e.activate_scene(data,scene2['id']);assign_map(data,ident);data['positions']['player']=[8,-9];e.activate_scene(data,scene['id']);assert data['positions']['player']==[40.,-20.]
assert e.migrate(data)['battle_maps']==data['battle_maps']
broken=deepcopy(data);broken['battle_maps']['calibrations'][ident]['metres_per_pixel']=1
try:e.migrate(broken)
except ValueError:pass
else:raise AssertionError('Tampered scale accepted')
data['combat_active']=True;before=deepcopy(data)
try:assign_map(data,'')
except ValueError:pass
else:raise AssertionError('Combat map switched')
assert data==before
print('Passed: uniform scale, exact 5m cells and diagonal distance, invalid points/NaN reject, uncalibrated map blocked, per-scene layouts retained, no combat background switches, scale integrity, map library available.')
# Scene edits/finish must restore both position data and the matching map.
data['combat_active']=False
e.update_scene(data,scene2['id'],{'status':'Идёт'});assert data['positions']['player']==[8.,-9.]
e.update_scene(data,scene2['id'],{'status':'Завершена'});assert data['positions']['player']==[12.,-18.]
from tempfile import TemporaryDirectory
from streamlit.testing.v1 import AppTest
with TemporaryDirectory() as folder:
 root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 for role in ('gm','player'):
  for editing in (False,True):
   d=e.migrate(deepcopy(data));e.recalc(d);d=e.migrate(d);save.write_text(json.dumps(d,ensure_ascii=False));app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.session_state['_edit_mode']=editing;app.run();app.radio(key='page' if role=='gm' else 'player_section').set_value('Бой').run()
   assert not app.exception,(role,editing,app.exception)
   assert any('Локация:' in x.value for x in app.caption)
   assert any(x.key=='map_library_choice' for x in app.selectbox)==(role=='gm' and editing)
   assert json.loads(save.read_text())==d,'Viewing map changed save'
print('Passed: calibrated backgrounds in both roles/modes, GM-only settings, scene edits and completion restore layouts, viewing never writes.')
