"""Read-only character views. Editing mode affects presentation, not permissions."""
import streamlit as st
import kalista_engine as e
from kalista_rarity import rarity_badge
from html import escape
from kalista_growth import effective_item

def editing():return bool(st.session_state.get('_edit_mode',False))

def show_stats(values):
    cols=st.columns(3)
    for i,(key,value) in enumerate(values):cols[i%3].metric(key,value)

def show_spell_damage(data,spell):
    kind=e.spell_action(spell)
    if kind=='damage':
        dual,soul=e.spell_bonuses(data,spell)
        damage=__import__('kalista_skills').spell_damage(data,spell,dual,soul)
        critical=round(damage*1.5)
        st.markdown(f"**Урон: {damage} · при крите: {critical}**")
        st.caption(f"База {spell['base']} · сила заклинаний +{data.get('spell_power',0)*100:g}% · до защиты цели"+(' · на каждую цель' if spell.get('area_radius_m') or spell.get('area_shape')=='cone' else ''))
        if spell['name']=='Теневой укол':st.caption('Чистый урон: броня и сопротивления не уменьшают; щит поглощает.')
        elif spell['school']=='Огонь+Тьма':st.caption(f"Огонь {damage/2:g} + Тьма {damage/2:g}; сопротивления считаются отдельно.")
        else:st.caption('Стихия: '+spell['school'])
        if dual or soul:st.caption('В расчёте активны: '+', '.join((['Двойное пламя'] if dual else [])+(['Ритуал Чёрного Пламени'] if soul else [])))
        from kalista_skills import rank
        sr=rank(spell);tier=int(sr>=5)+int(sr>=10);df=1+.2*(sr-1)
        if 'Огонь' in spell['school']:st.caption(f"Горение: {round(e.kalista_dot_damage(data,'burn')*df)} за тик × {3+tier}, шанс {50+10*tier}%; до сопротивления Огню.")
        if 'Тьма' in spell['school']:st.caption(f"Проклятие: {round(e.kalista_dot_damage(data,'curse')*df)} за тик × {3+tier}, шанс {50+10*tier}%; до сопротивления Тьме.")
    elif kind=='shield':
        value=e.shadow_shield_amount(data) if spell['name']=='Покров тьмы' else spell.get('effect_value',0)
        st.markdown(f'**Щит: {value}**')
    elif kind=='heal':st.markdown(f"**Лечение: {spell.get('effect_value',0)} HP**")


def show_book(actions,spells=False,data=None):
    for a in actions:
        if a.get('rule') in ('move_close','move_far','move_point'):continue
        with st.expander(a['name']+' · '+e.reach_label(a)):
            st.write(a.get('desc',a.get('description','')))
            if spells and data is not None:show_spell_damage(data,a)
            mana=a.get('mana',a.get('mana_cost',0));cd=a.get('cd_left',a.get('cooldown_left',0));maximum=a.get('cd_max',a.get('cooldown',0))
            st.caption(f'Мана {mana} · Перезарядка {cd}/{maximum}')
            if a.get('range_m') is not None:st.caption(f"Дальность {a['range_m']:g} м")
            if a.get('area_shape')=='cone':st.caption(f"Конус · длина {a['cone_length_m']:g} м · угол {a['cone_angle_deg']:g}° · от атакующего")
            elif a.get('area_radius_m',0):st.caption(f"Массовая атака · радиус {a['area_radius_m']:g} м · задевает всех в области")
            if a.get('kind','damage')=='damage':st.caption('Попаданий: '+str(a.get('hits',1)))
    st.caption('Применение — на странице «Бой». Настройка — в режиме редактирования.')

ROOT_BONUS_LABELS={'spell_power':'Сила заклинаний','armor':'Броня','attack':'Атака','int':'Интеллект','wis':'Мудрость','spi':'Дух','fire':'Огонь','dark':'Тьма','earth':'Земля','water':'Вода','air':'Воздух','light':'Свет'}
PERCENT_BONUSES={'Огонь','Тьма','Земля','Вода','Воздух','Свет','Шанс крита','Сила заклинаний'}

