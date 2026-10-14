"""Shared circular/conical area geometry in world metres.

A cone is a circular sector: length is the maximum radial distance, angle is
its full opening angle. The aiming point selects direction, not distance.
"""
import math
from kalista_map import point,area_targets,check_point_range

def is_area(ability):
    return ability.get('area_shape','circle')=='cone' or ability.get('area_radius_m',0)>0

def validate_shape(ability):
    if ability.get('area_shape','circle') not in ('circle','cone'):raise ValueError('Неизвестная форма области')
    length=ability.get('cone_length_m',0)
    angle=ability.get('cone_angle_deg',60)
    if isinstance(length,bool) or not isinstance(length,(int,float)) or not math.isfinite(length) or not 0<=length<=100000:raise ValueError('Неверная длина конуса')
    if isinstance(angle,bool) or not isinstance(angle,(int,float)) or not math.isfinite(angle) or not 1<=angle<=180:raise ValueError('Угол конуса должен быть от 1 до 180°')
    if ability.get('area_shape','circle')=='cone':
        if length<=0:raise ValueError('Задай длину конуса больше 0 м')
        if ability.get('action',ability.get('kind','damage'))!='damage':raise ValueError('Конус пока доступен только для урона')

def check_area_aim(data,source,ability,aim):
    validate_shape(ability)
    aim=point(aim)
    if ability.get('area_shape','circle')=='cone':
        if math.dist(data['positions'][source],aim)<=1e-9:raise ValueError('Укажи направление от атакующего: выбери другую точку')
        return aim
    from kalista_obstacles import check_path
    check_path(data,data["positions"][source],aim)
    return check_point_range(data,source,ability,aim)

def in_cone(origin,aim,target,length,angle):
    origin,aim,target=point(origin),point(aim),point(target)
    dx,dy=aim[0]-origin[0],aim[1]-origin[1]
    norm=math.hypot(dx,dy)
    if norm<=1e-9:raise ValueError('Укажи направление конуса')
    x,y=target[0]-origin[0],target[1]-origin[1]
    distance=math.hypot(x,y)
    if distance>length+1e-9:return False
    if distance<=1e-9:return True
    cosine=(x*dx+y*dy)/(distance*norm)
    return cosine>=math.cos(math.radians(angle/2))-1e-12

def shape_targets(data,source,ability,aim):
    from kalista_engine import participants,hp_fields
    aim=check_area_aim(data,source,ability,aim)
    from kalista_obstacles import blocking_wall
    if ability.get('area_shape','circle')!='cone':return [t for t in area_targets(data,aim,ability['area_radius_m']) if not blocking_wall(data,aim,data['positions'][t])]
    return [t for t,a in participants(data) if t!=source and a[hp_fields(a)[0]]>0 and in_cone(data['positions'][source],aim,data['positions'][t],ability['cone_length_m'],ability['cone_angle_deg']) and not blocking_wall(data,data['positions'][source],data['positions'][t])]

def area_label(ability):
    if ability.get('area_shape','circle')=='cone':return f"Конус · длина {ability['cone_length_m']:g} м · угол {ability['cone_angle_deg']:g}°"
    return f"Круг · радиус {ability.get('area_radius_m',0):g} м"
