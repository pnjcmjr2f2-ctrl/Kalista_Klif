"""Readable effect lifetimes and compact action results."""
import re

def effect_label(effect):
    n=effect.get('duration');kind=effect.get('kind');name=effect['name']
    if n is None:return name+' · бессрочно'
    if kind=='fear':return f'{name} · пропуск ещё {n} ходов'
    if kind in ('dot','hot'):return f'{name} · ещё {n} срабатываний в конце хода'
    if kind=='weakness':return f'{name} · ещё {n} личных ходов'
    return f'{name} · ещё {n} полных раундов'

def result_rows(entry):
    targets=[t.strip() for t in entry.get('target','').split(',') if t.strip()]
    grouped={};current=targets[0] if len(targets)==1 else ''
    for chunk in entry.get('result','').split(' · '):
        for name in targets:
            if chunk.startswith(name+':'):current=name;break
        loss=re.search(r'HP −(\d+)',chunk)
        gain=re.search(r'\+(\d+) HP',chunk)
        shield=re.search(r'щит −(\d+)',chunk)
        status=re.search(r'(Горение|Проклятие|Слабость|Страх): (не наложено|наложено)',chunk)
        miss=any(x in chunk.casefold() for x in ('уклонение','промах'))
        crit='КРИТ' in chunk
        if not (loss or gain or shield or status or miss or crit):continue
        name=current or entry.get('target','')
        row=grouped.setdefault(name,dict(hp=0,shield=0,details=[]))
        if loss:row['hp']-=int(loss[1])
        if gain:row['hp']+=int(gain[1])
        if shield:row['shield']+=int(shield[1])
        if status:row['details'].append(status[1]+(' наложено' if status[2]=='наложено' else ' не прошло'))
        if miss:row['details'].append('Промах / уклонение')
        if crit:row['details'].append('Крит')
    return [{'Цель':name,'HP':('−'+str(-r['hp']) if r['hp']<0 else '+'+str(r['hp']) if r['hp']>0 else '0'),'Щит':f"−{r['shield']}",'Эффекты':'; '.join(dict.fromkeys(r['details']))} for name,r in grouped.items()]


def render_recent_results(data):
    import streamlit as st
    actions=data.get('recent_actions',data.get('turn_actions',[]))
    if not actions:return
    entry=actions[-1]
    with st.container(border=True):
        st.markdown('**Последнее действие: '+entry['name']+'**')
        rows=result_rows(entry)
        if rows:st.table(rows)
        else:st.caption(entry.get('target',''))
        with st.expander('Броски и полный расчёт'):st.write(entry.get('result',''))
