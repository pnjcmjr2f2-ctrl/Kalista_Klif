"""Atomic area spell cast: one cost, independent hit and effect rolls per target."""
from copy import deepcopy
from kalista_map import validate_ability
from kalista_shapes import is_area,check_area_aim,shape_targets,area_label

def cast_area_spell(data,spell,center,final_damage=None):
    import kalista_engine as e
    candidate=deepcopy(data)
    if candidate.get('distance_mode')!='meters':raise ValueError('Для области нужна карта в метрах')
    spell=next((s for s in candidate['spells'] if s['id']==spell['id']),None)
    if not spell:raise ValueError('Заклинание изменилось')
    validate_ability(spell)
    if e.spell_action(spell)!='damage' or not is_area(spell):raise ValueError('Заклинание не является массовой атакой')
    e.check_action_limit(candidate,'player')
    if candidate['hp_current']<=0:raise ValueError('У Калисты 0 HP')
    if candidate['mana_current']<spell['mana']:raise ValueError('Не хватает маны')
    if spell.get('cd_left'):raise ValueError('Заклинание ещё на перезарядке')
    if final_damage is not None:e.nonnegative_int(final_damage,'Итоговый урон')
    center=check_area_aim(candidate,'player',spell,center)
    tokens=shape_targets(candidate,'player',spell,center)
    if not tokens:raise ValueError('В области нет живых целей')
    dual,soul=e.spell_bonuses(candidate,spell);raw=__import__('kalista_skills').spell_damage(candidate,spell,dual,soul)
    empowered=bool(candidate.get('pepel_empower') and 'Огонь' in spell['school'] and raw>0 and spell['name']!='Теневой укол')
    for token in tokens:e.spell_damage_preview(candidate,spell,e.participant(candidate,token),raw,final_damage)
    e.observe_mana_reserve(candidate);candidate['mana_current']-=spell['mana'];spell['cd_left']=spell.get('cd_max',0);candidate['last_school']=spell['school']
    if spell.get('gives') in ('pepel','both'):candidate['pepel']=min(5,candidate['pepel']+1)
    if spell.get('gives') in ('ten','both'):candidate['ten']=min(5,candidate['ten']+1)
    if soul:candidate['soul_flame_boost']=False
    messages=[f"«{spell['name']}» · {area_label(spell)} · целей: {len(tokens)} · −{spell['mana']} MP"]
    counters=[]
    for token in tokens:
        target=e.participant(candidate,token)
        if (target is candidate and candidate.get('ten_invis')) or (e.ranged_miss_chance(candidate,'player',spell,token) and e.random.random()<e.ranged_miss_chance(candidate,'player',spell,token)):
            messages.append(target['name']+': промах');counters.append((token,{'hp_loss':0}));continue
        amount=raw
        if final_damage is None and e.random.random()<e.effective_crit_chance(candidate):amount=round(raw*1.5);messages.append(target['name']+': КРИТ ×1,5')
        result=e.spell_damage_apply(candidate,spell,target,amount,final_damage);messages.append(e.damage_message(target['name'],result))
        messages.extend(target['name']+': '+m for m in e.roll_spell_effects(candidate,spell,target,amount));counters.append((token,result))
    if empowered:candidate['pepel_empower']=False
    for token,result in counters:
        if token!='player' and candidate['hp_current']>0:messages.extend(e.counterattack(candidate,'player',token,result))
    e.record_turn_action(candidate,'player',spell['name'],', '.join(e.participant(candidate,t)['name'] for t in tokens),' · '.join(messages))
    if candidate['combat_active']:e.refresh_turn_order(candidate)
    data.clear();data.update(candidate)
    return messages
