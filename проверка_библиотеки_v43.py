from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import kalista_engine as e
from kalista_map_background import catalog
from streamlit.testing.v1 import AppTest

with TemporaryDirectory() as folder:
    root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
    d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d);d=e.migrate(d)
    save.write_text(json.dumps(d,ensure_ascii=False))
    app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.run()
    app.radio(key='page').set_value('Ведущий').run();app.radio(key='gm_section').set_value('Карты').run();assert not app.exception
    assert next(x for x in app.selectbox if x.label=='Карта') and not any(x.key=='map_library_choice' for x in app.selectbox)
    assert json.loads(save.read_text())==d,'Browsing library mutated save'
    app.selectbox(key='hub_category').set_value('Город').run();assert not app.exception
    ident=next(x for x in app.selectbox if x.label=='Карта').value
    assert next(x for x in catalog() if x['id']==ident).get('category')=='Город'
    app.button(key='hub_show_scene').click().run();assert not app.exception
    actual=json.loads(save.read_text());assert actual['battle_maps']['scene_displays']['_table']==ident
    assert actual['positions']==d['positions'] and actual['battle_maps']['calibrations']==d['battle_maps']['calibrations']
    app.button(key='hub_show_world').click().run();assert not app.exception
    actual=json.loads(save.read_text());assert actual['battle_maps']['scene_displays']['_world']==ident
    app.toggle(key='_edit_mode').set_value(True).run();assert not app.exception
    assert any(x.key=='save_scale_'+ident for x in app.button)
    player=AppTest.from_file(str(source),default_timeout=30);player.secrets['access']={'gm_password':'g','player_password':'p'};player.session_state['_role']='player';player.run();player.radio(key='player_section').set_value('Сцена').run();assert not player.exception
    assert not any(x.key and x.key.startswith('hub_map_') for x in player.selectbox)
    assert json.loads(save.read_text())==actual
print('Passed: dedicated GM library, developer-only settings, scene/world publication without changing combat scale/positions, player view without controls, read-only browsing.')

# Two-click wall editor saves world metres, then removal remains recoverable.
from unittest.mock import patch
import kalista_interactive_map as board
from kalista_map_background import calibration,assign_map,ROOT
from kalista_obstacles import walls
with TemporaryDirectory() as folder:
    root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
    item=next(x for x in catalog() if (ROOT/x['file']).exists())
    d=e.migrate(deepcopy(e.DEFAULT));d['battle_maps']['calibrations'][item['id']]=calibration([0,0],[100,0],5,item['width'],item['height']);assign_map(d,item['id']);d=e.migrate(d);save.write_text(json.dumps(d,ensure_ascii=False))
    app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['_edit_mode']=True;app.run();app.radio(key='page').set_value('Ведущий').run();app.radio(key='gm_section').set_value('Карты').run()
    assert not app.exception
    app.text_input(key='hub_search').set_value(item['name']).run()
    def component(**k):
        return {'epoch':k['epoch'],'points':[[10,-10],[10,-20]]} if k['mode']=='wall' else None
    with patch.object(board,'_component',side_effect=component):
        app.run();assert not app.exception
        next(x for x in app.button if x.label=='Добавить преграду').click().run();assert not app.exception
    actual=json.loads(save.read_text());assert len(walls(actual))==1 and walls(actual)[0]['first']==[10.,-10.]
    assert actual['map_revision']==d['map_revision']+1
    wid=walls(actual)[0]['id'];app.button(key='wall_remove_'+wid).click().run();assert not app.exception
    assert not walls(json.loads(save.read_text()))
print('Passed: developer wall editor accepts two world-coordinate clicks, persists exact metres and map revision, and removes the wall.')
