"""End-of-combat XP settlement. No loot or random reward rolls."""
from uuid import uuid4
from math import floor
from kalista_progression import advance_levels,MAX_LEVEL

def begin_rewards(data):
    if data.get('combat_active'):raise ValueError('Бой уже начат')
    party=[]
    if data['hp_current']>0 and 'player' not in data.get('turn_excluded',[]):party.append(dict(token='player',name=data['name'],level=data['level']))
    ally=data['ally'];p=ally.get('sheet_profile')
    if p and ally['hp']>0 and 'ally' not in data.get('turn_excluded',[]):party.append(dict(token='ally',name=ally['name'],level=p['level']))
    data['battle_rewards']=dict(id=uuid4().hex,party=party,eligible=[],settled=False)
    for enemy in data['enemies']:register_enemy(data,enemy)

def register_enemy(data,enemy):
    state=data.get('battle_rewards')
    if state and not state['settled'] and enemy['hp']>0 and enemy.get('side','Враг')=='Враг' and enemy['id'] not in state['eligible']:
        state['eligible'].append(enemy['id'])

def xp_share(enemy,hero_level,party_size):
    level=enemy.get('level')
    if not isinstance(level,int) or isinstance(level,bool) or level<1:return 0,'уровень врага не указан'
    if hero_level>=MAX_LEVEL:return 0,'достигнут уровень 1650'
    if level<=hero_level-10:return 0,'враг на 10+ уровней ниже'
    high=level>=hero_level+15
    effective=min(level,hero_level+14) if high else level
    multiplier=5 if enemy.get('is_boss') else 2 if enemy.get('is_elite') else 1
    base=round(5*effective**1.2)*multiplier
    return floor(base*(.25 if high else 1)/max(1,party_size)),('слишком сильный враг: ограничение уровня и ×25%' if high else 'обычная награда')

def settle_rewards(data):
    from kalista_engine import recalc
    from kalista_player_model import recalc_player
    state=data.get('battle_rewards')
    if not state or state['settled'] or not data.get('combat_active'):return None
    fallen=[x for x in data['enemies'] if x['id'] in state['eligible'] and x['hp']<=0 and x.get('side','Враг')=='Враг']
    summary=dict(battle_id=state['id'],enemies=[dict(id=x['id'],name=x['name'],level=x.get('level')) for x in fallen],heroes=[])
    for member in state['party']:
        token=member['token'];character=data if token=='player' else data['ally'].get('sheet_profile')
        if character is None:continue
        details=[];amount=0
        for enemy in fallen:
            reward,reason=xp_share(enemy,member['level'],len(state['party']))
            details.append(dict(name=enemy['name'],xp=reward,reason=reason));amount+=reward
        if character['level']>=MAX_LEVEL:amount=0
        before=character['level'];character['xp']+=amount;gained=advance_levels(character)
        if token=='player':recalc(data)
        else:recalc_player(data['ally'])
        summary['heroes'].append(dict(token=token,name=member['name'],xp=amount,level_before=before,level_after=character['level'],free_points=gained*4,details=details))
    state['settled']=True;data['last_battle_reward']=summary
    return summary
