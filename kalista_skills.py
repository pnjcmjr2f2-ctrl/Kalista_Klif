"""Shared skill budgets, persistent ranks and effective (never compounded) bonuses."""
from copy import deepcopy
import random
COSTS=(0,1,1,1,2,2,2,3,3,3)
PASSIVES=('double_flame','ash_lady','shadow_child','mana_reserve','ritual_black_flame','cold_calculation')

def spent(rank):return sum(COSTS[1:rank])
def rank(a):return a.get('skill_rank',1)
def factor(a):
    n=rank(a)-1
    kind=a.get('kind',a.get('action','damage'))
    if kind=='shield':return 1+.045*n
    if kind=='heal':return 1+.2*n
    name=a.get('name','')
    if name=='Скорострел':return 1+.015*n
    if name=='Мощный удар':return 1+.06*n
    if a.get('shared_attack'):return 1+.03*n
    if name=='Теневой укол':return 1+.20*n
    if a.get('area_shape')=='cone' or a.get('area_radius_m',0):return 1+.20*n
    return 1+.35*n

def hero(data,owner):return data if owner=='player' else data['ally']
def level(a):return (a.get('sheet_profile') or {}).get('level') or a.get('level') or 1
def entries(data,owner):
    a=hero(data,owner)
    result=[('spell:'+str(s['id']),s) for s in data['spells']] if owner=='player' else [('action:'+s['id'],s) for s in a.get('actions',[]) if not s.get('rule','').startswith('move_') and not s.get('needs_setup')]
    if owner=='player':result += [('passive:'+key,data['passives'][key]) for key in PASSIVES if key in data['passives']]
    return result

def sync_actor(actor,items):
    ledger=actor.setdefault('skill_ranks',{})
    if not isinstance(ledger,dict):raise ValueError('Повреждены ранги навыков')
    for key,r in ledger.items():
        if not isinstance(key,str) or isinstance(r,bool) or not isinstance(r,int) or not 1<=r<=10:raise ValueError('Ранг навыка должен быть от I до X')
    used=sum(spent(r) for r in ledger.values())
    if used>level(actor)//4:raise ValueError('Потрачено больше очков навыков, чем получено')
    actor['skill_points']=level(actor)//4-used
    for key,item in items:item['skill_rank']=ledger.get(key,1)

def initialize(data):
    for owner in ('player','ally'):sync_actor(hero(data,owner),entries(data,owner))
    for enemy in data['enemies']:
        sync_actor(enemy,[('action:'+a['id'],a) for a in enemy.get('actions',[]) if not a.get('rule','').startswith('move_')])

def upgrade(data,owner,key):
    if data['combat_active']:raise ValueError('Улучшение навыков доступно вне боя')
    initialize(data)
    actor=hero(data,owner);available=dict(entries(data,owner))
    if key not in available:raise ValueError('Способность больше не существует')
    r=rank(available[key])
    if r>=10:raise ValueError('Достигнут X ранг')
    if actor['skill_points']<COSTS[r]:raise ValueError('Недостаточно очков навыков')
    actor['skill_ranks'][key]=r+1;initialize(data)

def distribute(enemy):
    actions=[a for a in enemy['actions'] if not a.get('rule','').startswith('move_') and not a.get('needs_setup')]
    enemy['skill_ranks']={}
    budget=level(enemy)//4
    while True:
        choices=[a for a in actions if rank(a)<10 and COSTS[rank(a)]<=budget]
        if not choices:break
        weights=[3 if a['kind'] in ('heal','shield') and enemy.get('enemy_role')=='Лекарь' else 2 if a['kind']=='damage' else 1 for a in choices]
        chosen=random.choices(choices,weights=weights)[0];r=rank(chosen);budget-=COSTS[r];chosen['skill_rank']=r+1
        enemy['skill_ranks']['action:'+chosen['id']]=r+1
    sync_actor(enemy,[('action:'+a['id'],a) for a in actions])

