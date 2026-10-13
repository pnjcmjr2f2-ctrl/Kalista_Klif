from copy import deepcopy
import kalista_engine as e
from kalista_progression import xp_needed,MAX_LEVEL

d=e.migrate(deepcopy(e.DEFAULT));assert d['level']==21 and d['xp']==0 and d['legacy_xp']==18450 and d['xp_to_next']==38607
assert e.migrate(d)['legacy_xp']==18450
d['xp']=1000;d=e.migrate(d);assert d['xp']==1000 and d['xp_to_next']==37607
d['ally']=e.imported_friend();old=d['ally']['sheet_profile']['xp'];d=e.migrate(d);p=d['ally']['sheet_profile']
assert p['level']==17 and p['xp']==0 and p['legacy_xp']==old and p['xp_goal']==29960
assert all(xp_needed(l)<xp_needed(l+1) for l in range(1,1649))
assert xp_needed(1650)==0
try:xp_needed(1651)
except ValueError:pass
else:raise AssertionError('Ceiling ignored')
d['level']=1650;d=e.migrate(d);assert d['xp_to_next']==0
print('Passed: curve, one-time XP reset, preserved legacy and levels, independent heroes, monotonic costs and divine ceiling.')
