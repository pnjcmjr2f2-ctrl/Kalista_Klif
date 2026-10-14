"""Linear growth of positive legendary bonuses; raw fields remain the editable baseline."""
from copy import deepcopy
import math
ROOT_FIELDS=('armor','attack','int','wis','spi','spell_power')
ALLY_FIELDS=('Сила','Выносливость','Ловкость','Мудрость','Интеллект','Харизма','Броня','Атака','Сила заклинаний')


def ensure_growth(item,owner,level,root=False):
    if item.get('rarity')!='Легендарный' or not item.get('name'):return
    if owner not in ('player','ally') or not isinstance(level,int) or isinstance(level,bool) or not 1<=level<=1650:raise ValueError('Неверная привязка легендарного предмета')
    values=item if root else item['bonuses'];fields=ROOT_FIELDS if root else ALLY_FIELDS
    basis={k:values.get(k,0) for k in fields}
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in basis.values()):raise ValueError('Неверный бонус легендарного предмета')
    if 'growth' not in item:item['growth']=dict(owner=owner,anchor_level=level,rate=.02,basis=basis,last_level=level)
    growth=item['growth']
    if growth.get('owner')!=owner:raise ValueError('Легендарный предмет привязан к другому герою; нужна перепривязка')
    anchor=growth.get('anchor_level')
    if not isinstance(anchor,int) or isinstance(anchor,bool) or not 1<=anchor<=1650 or growth.get('rate')!=.02:raise ValueError('Неверная формула роста легендарки')
    # Base edits change the basis, never compound the already scaled values.
    growth['basis']=basis;growth['last_level']=level


def effective_item(item,root=False,level=None):
    result=deepcopy(item)
    growth=item.get('growth')
    if item.get('rarity')!='Легендарный' or not growth:return result
    current=growth['last_level'] if level is None else level
    delta=max(0,current-growth['anchor_level'])
    values=result if root else result['bonuses']
    for key,base in growth['basis'].items():
        if key not in values and base==0:continue
        values[key]=round(base*(1+.02*delta)) if delta and base>0 else base
    return result


def bind_registry(data):
    for item in list(data['equipment'].values())+data.get('equipment_reserve',[]):ensure_growth(item,'player',data['level'],True)
    p=data.get('ally',{}).get('sheet_profile')
    if p:
        for item in p['equipment']:ensure_growth(item,'ally',p['level'])


def rebind(item,new_owner,new_level,root=False):
    current=effective_item(item,root)
    current.pop('growth',None)
    ensure_growth(current,new_owner,new_level,root)
    item.clear();item.update(current)
