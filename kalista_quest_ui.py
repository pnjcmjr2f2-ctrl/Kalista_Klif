"""Readable quest cards and explicit forms; rewards are notes, never auto payouts."""
import streamlit as st
from kalista_quests import description,reward,as_text,STATUSES

def show_quest(q):
    st.caption(q.get('status','Статус не указан'))
    st.markdown(description(q) or 'Описание пока не заполнено.')
    for field,label in (('tasks','Дополнительные задачи'),('objectives','Цели'),('notes','Заметки')):
        if q.get(field):st.markdown('**'+label+'**');st.write(as_text(q[field]))
    st.markdown('**Награда**')
    st.write(reward(q) or 'Награда пока не указана ведущим.')

def render_root(data,persist=None,editable=False):
    if not data.get('quests'):st.caption('Квестов пока нет.')
    for i,q in enumerate(list(data.get('quests',[]))):
        key='quest_'+str(q.get('id',i))
        with st.container(border=True):
            st.subheader(q.get('name') or 'Без названия')
            show_quest(q)
            if editable:
                with st.expander('Изменить квест',expanded=False):
                    with st.form(key):
                        name=st.text_input('Название квеста',value=q['name'],key=key+'_name')
                        status=st.selectbox('Статус квеста',STATUSES,index=STATUSES.index(q.get('status')) if q.get('status') in STATUSES else 0,key=key+'_status')
                        desc=st.text_area('Описание и условия завершения',value=description(q),height=230,key=key+'_desc')
                        rewards=st.text_area('Награда за квест',value=reward(q),key=key+'_reward')
                        if st.form_submit_button('Сохранить квест'):
                            if not name.strip():st.error('Укажи название квеста.')
                            else:
                                q.update(name=name.strip(),status=status,desc=desc)
                                if rewards!=reward(q):q['reward']=rewards
                                persist('Изменён квест: '+q['name'])
                    if st.button('Удалить квест',key=key+'_delete'):
                        data['quests'].remove(q);persist('Удалён квест: '+q['name'])
    if editable:
        with st.expander('Новый квест'):
            with st.form('aq'):
                name=st.text_input('Название квеста',key='new_quest_name')
                status=st.selectbox('Статус квеста',STATUSES,key='new_quest_status')
                desc=st.text_area('Описание и условия завершения',key='new_quest_desc')
                rewards=st.text_area('Награда за квест',key='new_quest_reward')
                if st.form_submit_button('Добавить квест'):
                    if not name.strip():st.error('Укажи название квеста.')
                    else:
                        nid=max((x.get('id',0) for x in data.get('quests',[]) if isinstance(x.get('id'),int)),default=0)+1
                        data.setdefault('quests',[]).append(dict(id=nid,name=name.strip(),status=status,desc=desc,reward=rewards));persist('Добавлен квест: '+name.strip())
        with st.form('quest_notes'):
            notes=st.text_area('Личные заметки',value=data.get('notes',''),key='quest_personal_notes')
            if st.form_submit_button('Сохранить заметки'):
                data['notes']=notes;persist('Заметки Калисты')
    elif data.get('notes'):
        with st.expander('Личные заметки'):st.write(data['notes'])
    st.caption('Награды записаны для ведущего. Смена статуса квеста сама не начисляет опыт, деньги и предметы.')
