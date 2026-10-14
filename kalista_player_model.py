"""The player's editable sheet, isolated from campaign and GM data."""
from copy import deepcopy
from uuid import uuid4
import math
from kalista_rarity import validate_rarity
from kalista_growth import ensure_growth,effective_item
from kalista_progression import MAX_LEVEL,advance_levels
from urllib.parse import urlparse

STATS=('Сила','Выносливость','Ловкость','Мудрость','Интеллект','Харизма')
EQUIPMENT_SLOTS=('Оружие 1','Оружие 2','Шлем','Наплечники','Перчатки','Нагрудник','Пояс','Штаны','Сапоги','Серьга 1','Серьга 2','Ожерелье','Кольцо 1','Кольцо 2','Кольцо 3','Кольцо 4')
ITEM_TYPES=('Расходник','Реагент','Свиток','Оружие','Броня','Реликвия','Инструмент','Книга','Валюта','Прочее')
BONUSES=STATS+('Броня','Атака','Сила заклинаний','Критический урон','Шанс крита','Огонь','Земля','Вода','Воздух','Тьма','Свет')

def number(value,label,minimum=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or (minimum is not None and value<minimum):
        raise ValueError('Неверное число: '+label)

def gear_totals(profile):
    totals={key:0 for key in BONUSES}
    for item in profile['equipment']:
        ensure_growth(item,'ally',profile['level'])
        if item['equipped']:
            for key,value in effective_item(item)['bonuses'].items(): totals[key]+=value
    return totals

def ensure_player_sheet(ally):
    p=ally.get('sheet_profile')
    if not p: return
    for item in p['equipment']:
        item.setdefault('id',uuid4().hex);item.setdefault('equipped',True)
    if not p.get('equipment_reference_imported'):
        for name in p.get('equipment_note','').splitlines():
            if name.strip() and not any(item['name']==name.strip() for item in p['equipment']):
                p['equipment'].append(dict(id=uuid4().hex,name=name.strip(),slot='Резерв',description='Из Long Story Short; числовые бонусы не заполнены.',bonuses={},equipped=False))
        p['equipment_reference_imported']=True
    if 'inventory' not in p:
        p['inventory']=[dict(id=uuid4().hex,name=x['name'],type='Предмет',qty=x['qty'],desc='',use=None) for x in p.get('reference',{}).get('resources',[])]
    p.setdefault('currency',{key:p.get('reference',{}).get('coins',{}).get(code,0) for key,code in (('gold','gp'),('silver','sp'),('copper','cp'))})
    p.setdefault('quests',[]);p.setdefault('biography','');p.setdefault('portrait_url','')
    p.setdefault('xp',0);p.setdefault('xp_known',False)
    g=gear_totals(p)
    p.setdefault('stat_adjustments',{key:p['stats'][key]-p['base_stats'][key]-g[key] for key in STATS})
    p.setdefault('formula_adjustments',dict(hp=ally['hp_max']-(p['level']*20+p['stats']['Выносливость']*10),
        armor=ally['armor']-(10+p['stats']['Выносливость']*5+g['Броня']),
        attack=p['attack']-g['Атака']*(1+p['stats']['Сила']/500),
        critical_damage=p['critical_damage']-(p['attack']*2+g['Критический урон']),
        critical_chance=p['critical_chance']-min(95,5+p['stats']['Ловкость']*.05+g['Шанс крита'])))
    p.setdefault('resist_adjustments',{e:ally['resists'][e]-g[e] for e in ('Огонь','Земля','Вода','Воздух','Тьма','Свет')})
    # Preserve explicit edits made through the GM's existing character editor.
    for key in STATS:
        if max(0,p['base_stats'][key]+g[key]+p['stat_adjustments'][key])!=p['stats'][key]:
            p['stat_adjustments'][key]=p['stats'][key]-p['base_stats'][key]-g[key]
    computed=dict(hp=p['level']*20+p['stats']['Выносливость']*10,armor=10+p['stats']['Выносливость']*5+g['Броня'],
                  attack=g['Атака']*(1+p['stats']['Сила']/500),critical_damage=p['attack']*2+g['Критический урон'],critical_chance=min(95,5+p['stats']['Ловкость']*.05+g['Шанс крита']))
    actual=dict(hp=ally['hp_max'],armor=ally['armor'],attack=p['attack'],critical_damage=p['critical_damage'],critical_chance=p['critical_chance'])
    for key in computed:
        if abs(computed[key]+p['formula_adjustments'][key]-actual[key])>.00001:p['formula_adjustments'][key]=actual[key]-computed[key]
    for key in p['resist_adjustments']:
        if max(-100,min(95,p['resist_adjustments'][key]+g[key]))!=ally['resists'][key]:p['resist_adjustments'][key]=ally['resists'][key]-g[key]
    validate_player_sheet(ally)

def validate_player_sheet(ally):
    p=ally['sheet_profile']
    for key in ('notes','biography','portrait_url'):
        if not isinstance(p[key],str): raise ValueError('Ожидается текст: '+key)
    if p['portrait_url']:
        parsed=urlparse(p['portrait_url'])
        if parsed.scheme not in ('http','https') or not parsed.netloc:raise ValueError('Для портрета нужна ссылка http:// или https://')
    if not isinstance(p['xp_known'],bool): raise ValueError('Неверное состояние опыта')
    number(p['xp'],'Опыт',0)
    if not 1<=p['level']<=MAX_LEVEL:raise ValueError('Уровень должен быть от 1 до 1650')
    for collection in ('inventory','equipment','quests'):
        if not isinstance(p[collection],list): raise ValueError('Ожидается список: '+collection)
        ids=set()
        for item in p[collection]:
            if collection in ('inventory','equipment'):validate_rarity(item)
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'] or item['id'] in ids: raise ValueError('Неверный ID: '+collection)
            ids.add(item['id'])
            if not isinstance(item.get('name'),str) or not item['name'].strip(): raise ValueError('Укажи название')
            if collection=='equipment':
                if not isinstance(item.get('equipped'),bool) or not isinstance(item.get('bonuses'),dict): raise ValueError('Неверное снаряжение')
                for key in ('slot','description'):
                    if not isinstance(item.get(key),str): raise ValueError('Неверное описание снаряжения')
                for key,v in item['bonuses'].items():
                    if key not in BONUSES: raise ValueError('Неизвестный бонус снаряжения')
                    number(v,key)
                    if key in STATS and not isinstance(v,int): raise ValueError('Характеристика должна быть целой')
            elif collection=='inventory':
                if not isinstance(item.get('qty'),int) or isinstance(item['qty'],bool) or item['qty']<0: raise ValueError('Количество должно быть целым и неотрицательным')
                if not isinstance(item.get('type'),str) or not isinstance(item.get('desc'),str): raise ValueError('Неверное описание предмета')
                use=item.get('use')
                if use is not None:
                    if not isinstance(use,dict) or use.get('kind') not in ('heal','mana','shield'): raise ValueError('Неверное применение предмета')
                    if not isinstance(use.get('value'),int) or isinstance(use['value'],bool) or use['value']<1: raise ValueError('Укажи силу применения выше 0')
            else:
                if item.get('status') not in ('Активен','Выполнен','Провален') or not isinstance(item.get('desc'),str): raise ValueError('Неверный квест')
    for key in ('gold','silver','copper'):
        value=p['currency'].get(key)
        if not isinstance(value,int) or isinstance(value,bool) or value<0: raise ValueError('Монеты должны быть целыми и неотрицательными')
    for key in STATS:
        if not isinstance(p['base_stats'].get(key),int) or isinstance(p['base_stats'][key],bool) or p['base_stats'][key]<0: raise ValueError('Неверная базовая характеристика')
        number(p['stat_adjustments'].get(key),key)
    for key in ('hp','armor','attack','critical_damage','critical_chance'): number(p['formula_adjustments'].get(key),key)
    for key in ('Огонь','Земля','Вода','Воздух','Тьма','Свет'): number(p['resist_adjustments'].get(key),key)

def recalc_player(ally):
    p=ally['sheet_profile'];advance_levels(p);g=gear_totals(p);a=p['formula_adjustments']
    p['stats']={key:max(0,p['base_stats'][key]+g[key]+p['stat_adjustments'][key]) for key in STATS}
    ally['spell_power']=max(0,(p['stats']['Интеллект']/5+g['Сила заклинаний'])/100)
    ally['hp_max']=max(1,round(p['level']*20+p['stats']['Выносливость']*10+a['hp']))
    ally['hp']=min(ally['hp'],ally['hp_max'])
    ally['armor']=max(0,round(10+p['stats']['Выносливость']*5+g['Броня']+a['armor']))
    p['attack']=max(0,round(g['Атака']*(1+p['stats']['Сила']/500)+a['attack'],4));ally['attack_damage']=round(p['attack'])
    p['critical_damage']=max(0,round(p['attack']*2+g['Критический урон']+a['critical_damage'],4))
    p['critical_chance']=max(0,min(95,5+p['stats']['Ловкость']*.05+g['Шанс крита']+a['critical_chance']))
    ally['resists']={e:max(-100,min(95,p['resist_adjustments'][e]+g[e])) for e in p['resist_adjustments']}

def sheet_snapshot(data,section):
    a=data['ally'];p=a['sheet_profile']
    mapping={'identity':{k:deepcopy(p[k]) for k in ('portrait_url','biography')},
        'inventory':dict(items=deepcopy(p['inventory']),currency=deepcopy(p['currency'])),
        'equipment':deepcopy(p['equipment']),'notes':p['notes'],'quests':deepcopy(p['quests']),
        'actions':deepcopy(a['actions']),
        'attributes':{k:deepcopy(p[k]) for k in ('base_stats','stat_adjustments','formula_adjustments','resist_adjustments','level','free_points','xp','xp_known')},
        'resources':{k:deepcopy(a.get(k)) for k in ('hp','mana_current','mana_max','effects')}}
    mapping['rest']=dict(resources=deepcopy(mapping['resources']),actions=deepcopy(a['actions']))
    mapping['identity'].update(name=a['name'],race=p['race'],klass=p['class'])
    if section not in mapping: raise ValueError('Неизвестный раздел')
    return mapping[section]

def edit_player_sheet(data,section,values,expected):
    candidate=deepcopy(data);a=candidate['ally'];ensure_player_sheet(a);p=a['sheet_profile']
    if sheet_snapshot(candidate,section)!=expected: raise ValueError('Этот раздел уже изменился. Нажми «Обновить раздел» и повтори правку.')
    if section=='identity':
        if set(values)!= {'name','race','klass','portrait_url','biography'}: raise ValueError('Неверная правка персонажа')
        if any(not isinstance(v,str) for v in values.values()) or not values['name'].strip(): raise ValueError('Укажи имя и текстовые поля')
        a['name']=values['name'].strip();p.update(race=values['race'],**{'class':values['klass']},portrait_url=values['portrait_url'],biography=values['biography'])
        for actor in candidate['turn_order']:
            if actor['kind']=='ally': actor['name']=a['name']
    elif section=='inventory':
        if set(values)!= {'items','currency'}: raise ValueError('Неверная правка инвентаря')
        p['inventory']=deepcopy(values['items']);p['currency']=deepcopy(values['currency'])
    elif section=='equipment': p['equipment']=deepcopy(values)
    elif section=='notes': p['notes']=values
    elif section=='quests': p['quests']=deepcopy(values)
    elif section=='actions': a['actions']=deepcopy(values)
    elif section=='attributes':
        if set(values)!=set(expected): raise ValueError('Неверная правка характеристик')
        for key,value in values.items():p[key]=deepcopy(value)
        for key in ('level','free_points','xp'):
            if not isinstance(p[key],int) or isinstance(p[key],bool) or p[key]<(1 if key=='level' else 0): raise ValueError('Неверное целое число: '+key)
    elif section=='resources':
        if set(values)!= {'hp','mana_current','mana_max','effects'}: raise ValueError('Неверная правка ресурсов')
        for key in ('hp','mana_current','mana_max'):
            if not isinstance(values[key],int) or isinstance(values[key],bool) or values[key]<0: raise ValueError('Неверный ресурс')
        if values['hp']>a['hp_max'] or values['mana_current']>values['mana_max']: raise ValueError('Ресурс выше максимума')
        a['hp']=values['hp'];a['effects']=deepcopy(values['effects'])
        if values['mana_max']:
            a['mana_max']=values['mana_max'];a['mana_current']=values['mana_current']
        else:a.pop('mana_max',None);a.pop('mana_current',None)
    elif section=='rest':
        if candidate['combat_active']:raise ValueError('Сначала заверши бой')
        a['hp']=a['hp_max'];a['effects']=[]
        if 'mana_max' in a:a['mana_current']=a['mana_max']
        for action in a['actions']:
            if not action['manual_recharge']:action['cooldown_left']=0
        for request in candidate.get('player_requests',[]):
            if request['status']=='pending':request.update(status='rejected',message='Персонаж отдыхает; предложи действие заново')
    else:raise ValueError('Неизвестный раздел')
    validate_player_sheet(a);recalc_player(a)
    if section=='actions':
        for request in candidate.get('player_requests',[]):
            if request['status']=='pending': request.update(status='rejected',message='Способности изменились; предложи действие заново')
    return candidate

def use_player_item(data,item_id,expected):
    candidate=deepcopy(data);a=candidate['ally'];ensure_player_sheet(a)
    if sheet_snapshot(candidate,'inventory')!=expected: raise ValueError('Инвентарь изменился. Обнови раздел.')
    item=next((x for x in a['sheet_profile']['inventory'] if x['id']==item_id),None)
    if not item or item['qty']<1 or not item['use']: raise ValueError('Предмет недоступен')
    use=item['use'];value=use['value']
    if use['kind']=='heal':
        actual=min(value,max(0,a['hp_max']-a['hp']));a['hp']+=actual
    elif use['kind']=='mana':
        if 'mana_max' not in a: raise ValueError('У персонажа не задан ресурс маны')
        actual=min(value,max(0,a['mana_max']-a['mana_current']));a['mana_current']+=actual
    else:
        actual=value;a['effects'].append(dict(id=uuid4().hex,kind='shield',name=item['name'],value=value,duration=None,element='Огонь',source='ally-item:'+item_id,desc=item['desc'],applied_round=candidate['round'] if candidate['combat_active'] else 0))
    if not actual: raise ValueError('Ресурс уже заполнен; предмет сохранён')
    item['qty']-=1
    candidate.setdefault('turn_actions',[]).append(dict(source='ally',name=item['name'],target=a['name'],result=f'Применён предмет: +{actual}',counts=False))
    return candidate