def bonus_values(item,root=False):
    current=effective_item(item,root)
    source=current if root else current.get('bonuses',{})
    result=[]
    for key,value in source.items():
        if root and key not in ROOT_BONUS_LABELS:continue
        if not isinstance(value,(int,float)) or isinstance(value,bool) or value==0:continue
        label=ROOT_BONUS_LABELS[key] if root else key
        value_text=f"{value:+g}".replace('.',',')+('%' if label in PERCENT_BONUSES else '')
        result.append((label,value_text))
    return result


def show_gear(item,root=False):
    if not item.get('name'):
        st.caption('Ячейка свободна')
        return
    st.markdown(rarity_badge(item),unsafe_allow_html=True)
    if item.get('growth'):
        growth=item['growth'];owner='Калисте' if growth['owner']=='player' else 'Шеогарату'
        st.caption(f"Привязано к {owner} · +2% исходных бонусов за уровень · исходный уровень {growth['anchor_level']}")
    description=item.get('description',item.get('desc',''))
    if description:st.write(description)
    values=bonus_values(item,root)
    if values:
        html=''.join(f'<div class="stat-tile"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>' for label,value in values)
        st.markdown('<div class="stat-grid">'+html+'</div>',unsafe_allow_html=True)
    else:st.caption('Без числовых бонусов')
    if item.get('growth'):
        with st.expander('Рост легендарного предмета · исходные → текущие'):
            baseline=dict(bonus_values({k:v for k,v in item.items() if k!='growth'},root))
            current=dict(values)
            for label,base in baseline.items():st.caption(label+': '+base+' → '+current.get(label,base))


def gear_summary(item,root=False):
    if not item.get('name'):
        st.caption('Свободная ячейка');return
    priority=['Сила заклинаний','Атака','Броня','Интеллект','Сила','Выносливость']
    values=sorted(bonus_values(item,root),key=lambda pair:priority.index(pair[0]) if pair[0] in priority else len(priority))
    brief=' · '.join(label+' '+value for label,value in values[:4]) or 'Без числовых бонусов'
    extra=f'<small>Ещё свойств: {len(values)-4}</small>' if len(values)>4 else ''
    st.markdown('<div class="gear-summary"><strong>'+escape(item['name'])+'</strong>'+rarity_badge(item)+'<small>'+escape(brief)+'</small>'+extra+'</div>',unsafe_allow_html=True)


def inventory_details(item):
    use=item.get('use')
    if use:st.caption({'heal':'Лечение','mana':'Восстановление маны','shield':'Щит'}.get(use['kind'],'Эффект')+': +'+str(use['value']))
    if item.get('desc'):
        with st.expander('Описание предмета'):
            st.write(item['desc'])


def show_comparison(data,item,owner,loot=False):
    from kalista_compare import preview_equipment
    try:preview=preview_equipment(data,item,owner,loot)
    except ValueError as exc:st.caption(str(exc));return
    st.caption('При надевании · '+preview['slot'].replace(' (посох)','')+' · вместо: '+(', '.join(preview['replaces']) or 'свободной ячейки'))
    st.caption('Итоговые показатели персонажа: сейчас → после надевания. Текущие HP и мана не восстанавливаются.')
    if not preview['rows']:st.caption('Числовые показатели не изменятся');return
    rows=[]
    for label,before,after in preview['rows']:
        percent=label in PERCENT_BONUSES or label=='Уклонение'
        unit='%' if percent else ''
        delta=after-before
        delta_text=f"{delta:+.2f}".rstrip('0').rstrip('.').replace('.',',')+(' п.п.' if percent else '')
        text=lambda value:f"{value:.2f}".rstrip('0').rstrip('.').replace('.',',')+unit
        rows.append(f'<div class="gear-change"><span>{escape(label)}</span><strong>{text(before)} → {text(after)}</strong><span>{delta_text}</span></div>')
    st.markdown('<div class="gear-comparison">'+''.join(rows)+'</div>',unsafe_allow_html=True)


