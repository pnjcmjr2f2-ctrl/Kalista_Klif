"""Developer-only map wall editor, with two world-coordinate clicks."""
import streamlit as st
from uuid import uuid4
from kalista_obstacles import walls,key
from kalista_interactive_map import draw_wall

def render_obstacles(data,persist):
    with st.expander('Преграды карты · настройка'):
        st.caption('Две точки задают отрезок стены. Дверь оставляй разрывом; касание стены тоже блокирует путь. Разметка сохраняется для этой карты. Проверки в бою автоматические.')
        pair=draw_wall(data,'wall_editor')
        with st.form('add_wall'):
            name=st.text_input('Название преграды',value='Стена')
            movement=st.checkbox('Блокирует движение',value=True)
            attacks=st.checkbox('Блокирует атаки',value=True)
            if st.form_submit_button('Добавить преграду'):
                if not pair:st.error('Выбери две разные точки на карте')
                elif not movement and not attacks:st.error('Выбери, что блокирует преграда')
                else:
                    data['battle_maps'].setdefault('obstacles',{}).setdefault(key(data),[]).append(dict(id=uuid4().hex,name=name,first=pair[0],second=pair[1],movement=movement,attacks=attacks))
                    data['map_revision']+=1;persist('Преграда карты')
        for w in walls(data):
            left,right=st.columns([4,1]);left.caption(w['name']+' · '+('движение ' if w['movement'] else '')+('атаки' if w['attacks'] else ''))
            if right.button('Удалить',key='wall_remove_'+w['id']):
                data['battle_maps']['obstacles'][key(data)]=[x for x in walls(data) if x['id']!=w['id']]
                data['map_revision']+=1;persist('Удаление преграды')
