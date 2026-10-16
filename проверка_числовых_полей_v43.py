"""Regression: fractional ally attack must open in the GM participant editor."""
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import json
from streamlit.testing.v1 import AppTest
import kalista_engine as e

with TemporaryDirectory() as folder:
    root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
    d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d);d=e.migrate(d)
    assert isinstance(d['ally']['sheet_profile']['attack'],float)
    save.write_text(json.dumps(d,ensure_ascii=False))
    app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['_edit_mode']=True;app.run()
    for page in ('Отряд','Характеристики','Бой'):
        app.radio(key='page').set_value(page).run();assert not app.exception,(page,app.exception)
        if page=='Отряд':
            app.radio(key='friend_view').set_value('Правка').run();assert not app.exception
            attack=next(x for x in app.number_input if x.label=='Урон атаки')
            assert attack.value==d['ally']['sheet_profile']['attack']
            assert attack.min==0.0
    assert json.loads(save.read_text())==d,'Opening numeric editors changed save'
print('Passed: fractional ally attack and related numeric editors open without type mismatch; viewing preserves saved values.')