def show_text_value(value):
    if isinstance(value,dict):
        labels={'xp':'Опыт','gold':'Золото','silver':'Серебро','copper':'Медь','name':'Название','description':'Описание','desc':'Описание','items':'Предметы','qty':'Количество'}
        for key,entry in value.items():
            if key in ('id','source','source_id'):continue
            if key in labels:st.caption(labels[key])
            show_text_value(entry)
    elif isinstance(value,(list,tuple)):
        for entry in value:show_text_value(entry)
    elif value is not None:st.write(str(value))


def player_view(section,data,root,commit):
    if editing() or section in ('Обзор','Бой','Кубики','Сцена'):return False
    a=data['ally'];p=a['sheet_profile'];st.subheader(section)
    selected=st.selectbox('Редкость предметов',['Все']+list(e.RARITIES),key='ps_view_rarity_'+section) if section in ('Снаряжение','Инвентарь') else 'Все'
    if section=='Характеристики':
        show_stats(p['stats'].items());st.caption(f"Уровень {p['level']} · Свободные очки {p['free_points']}")
        show_stats([('Броня',a['armor']),('Атака',p['attack']),('Критический урон',p['critical_damage']),('Шанс крита',str(p['critical_chance'])+'%'),('Уклонение',f"{e.evasion_chance(a)*100:.1f}%"),('Сила заклинаний',f"+{a.get('spell_power',0)*100:g}%")])
        with st.expander('Сопротивления'):show_stats([(x,str(e.effective_defense(a,x))+'%') for x in e.ELEMENTS])
        with st.expander('Расовые и классовые способности'):st.write(p['abilities'])
    elif section=='Заклинания и способности':show_book(a['actions'])
    elif section=='Снаряжение':
        from kalista_player_model import EQUIPMENT_SLOTS
        with st.container(key='equipment_cards_ally'):
            columns=st.columns(2)
        for slot_index,slot in enumerate(EQUIPMENT_SLOTS):
            items=[x for x in p['equipment'] if x['equipped'] and x['slot']==slot and (selected=='Все' or x.get('rarity','Обычный')==selected)]
            if selected!='Все' and not items:continue
            with columns[slot_index%2]:
                with st.container(border=True):
                    st.caption(slot)
                    if not items:st.caption('Свободная ячейка')
                    for x in items:
                        gear_summary(x)
                        with st.expander('Все свойства · '+x['name']):show_gear(x)
        with st.expander('Резерв'):
            from copy import deepcopy
            from kalista_player_model import sheet_snapshot
            for x in p['equipment']:
                if not x['equipped'] and (selected=='Все' or x.get('rarity','Обычный')==selected):
                    gear_summary(x)
                    with st.expander('Свойства и сравнение · '+x['name']):
                        show_gear(x);show_comparison(data,x,'ally')
                    if x['slot'] in EQUIPMENT_SLOTS and st.button('Надеть',key='ps_reserve_equip_'+x['id']):
                        expected=sheet_snapshot(data,'equipment');values=deepcopy(expected)
                        for old in values:
                            if old['slot']==x['slot']:old['equipped']=old['id']==x['id']
                        commit(root,'equipment',values,expected)
    elif section=='Инвентарь':
        from kalista_player_model import sheet_snapshot
        st.caption(f"Золото {p['currency']['gold']} · Серебро {p['currency']['silver']} · Медь {p['currency']['copper']}")
        expected=sheet_snapshot(data,'inventory')
        for x in p['inventory']:
            if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
            with st.container(border=True):
                cols=st.columns([4,1]);cols[0].write(f"**{x['name']}** × {x['qty']}")
                cols[0].markdown(rarity_badge(x),unsafe_allow_html=True)
                inventory_details(x)
                if x.get('use') and cols[1].button('Применить',key='ps_view_use_'+x['id'],disabled=x['qty']<=0 or x['use']['value']<=0):commit(root,'inventory',None,expected,x['id'])
    elif section=='Квесты':
        for x in p['quests']:
            with st.expander(x['name']+' · '+x['status']):
                from kalista_quest_ui import show_quest
                show_quest(x)
    elif section=='Заметки':st.write(p['notes'] or 'Заметок пока нет')
    elif section=='Биография':st.write(p['biography'] or 'Биография пока не заполнена')
    else:return False
    return True

