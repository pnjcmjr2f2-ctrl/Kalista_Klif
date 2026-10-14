"""Calibrated map backgrounds. A single uniform metres/pixel ratio prevents stretching."""
import math,json,base64
from pathlib import Path
from copy import deepcopy
from kalista_map import point
ROOT=Path(__file__).parent/'components'/'tactical_map'/'maps'

def catalog():
    try:return json.loads((ROOT/'catalog.json').read_text())
    except FileNotFoundError:return []

def scene_key(data):return data.get('active_scene_id') or '_table'
def map_id(data):return data.get('battle_maps',{}).get('assignments',{}).get(scene_key(data),'')
def layout_key(data,ident=None):return scene_key(data)+'|'+(map_id(data) if ident is None else ident)

def ensure_backgrounds(data):
    state=data.setdefault('battle_maps',dict(calibrations={},assignments={},layouts={}))
    if not isinstance(state,dict):raise ValueError('Повреждены настройки карт')
    for key in ('calibrations','assignments','layouts'):
        state.setdefault(key,{})
        if not isinstance(state[key],dict):raise ValueError('Повреждены настройки карт')
    state.setdefault('metadata',{});state.setdefault('scene_displays',{})
    if not isinstance(state['metadata'],dict) or not isinstance(state['scene_displays'],dict):raise ValueError('Повреждена библиотека карт')
    for ident,info in state['metadata'].items():
        if not isinstance(ident,str) or not isinstance(info,dict) or info.get('category','Боевая') not in ('Боевая','Город','Регион','Мир'):raise ValueError('Неверные настройки карты')
        if any(not isinstance(info.get(k,''),str) for k in ('name','note')):raise ValueError('Неверные подписи карты')
    if any(not isinstance(k,str) or not isinstance(v,str) for k,v in state['scene_displays'].items()):raise ValueError('Неверная карта сцены')
    from kalista_obstacles import validate
    validate(data)
    for ident,record in state['calibrations'].items():
        if not isinstance(ident,str) or not isinstance(record,dict):raise ValueError('Неверная калибровка карты')
        p1,p2=point(record.get('first')),point(record.get('second'))
        distance=record.get('distance_m');ratio=record.get('metres_per_pixel')
        if isinstance(distance,bool) or not isinstance(distance,(int,float)) or not math.isfinite(distance) or not 0<distance<=100000:raise ValueError('Неверное расстояние калибровки')
        pixels=math.dist(p1,p2)
        if pixels<1 or isinstance(ratio,bool) or not isinstance(ratio,(int,float)) or not math.isfinite(ratio) or not math.isclose(ratio,distance/pixels,rel_tol=1e-10):raise ValueError('Масштаб карты не совпадает с калибровкой')
    for key,ident in state['assignments'].items():
        if not isinstance(key,str) or not isinstance(ident,str) or ident and ident not in state['calibrations']:raise ValueError('Карта сцены не откалибрована')
    for key,positions in state['layouts'].items():
        if not isinstance(key,str) or not isinstance(positions,dict):raise ValueError('Повреждена расстановка карты')
        for token,value in positions.items():
            if not isinstance(token,str):raise ValueError('Неверный участник на карте')
            point(value)

def calibration(first,second,distance_m,width,height):
    first,second=point(first),point(second)
    for p in (first,second):
        if not (0<=p[0]<=width and 0<=p[1]<=height):raise ValueError('Обе точки должны находиться на изображении')
    if math.dist(first,second)<1:raise ValueError('Выбери две разные точки; для точности лучше подальше друг от друга')
    if isinstance(distance_m,bool) or not isinstance(distance_m,(int,float)) or not math.isfinite(distance_m) or not 0<distance_m<=100000:raise ValueError('Укажи положительное расстояние в метрах')
    return dict(first=first,second=second,distance_m=float(distance_m),metres_per_pixel=distance_m/math.dist(first,second))

def remember_layout(data):
    data['battle_maps']['layouts'][layout_key(data)]=deepcopy(data['positions'])

def restore_layout(data):
    saved=data['battle_maps']['layouts'].get(layout_key(data),{})
    for token in data['positions']:
        if token in saved:data['positions'][token]=point(saved[token])

def assign_map(data,ident):
    if data.get('combat_active'):raise ValueError('Сменить фон можно после завершения боя')
    if ident and ident not in data['battle_maps']['calibrations']:raise ValueError('Сначала откалибруй карту')
    remember_layout(data);data['battle_maps']['assignments'][scene_key(data)]=ident;restore_layout(data)
    data['map_revision']=data.get('map_revision',0)+1
    from kalista_engine import invalidate_player_requests
    invalidate_player_requests(data,'Карта изменилась; предложи действие заново')

def background(data,ident=None,uncalibrated=False):
    ident=map_id(data) if ident is None else ident
    item=next((i for i in catalog() if i['id']==ident),None)
    if not item:return None
    config=data.get('battle_maps',{}).get('calibrations',{}).get(ident)
    if not config and not uncalibrated:return None
    src=ROOT/item['file']
    if not src.is_file():return None
    return dict(id=ident,src='maps/'+item['file'],width=item['width'],height=item['height'],metres_per_pixel=config['metres_per_pixel'] if config and not uncalibrated else 1.,name=item['name'])