def spell_damage(data,spell,dual=False,soul=False):
    from kalista_engine import spell_raw
    amount=spell_raw(spell['base']*factor(spell),data.get('spell_power',0))
    if dual:amount=round(amount*(1+.05+.01*(rank(data['passives']['double_flame'])-1)))
    if soul:amount=round(amount*(1+.40+.025*(rank(data['passives']['ritual_black_flame'])-1)))
    return amount

def details(a):
    r=rank(a);name=a.get('name','')
    if name=='Защитная стойка':return f'Снижение входящего урона: {30+r-1}%'
    if name=='Десница Ока':return f'Бонус урона: +{100+5*(r-1)}%'
    passive_rates={'Двойное пламя':(5,1),'Повелительница пепла':(30,1),'Дитя тени':(20,1),'Магический резерв':(50,2.5),'Ритуал Чёрного Пламени':(40,2.5),'Холодный расчёт':(10,.5)}
    if name in passive_rates:
        base,growth=passive_rates[name];return f'Бонус свойства: {base+growth*(r-1):g}%'
    if a.get('kind',a.get('action','damage')) in ('damage','heal','shield'):return f'Сила ×{factor(a):g}'
    return 'Усиление классового свойства'


def render(data,owner,path):
    import streamlit as st
    from pathlib import Path
    from kalista_storage import read_state,write_state
    import kalista_engine as e
    actor=hero(data,owner)
    st.info(f"Очки навыков: {actor.get('skill_points',0)} · 1 очко за каждые 4 уровня")
    for key,item in entries(data,owner):
        r=rank(item)
        with st.expander(f"{item['name']} · ранг {r}/10"):
            st.caption(details(item))
            if owner=='player' and key.startswith('spell:'):
                from kalista_view import show_spell_damage
                show_spell_damage(data,item)
            elif owner=='ally' and item.get('kind')=='damage':
                amount=e.action_amount(actor,item)*item.get('multiplier',1)
                st.caption(f"Урон: {round(amount)} × {item.get('hits',1)} до защиты цели")
            if r<10:
                following=deepcopy(item);following['skill_rank']=r+1
                st.caption(f'Следующий ранг: {details(following)} · цена {COSTS[r]} очк.')
                if owner=='player' and key.startswith('spell:') and item.get('action','damage')=='damage':st.caption(f'Урон следующего ранга: {spell_damage(data,following)} до защиты цели')
                if owner=='ally' and item.get('kind')=='damage':st.caption(f"Урон следующего ранга: {round(e.action_amount(actor,following)*item.get('multiplier',1))} × {item.get('hits',1)} до защиты")
            if st.button('Улучшить',key='skill_buy_'+owner+'_'+key,disabled=r>=10 or actor.get('skill_points',0)<(COSTS[r] if r<10 else 999) or data['combat_active']):
                try:
                    latest,revision=read_state(Path(path));latest=e.migrate(latest)
                    if hero(latest,owner)['skill_ranks']!=actor['skill_ranks']:raise ValueError('Ранги изменились; обнови страницу')
                    upgrade(latest,owner,key);e.recalc(latest)
                    revision=write_state(Path(path),latest,revision,e.migrate)
                    if st.session_state.get('_role')=='gm':
                        st.session_state['data']=latest;st.session_state['_committed_data']=deepcopy(latest);st.session_state['_save_revision']=revision
                    st.rerun()
                except (ValueError,OSError) as exc:st.error(str(exc))
    if st.session_state.get('_role')=='gm' and st.session_state.get('_edit_mode'):
        confirm=st.checkbox('Подтверждаю сброс рангов',key='skill_reset_confirm_'+owner)
        if st.button('Вернуть очки навыков',key='skill_reset_'+owner,disabled=not confirm or data['combat_active']):
            latest,revision=read_state(Path(path));latest=e.migrate(latest)
            if latest['combat_active']:st.error('Бой уже начался; сброс недоступен');return
            hero(latest,owner)['skill_ranks']={};initialize(latest)
            revision=write_state(Path(path),latest,revision,e.migrate)
            st.session_state['data']=latest;st.session_state['_committed_data']=deepcopy(latest);st.session_state['_save_revision']=revision;st.rerun()
