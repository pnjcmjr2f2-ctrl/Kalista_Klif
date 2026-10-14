"""GM-only map library and explicit two-point calibration."""
import streamlit as st
import hashlib
from kalista_map_background import catalog,background,calibration,assign_map,map_id,scene_key,ROOT
from kalista_interactive_map import calibrate_map

def render_library(data,persist,selected_id=None):
    maps=[m for m in catalog() if (ROOT/(m["id"]+".webp")).exists()]
    if not maps:
        st.info('Карты ещё не добавлены в библиотеку.');return
    by_id={m['id']:m for m in maps}
    with st.expander('Фон локации и масштаб · ведущий'):
        st.caption('Настройки сохраняются отдельно для каждой карты. Ориентир: 5 м на клетку. Метры задаются только после калибровки.')
        options=list(by_id);current=map_id(data)
        ident=selected_id if selected_id in by_id else st.selectbox('Карта из библиотеки',options,index=options.index(current) if current in options else 0,format_func=lambda i:by_id[i]['name'],key='map_library_choice')
        item=by_id[ident];cfg=data['battle_maps']['calibrations'].get(ident)
        st.caption(f"Изображение: {item['width']} × {item['height']} пикселей · пропорции сохранены")
        if cfg:
            st.success(f"Масштаб задан: вся карта {item['width']*cfg['metres_per_pixel']:.1f} × {item['height']*cfg['metres_per_pixel']:.1f} м")
            st.caption(f"Контрольный отрезок: {cfg['distance_m']:g} м. Приближение и размер экрана не меняют расстояния.")
        else:st.warning('Масштаб пока не задан. Этот фон нельзя включить для боя.')
        with st.expander('Калибровка масштаба',expanded=not cfg):
            st.caption('Отметь две точки на картинке. Для сетки лучше взять 10 клеток = 50 м. Без сетки задай известное расстояние. Третье касание начинает новый отрезок.')
            pair=calibrate_map(data,ident,'calibrate_'+ident)
            distance=st.number_input('Расстояние между точками (м)',min_value=.01,max_value=100000.,value=50.,step=5.,key='calibrate_distance_'+ident)
            if pair:
                st.caption('Две точки выбраны. Перед сохранением проверь, что отрезок проходит по нужным ориентирам.')
            if st.button('Сохранить масштаб',key='save_scale_'+ident,disabled=not pair or bool(data['combat_active'])):
                try:
                    if data['combat_active']:raise ValueError('Менять масштаб можно после завершения боя')
                    data['battle_maps']['calibrations'][ident]=calibration(pair[0],pair[1],distance,item['width'],item['height'])
                    data['map_revision']=data.get('map_revision',0)+1
                    from kalista_engine import invalidate_player_requests
                    invalidate_player_requests(data,'Масштаб изменился; предложи действие заново')
                    persist('Калибровка карты: '+item['name'])
                except ValueError as exc:st.error(str(exc))
        if data['combat_active']:st.caption('Фон и масштаб доступны для изменения после завершения боя.')
        active_label='Назначена текущей сцене' if current==ident else 'Показать в текущей сцене'
        if st.button(active_label,key='assign_map_'+ident,disabled=not cfg or current==ident or bool(data['combat_active']),use_container_width=True):
            assign_map(data,ident);persist('Фон карты: '+item['name'])
        if current and st.button('Убрать фон',key='clear_map_background',disabled=bool(data['combat_active'])):
            assign_map(data,'');persist('Фон карты убран')
        st.caption('Расстановка сохраняется для сочетания сцены и карты. После первого включения расставь фигурки на нужных местах. Преграды учитываются после разметки ведущим в настройках карты.')


def render_scene_map(data,key='scene_location'):
    from kalista_map_background import ROOT
    from kalista_interactive_map import view_location
    assignments=data.get('battle_maps',{}).get('scene_displays',{})
    ident=assignments.get(scene_key(data),assignments.get('_world',''))
    item=next((x for x in catalog() if x['id']==ident),None)
    if item and (ROOT/(ident+'.webp')).exists():
        st.markdown('**'+data['battle_maps'].get('metadata',{}).get(ident,{}).get('name',item['name'])+'**')
        view_location(data,ident,key)
        if item.get('author'):st.caption(item['author']+' · '+item.get('license',''))


