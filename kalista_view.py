"""Read-only character views. Editing mode affects presentation, not permissions."""
import streamlit as st
import kalista_engine as e
from kalista_rarity import rarity_label,rarity_badge

def editing():return bool(st.session_state.get('_edit_mode',False))

def show_stats(values):
    cols=st.columns(3)
    for i,(key,value) in enumerate(values):cols[i%3].metric(key,value)

def show_book(actions,spells=False):
    for a in actions:
        if a.get('rule') in ('move_close','move_far'):continue
        with st.expander(a['name']+' · '+e.reach_label(a)):
            st.write(a.get('desc',a.get('description','')))
            mana=a.get('mana',a.get('mana_cost',0));cd=a.get('cd_left',a.get('cooldown_left',0));maximum=a.get('cd_max',a.get('cooldown',0))
            st.caption(f'Мана {mana} · Перезарядка {cd}/{maximum}')
            if a.get('kind','damage')=='damage':st.caption('Попаданий: '+str(a.get('hits',1)))
    st.caption('Применение — на странице «Бой». Настройка — в режиме редактирования.')

def player_view(section,data,root,commit):
    if editing() or section in ('Обзор','Бой','Кубики','Сцена'):return False
    a=data['ally'];p=a['sheet_profile'];st.subheader(section)
    selected=st.selectbox('Редкость предметов',['Все']+list(e.RARITIES),key='ps_view_rarity_'+section) if section in ('Снаряжение','Инвентарь') else 'Все'
    if section=='Характеристики':
        show_stats(p['stats'].items());st.caption(f"Уровень {p['level']} · Свободные очки {p['free_points']}")
        show_stats([('Броня',a['armor']),('Атака',p['attack']),('Критический урон',p['critical_damage']),('Шанс крита',str(p['critical_chance'])+'%')])
        with st.expander('Сопротивления'):show_stats([(x,str(e.effective_defense(a,x))+'%') for x in e.ELEMENTS])
        with st.expander('Расовые и классовые способности'):st.write(p['abilities'])
    elif section=='Заклинания и способности':show_book(a['actions'])
    elif section=='Снаряжение':
        from kalista_player_model import EQUIPMENT_SLOTS
        for slot in EQUIPMENT_SLOTS:
            items=[x for x in p['equipment'] if x['equipped'] and x['slot']==slot and (selected=='Все' or x.get('rarity','Обычный')==selected)]
            if selected!='Все' and not items:continue
            with st.expander(slot+': '+(', '.join(x['name'] for x in items) or '—')):
                for x in items:st.markdown(rarity_badge(x),unsafe_allow_html=True);st.write(x['description']);st.write({k:v for k,v in x['bonuses'].items() if v})
        with st.expander('Резерв'):
            from copy import deepcopy
            from kalista_player_model import sheet_snapshot
            for x in p['equipment']:
                if not x['equipped'] and (selected=='Все' or x.get('rarity','Обычный')==selected):
                    st.write(x['name']+' · '+rarity_label(x))
                    st.caption(x['description'])
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
            cols=st.columns([4,1]);cols[0].write(f"**{x['name']}** × {x['qty']}")
            cols[0].markdown(rarity_badge(x),unsafe_allow_html=True)
            if x['desc']:cols[0].caption(x['desc'])
            if x.get('use') and cols[1].button('Применить',key='ps_view_use_'+x['id'],disabled=x['qty']<=0 or x['use']['value']<=0):commit(root,'inventory',None,expected,x['id'])
    elif section=='Квесты':
        for x in p['quests']:
            with st.expander(x['name']+' · '+x['status']):st.write(x['desc'])
    elif section=='Заметки':st.write(p['notes'] or 'Заметок пока нет')
    elif section=='Биография':st.write(p['biography'] or 'Биография пока не заполнена')
    else:return False
    return True

def gm_view(page,data,apply_item,apply_special=None,apply_equip=None):
    if editing() or page not in ('Экипировка','Инвентарь','Характеристики','Заклинания','Квесты','Ведущий'):return False
    st.subheader(page)
    selected=st.selectbox('Редкость предметов',['Все']+list(e.RARITIES),key='root_view_rarity_'+page) if page in ('Экипировка','Инвентарь') else 'Все'
    if page=='Заклинания':show_book(data['spells'],True)
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
        for slot,x in data['equipment'].items():
            if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
            with st.expander(slot+': '+(x['name'] or '—')):st.markdown(rarity_badge(x),unsafe_allow_html=True);st.write({k:v for k,v in x.items() if k!='name' and v})
        with st.expander('Резерв'):
            for x in data.get('equipment_reserve',[]):
                if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
                st.write(x['name']+' · '+rarity_label(x));st.caption(x.get('description',''))
                if apply_equip and st.button('Надеть',key='root_reserve_equip_'+x['id']):apply_equip(x['id'])
    elif page=='Инвентарь':
        st.caption(f"Золото {data['gold']} · Серебро {data['silver']} · Медь {data['copper']}")
        for i,x in enumerate(data['inventory']):
            if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
            cols=st.columns([4,1]);cols[0].write(f"**{x['name']}** × {x['qty']}")
            cols[0].markdown(rarity_badge(x),unsafe_allow_html=True)
            if x.get('desc'):cols[0].caption(x['desc'])
            if x.get('use') and cols[1].button('Применить',key='view_use_'+str(i),disabled=x['qty']<=0 or x['use']['value']<=0):apply_item(x)
    elif page=='Квесты':
        for x in data.get('quests',[]):
            if isinstance(x,dict):
                with st.expander(x.get('name','Квест')):st.write(x)
    elif page=='Ведущий':
        for x in data.get('scenes',[]):
            with st.expander(x['name']+' · '+x['status']):st.write(x.get('summary',''));st.write(x.get('gm_notes',''))
        with st.expander('NPC'):
            for x in data.get('npcs',[]):st.write(x['name']+' · '+x.get('description',''))
        with st.expander('Заметки ведущего'):st.write(data.get('gm_notes',''))
        st.caption('Сцены, NPC и снимки сохранений настраиваются в режиме редактирования.')
    return True
