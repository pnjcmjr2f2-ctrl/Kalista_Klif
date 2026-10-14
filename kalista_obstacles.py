"""Map-specific wall segments, used by movement and every attack shape."""
import math
from kalista_map import point

def key(data):
    from kalista_map_background import map_id,scene_key
    return 'map:'+map_id(data) if map_id(data) else 'scene:'+scene_key(data)

def walls(data):return data.get('battle_maps',{}).get('obstacles',{}).get(key(data),[])

def validate(data):
    table=data.setdefault('battle_maps',{}).setdefault('obstacles',{})
    if not isinstance(table,dict):raise ValueError('Повреждены преграды карты')
    for ident,items in table.items():
        if not isinstance(ident,str) or not isinstance(items,list) or len(items)>1000:raise ValueError('Неверные преграды карты')
        ids=set()
        for w in items:
            if not isinstance(w,dict) or not isinstance(w.get('id'),str) or w['id'] in ids:raise ValueError('Неверная преграда')
            ids.add(w['id'])
            if math.dist(point(w.get('first')),point(w.get('second')))<=1e-9:raise ValueError('Преграда должна иметь длину')
            if any(type(w.get(k)) is not bool for k in ('movement','attacks')):raise ValueError('Неверные свойства преграды')
            if not isinstance(w.get('name',''),str):raise ValueError('Неверное имя преграды')

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def intersects(a,b,c,d):
    eps=1e-8
    def on(p,q,r):return abs(cross(p,q,r))<=eps and all(min(p[i],q[i])-eps<=r[i]<=max(p[i],q[i])+eps for i in (0,1))
    x,y,z,t=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
    return (x*y<0 and z*t<0) or on(a,b,c) or on(a,b,d) or on(c,d,a) or on(c,d,b)

def blocking_wall(data,start,end,kind='attacks'):
    start,end=point(start),point(end)
    if math.dist(start,end)<=1e-9:return None
    return next((w for w in walls(data) if w[kind] and intersects(start,end,w['first'],w['second'])),None)

def check_path(data,start,end,kind='attacks'):
    w=blocking_wall(data,start,end,kind)
    if w:raise ValueError(('Путь' if kind=='movement' else 'Атаку')+' перекрывает преграда: '+(w.get('name') or 'стена'))
