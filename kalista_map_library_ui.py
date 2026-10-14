"""GM-only map library and explicit two-point calibration."""
import streamlit as st
from kalista_map_background import catalog,background,calibration,assign_map,map_id,scene_key
from kalista_interactive_map import calibrate_map

def render_library(data,persist):
    maps=catalog()
    if not maps:
        st.info('Карты ещё не добавлены в библиотеку.');return
    by_id={m['id']:m for m in maps}
    with st.expander('Фон локации и масштаб · ведущий'):
        st.caption('Настройки сохраняются отдельно для каждой карты. Ориентир: 5 м на клетку. Метры задаются только после калибровки.')
        options=list(by_id);current=map_id(data)
        ident=st.selectbox('Карта из библиотеки',options,index=options.index(current) if current in options else 0,format_func=lambda i:by_id[i]['name'],key='map_library_choice')
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
        st.caption('Расстановка сохраняется для сочетания сцены и карты. После первого включения расставь фигурки на нужных местах. Стены на изображении пока не ограничивают движение и атаки.')
