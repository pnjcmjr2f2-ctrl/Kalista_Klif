from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from streamlit.testing.v1 import AppTest
import kalista_engine as e
from kalista_map import ensure_positions,separation
from kalista_loot import DEFAULT_CHANCES,WEIGHTS

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d);return d

def foe(i):return dict(id=i,name='Враг '+str(i),level=21,hp=10000,hp_max=10000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=100,attack_type='Физический')
# Reinforcement while already fighting: preserve existing positions, initialize new one.
d=fresh();d['enemies']=[foe(1)];d=e.migrate(d);e.start_combat(d);old=deepcopy(d['positions']);d['enemies'].append(foe(10));e.register_enemy(d,d['enemies'][-1]);ensure_positions(d);e.refresh_turn_order(d)
assert all(d['positions'][k]==v for k,v in old.items()) and separation(d,'enemy:10','ally')>=0
# Every direct close hit that removes HP gets its own 65% roll; shields don't.
d['positions']['ally']=[0.,0.];d['positions']['enemy:10']=[1.,0.];d['ally']['armor']=0;d['ally']['effects']=[];d['ally']['sheet_profile']['stats']['Ловкость']=0
attack=e.action_template('Два удара',amount=20,hits=2,reach='Ближняя');d['enemies'][-1]['actions']=[attack];e.validate_action_state(d)
with patch.object(e.random,'random',return_value=0):messages=e.perform_action(d,'enemy:10',attack['id'],['ally'])
assert sum(m.startswith('Контратака:') for m in messages)==2,messages
preview=e.preview_action(d,'enemy:10',attack,'ally');assert preview['incoming']==40
# Guaranteed drop fixture; XP and loot settle once at explicit battle completion.
d=fresh();d['enemies']=[foe(1)];d['loot_settings']=dict(chances={k:100 for k in DEFAULT_CHANCES},weights=deepcopy(WEIGHTS));d=e.migrate(d);e.start_combat(d)
before=d['xp'];ally_before=d['ally']['sheet_profile']['xp'];d['enemies'][0]['hp']=0;e.end_combat(d)
assert d['xp']>before and d['ally']['sheet_profile']['xp']>ally_before
assert len(d['loot_batches'][-1]['items'])==1
snapshot=deepcopy((d['xp'],d['ally']['sheet_profile']['xp'],d['loot_batches']));e.end_combat(d);assert snapshot==(d['xp'],d['ally']['sheet_profile']['xp'],d['loot_batches'])
# Rest is a gameplay action visible without editing.
with TemporaryDirectory() as folder:
 root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 d=fresh();e.recalc(d);d['ally']['hp']=1;save.write_text(json.dumps(d,ensure_ascii=False))
 app=AppTest.from_file(str(source),default_timeout=40);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='player';app.session_state['_edit_mode']=False;app.run();assert not app.exception
 app.button(key='ps_long_rest').click().run();assert not app.exception
 actual=json.loads(save.read_text());assert actual['ally']['hp']==actual['ally']['hp_max']
print('Reinforcement positions, repeated close counterattacks, final damage, XP/loot once, and player rest without editing: OK')
