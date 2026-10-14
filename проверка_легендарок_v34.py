from copy import deepcopy
import kalista_engine as e
from kalista_growth import ensure_growth,effective_item,rebind
from kalista_player_model import recalc_player,gear_totals,sheet_snapshot,edit_player_sheet

item=dict(name='Сапоги',rarity='Легендарный',bonuses={'Броня':150,'Сила':20,'Шанс крита':3,'Огонь':10,'Харизма':-10},equipped=True)
ensure_growth(item,'ally',17);assert effective_item(item)['bonuses']==item['bonuses']
ensure_growth(item,'ally',27);values=effective_item(item)['bonuses'];assert values['Броня']==180 and values['Сила']==24 and values['Шанс крита']==3 and values['Огонь']==10 and values['Харизма']==-10
ensure_growth(item,'ally',27);assert effective_item(item)['bonuses']==values
ensure_growth(item,'ally',37);assert effective_item(item)['bonuses']['Броня']==210 and item['bonuses']['Броня']==150
try:ensure_growth(item,'player',21)
except ValueError:pass
else:raise AssertionError('Unapproved transfer accepted')
rebind(item,'player',21);assert item['growth']['anchor_level']==21 and effective_item(item)['bonuses']['Броня']==210
# Current gear preserves all numbers at binding, then grows without stacking or manual-adjustment compensation.
d=e.migrate(deepcopy(e.DEFAULT));d['ally']=e.imported_friend();d=e.migrate(d);e.recalc(d)
p=d['ally']['sheet_profile'];legend=next(x for x in p['equipment'] if x['name']=='Ледяная скорбь');oldattack=p['attack'];oldstrength=p['stats']['Сила']
p['level']+=10;recalc_player(d['ally']);assert p['stats']['Сила']==oldstrength+10 and p['attack']>oldattack
before=p['attack'];d=e.migrate(d);assert d['ally']['sheet_profile']['attack']==before
# Explicit bonus edits retain binding and preserve the original growth rate.
p=d['ally']['sheet_profile'];expected=sheet_snapshot(d,'equipment');values=deepcopy(expected);weapon=next(x for x in values if x['name']=='Ледяная скорбь');anchor=weapon['growth']['anchor_level'];weapon['bonuses']['Атака']=300
updated=edit_player_sheet(d,'equipment',values,expected);weapon=next(x for x in updated['ally']['sheet_profile']['equipment'] if x['name']=='Ледяная скорбь');assert weapon['growth']['anchor_level']==anchor and effective_item(weapon)['bonuses']['Атака']==360
# Direct spell-power bonuses are percentage points, added once to Intelligence's existing contribution.
d=e.migrate(deepcopy(e.DEFAULT));e.recalc(d);assert d['spell_power']==.59
staff=d['equipment']['Оружие 1 (посох)'];staff['spell_power']=10;e.recalc(d);assert d['spell_power']==.69
shield=e.shadow_shield_amount(d);assert shield==round(295*1.69)
d['level']+=10;e.recalc(d);staff=e.effective_item(d['equipment']['Оружие 1 (посох)'],True);assert staff['int']==72 and staff['spell_power']==12
assert d['spell_power']==(307/5+12)/100
# A reserve legendary grows too, and does not apply its stats until equipped.
reserve=dict(name='Посох в резерве',rarity='Легендарный',attack=100,spell_power=10);d['equipment_reserve']=[reserve];e.recalc(d);anchor=d['level'];before=d['spell_power'];d['level']+=10;e.recalc(d);assert effective_item(reserve,True)['attack']==120
assert d['equip_spell_power']==staff['spell_power']+2 # worn staff, not reserve
print('Passed: linear 2% growth, fixed crit/resists/penalties, ownership, rebinding, persistent basis, no adjustment cancellation, spell power +10pp, shield, reserve growth and no auto-equip.')
