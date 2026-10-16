"""Editable enemy loadouts built on the shared combat engine."""
from copy import deepcopy

ROLES = ('Воин', 'Лучник', 'Маг', 'Лекарь', 'Некромант', 'Босс')


def loadout(enemy, role):
    from kalista_engine import action_template as a
    if role not in ROLES:
        raise ValueError('Неизвестный шаблон врага')
    power = max(1, round(enemy.get('attack_damage', 1)))
    def hit(name, **kw):
        return a(name, shared_attack=True, reach='Ближняя', range_m=5., **kw)
    def magic(name, element, **kw):
        return a(name, amount=power, damage_type=element, reach='Дальняя', range_m=80., **kw)
    strike = hit('Удар оружием')
    stance = a('Защитная стойка', kind='note', rule='stance', reach='Любая', cooldown=1,
               description='−30% входящего урона до начала следующего личного хода.')
    fear = a('Ужас', kind='note', effect_kind='fear', duration=1, effect_chance=50,
             reach='Дальняя', range_m=40., cooldown=3,
             description='50% × (1 − сопротивление контролю): пропуск одного хода. Учитывает иммунитет к страху.')
    heal = a('Исцеление союзника', kind='heal', amount=round(power*1.2), reach='Дальняя',
             range_m=40., cooldown=2, mana_cost=15)
    shield = a('Магический щит', kind='shield', amount=round(power*1.5), reach='Дальняя',
               range_m=40., cooldown=3, mana_cost=20, duration=2)
    choices = {
        'Воин': [strike, hit('Мощный удар', multiplier=1.5, cooldown=2), stance,
                  hit('Подлый удар', cooldown=2, effect_kind='weakness', effect_value=35, duration=2, effect_chance=35)],
        'Лучник': [strike, a('Выстрел', shared_attack=True, reach='Дальняя', range_m=80.),
                   a('Двойной выстрел', shared_attack=True, hits=2, reach='Дальняя', range_m=80., cooldown=2)],
        'Маг': [strike, magic('Огненная стрела', 'Огонь', mana_cost=10),
                magic('Огненный шар', 'Огонь', mana_cost=35, cooldown=1, area_radius_m=10.), shield],
        'Лекарь': [strike, magic('Луч света', 'Свет', mana_cost=10), heal, shield],
        'Некромант': [strike, magic('Стрела тьмы', 'Тьма', mana_cost=10),
                      magic('Проклятие', 'Тьма', cooldown=2, mana_cost=20, effect_kind='dot',
                            effect_value=max(1,round(power*.15)), effect_element='Тьма', duration=3), fear],
        'Босс': [strike, hit('Сокрушение', multiplier=1.5, cooldown=2),
                 magic('Дыхание пламени', 'Огонь', cooldown=2, area_shape='cone', cone_length_m=30., cone_angle_deg=60.), stance, fear],
    }
    return deepcopy(choices[role])


def apply_loadout(enemy, role):
    """Explicit replacement; identity, HP, defenses and rewards stay unchanged."""
    enemy['actions'] = loadout(enemy, role)
    enemy['enemy_role'] = role
    customize_race(enemy)
    configure_procs(enemy)
    from kalista_skills import distribute
    distribute(enemy)
    enemy.setdefault('critical_chance', 5.)
    enemy.setdefault('critical_multiplier', 2.)
    if role in ('Маг','Лекарь','Некромант') and not enemy.get('mana_max'):
        enemy['mana_max'] = max(60, round(enemy.get('attack_damage',1)*3))
        enemy['mana_current'] = enemy['mana_max']

RACES = ('Человек', 'Гоблин', 'Орк', 'Скелет', 'Лич', 'Другое')


def suggested_role(name):
    text = name.casefold()
    for words, role in ((('лич','некромант'), 'Некромант'), (('шаман','лекарь','жрец'), 'Лекарь'),
                        (('маг','колдун'), 'Маг'), (('лучник','арбалет'), 'Лучник')):
        if any(w in text for w in words):return role
    return 'Воин'


def customize_race(enemy):
    race = enemy.get('race','').casefold()
    actions = enemy['actions']
    if 'гоблин' in race:
        for a in actions:
            if a['name']=='Подлый удар':a['name']='Грязный приём'
    if 'орк' in race:
        for a in actions:
            if a['name']=='Мощный удар':a['name']='Рассекающий удар'
    if 'лич' in race:
        from kalista_engine import action_template
        actions.append(action_template('Волна могильного холода',amount=max(1,round(enemy.get('attack_damage',1))),
                       damage_type='Вода',reach='Дальняя',range_m=80.,area_radius_m=10.,cooldown=2,mana_cost=25,
                       description='Массовый холод: в текущей системе стихия Вода. Задевает союзников в области.'))


def configure_procs(enemy):
    from kalista_statuses import PRESETS
    element=enemy.get('magic_element')
    for a in enemy['actions']:
        if a['kind']!='damage':continue
        if a['damage_type']=='Физический':kind='bleed'
        else:
            if element in ('Огонь','Вода','Земля','Воздух','Тьма','Свет') and enemy.get('race')!='Лич':
                a['damage_type']=element
                if a['name'] in ('Огненная стрела','Луч света','Стрела тьмы'):a['name']='Магический снаряд · '+element
                if a['name']=='Огненный шар' and element!='Огонь':a['name']='Сфера · '+element
            kind={'Огонь':'burn','Тьма':'curse','Вода':'chill','Земля':'slow','Воздух':'armor_break','Свет':'blind'}.get(a['damage_type'])
        if kind and a['effect_kind']=='note':
            _,chance,duration,value=PRESETS[kind]
            a['hit_effect']=dict(kind=kind,chance=chance,duration=duration,value=value)
    enemy['bloodless']=any(w in enemy.get('race','').casefold() for w in ('скелет','лич','голем','нежить'))
