"""Wall geometry, direct actions, duplicate protection and durable undo."""
from copy import deepcopy
from pathlib import Path
import tempfile
import kalista_engine as e
from kalista_storage import read_state,write_state,undo_entries,undo_state,StaleState
from kalista_direct import apply_player_action,finish_player_turn
from kalista_obstacles import walls,key,intersects,blocking_wall
from kalista_shapes import shape_targets

def fixture():
    d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();e.recalc(d)
    d['distance_mode']='meters';d['positions']={'player':[0,0],'ally':[10,0]}
    d['hp_current']=d['hp_max'];d['ally']['hp']=d['ally']['hp_max'];d['mana_current']=d['mana_max']
    foe=e.gen_enemy(1,'Обычный',False);foe.update(id=991,name='Проверочный гоблин',hp=5000,hp_max=5000,armor=0,resists={x:0 for x in e.ELEMENTS})
    d['enemies']=[foe];d['positions']['enemy:991']=[12,0];d=e.migrate(d);e.start_combat(d)
    e.set_manual_turn(d,next(i for i,a in enumerate(d['turn_order']) if a['kind']=='ally'))
    return d

assert intersects([0,0],[10,0],[5,-2],[5,2])
assert intersects([0,0],[5,0],[5,0],[5,2])
assert intersects([0,0],[10,0],[2,0],[3,0])
assert not intersects([0,0],[10,0],[5,1],[5,2])
d=fixture();w=dict(id='wall',name='Стена',first=[11,-5],second=[11,5],movement=True,attacks=True)
d['battle_maps']['obstacles'][key(d)]=[w]
assert blocking_wall(d,[10,0],[12,0])
a=next(x for x in d['ally']['actions'] if x['kind']=='damage' and x.get('shared_attack'))
for op in (lambda:e.perform_action(d,'ally',a['id'],['enemy:991']),lambda:e.move(d,'ally',destination=[12,0])):
    before=deepcopy(d)
    try:op();raise AssertionError('Wall ignored')
    except ValueError:assert d==before
cone={'area_shape':'cone','cone_length_m':30,'cone_angle_deg':60,'kind':'damage'}
assert 'enemy:991' not in shape_targets(d,'ally',cone,[20,0])
circle=dict(kind='damage',area_radius_m=5,range_m=30)
try:shape_targets(d,'ally',circle,[12,0]);raise AssertionError('Explosion placed through wall')
except ValueError:pass
# Same background retains walls across scenes; another map does not inherit them.
d['battle_maps']['assignments']['_table']='one';d['battle_maps']['obstacles']['map:one']=[w]
assert walls(d)==[w];d['battle_maps']['assignments']['_table']='two';assert not walls(d)
with tempfile.TemporaryDirectory() as folder:
    p=Path(folder)/'save.json';d=fixture();a=next(x for x in d['ally']['actions'] if x['kind']=='damage' and x.get('shared_attack'));_,rev=read_state(p);write_state(p,d,rev,e.migrate)
    seen=deepcopy(d);before=e.participant(d,'enemy:991')['hp']
    n,rev,msg=apply_player_action(p,seen,a['id'],['enemy:991'])
    assert e.participant(n,'enemy:991')['hp']<before and len(n['turn_actions'])==1
    assert not any(x['status']=='pending' for x in n.get('player_requests',[]))
    try:apply_player_action(p,seen,a['id'],['enemy:991']);raise AssertionError('Duplicate action accepted')
    except ValueError:pass
    # New session needs no in-memory history.
    assert undo_entries(p)
    restored,rev=undo_state(p,rev,e.migrate);assert restored==d
    n,rev,msg=apply_player_action(p,restored,a['id'],['enemy:991'])
    after,rev=finish_player_turn(p,n);assert after['turn_serial']!=n['turn_serial']
    try:finish_player_turn(p,n);raise AssertionError('Old turn ended twice')
    except ValueError:pass
print('Passed: wall intersections, blocked movement/attacks/cone/explosion, map isolation, direct player action, duplicate prevention, durable undo and own end-turn.')