def gm_view(page,data,apply_item,apply_special=None,apply_equip=None,persist=None):
    if editing() or page not in ('Экипировка','Инвентарь','Характеристики','Заклинания','Квесты','Ведущий'):return False
    st.subheader(page)
    selected=st.selectbox('Редкость предметов',['Все']+list(e.RARITIES),key='root_view_rarity_'+page) if page in ('Экипировка','Инвентарь') else 'Все'
    if page=='Заклинания':show_book(data['spells'],True,data)
    elif page=='Характеристики':
        show_stats([(n,e.total_stat(data,n)) for n in data['base_stats']]);st.caption(f"Уровень {data['level']} · Свободные очки {data['free_points']}")
        show_stats([('Броня',data['armor']),('Сила заклинаний',f"+{data['spell_power']*100:.0f}%"),('Инициатива',data['initiative'])])
        with st.expander('Сопротивления'):show_stats([(x,str(e.effective_defense(data,x))+'%') for x in e.ELEMENTS])
        with st.expander('Способности'):
            for key,x in data['passives'].items():
                st.write(x['name']+' — '+x['desc'])
                if x.get('type')=='special' and apply_special:
                    allowed,reason=e.special_availability(data,key)
                    if st.button('Использовать',key='view_special_'+key,disabled=not allowed):apply_special(key)
                    if not allowed:st.caption(reason)
    elif page=='Экипировка':
        with st.container(key='equipment_cards_root'):
            columns=st.columns(2)
        for slot_index,(slot,x) in enumerate(data['equipment'].items()):
            if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
            with columns[slot_index%2]:
                with st.container(border=True):
                    st.caption(slot.replace(' (посох)',''))
                    gear_summary(x,root=True)
                    if x['name']:
                        with st.expander('Все свойства · '+x['name']):show_gear(x,root=True)
        with st.expander('Резерв'):
            for x in data.get('equipment_reserve',[]):
                if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
                gear_summary(x,root=True)
                with st.expander('Свойства и сравнение · '+x['name']):
                    show_gear(x,root=True);show_comparison(data,x,'player')
                if apply_equip and st.button('Надеть',key='root_reserve_equip_'+x['id']):apply_equip(x['id'])
    elif page=='Инвентарь':
        st.caption(f"Золото {data['gold']} · Серебро {data['silver']} · Медь {data['copper']}")
        for i,x in enumerate(data['inventory']):
            if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
            with st.container(border=True):
                cols=st.columns([4,1]);cols[0].write(f"**{x['name']}** × {x['qty']}")
                cols[0].markdown(rarity_badge(x),unsafe_allow_html=True)
                inventory_details(x)
                if x.get('use') and cols[1].button('Применить',key='view_use_'+str(i),disabled=x['qty']<=0 or x['use']['value']<=0):apply_item(x)
    elif page=='Квесты':
        from kalista_quest_ui import render_root
        render_root(data,editable=False)
    elif page=='Ведущий':
        section=st.radio('Раздел ведущего',['Сцены','NPC','Карты','Записная книжка'],key='gm_section',horizontal=True,label_visibility='collapsed')
        if section=='Карты':
            from kalista_map_library_ui import render_map_hub
            render_map_hub(data,persist);return True
        from kalista_map_library_ui import render_scene_map
        render_scene_map(data,'gm_scene_location')
        for x in data.get('scenes',[]):
            with st.expander(x['name']+' · '+x['status']):st.write(x.get('summary',''));st.write(x.get('gm_notes',''))
        with st.expander('NPC'):
            for x in data.get('npcs',[]):st.write(x['name']+' · '+x.get('description',''))
        with st.expander('Заметки ведущего'):st.write(data.get('gm_notes',''))
        st.caption('Сцены, NPC и снимки сохранений настраиваются в режиме редактирования.')
    return True
