"""Area editors are called only from developer-mode editor flows."""
from copy import deepcopy
import streamlit as st
from kalista_shapes import validate_shape

def edit_shape(ability,prefix,standalone=False):
    original={k:ability.get(k,default) for k,default in [('area_shape','circle'),('cone_length_m',0.),('cone_angle_deg',60.)]}
    def fields():
        shape=st.selectbox('Форма области',['circle','cone'],index=['circle','cone'].index(original['area_shape']),format_func=lambda s:'Круг' if s=='circle' else 'Конус от атакующего',key=prefix+'_shape')
        length=st.number_input('Длина конуса (м)',min_value=0.,max_value=100000.,value=float(original['cone_length_m']),key=prefix+'_length')
        angle=st.number_input('Полный угол конуса (°)',min_value=1.,max_value=180.,value=float(original['cone_angle_deg']),key=prefix+'_angle')
        st.caption('Для конуса задай длину больше 0. Направление выбирается на карте, вершина всегда у атакующего. Длина ограничивает расстояние до цели, дальний край — дуга. Атакующего не задевает; союзников задевает. Дальность и радиус круга при конусе не используются.')
        return dict(area_shape=shape,cone_length_m=length,cone_angle_deg=angle)
    with st.expander('Форма массовой атаки · настройки'):
        if standalone:
            with st.form(prefix+'_form'):
                values=fields()
                if st.form_submit_button('Сохранить форму области',key=prefix+'_save'):
                    candidate=deepcopy(ability);candidate.update(values)
                    try:validate_shape(candidate)
                    except ValueError as exc:st.error(str(exc))
                    else:return values
            return original
        return fields()
