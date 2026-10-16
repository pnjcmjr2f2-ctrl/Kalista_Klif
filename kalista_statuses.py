"""Shared configurable hit effects, movement penalties and control."""
import random
PRESETS={
 'none':('Без дополнительного эффекта',0,0,0),
 'bleed':('Кровотечение',25,3,10),
 'burn':('Горение',50,3,10),
 'curse':('Проклятие',50,3,10),
 'chill':('Охлаждение',50,2,30),
 'freeze':('Заморозка',35,1,0),
 'slow':('Замедление',50,2,50),
 'armor_break':('Режущий вихрь',50,2,20),
 'blind':('Ослепление',35,1,30),
}
TIMED=('chill','freeze','slow','armor_break','blind','bleed')


def movement_limit(actor):
    penalty=max([0]+[e['value'] for e in actor.get('effects',[]) if e['kind'] in ('slow','chill')])
    return 30.*(1-min(100,max(0,penalty))/100)


def blind_chance(actor):
    return max([0]+[min(100,max(0,e['value']))/100 for e in actor.get('effects',[]) if e['kind']=='blind'])


def validate_proc(ability):
    proc=ability.get('hit_effect')
    if proc is None:return
    if not isinstance(proc,dict) or proc.get('kind') not in PRESETS:raise ValueError('Неизвестный эффект попадания')
    for key in ('chance','duration','value'):
        v=proc.get(key)
        if isinstance(v,bool) or not isinstance(v,int) or v<0:raise ValueError('Параметры эффекта должны быть целыми неотрицательными')
    if proc['chance']>100 or proc['value']>100 or proc['duration']<1:raise ValueError('Неверный шанс, сила или длительность эффекта')


def on_hit(target,ability,raw,round_number=0):
    from kalista_engine import add_effect,hp_fields
    proc=ability.get('hit_effect')
    if proc:
        from kalista_skills import rank
        proc=dict(proc);r=rank(ability);tier=int(r>=5)+int(r>=10)
        if proc['kind'] in ('bleed','burn','curse'):
            proc['duration']+=tier
            proc['chance']=min(100,proc['chance']+(5 if proc['kind']=='bleed' else 10)*tier)
    if not proc or proc['kind']=='none' or target[hp_fields(target)[0]]<=0:return []
    kind=proc['kind'];name=PRESETS[kind][0]
    if kind=='bleed' and (target.get('bloodless') or any(w in target.get('race','').casefold() for w in ('скелет','лич','нежить','голем'))):return [name+': цель невосприимчива']
    if kind=='freeze' and target.get('fear_immunity_turns',0):return ['Заморозка: иммунитет к контролю']
    chance=proc['chance']/100
    if kind=='freeze':chance*=1-min(.9,max(0,target.get('control_resist',0)))
    if random.random()>=chance:return [name+': не наложено']
    value=max(1,round(raw*proc['value']/100)) if kind in ('bleed','burn','curse') else proc['value']
    stored_kind='dot' if kind in ('burn','curse') else kind
    def matches(e):return e['kind']==stored_kind and (stored_kind!='dot' or e['name']==name)
    old=[e for e in target.get('effects',[]) if matches(e)]
    if old:value=max(value,max(e['value'] for e in old))
    target['effects']=[e for e in target.get('effects',[]) if not matches(e)]
    add_effect(target,dict(kind=stored_kind,name=name,value=value,duration=proc['duration'],element={'burn':'Огонь','curse':'Тьма'}.get(kind,'Физический'),source='hit:'+kind),round_number)
    return [f'{name}: наложено ({proc["duration"]} ход.)']


def edit_proc(ability,key):
    import streamlit as st
    current=ability.get('hit_effect') or dict(kind='none',chance=25,duration=3,value=10)
    kinds=list(PRESETS)
    kind=st.selectbox('Эффект попадания',kinds,index=kinds.index(current['kind']),format_func=lambda k:PRESETS[k][0],key=key+'_kind')
    st.caption('Кровотечение: сила — % урона попадания до защиты. Остальные: сила — процент штрафа. Для заморозки сила не используется. Самый сильный штраф, без сложения.')
    chance=st.number_input('Шанс эффекта попадания (%)',0,100,int(current['chance']),key=key+'_chance')
    duration=st.number_input('Личных ходов / тиков эффекта',1,100,int(current['duration']),key=key+'_duration')
    value=st.number_input('Сила эффекта попадания (%)',0,100,int(current['value']),key=key+'_value')
    return None if kind=='none' else dict(kind=kind,chance=chance,duration=duration,value=value)
