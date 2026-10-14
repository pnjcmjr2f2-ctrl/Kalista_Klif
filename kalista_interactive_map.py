"""Public-only payload and validated selection for the tactical component."""
from pathlib import Path
import math
import streamlit as st
import streamlit.components.v1 as components
from kalista_map import point

_component = components.declare_component('kalista_tactical_map', path=str(Path(__file__).parent/'components'/'tactical_map'))

def tactical_map(data, source, key, center=None, radius=0, mode='move', selected=None):
    from kalista_engine import participants, hp_fields, combat_side
    actors=[dict(id=t,name=a['name'],position=data['positions'][t],enemy=combat_side(data,t)=='Враг') for t,a in participants(data) if a[hp_fields(a)[0]]>0]
    from kalista_map_background import background, map_id
    backdrop=background(data)
    epoch=f"{data.get('map_revision',0)}:{source}:{selected or source}:{mode}:{data.get('turn_serial',0)}:{center}:{map_id(data)}"
    event=_component(background=backdrop,actors=actors,source=selected or source,center=center,radius=radius,mode=mode,epoch=epoch,key=key,default=None)
    if isinstance(event,dict) and event.get('epoch')==epoch:
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
