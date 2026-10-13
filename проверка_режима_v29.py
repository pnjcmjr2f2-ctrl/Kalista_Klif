from pathlib import Path
from tempfile import TemporaryDirectory
import json
from copy import deepcopy
from streamlit.testing.v1 import AppTest
import kalista_engine as e
from kalista_storage import read_state

with TemporaryDirectory() as directory:
 root=Path(directory);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text())
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d);save=root/'kalista_save.json';save.write_text(json.dumps(d,ensure_ascii=False))
 for role,selector,pages in [('gm','page',['Экипировка','Инвентарь','Характеристики','Заклинания','Квесты','Ведущий']),('player','player_section',['Снаряжение','Инвентарь','Характеристики','Заклинания и способности','Квесты','Заметки','Биография'])]:
  app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.run();assert not app.exception
  for page in pages:
   app.radio(key=selector).set_value(page).run();assert not app.exception,(role,page,app.exception)
   assert not app.number_input and not app.text_input and not app.text_area,(role,page)
   assert not app.get('file_uploader')
  app.session_state['_edit_mode']=True;app.radio(key=selector).set_value('Характеристики').run();assert not app.exception
  assert app.number_input or any(b.label=='＋' for b in app.button)
  app.session_state['_edit_mode']=False;app.radio(key=selector).set_value('Бой').run();assert not app.exception
  assert any(b.label in ('Начать','Применить способность','Предложить действие') for b in app.button)
  assert not any(x.label in ('Назначить итоговый урон вручную','Ручная поправка: урон, лечение, мана и щит') for x in app.checkbox)
 assert read_state(save)[0]['ally']['hp']==d['ally']['hp']
print('Passed: view-only pages for both roles, editing toggle, retained combat actions, hidden admin fields and preserved resources.')
