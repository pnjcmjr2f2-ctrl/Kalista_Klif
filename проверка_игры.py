import sys,json
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import kalista_engine as e
from kalista_storage import read_state,write_state,StaleState
def gm_app(*args,**kwargs):
 app=AppTest.from_file(*args,**kwargs);app.secrets['access']={'gm_password':'test-gm','player_password':'test-player'};app.session_state['_role']='gm';app.session_state['_edit_mode']=True;return app
from streamlit.testing.v1 import AppTest

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d['ally']['sheet_profile']['critical_chance']=0;e.recalc(d);return e.migrate(d)
def enemy(id,hp=1500):
 return dict(id=id,name='Страж '+str(id),hp=hp,hp_max=hp,armor=185,resists={x:0 for x in e.ELEMENTS},initiative=5,effects=[],attack_damage=50,attack_type='Физический')

# A full encounter: two independently defended hits, healing, effects, expiry, mana and undo-ready records.
d=fresh();d['enemies']=[enemy(1),enemy(2)];d['next_enemy_id']=3;e.start_combat(d)
double=next(a for a in d['ally']['actions'] if a['name']=='Скорострел')
preview=e.preview_action(d,'ally',double,'enemy:1')
before=d['enemies'][0]['hp'];e.perform_action(d,'ally',double['id'],['enemy:1'])
assert before-d['enemies'][0]['hp']==preview['hp_min']==preview['hp_max'] and len(d['turn_actions'])==1
assert d['enemies'][0]['hp']==before-2*e.real_dmg(round(302*.7),185)
bad=deepcopy(d)
try:e.perform_action(d,'ally',double['id'],['enemy:1','enemy:999'])
except ValueError:pass
else:raise AssertionError('Bad multi-target action accepted')
assert d==bad
e.perform_action(d,'ally',double['id'],['enemy:2'])
try:e.perform_action(d,'ally',double['id'],['enemy:2'])
except ValueError:pass
else:raise AssertionError('Action limit ignored')
counter=e.action_template('Проверочная реакция',shared_attack=True,reaction=True);d['ally']['actions'].append(counter)
e.perform_action(d,'ally',counter['id'],['enemy:2'],reaction=True)
assert not d['turn_actions'][-1]['counts']
d['ally']['action_limit']=0
healer=d['enemies'][1];healer['actions']=[e.action_template('Перевязка',kind='heal',amount=200,cooldown=2,charges_max=2,charges_left=2)]
heal=healer['actions'][0];before=d['enemies'][0]['hp'];e.perform_action(d,'enemy:2',heal['id'],['enemy:1']);assert d['enemies'][0]['hp']==before+200
assert d['enemies'][1]['actions'][0]['charges_left']==1 and d['enemies'][1]['actions'][0]['cooldown_left']==2
failed=deepcopy(d)
try:e.perform_action(d,'enemy:2',heal['id'],['enemy:1'])
except ValueError:pass
else:raise AssertionError('Cooldown ignored')
assert d==failed
while d['round']==1:e.advance_turn(d)
assert d['turn_actions']==[]
# Configured armor stacks, delayed expiry, manual recharge and additional dice/penetration.
acid=e.action_template('Проверочный эффект брони',amount=10,effect_kind='armor',effect_value=-2,duration=3,max_stacks=5);d['ally']['actions'].append(acid)
for _ in range(6):
 d['turn_actions']=[] # Independent turns for the effect stacking regression.
 e.perform_action(d,'ally',acid['id'],['enemy:1'])
