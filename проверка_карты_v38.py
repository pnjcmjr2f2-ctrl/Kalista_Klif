from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import kalista_engine as e
from kalista_map import ensure_positions,separation,area_targets,move,map_svg
from kalista_area import cast_area_spell
from streamlit.testing.v1 import AppTest

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d['mana_current']=2950;d['hp_current']=820;d['distance_mode']='meters'
 d['enemies']=[dict(id=i,name='Враг '+str(i),hp=2000,hp_max=2000,armor=100,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=30,attack_type='Физический') for i in (1,2,3)]
 d['next_enemy_id']=4;e.recalc(d);d=e.migrate(d);d['positions']={'player':[0.,0.],'ally':[35.,0.],'enemy:1':[40.,0.],'enemy:2':[50.,0.],'enemy:3':[50.001,0.]}
 s=next(s for s in d['spells'] if s['name']=='Огненный шар');s.update(range_m=80.,area_radius_m=10.)
 return d,s

d,s=fresh();assert area_targets(d,[40,0],10)==['ally','enemy:1','enemy:2'];assert 'svg' in map_svg(d,[40,0],10)
for center in ([80.001,0],[float('nan'),0]):
 before=deepcopy(d)
 try:cast_area_spell(d,s,center)
 except ValueError:pass
 else:raise AssertionError('Invalid center accepted')
 assert d==before
# Each target receives its own full hit; crits and burn rolls are independent.
d['ally']['counterattack_enabled']=False;d['enemies'][0]['resists']['Огонь']=50
mp=d['mana_current'];raw=e.spell_raw(s['base'],d['spell_power']);burn=e.kalista_dot_damage(d,'burn')
with patch.object(e.random,'random',side_effect=[.99,.99, .0,.0, .99,.99]):cast_area_spell(d,s,[40,0])
assert d['mana_current']==mp-s['mana'] and len([a for a in d['turn_actions'] if a['counts']])==1
assert next(s for s in d['spells'] if s['name']=='Огненный шар')['cd_left']==1
assert d['ally']['hp']==440-round(raw*.9)
assert d['enemies'][0]['hp']==2000-round(round(raw*1.5)*.5)
assert d['enemies'][1]['hp']==2000-raw and d['enemies'][2]['hp']==2000
assert any(x['kind']=='dot' and x['value']==burn for x in d['enemies'][0]['effects'])
assert not d['enemies'][1]['effects']
# The radius, rather than a 20-target cap, controls large bursts; empowerment covers every hit.
d,s=fresh();d['enemies']=[dict(d['enemies'][0],id=i,name='Цель '+str(i),resists={el:95 if el=='Огонь' else 0 for el in e.ELEMENTS},effects=[]) for i in range(1,26)]
ensure_positions(d)
for a in d['enemies']:d['positions']['enemy:'+str(a['id'])]=[45.,0.]
d['pepel_empower']=True;raw=e.spell_raw(s['base'],d['spell_power'])
with patch.object(e.random,'random',return_value=.99):cast_area_spell(d,s,[40,0])
expected=round(raw*(1-.95*.7));assert all(a['hp']==2000-expected for a in d['enemies'])
assert not d['pepel_empower'] and d['mana_current']==2950-s['mana']
# A defeated character cannot retaliate, including friendly fire.
d,s=fresh();d['ally']['hp']=0;assert e.counterattack(d,'player','ally',{'hp_loss':1})==[]
# Melee 5m boundary; exact 30m free movement once per turn, no action use.
d,s=fresh();d['positions']['ally']=[0.,0.];d['positions']['enemy:1']=[5.,0.]
a=next(x for x in d['ally']['actions'] if x['name']=='Удар оружием');e.check_reach(d,'ally',a,'enemy:1')
d['positions']['enemy:1']=[5.001,0.]
try:e.check_reach(d,'ally',a,'enemy:1')
except ValueError:pass
else:raise AssertionError('Melee beyond 5m accepted')
e.start_combat(d);p=next(a for a in d['ally']['actions'] if a.get('rule')=='move_point');before=deepcopy(d)
try:e.perform_action(d,'ally',p['id'],['ally'],destination=[30.001,0])
except ValueError:pass
else:raise AssertionError('Movement beyond 30m accepted')
assert d==before
e.perform_action(d,'ally',p['id'],['ally'],destination=[30,0]);assert separation(d,'player','ally')==30 and d['ally']['movement_used']
assert not d['turn_actions'][-1]['counts']
try:e.perform_action(d,'ally',p['id'],['ally'],destination=[31,0])
except ValueError:pass
else:raise AssertionError('Second movement accepted')
# Skill areas use their own physical evasion and area targets; stale geometry rejected.
d,s=fresh();a=e.action_template('Удар по области',amount=100,area_radius_m=10.,range_m=80.,reach='Дальняя');d['ally']['actions'].append(a);victims=area_targets(d,[40,0],10)
with patch.object(e.random,'random',return_value=.99):e.perform_action(d,'ally',a['id'],victims,area_center=[40,0])
assert d['enemies'][0]['hp']<2000 and d['enemies'][1]['hp']<2000
# Position revisions prevent applying proposals against a changed layout.
d,s=fresh();action=next(a for a in d['ally']['actions'] if a.get('rule')=='move_point')
d['player_requests']=[dict(id='move',action_id=action['id'],action_name=action['name'],victims=['ally'],critical=False,turn_serial=d['turn_serial'],status='pending',message='',destination=[40.,0.],area_center=None,map_revision=0)]
d['map_revision']=1;before=deepcopy(d)
try:e.resolve_player_request(d,'move',True)
except ValueError:pass
else:raise AssertionError('Stale map proposal accepted')
assert d==before
# Metric UI: area settings/edit controls and actor map in both roles/modes.
with TemporaryDirectory() as directory:
 root=Path(directory);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json'
 for role in ('gm','player'):
  for editing in (False,True):
   d,s=fresh();save.write_text(json.dumps(d,ensure_ascii=False));app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']=role;app.session_state['_edit_mode']=editing;app.run()
   app.radio(key='page' if role=='gm' else 'player_section').set_value('Бой').run();assert not app.exception,(role,editing,app.exception)
   if role=='gm':
    app.selectbox(key='battle_spell').set_value(s['id']).run();assert not app.exception
    assert any('Заденет героев' in x.value for x in app.warning)
    assert app.session_state['spell_area_'+str(s['id'])+'_x']==40
   assert json.loads(save.read_text())==d,'Viewing metric map changed save'
   if role=='gm' and not editing:
    app.button(key='cast_area_'+str(s['id'])).click().run();assert not app.exception
    actual=json.loads(save.read_text());assert actual['mana_current']==d['mana_current']-s['mana']
    assert len([x for x in actual['turn_actions'] if x['counts']])==1
print('Passed: 80m cast / 10m area boundaries, full independent hits, resistances and crit/DoT rolls, one cost/action/CD, 5m melee, 30m movement, no second move, no self counter, skill areas and metric UI both roles/modes.')
