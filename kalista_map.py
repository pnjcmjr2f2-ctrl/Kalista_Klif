"""Metric positions, straight-line ranges and circular areas. No file or UI writes."""
import math
from html import escape

def point(value):
    if not isinstance(value,(list,tuple)) or len(value)!=2 or any(isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or abs(n)>1000000 for n in value):raise ValueError('Позиция должна содержать две конечные координаты в метрах')
    return [float(value[0]),float(value[1])]

def ensure_positions(data):
    from kalista_engine import participants,combat_side
    positions=data.setdefault('positions',{})
    if not isinstance(positions,dict):raise ValueError('Повреждены позиции на карте')
    known={t for t,_ in participants(data)}
    for token,value in list(positions.items()):
        if token not in known:positions.pop(token)
        else:positions[token]=point(value)
    for token,_ in participants(data):
        if token not in positions:
            if token=='player':positions[token]=[0.,0.]
            elif token=='ally':positions[token]=[0.,5.]
            else:
                index=sum(t.startswith('enemy:') for t in positions)
                positions[token]=[20.+10*index,10.*(index%3)] if combat_side(data,token)=='Враг' else [-10.-10*index,0.]

def separation(data,first,second):return math.dist(data['positions'][first],data['positions'][second])
def ability_range(ability):
    value=ability.get('range_m')
    if value is not None:
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100000:raise ValueError('Неверная дальность в метрах')
        return value
    return 5. if ability.get('reach','Ближняя' if ability.get('damage_type')=='Физический' else 'Дальняя')=='Ближняя' else None

def validate_ability(ability):
    ability_range(ability)
    radius=ability.get('area_radius_m',0)
    if isinstance(radius,bool) or not isinstance(radius,(int,float)) or not math.isfinite(radius) or not 0<=radius<=100000:raise ValueError('Неверный радиус области')
    if radius and ability.get('action',ability.get('kind','damage'))!='damage':raise ValueError('Массовая область пока доступна только для урона')

def check_point_range(data,source,ability,center):
    center=point(center);maximum=ability_range(ability)
    if maximum is not None and math.dist(data['positions'][source],center)>maximum+1e-9:raise ValueError(f'Точка дальше допустимой дальности {maximum:g} м')
    return center

def area_targets(data,center,radius):
    from kalista_engine import participants,hp_fields
    center=point(center)
    if not isinstance(radius,(int,float)) or isinstance(radius,bool) or not math.isfinite(radius) or radius<=0:raise ValueError('Нужен положительный радиус')
    return [t for t,a in participants(data) if a[hp_fields(a)[0]]>0 and math.dist(data['positions'][t],center)<=radius+1e-9]

def move(data,source,target=None,rule='move_point',destination=None):
    start=data['positions'][source]
    if rule=='move_point':end=point(destination)
    else:
        if target==source:raise ValueError('Выбери другого участника для перемещения')
        goal=data['positions'][target];distance=math.dist(start,goal)
        if rule=='move_close':
            amount=min(30.,max(0,distance-5.))
            if amount<=1e-9:raise ValueError('Цель уже в ближней дистанции')
            vector=[(goal[i]-start[i])/distance for i in (0,1)]
        else:
            amount=30.;vector=[(start[i]-goal[i])/distance for i in (0,1)] if distance else [1.,0.]
        end=[start[i]+vector[i]*amount for i in (0,1)]
    distance=math.dist(start,end)
    if distance<=1e-9:raise ValueError('Укажи другую позицию')
    if distance>30.+1e-9:raise ValueError('За одно перемещение можно пройти не более 30 м')
    data['positions'][source]=point(end);data['map_revision']=data.get('map_revision',0)+1
    return distance

def map_svg(data,center=None,radius=0):
    from kalista_engine import participants,combat_side,hp_fields
    actors=[(t,a) for t,a in participants(data) if a[hp_fields(a)[0]]>0]
    points=[data['positions'][t] for t,_ in actors]+([point(center)] if center is not None else [])
    if not points:return '<p>Нет участников на карте</p>'
    xs=[p[0] for p in points];ys=[p[1] for p in points]
    if center is not None:xs.extend([center[0]-radius,center[0]+radius]);ys.extend([center[1]-radius,center[1]+radius])
    lo_x=min(xs)-8;lo_y=min(ys)-8;span=max(max(xs)-lo_x+8,max(ys)-lo_y+8,30);scale=340/span
    convert=lambda p:(25+(p[0]-lo_x)*scale,365-(p[1]-lo_y)*scale)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 400" role="img" aria-label="Карта боя в метрах" style="width:100%;max-width:600px;background:#211a28;border-radius:12px">']
    step=5 if span<=100 else 10**math.floor(math.log10(span/10))
    for axis,low in ((0,lo_x),(1,lo_y)):
        n=math.ceil(low/step)*step
        for _ in range(50):
            if n>low+span:break
            x,y=convert([n,lo_y] if axis==0 else [lo_x,n]);parts.append(f'<path d="M {x if axis==0 else 25:g} {25 if axis==0 else y:g} L {x if axis==0 else 365:g} {365 if axis==0 else y:g}" stroke="#44364e"/>')
            parts.append(f'<text x="{x if axis==0 else 2:g}" y="{389 if axis==0 else y:g}" fill="#afa0bb" font-size="9">{n:g}</text>');n+=step
    if center is not None:
        x,y=convert(center);parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="{radius*scale:g}" fill="#ff8f0033" stroke="#ffb45e"/><path d="M{x-4:g} {y:g}h8 M{x:g} {y-4:g}v8" stroke="#ffb45e"/>')
    affected=set(area_targets(data,center,radius)) if center is not None and radius>0 else set()
    for index,(token,actor) in enumerate(actors,1):
        x,y=convert(data['positions'][token]);color='#db7b87' if combat_side(data,token)=='Враг' else '#91c5a6'
        parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="8" fill="{color}" stroke="{"#ffb45e" if token in affected else "#efe8f4"}" stroke-width="2"><title>{escape(actor["name"])}</title></circle><text x="{x:g}" y="{y+3:g}" text-anchor="middle" fill="#17131d" font-weight="bold" font-size="10">{index}</text>')
    return ''.join(parts)+'</svg>'


def map_legend(data):
    from kalista_engine import participants,hp_fields
    actors=[(t,a) for t,a in participants(data) if a[hp_fields(a)[0]]>0]
    return ' · '.join(f"{i}. {a['name']} ({data['positions'][t][0]:g}; {data['positions'][t][1]:g})" for i,(t,a) in enumerate(actors,1))
