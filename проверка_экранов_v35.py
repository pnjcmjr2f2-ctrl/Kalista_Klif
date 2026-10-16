from pathlib import Path
import sys,json
from copy import deepcopy
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parent))
from streamlit.testing.v1 import AppTest
import kalista_engine as e
ROOT=Path(__file__).resolve().parent
original=json.loads((ROOT/'kalista_save.json').read_text())
pages={'gm':('page',['Обзор','Отряд','Бой','Экипировка','Инвентарь','Характеристики','Заклинания','Квесты','Ведущий','Кубики','Биография']),'player':('player_section',['Обзор','Бой','Снаряжение','Инвентарь','Характеристики','Заклинания и способности','Квесты','Заметки','Биография','Кубики','Сцена'])}
checks=0
with TemporaryDirectory() as tmp:
 root=Path(tmp);source=root/'kalista_app.py';source.write_text((ROOT/'kalista_app.py').read_text());save=root/'kalista_save.json'
 for combat in (False,True):
  d=e.migrate(deepcopy(original))
  if d['combat_active']:e.end_combat(d);d=e.migrate(d)
  if combat:
   d['enemies']=[dict(id=998,name='Проверочный враг',level=21,hp=10000,hp_max=10000,armor=150,resists={el:10 for el in e.ELEMENTS},initiative=1,effects=[],attack_damage=100,attack_type='Физический')];d['next_enemy_id']=999;d=e.migrate(d);e.start_combat(d);d=e.migrate(d)
  for role,(selector,sections) in pages.items():
   for editing in (False,True):
    save.write_text(json.dumps(d,ensure_ascii=False))
    app=AppTest.from_file(str(source),default_timeout=40);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.session_state['_edit_mode']=editing;app.run()
    for page in sections:
     app.radio(key=selector).set_value(page).run();assert not app.exception,(combat,role,editing,page,app.exception)
     assert not app.get('json') and not app.get('code'),(role,page,'Raw data')
     if role=='player':assert not app.get('file_uploader') and not app.get('download_button')
     checks+=1
    actual=json.loads(save.read_text());assert actual==d,(role,editing,combat,'Viewing changed persistent save')
    print('PASS',role,'edit' if editing else 'view','battle' if combat else 'peace',flush=True)
print('Passed',checks,'screens; actual saved gear; both roles/modes, peace and combat, no persistent writes or raw data.')
