"""Public-only payload and validated selection for the tactical component."""
from pathlib import Path
import math
import streamlit as st
import streamlit.components.v1 as components
from kalista_map import point

_component = components.declare_component('kalista_tactical_map', path=str(Path(__file__).parent/'components'/'tactical_map'))

def tactical_map(data, source, key, center=None, radius=0, mode='move', selected=None,target=None,target_key=None,range_m=None):
    from kalista_engine import participants, hp_fields, combat_side,get_current_actor,actor_token
    current=get_current_actor(data) if data['combat_active'] else None
    active=actor_token(current) if current else source
    actors=[dict(id=t,name=a['name'],position=data['positions'][t],enemy=combat_side(data,t)=='Враг',active=t==active,hp=a[hp_fields(a)[0]],hp_max=a[hp_fields(a)[1]],portrait='kalista.png' if t=='player' else (a.get('sheet_profile',{}).get('portrait_url') or 'sheogarat.webp') if t=='ally' else '',effects=[e['name'] for e in a.get('effects',[])][:3]) for t,a in participants(data) if a[hp_fields(a)[0]]>0]
    from kalista_map_background import background, map_id
    backdrop=background(data)
    palette=st.session_state.get('_board_palette_'+source,[]) if key.startswith('shared_map_') else []
    ability_key='battle_spell' if source=='player' else 'action_choice_'+source
    active_ability=st.session_state.get(ability_key)
    epoch=f"{data.get('map_revision',0)}:{source}:{selected or source}:{mode}:{data.get('turn_serial',0)}:{center}:{map_id(data)}:{target}:{active_ability}"
    event=_component(background=backdrop,actors=actors,palette=palette,active_ability=active_ability,view_epoch=str(data.get('map_revision',0))+map_id(data)+(selected or source),target=target,range_m=range_m,source=selected or source,center=center,radius=radius,mode=mode,epoch=epoch,key=key,default=None)
    if isinstance(event,dict) and event.get('epoch')==epoch:
        if isinstance(event.get('ability'),(str,int)) and not isinstance(event.get('ability'),bool) and event.get('ability') in {a['id'] for a in palette} and event['ability']!=active_ability:
            st.session_state['_pending_ability_'+source]=event['ability'];st.rerun()
        if mode=='target' and target_key and isinstance(event.get('target'),str) and event.get('target') in {a['id'] for a in actors}:
            if st.session_state.get(target_key)!=event['target']:
                st.session_state[target_key]=event['target'];st.rerun()
        try:return point(event.get('point'))
        except ValueError:pass
    return point(center if center is not None else data['positions'][selected or source])


def calibrate_map(data,ident,key):
    from kalista_map_background import background
    backdrop=background(data,ident,uncalibrated=True)
    if not backdrop:return None
    event=_component(background=backdrop,actors=[],source='',center=None,radius=0,mode='calibrate',epoch=ident,key=key,default=None)
    if isinstance(event,dict) and event.get('epoch')==ident:
        try:
            pair=event.get('points')
            if isinstance(pair,list) and len(pair)==2:return [point(p) for p in pair]
        except ValueError:pass
    return None