def render_map_hub(data,persist):
    from kalista_map_background import ROOT
    from kalista_interactive_map import view_location
    from kalista_view import editing
    maps=[x for x in catalog() if (ROOT/(x['id']+'.webp')).exists()]
    if not maps:st.info('Библиотека пока пуста. Добавь карты в components/tactical_map/maps.');return
    st.markdown('### Библиотека карт')
    category=st.selectbox('Вид карты',['Все','Боевая','Город','Регион','Мир'],key='hub_category')
    query=st.text_input('Найти карту',key='hub_search')
    meta=data['battle_maps'].setdefault('metadata',{})
    filtered=[x for x in maps if (category=='Все' or meta.get(x['id'],{}).get('category',x.get('category','Боевая'))==category) and query.casefold() in meta.get(x['id'],{}).get('name',x['name']).casefold()]
    if not filtered:st.caption('Нет карт по этому фильтру.');return
    options={x['id']:x for x in filtered}
    widget_key='hub_map_'+hashlib.sha256((category+'|'+query).encode()).hexdigest()[:10]
    preferred=st.session_state.get('hub_map')
    default=preferred if preferred in options else next(iter(options))
    if st.session_state.get(widget_key) not in options:st.session_state[widget_key]=default
    ident=st.selectbox('Карта',list(options),format_func=lambda i:meta.get(i,{}).get('name',options[i]['name']),key=widget_key)
    st.session_state['hub_map']=ident
    item=options[ident];view_location(data,ident,'hub_view_'+ident)
    cfg=data['battle_maps']['calibrations'].get(ident)
    st.caption('Масштаб: '+(f"{cfg['metres_per_pixel']:.5g} м/пиксель" if cfg else 'не задан; просмотр доступен, боевые расстояния не назначены'))
    if item.get('source_url'):st.markdown('Автор: '+item.get('author','')+' · ['+item.get('license','Источник')+']('+item['source_url']+')')
    scenes={'_table':'Текущий стол без сцены',**{x['id']:x['name'] for x in data.get('scenes',[])}}
    current=scene_key(data)
    if current not in scenes:scenes[current]='Текущая сцена'
    target=st.selectbox('Показать в сцене',list(scenes),index=list(scenes).index(current),format_func=lambda k:scenes[k],key='hub_scene')
    left,right=st.columns(2)
    if left.button('Показать карту в сцене',key='hub_show_scene',use_container_width=True):
        data['battle_maps'].setdefault('scene_displays',{})[target]=ident;persist('Карта сцены: '+item['name'])
    if right.button('Сделать картой мира',key='hub_show_world',use_container_width=True):
        data['battle_maps'].setdefault('scene_displays',{})['_world']=ident;persist('Карта мира: '+item['name'])
    displays=data['battle_maps'].get('scene_displays',{})
    if displays.get(target) and st.button('Убрать карту выбранной сцены',key='hub_hide_scene'):
        displays.pop(target);persist('Карта сцены убрана')
    if displays.get('_world') and st.button('Убрать карту мира',key='hub_hide_world'):
        displays.pop('_world');persist('Карта мира убрана')
    if st.button('Использовать в бою текущей сцены',key='hub_to_battle',disabled=not cfg or bool(data['combat_active']) or map_id(data)==ident,use_container_width=True):
        assign_map(data,ident);persist('Боевая карта: '+item['name'])
    st.caption('Карта сцены и мира служит для обзора. Боевой фон назначается отдельно и требует калибровки. Во время боя фон и масштаб заблокированы.')
    if editing():
        with st.form('hub_meta_'+ident):
            info=meta.get(ident,{})
            name=st.text_input('Название карты',value=info.get('name',item['name']))
            cats=['Боевая','Город','Регион','Мир'];kind=st.selectbox('Категория',cats,index=cats.index(info.get('category',item.get('category','Боевая'))))
            note=st.text_area('Заметки о карте',value=info.get('note',''))
            if st.form_submit_button('Сохранить настройки карты'):
                meta[ident]=dict(name=name or item['name'],category=kind,note=note);persist('Настройки карты')
        render_library(data,persist,selected_id=ident)
        if map_id(data)==ident:
            from kalista_obstacle_ui import render_obstacles
            render_obstacles(data,persist)
        else:st.caption('Для разметки преград назначь эту карту боевым фоном.')
