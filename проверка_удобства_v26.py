from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import json
import kalista_engine as e
from kalista_storage import read_state,write_state,create_snapshot,list_snapshots,restore_snapshot,StaleState

def fresh():return e.migrate(deepcopy(e.DEFAULT))
t=dict(name='Цель',hp=1000,hp_max=1000,armor=800,resists={x:0 for x in e.ELEMENTS},effects=[])
e.add_effect(t,dict(kind='shield',name='Щит',value=30))
r=e.apply_damage(t,100);assert r['raw']==100 and r['incoming']==50 and r['absorbed']==30 and r['hp_loss']==20
assert '100 урона → после защиты 50 → щит −30 → HP −20' in e.damage_message(t['name'],r)
d=fresh();soul=next(s for s in d['spells'] if s['name']=='Пламя души');t['resists']['Огонь']=50;t['resists']['Тьма']=20
r=e.spell_damage_apply(d,soul,t,100);assert r['raw']==100 and r['incoming']==65 and len(r['components_detail'])==2
with TemporaryDirectory() as directory:
 path=Path(directory)/'kalista_save.json';d=fresh();_,rev=read_state(path);rev=write_state(path,d,rev,e.migrate)
 name=create_snapshot(path,'before-battle');original=deepcopy(d)
 for i in range(35):
  d['xp']+=1;rev=write_state(path,d,rev,e.migrate)
 assert len([p for p in list_snapshots(path) if '_auto_' in p.name])==30
 assert (path.parent/'save_snapshots'/name).exists()
 before,oldrev=read_state(path);restored=restore_snapshot(path,name,oldrev,e.migrate);assert restored['xp']==original['xp']
 assert any(json.loads(p.read_text())['xp']==before['xp'] for p in list_snapshots(path))
 try:restore_snapshot(path,name,oldrev,e.migrate)
 except StaleState:pass
 else:raise AssertionError('Stale restore accepted')
 _,rev=read_state(path)
 try:restore_snapshot(path,'../kalista_save.json',rev,e.migrate)
 except ValueError:pass
 else:raise AssertionError('Traversal accepted')
 assert read_state(path)[0]==restored
print('Passed: damage chain, split elements, snapshot retention, restore, rollback snapshot, stale restore and traversal rejection.')
