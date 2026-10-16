from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from streamlit.testing.v1 import AppTest
import kalista_engine as e
import kalista_skills as s
x=e.migrate(deepcopy(e.DEFAULT));x['level']=21;x['ally']=e.imported_friend();x=e.migrate(x)
assert x['skill_points']==5 and x['ally']['skill_points']==4
assert s.spent(10)==18
key='spell:'+str(x['spells'][0]['id']);base=x['spells'][0]['base'];raw=s.spell_damage(x,x['spells'][0])
s.upgrade(x,'player',key);assert x['skill_points']==4 and s.rank(x['spells'][0])==2
assert x['spells'][0]['base']==base and s.spell_damage(x,x['spells'][0])>raw
assert e.migrate(deepcopy(x))==x
for _ in range(2):s.upgrade(x,'player',key)
s.upgrade(x,'player',key);assert x['skill_points']==0 and s.rank(x['spells'][0])==5
try:s.upgrade(x,'player',key)
except ValueError:pass
else:raise AssertionError('Overspending accepted')
x['level']=24;e.migrate(x);s.initialize(x);assert x['skill_points']==1
sword=next(a for a in x['ally']['actions'] if a['name']=='Скорострел');assert sword['multiplier']==.7
heavy=next(a for a in x['ally']['actions'] if a['name']=='Мощный удар')
for r,value in ((1,.85),(5,.7),(10,.5)):
 heavy['skill_rank']=r;assert abs(e.action_damage_factor(dict(armor=1000,effects=[]),heavy)-value)<1e-8
foe=dict(level=80,enemy_role='Маг',attack_damage=100,actions=[e.action_template('Атака',shared_attack=True)])
s.distribute(foe);assert s.rank(foe['actions'][0])==10 and foe['skill_points']==2
# Real purchase controls in both modes; persistent CAS commit, no buying on mere view.
with TemporaryDirectory() as folder:
 root=Path(folder);appfile=root/'kalista_app.py';appfile.write_text(Path(__file__).with_name('kalista_app.py').read_text())
 data=e.migrate(deepcopy(e.DEFAULT));data['level']=21;data['ally']=e.imported_friend();e.recalc(data);data=e.migrate(data);save=root/'kalista_save.json';save.write_text(json.dumps(data,ensure_ascii=False))
 app=AppTest.from_file(str(appfile),default_timeout=40);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.session_state['_edit_mode']=False;app.run();app.radio(key='page').set_value('Заклинания').run();assert not app.exception
 assert json.loads(save.read_text())==data
 button=next(b for b in app.button if str(b.key).startswith('skill_buy_player_spell:'));button.click().run();assert not app.exception
 actual=json.loads(save.read_text());assert actual['skill_points']==4
 assert len(actual['skill_ranks'])==1
print('Skill budget, cumulative costs, ranks, effective damage, no compounding, level accrual, enemy distribution, UI purchase and persistence OK')
