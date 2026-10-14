from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import json
import kalista_engine as e
from streamlit.testing.v1 import AppTest

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d)
 d['enemies']=[dict(id=i,name='Страж '+str(i),hp=2000,hp_max=2000,armor=0,resists={x:0 for x in e.ELEMENTS},initiative=1,effects=[],attack_damage=10,attack_type='Физический') for i in (1,2)]
 d['next_enemy_id']=3;return e.migrate(d)
with TemporaryDirectory() as directory:
 root=Path(directory);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 d=fresh();save.write_text(json.dumps(d,ensure_ascii=False))
 app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='player';app.run();app.radio(key='player_section').set_value('Бой').run();assert not app.exception
 app.selectbox(key='player_battle_target').set_value('enemy:2').run();assert not app.exception
 attack=next(x['id'] for x in d['ally']['actions'] if x['name']=='Удар оружием')
 app.selectbox(key='action_choice_ally').set_value(attack).run();assert app.multiselect(key='action_targets_ally_'+attack).value==['enemy:2']
 assert json.loads(save.read_text())==d
 app.radio(key='player_section').set_value('Обзор').run();app.radio(key='player_section').set_value('Бой').run();assert app.selectbox(key='player_battle_target').value=='enemy:2'
 app.button(key='move_ally_move_close').click().run();assert not app.exception
 actual=json.loads(save.read_text());assert actual['player_requests'][-1]['victims']==['enemy:2'] and actual['player_requests'][-1]['status']=='pending'
 assert actual['enemies'][1]['hp']==2000
 # Main target follows selection; extra targets persist through unrelated reruns.
 app.multiselect(key='action_targets_ally_'+attack).set_value(['enemy:1','enemy:2']).run();app.run();assert app.multiselect(key='action_targets_ally_'+attack).value==['enemy:1','enemy:2']
 app.selectbox(key='player_battle_target').set_value('enemy:1').run();assert app.multiselect(key='action_targets_ally_'+attack).value==['enemy:1']
 # Self-only buffs explicitly target the caster, not the selected enemy.
 eye=next(x['id'] for x in d['ally']['actions'] if x.get('rule')=='eye')
 app.selectbox(key='action_choice_ally').set_value(eye).run();assert app.multiselect(key='action_targets_ally_'+eye).value==['ally']
 assert any('Применится к: Шеогарат' in x.value for x in app.caption)
 assert app.button(key='perform_ally_'+eye).disabled # unavailable outside a battle
print('Passed: compact controls, shared target for player movement/attack, additional targets survive reruns, self buffs target caster, previews preserve save and proposals do not deal damage.')
