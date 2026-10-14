from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import json
from streamlit.testing.v1 import AppTest
import kalista_engine as e
from kalista_view import bonus_values

assert bonus_values(dict(name='Посох',attack=50,int=60,wis=15,spi=60,fire=50,dark=50,rarity='Легендарный',id='internal'),True)==[('Атака','+50'),('Интеллект','+60'),('Мудрость','+15'),('Дух','+60'),('Огонь','+50%'),('Тьма','+50%')]
assert bonus_values(dict(bonuses={'Свет':-50,'Шанс крита':3,'Броня':150,'Сила':0}))==[('Свет','-50%'),('Шанс крита','+3%'),('Броня','+150')]
with TemporaryDirectory() as directory:
 root=Path(directory);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text())
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d);save=root/'kalista_save.json';save.write_text(json.dumps(d,ensure_ascii=False))
 for role,selector,pages in [('gm','page',['Обзор','Отряд','Бой','Экипировка','Инвентарь','Характеристики','Заклинания','Квесты','Ведущий','Кубики','Биография']),('player','player_section',['Обзор','Бой','Снаряжение','Инвентарь','Характеристики','Заклинания и способности','Квесты','Заметки','Биография','Кубики','Сцена'])]:
  app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.run();assert not app.exception
  for page in pages:
   app.radio(key=selector).set_value(page).run();assert not app.exception,(role,page,app.exception)
   assert not app.get('json'),(role,page,'Raw JSON rendered')
   assert not app.get('code'),(role,page,'Raw code rendered')
print('Passed: Russian bonus labels, percent signs, metadata excluded, no JSON/code blocks in all GM and player view-mode pages.')
