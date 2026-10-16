from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import json
from streamlit.testing.v1 import AppTest
import kalista_engine as e

with TemporaryDirectory() as folder:
    root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
    d=e.migrate(deepcopy(e.DEFAULT));save.write_text(json.dumps(d,ensure_ascii=False))
    app=AppTest.from_file(str(source),default_timeout=40);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['_edit_mode']=True;app.run()
    app.radio(key='page').set_value('Бой').run();assert not app.exception
    app.radio(key='battle_section').set_value('Участники').run();assert not app.exception
    app.selectbox(key='new_enemy_race').set_value('Лич')
    next(x for x in app.text_input if x.label=='Имя нового врага').set_value('Лич испытаний')
    next(x for x in app.button if x.label=='Добавить врага').click().run();assert not app.exception
    actual=json.loads(save.read_text());foe=actual['enemies'][-1]
    assert foe['enemy_role']=='Некромант' and foe['bloodless']
    assert any(a['name']=='Волна могильного холода' for a in foe['actions'])
    assert foe['mana_max']>0
    assert not app.get('json')
print('Enemy creation UI: race/class auto binding, lich abilities, mana and persistence: OK')
