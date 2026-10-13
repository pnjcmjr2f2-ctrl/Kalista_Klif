from copy import deepcopy
import kalista_engine as e
from kalista_rewards import xp_share,register_enemy
from kalista_progression import advance_levels,xp_needed

def fresh():
 d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d)
 d['enemies']=[dict(id=i,name='Враг '+str(i),level=l,hp=1000,hp_max=1000,armor=0,resists={x:0 for x in e.ELEMENTS},effects=[],initiative=1,attack_damage=10,attack_type='Физический') for i,l in ((1,21),(2,11),(3,36),(4,1000))]
 return e.migrate(d)

assert xp_share(dict(level=11),21,2)[0]==0
assert xp_share(dict(level=12),21,2)[0]>0
assert xp_share(dict(level=35),21,2)[0]>xp_share(dict(level=36),21,2)[0]
assert xp_share(dict(level=36),21,2)[0]==xp_share(dict(level=100000),21,2)[0]
assert xp_share(dict(level=21),21,2)[0]==96
assert xp_share(dict(level=21,is_elite=True),21,2)[0]==193
assert xp_share(dict(level=21,is_boss=True,is_elite=True),21,2)[0]==482
assert xp_share({},21,2)[0]==0
assert xp_share(dict(level=1649),1650,2)[0]==0
# Start roster survives ally defeat; losses grant XP for kills, no XP for surviving enemies.
d=fresh();e.start_combat(d);d['ally']['hp']=0
for x in d['enemies'][:3]:x['hp']=0
expected={h['token']:sum(xp_share(x,h['level'],2)[0] for x in d['enemies'][:3]) for h in d['battle_rewards']['party']}
e.end_combat(d);r=d['last_battle_reward'];assert {x['token']:x['xp'] for x in r['heroes']}==expected
assert len(d['enemies'])==1 and d['ally']['sheet_profile']['xp']==expected['ally']
before=deepcopy(d);e.end_combat(d);assert d['xp']==before['xp'] and d['ally']['sheet_profile']['xp']==before['ally']['sheet_profile']['xp']
# New battle does not pay archived kills; reinforcements can be registered.
d=fresh();d['enemies'][0]['hp']=0;e.start_combat(d);assert 1 not in d['battle_rewards']['eligible']
extra=deepcopy(d['enemies'][1]);extra.update(id=5,hp=1000,level=21);d['enemies'].append(extra);register_enemy(d,extra);extra['hp']=0
e.end_combat(d);assert [x['id'] for x in d['last_battle_reward']['enemies']]==[5]
# Exact and multiple thresholds, +4 per level, carry, no automatic healing.
d=fresh();goal=xp_needed(21);d['xp']=goal+xp_needed(22)+7;oldhp=d['hp_current'];oldpoints=d['free_points'];e.recalc(d)
assert d['level']==23 and d['xp']==7 and d['free_points']==oldpoints+8 and d['hp_current']==oldhp
p=dict(level=1649,xp=xp_needed(1649)+999,free_points=0);advance_levels(p);assert p==dict(level=1650,xp=0,free_points=4,xp_goal=0,xp_to_next=0)
# A recipient reaching a level during reward settlement does not change the XP calculation for other kills.
d=fresh();e.start_combat(d);d['xp']=xp_needed(21)-1
for x in d['enemies']:x['hp']=0
e.end_combat(d);assert d['level']==22 and d['last_battle_reward']['heroes'][0]['level_before']==21
saved=e.migrate(deepcopy(d));xp=saved['xp'];e.end_combat(saved);assert saved['xp']==xp
print('Passed: base 5, exact ± boundaries, high cap, elite/boss, roster/dead hero, retreat, reinforcement, no duplicate XP, multiple levels/carry, points, 1650 cap and no heal.')
