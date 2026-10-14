from copy import deepcopy
import kalista_engine as e
from kalista_rarity import ensure_rarities,validate_rarity

d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d)
assert d['equipment']['Нагрудник']['rarity']=='Редкий'
assert d['equipment']['Ожерелье']['rarity']=='Эпический'
assert d['equipment']['Оружие 1 (посох)']['rarity']=='Легендарный'
assert d['equipment']['Кольцо 1']['rarity']=='Необычный'
p=d['ally']['sheet_profile'];assert next(x for x in p['equipment'] if x['name']=='Ледяная скорбь')['rarity']=='Легендарный'
assert all(x['rarity']=='Легендарный' for x in p['equipment'] if 'ниргхал' in x['name'].lower())
d['equipment']['Нагрудник']['rarity']='Эпический';e.migrate(d);assert d['equipment']['Нагрудник']['rarity']=='Эпический'
try:validate_rarity(dict(rarity='Божественный'))
except ValueError:pass
else:raise AssertionError('Unknown rarity accepted')
print('Passed: five rarities, known gear classifications, late ally import, editable persistence and invalid rarity rejected.')
