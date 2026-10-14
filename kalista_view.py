"""Read-only character views. Editing mode affects presentation, not permissions."""
import streamlit as st
import kalista_engine as e
from kalista_rarity import rarity_label,rarity_badge
from html import escape
from kalista_growth import effective_item

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
        for slot in EQUIPMENT_SLOTS:
            items=[x for x in p['equipment'] if x['equipped'] and x['slot']==slot and (selected=='Все' or x.get('rarity','Обычный')==selected)]
            if selected!='Все' and not items:continue
            with st.expander(slot+': '+(', '.join(x['name'] for x in items) or '—')):
                for x in items:show_gear(x)
        with st.expander('Резерв'):
            from copy import deepcopy
            from kalista_player_model import sheet_snapshot
            for x in p['equipment']:
                if not x['equipped'] and (selected=='Все' or x.get('rarity','Обычный')==selected):
                    st.write(x['name']+' · '+rarity_label(x))
                    show_gear(x)
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
            with st.expander(slot.replace(' (посох)','')+': '+(x['name'] or '—')):show_gear(x,root=True)
        with st.expander('Резерв'):
            for x in data.get('equipment_reserve',[]):
                if selected!='Все' and x.get('rarity','Обычный')!=selected:continue
                st.write(x['name']);show_gear(x,root=True)
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
                with st.expander(x.get('name','Квест')):
                    if x.get('status'):st.caption(x['status'])
                    for key in ('desc','tasks','notes','reward','rewards','description'):
                        if x.get(key):show_text_value(x[key])
    elif page=='Ведущий':
        for x in data.get('scenes',[]):
            with st.expander(x['name']+' · '+x['status']):st.write(x.get('summary',''));st.write(x.get('gm_notes',''))
        with st.expander('NPC'):
            for x in data.get('npcs',[]):st.write(x['name']+' · '+x.get('description',''))
        with st.expander('Заметки ведущего'):st.write(data.get('gm_notes',''))
        st.caption('Сцены, NPC и снимки сохранений настраиваются в режиме редактирования.')
    return True
