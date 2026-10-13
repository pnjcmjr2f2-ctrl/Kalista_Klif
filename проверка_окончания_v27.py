from copy import deepcopy
import kalista_engine as e

d=e.migrate(deepcopy(e.DEFAULT));d['enemies']=[dict(id=i,name='Гоблин',hp=hp,hp_max=100,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=10,attack_type='Физический') for i,hp in ((1,0),(2,100))];d=e.migrate(d)
for _,t in e.participants(d):e.add_effect(t,dict(kind='shield',name='Щит',value=50))
e.add_effect(d,dict(kind='dot',name='Горение',value=1,duration=3,element='Огонь'))
assert 'enemy:1' not in [t for t,_ in e.visible_battle_participants(d)]
d['distances']={'enemy:1|player':'Ближняя','enemy:2|player':'Дальняя'};d['turn_excluded']=['enemy:1'];d['initiative_overrides']={'enemy:1':30}
before=deepcopy(d);e.end_combat(d)
assert all(not any(x['kind']=='shield' for x in t['effects']) for _,t in e.participants(d))
assert any(x['kind']=='dot' for x in d['effects'])
assert [x['id'] for x in d['enemies']]==[2] and d['defeated_enemies'][0]['id']==1
assert not d['turn_excluded'] and not d['initiative_overrides'] and len(d['distances'])==1
assert d['xp']==before['xp']
e.migrate(d);e.end_combat(d);assert len(d['defeated_enemies'])==1
print('Passed: shields removed, defeated foes hidden/archived, live foes retained, links cleaned, no XP grant, idempotent ending.')
