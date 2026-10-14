"""Regression checks for resource changes and damaged legendary binding."""
from copy import deepcopy
import kalista_engine as e
from kalista_loot import equip_root_reserve
from kalista_growth import ensure_growth

d=e.migrate(deepcopy(e.DEFAULT));e.recalc(d)
d['equipment']['Оружие 1 (посох)']['spell_power']=47;e.recalc(d)
d['mana_current']=d['mana_max'];d['hp_current']=d['hp_max']
d['equipment_reserve']=[dict(id='replacement',slot='Оружие 1',name='Простой посох',rarity='Обычный',attack=10)]
equip_root_reserve(d,'replacement')
assert d['mana_current']==d['mana_max']==2350
assert d['spell_power']==.47
old=next(x for x in d['equipment_reserve'] if x['name']=='Посох Магистра Огня и Тьмы')
equip_root_reserve(d,old['id'])
assert d['mana_current']==2350 and d['mana_max']==2950 and d['spell_power']==1.06
# Reducing maximum HP clamps excess; increasing the maximum never heals.
d['level']-=1;e.recalc(d);assert d['hp_current']==d['hp_max']==800
d['level']+=1;e.recalc(d);assert d['hp_current']==800 and d['hp_max']==820
broken=dict(name='Предмет',rarity='Легендарный',growth=[])
try:ensure_growth(broken,'player',21,True)
except ValueError as exc:assert 'привязка' in str(exc)
else:raise AssertionError('Malformed binding accepted')
print('Passed: staff swap at full MP, no free refill on re-equip, HP maximum reduction, controlled malformed binding rejection.')
