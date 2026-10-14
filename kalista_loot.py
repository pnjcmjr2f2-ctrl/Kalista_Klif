"""Seeded procedural loot proposals; explicit assignment, no auto-equipping."""
from copy import deepcopy
from random import Random
from uuid import uuid5,NAMESPACE_URL
import math
from kalista_rarity import RARITIES,validate_rarity

DEFAULT_CHANCES={'Обычный':25,'Элитный':50,'Босс':100}
WEIGHTS={'Обычный':[70,22,6,1.8,.2],'Элитный':[45,35,15,4.5,.5],'Босс':[10,30,40,18,2]}
SLOTS=[('Шлем','Шлем'),('Перчатки','Перчатки'),('Нагрудник','Кираса'),('Штаны','Поножи'),('Сапоги','Сапоги')]


def settings(data):
    result=deepcopy(data.get('loot_settings',dict(chances=DEFAULT_CHANCES,weights=WEIGHTS)))
    for kind in DEFAULT_CHANCES:
        chance=result['chances'][kind];weights=result['weights'][kind]
        if not isinstance(chance,(int,float)) or isinstance(chance,bool) or not math.isfinite(chance) or not 0<=chance<=100:raise ValueError('Шанс добычи должен быть от 0 до 100%')
        if len(weights)!=5 or any(not isinstance(w,(int,float)) or isinstance(w,bool) or not math.isfinite(w) or w<0 for w in weights) or sum(weights)<=0:raise ValueError('Неверные веса редкости')
    return result


def generate_item(rng,level,rarity,identifier):
    factor=[1,1.2,1.5,1.9,2.4][RARITIES.index(rarity)]
    category=rng.choice(['Расходник','Реагент','Броня','Оружие'])
    item=dict(id=identifier,name='',type=category,rarity=rarity,qty=1,desc='',use=None)
    if category=='Расходник':
        kind=rng.choice(['heal','mana']);value=round((30+level*8)*factor)
        item.update(name='Зелье '+('лечения' if kind=='heal' else 'маны'),use=dict(kind=kind,value=value),desc=f'Восстанавливает {value} '+('HP' if kind=='heal' else 'MP')+'.')
    elif category=='Реагент':
        item.update(name=rng.choice(['Кристаллический осколок','Прах зачарования','Сгусток эссенции']),qty=rng.randint(1,3),desc='Материал для ремесла и ритуалов. Конкретное применение определяет ведущий.')
    else:
        suffix=rng.choice(['стража','странника','хранителя','ветерана'])
        if category=='Броня':
            slot,noun=rng.choice(SLOTS);armor=round((10+level*2 if slot=='Нагрудник' else 5+level*.4)*factor)
            ally={'Броня':armor};root={'armor':armor}
            item['name']=noun+' '+suffix
        else:
            weapon=rng.choice(['Меч','Посох']);slot='Оружие 1';attack=round((10+level*3)*factor)
            ally={'Атака':attack};root={'attack':attack}
            if weapon=='Посох':
                intel=max(1,round((1+level/10)*factor));ally['Интеллект']=intel;root['int']=intel
                power=max(1,round((2+level/10)*factor));ally['Сила заклинаний']=power;root['spell_power']=power
            item['name']=weapon+' '+suffix
        item['gear']=dict(slot=slot,ally_bonuses=ally,root_bonuses=root)
        item['desc']='; '.join(f'{k}: +{v}' for k,v in ally.items())+'. Сгенерированный предмет; ведущий может скорректировать свойства до выдачи.'
    return item


def roll_battle_loot(data,state,fallen):
    batches=data.setdefault('loot_batches',[])
    if any(b['battle_id']==state['id'] for b in batches):return
    config=state.get('loot_settings',settings(data));party=state['party'];cap=max((p['level'] for p in party),default=1)+5
    items=[]
    for enemy in fallen:
        if not isinstance(enemy.get('level'),int) or enemy['level']<1:continue
        rng=Random(state['id']+':'+str(enemy['id']))
        kind='Босс' if enemy.get('is_boss') else 'Элитный' if enemy.get('is_elite') else 'Обычный'
        if rng.random()*100>=config['chances'][kind]:continue
        rarity=rng.choices(RARITIES,weights=config['weights'][kind],k=1)[0]
        level=min(enemy['level'],cap)
        identifier=uuid5(NAMESPACE_URL,state['id']+':loot:'+str(enemy['id'])).hex
        item=generate_item(rng,level,rarity,identifier)
        items.append(dict(id=identifier,enemy=enemy['name'],item=item,recipient='',discarded=False))
    batches.append(dict(battle_id=state['id'],items=items))


def assign_loot(data,loot_id,recipient,changes=None):
    from kalista_engine import migrate
    candidate=deepcopy(data)
    record=next((r for b in candidate.get('loot_batches',[]) for r in b['items'] if r['id']==loot_id),None)
    if not record or record['recipient'] or record['discarded']:raise ValueError('Добыча уже выдана или больше недоступна')
    if recipient not in ('player','ally','discard'):raise ValueError('Неверный получатель')
    if recipient=='discard':record['discarded']=True
    else:
        item=deepcopy(changes or record['item']);validate_rarity(item)
        if not isinstance(item['qty'],int) or isinstance(item['qty'],bool) or not 1<=item['qty']<=100 or not item['name'].strip():raise ValueError('Укажи название и положительное количество')
        item['name']=item['name'].strip();gear=item.get('gear')
        if gear:
            if recipient=='ally':
                p=candidate['ally'].get('sheet_profile')
                if not p:raise ValueError('Лист Шеогарата не загружен')
                for index in range(item['qty']):p['equipment'].append(dict(id=record['id']+':'+str(index),name=item['name'],slot=gear['slot'],description=item['desc'],rarity=item['rarity'],bonuses=deepcopy(gear['ally_bonuses']),equipped=False))
            else:
                for index in range(item['qty']):candidate.setdefault('equipment_reserve',[]).append(dict(id=record['id']+':'+str(index),slot=gear['slot'],name=item['name'],description=item['desc'],rarity=item['rarity'],**deepcopy(gear['root_bonuses'])))
        else:
            inventory=candidate['inventory'] if recipient=='player' else candidate['ally']['sheet_profile']['inventory']
            copy={k:deepcopy(item[k]) for k in ('name','type','qty','desc','rarity','use')}
            if recipient=='ally':copy['id']=record['id']
            inventory.append(copy)
        record['item']=item;record['recipient']=recipient
    candidate=migrate(candidate);data.clear();data.update(candidate)


def equip_root_reserve(data,item_id):
    from kalista_engine import recalc,migrate
    candidate=deepcopy(data);reserve=candidate.setdefault('equipment_reserve',[])
    item=next((x for x in reserve if x['id']==item_id),None)
    if not item:raise ValueError('Предмет уже надет или отсутствует')
    slot=item['slot'];slot='Оружие 1 (посох)' if slot=='Оружие 1' else slot
    if slot not in candidate['equipment']:raise ValueError('Неизвестная ячейка')
    old=deepcopy(candidate['equipment'][slot]);reserve.remove(item)
    if old.get('name'):old.update(id=uuid5(NAMESPACE_URL,item_id+':old:'+old['name']).hex,slot=slot);reserve.append(old)
    candidate['equipment'][slot]={key:0 for key in ('armor','attack','int','wis','spi','fire','dark','earth','water','air','light')}
    candidate['equipment'][slot].update({k:deepcopy(v) for k,v in item.items() if k not in ('id','slot')})
    recalc(candidate);candidate=migrate(candidate);data.clear();data.update(candidate)
