"""Master-only enemy loadout settings; gameplay uses the common action panel."""
import streamlit as st
from kalista_enemies import ROLES, RACES, suggested_role, apply_loadout


def render_enemy_setup(data, token, persist):
    from kalista_engine import participant, validate_action_state, ELEMENTS
    from copy import deepcopy
    target=participant(data,token)
    with st.expander('Раса, класс и готовый набор способностей'):
        st.caption('Шаблон заменяет способности, сохраняя HP, броню, сопротивления и награду. Числа можно изменить в редакторе действий. Во время боя замена заблокирована.')
        with st.form('enemy_loadout_'+token):
            race=st.selectbox('Раса / вид',RACES,index=RACES.index(target.get('race')) if target.get('race') in RACES else 0)
            role=st.selectbox('Класс / боевой шаблон',ROLES,index=ROLES.index(target.get('enemy_role',suggested_role(target['name']))))
            schools=['По классу']+ELEMENTS
            element=st.selectbox('Стихия магии',schools,index=schools.index(target.get('magic_element','По классу')))
            bloodless=st.checkbox('Нет крови — иммунитет к кровотечению',value=target.get('bloodless',False))
            crit=st.number_input('Автоматический шанс крита (%)',min_value=0.,max_value=95.,value=float(target.get('critical_chance',0)))
            multiplier=st.number_input('Множитель критического урона',min_value=1.,max_value=10.,value=float(target.get('critical_multiplier',2)))
            mana=st.number_input('Максимум маны',min_value=0,value=int(target.get('mana_max',0)))
            replace=st.checkbox('Заменить способности выбранным шаблоном')
            if st.form_submit_button('Сохранить врага',disabled=bool(data['combat_active'])):
                candidate=deepcopy(data);enemy=participant(candidate,token)
                enemy.update(race=race,enemy_role=role,magic_element=element,bloodless=bloodless,critical_chance=crit,critical_multiplier=multiplier,mana_max=mana,mana_current=min(mana,enemy.get('mana_current',mana)))
                if replace:apply_loadout(enemy,role)
                enemy['bloodless']=bloodless or race in ('Скелет','Лич')
                validate_action_state(candidate);data.clear();data.update(candidate);persist('Настроен враг')
