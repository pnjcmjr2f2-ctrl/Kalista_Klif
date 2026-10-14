"""Read-only equipment previews using the same formulas as actual equip operations."""
from copy import deepcopy
from kalista_growth import ensure_growth

def preview_equipment(data,item,owner,loot=False):
    import kalista_engine as e
    from kalista_player_model import recalc_player,EQUIPMENT_SLOTS
    candidate=deepcopy(data)
    if owner=='player':
        if loot:
            gear=item['gear'];new=dict(name=item['name'],rarity=item['rarity'],description=item['desc'],**deepcopy(gear['root_bonuses']));slot=gear['slot']
        else:new=deepcopy(item);slot=new['slot']
        slot='Оружие 1 (посох)' if slot=='Оружие 1' else slot
        if slot not in candidate['equipment']:raise ValueError('У предмета нет подходящей ячейки Калисты')
        old=candidate['equipment'][slot];names=[old['name']] if old.get('name') else []
        ensure_growth(new,'player',candidate['level'],True)
        candidate['equipment'][slot]={k:0 for k in ('armor','attack','int','wis','spi','fire','dark','earth','water','air','light','spell_power')}
        candidate['equipment'][slot].update(new);e.recalc(candidate)
    elif owner=='ally':
        p=candidate['ally'].get('sheet_profile')
        if not p:raise ValueError('Лист Шеогарата не загружен')
        if loot:
            gear=item['gear'];new=dict(id='preview-only',name=item['name'],rarity=item['rarity'],description=item['desc'],bonuses=deepcopy(gear['ally_bonuses']),slot=gear['slot'],equipped=True)
        else:new=deepcopy(item)
        slot=new['slot']
        if slot not in EQUIPMENT_SLOTS:raise ValueError('Сначала укажи ячейку предмета')
        names=[x['name'] for x in p['equipment'] if x['slot']==slot and x['equipped'] and x.get('id')!=new.get('id')]
        p['equipment']=[x for x in p['equipment'] if x.get('id')!=new.get('id')]
        for x in p['equipment']:
            if x['slot']==slot:x['equipped']=False
        new['equipped']=True;ensure_growth(new,'ally',p['level']);p['equipment'].append(new);recalc_player(candidate['ally'])
    else:raise ValueError('Неизвестный персонаж')
    before=totals(data,owner);after=totals(candidate,owner)
    rows=[(label,value,after[label]) for label,value in before.items() if abs(value-after[label])>1e-8]
    return dict(slot=slot,replaces=names,rows=rows)

def totals(data,owner):
    import kalista_engine as e
    if owner=='player':
        result={k:e.total_stat(data,k) for k in data['base_stats']}
        result.update({'Броня':data['armor'],'Атака':data['phys_attack'],'Сила заклинаний':data['spell_power']*100,'Максимум HP':data['hp_max'],'Максимум маны':data['mana_max'],'Инициатива':data['initiative'],'Уклонение':e.evasion_chance(data)*100})
        result.update({el:e.effective_defense(data,el) for el in e.ELEMENTS})
    else:
        a=data['ally'];p=a['sheet_profile'];result=dict(p['stats'])
        result.update({'Броня':a['armor'],'Атака':p['attack'],'Критический урон':p['critical_damage'],'Шанс крита':p['critical_chance'],'Сила заклинаний':a.get('spell_power',0)*100,'Максимум HP':a['hp_max'],'Уклонение':e.evasion_chance(a)*100})
        result.update({el:e.effective_defense(a,el) for el in e.ELEMENTS})
    return result