assert len([x for x in d['enemies'][0]['effects'] if x['source']==acid['id']])==5
assert e.effective_defense(d['enemies'][0],'Физический')==175
special=e.action_template('Проверочный удар',manual_recharge=True,amount=20,extra_dice_count=1,extra_dice_sides=6,armor_penetration=10);d['ally']['actions'].append(special);d['turn_actions']=[]
result=e.preview_action(d,'ally',special,'enemy:2');before=d['enemies'][1]['hp'];e.perform_action(d,'ally',special['id'],['enemy:2']);assert result['hp_min']<=before-d['enemies'][1]['hp']<=result['hp_max']
assert next(a for a in d['ally']['actions'] if a['id']==special['id'])['spent']
# Prototype NPC abilities survive public battle copies, without any private field.
n=e.create_npc(d,'Целитель','Жрец');n['gm_notes']='SECRET_NPC';n['combat']['actions']=[e.action_template('Лечение',kind='heal',amount=100)]
token=e.add_npc_to_battle(d,n['id']);assert e.participant(d,token)['actions'][0]['name']=='Лечение'
assert 'SECRET_NPC' not in str(e.participant(d,token))
# Public payload strips campaign secrets.
scene=e.create_scene(d,'Врата');e.update_scene(d,scene['id'],dict(summary='Публичная сцена',gm_notes='SECRET_SCENE',result='SECRET_RESULT',npc_ids=[n['id']]));e.activate_scene(d,scene['id']);d['gm_notes']='SECRET_NOTEBOOK'
assert 'SECRET' not in json.dumps(e.public_player_state(d),ensure_ascii=False)
d['ten']=5;e.activate_shadow_invisibility(d)
d['player_requests']=[dict(id='pending',action_id=double['id'],action_name='Скорострел',victims=['enemy:1'],critical=False,turn_serial=d['turn_serial'],status='pending',message='Ожидает')]
remaining=d['ten_invis_turn_starts_left'];e.set_manual_turn(d,d['current_turn'])
assert d['ten_invis_turn_starts_left']==remaining and d['player_requests'][0]['status']=='rejected'
d['player_requests'][0]['status']='pending';e.end_combat(d);assert d['player_requests'][0]['status']=='rejected'

with TemporaryDirectory() as directory:
 root=Path(directory);p=root/'kalista_app.py';p.write_text((ROOT/'kalista_app.py').read_text())
 state=fresh();state['enemies']=[enemy(1)];state['next_enemy_id']=2;state['gm_notes']='SECRET_NOTEBOOK'
 state['scenes']=[dict(id='s',name='Врата',location='',summary='PUBLIC_SCENE',gm_notes='SECRET_SCENE',result='SECRET_RESULT',status='Идёт',npc_ids=[])];state['active_scene_id']='s'
 save=root/'kalista_save.json';save.write_text(json.dumps(state,ensure_ascii=False))
 # Two readers cannot overwrite one another.
 left,rev=read_state(save);right,rev2=read_state(save);left['gold']+=1;write_state(save,left,rev,e.migrate)
 try:write_state(save,right,rev2,e.migrate)
 except StaleState:pass
 else:raise AssertionError('Stale overwrite accepted')
 gm=gm_app(str(p),default_timeout=30).run();assert not gm.exception
 for page in ('Обзор','Отряд','Бой','Ведущий','Характеристики','Инвентарь','Экипировка','Заклинания','Квесты','Кубики','Биография'):
  gm.radio(key='page').set_value(page).run();assert not gm.exception,(page,gm.exception)
 # Unauthenticated and player sessions never render GM controls / exports / secrets.
 anon=AppTest.from_file(str(p),default_timeout=30);anon.secrets['access']={'gm_password':'test-gm','player_password':'test-player'};anon.run();assert not anon.exception and not any(b.label=='💾 Сохранить' for b in anon.button)
 player=AppTest.from_file(str(p),default_timeout=30);player.secrets['access']={'gm_password':'test-gm','player_password':'test-player'};player.session_state['_role']='player';player.run();assert not player.exception
 player.radio(key='player_section').set_value('Бой').run();assert not player.exception
 assert not player.get('file_uploader') and not player.get('download_button') and not any(r.key=='page' for r in player.radio)
 assert 'SECRET' not in str(player)
 aid=next(a['id'] for a in state['ally']['actions'] if a['name']=='Удар оружием')
 player.selectbox(key='action_choice_ally').set_value(aid).run()
 player.button(key='perform_ally_'+aid).click().run();assert not player.exception
 actual,_=read_state(save);assert not actual['player_requests']
 hp=1500;assert actual['enemies'][0]['hp']<hp
 gm.button(key='sync_game').click().run();gm.radio(key='page').set_value('Бой').run();assert not gm.exception
 accepted_hp=actual['enemies'][0]['hp'];gm.run();actual,_=read_state(save);assert actual['enemies'][0]['hp']==accepted_hp
 gm.button(key='battle_undo').click().run();actual,_=read_state(save);assert actual['enemies'][0]['hp']==hp and not actual['player_requests']
 print('Passed: full encounter, separate hits/shields, multi-target atomicity, action limits/reactions, healing cooldown/charges, armor stack cap, dice/penetration, NPC action copies, public secrecy, all pages, login/player separation, two-reader CAS, direct player action/GM undo/no double apply.')
