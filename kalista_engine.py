"""Game rules and migrations. No Streamlit or file writes in this module."""
import math
import random
import json
from copy import deepcopy
from uuid import uuid4
from datetime import datetime
from kalista_player_model import ensure_player_sheet
from kalista_progression import xp_needed,initialize_progress,MAX_LEVEL,advance_levels
from kalista_rewards import begin_rewards,register_enemy,settle_rewards

ELEMENTS = ["Огонь", "Земля", "Вода", "Воздух", "Тьма", "Свет"]


DEFAULT = {
    "name": "Калиста Клиф", "race": "Тёмный эльф (Дроу)", "class": "Маг огня и тьмы",
    "level": 21, "xp": 18450, "xp_to_next": 2150, "free_points": 0,
    "hp_current": 420, "hp_max": 820, "mana_current": 0, "mana_max": 2950,
    "base_stats": {"Сила":10,"Выносливость":15,"Ловкость":14,"Мудрость":10,"Интеллект":60,"Харизма":10,"Дух":35},
    "equip_bonuses": {"Сила":0,"Выносливость":25,"Ловкость":0,"Мудрость":85,"Интеллект":235,"Харизма":0,"Дух":175},
    "armor": 535, "phys_attack": 55,
    "pepel": 0, "ten": 0, "buffs": "", "debuffs": "", "concentration": "", "last_school": None,
    "gold": 84, "silver": 34, "copper": 0,
    "inventory": [
        {"name":"Зелье маны (большое)","type":"Расходник","qty":3,"desc":"+400 маны"},
        {"name":"Зелье лечения","type":"Расходник","qty":2,"desc":"+250 HP"},
        {"name":"Свиток «Щит теней»","type":"Свиток","qty":1,"desc":"Щит 300"},
        {"name":"Кристалл пустоты","type":"Реагент","qty":5,"desc":""},
        {"name":"Пепел древнего костра","type":"Реагент","qty":4,"desc":""},
        {"name":"Чёрный дневник","type":"Книга","qty":1,"desc":""},
        {"name":"Амулет старого дома","type":"Реликвия","qty":1,"desc":""},
        {"name":"Набор алхимика","type":"Инструмент","qty":1,"desc":""},
        {"name":"Факел вечного огня","type":"Инструмент","qty":1,"desc":""},
    ],
    "spells": [
        {"id":1,"name":"Искровой заряд","base":35,"mana":18,"school":"Огонь","desc":"Быстрый сгусток","gives":"pepel","cd_max":0,"cd_left":0,"dot":None},
        {"id":2,"name":"Огненный шар","base":80,"mana":35,"school":"Огонь","desc":"Шар пламени","gives":"pepel","cd_max":1,"cd_left":0,"dot":None},
        {"id":3,"name":"Язык пламени","base":55,"mana":28,"school":"Огонь","desc":"Полоса огня","gives":"pepel","cd_max":0,"cd_left":0,"dot":None},
        {"id":4,"name":"Пепел и тлен","base":20,"mana":22,"school":"Огонь","desc":"DoT 3 раунда","gives":"pepel","cd_max":2,"cd_left":0,"dot":{"name":"Горение","damage":18,"element":"Огонь","duration":3}},
        {"id":5,"name":"Адское дыхание","base":120,"mana":55,"school":"Огонь","desc":"Конус огня","gives":"pepel","cd_max":3,"cd_left":0,"dot":None},
        {"id":6,"name":"Теневой укол","base":45,"mana":20,"school":"Тьма","desc":"Игнор части брони","gives":"ten","cd_max":0,"cd_left":0,"dot":None},
        {"id":7,"name":"Покров тьмы","base":0,"mana":30,"school":"Тьма","desc":"Щит","gives":None,"cd_max":4,"cd_left":0,"dot":None},
        {"id":8,"name":"Проклятие слабости","base":15,"mana":25,"school":"Тьма","desc":"Слабость + DoT","gives":"ten","cd_max":2,"cd_left":0,"dot":{"name":"Проклятие","damage":10,"element":"Тьма","duration":3}},
        {"id":9,"name":"Разряд бездны","base":95,"mana":45,"school":"Тьма","desc":"Шанс страха","gives":"ten","cd_max":2,"cd_left":0,"dot":None},
        {"id":10,"name":"Пламя души","base":150,"mana":70,"school":"Огонь+Тьма","desc":"Ультиматив","gives":"both","cd_max":5,"cd_left":0,"dot":None},
    ],
    "equipment": {
        "Оружие 1 (посох)":{"name":"Посох Магистра Огня и Тьмы","armor":0,"attack":50,"int":60,"wis":15,"spi":60,"fire":50,"dark":50,"earth":0,"water":0,"air":0,"light":0},
        "Оружие 2":{"name":"","armor":0,"attack":0,"int":0,"wis":0,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Шлем":{"name":"Капюшон тьмы","armor":15,"attack":0,"int":20,"wis":10,"spi":10,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Наплечники":{"name":"Наплечники тьмы","armor":5,"attack":0,"int":20,"wis":10,"spi":10,"fire":0,"dark":5,"earth":0,"water":0,"air":0,"light":0},
        "Перчатки":{"name":"Перчатки тьмы","armor":5,"attack":0,"int":10,"wis":5,"spi":15,"fire":0,"dark":5,"earth":0,"water":0,"air":0,"light":0},
        "Нагрудник":{"name":"Нагрудник тьмы","armor":50,"attack":0,"int":40,"wis":0,"spi":30,"fire":0,"dark":5,"earth":0,"water":0,"air":0,"light":0},
        "Пояс":{"name":"Пояс тьмы","armor":10,"attack":0,"int":10,"wis":5,"spi":5,"fire":0,"dark":5,"earth":0,"water":0,"air":0,"light":0},
        "Штаны":{"name":"Поножи тьмы","armor":25,"attack":0,"int":15,"wis":0,"spi":5,"fire":0,"dark":5,"earth":0,"water":0,"air":0,"light":0},
        "Сапоги":{"name":"Сапоги тьмы","armor":15,"attack":0,"int":10,"wis":0,"spi":10,"fire":0,"dark":5,"earth":0,"water":0,"air":0,"light":0},
        "Серьга 1":{"name":"","armor":0,"attack":0,"int":0,"wis":0,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Серьга 2":{"name":"","armor":0,"attack":0,"int":0,"wis":0,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Ожерелье":{"name":"Фамильный Амулет","armor":0,"attack":0,"int":0,"wis":40,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Кольцо 1":{"name":"Кольцо разрушения","armor":0,"attack":0,"int":25,"wis":0,"spi":30,"fire":20,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Кольцо 2":{"name":"Кольцо сосредоточения","armor":0,"attack":0,"int":25,"wis":0,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Кольцо 3":{"name":"","armor":0,"attack":0,"int":0,"wis":0,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
        "Кольцо 4":{"name":"","armor":0,"attack":0,"int":0,"wis":0,"spi":0,"fire":0,"dark":0,"earth":0,"water":0,"air":0,"light":0},
    },
    "ally": {
        "name":"Союзник","hp":200,"hp_max":200,"armor":80,"dots":[],"initiative":12,
        "attack_damage": 40,
        "attack_type": "Физический",
        "resists": {"Огонь":10,"Земля":10,"Вода":10,"Воздух":10,"Тьма":10,"Свет":10}
    },
    "enemies": [],
    "next_enemy_id": 1,
    "passives": {
        # Расовые: числовая защита и справочные правила
        "darkvision": {"name":"Зрение в темноте","type":"racial","used":False,"desc":"Видит в полной темноте на 36м. Яркий свет может ослепить на 1 ход."},
        "dark_resist": {"name":"Сопротивление тьме","type":"racial","used":False,"desc":"Базовые +35 уже включены в характеристики. Получаемый урон Тьмой дополнительно уменьшается на 10% после сопротивления, перед щитом."},
        "water_sense": {"name":"Чувствительность к воде","type":"racial","used":False,"desc":"Базовое сопротивление Воде 10 уже учтено; отдельной прибавки нет. Долгий дождь вызывает дискомфорт."},
        "drow_grace": {"name":"Дроу-грация","type":"racial","used":False,"desc":"+2 к скрытности и акробатике в темноте/слабом свете."},
        # Классовые
        "double_flame": {"name":"Двойное пламя","type":"class","used":False,"desc":"+5% прямого урона при Огонь↔Тьма. Любой успешный каст задаёт предыдущую школу, включая щит. Огонь+Тьма прерывает цепочку."},
        "ash_lady": {"name":"Повелительница пепла","type":"class","used":False,"desc":"Огненные заклинания дают Пепел. При 5 — активация: след. огненное игнор 30% сопр. огню."},
        "shadow_child": {"name":"Дитя тени","type":"class","used":False,"desc":"Тёмные заклинания дают Тень. При 5 — активация: невидимость до начала 3-го хода Калисты (ход активации — 1-й) ИЛИ +20 к сопротивлениям (предел 95) до начала 3-го хода Калисты."},
        "mana_reserve": {"name":"Магический резерв","type":"class","used":False,"desc":"При мане <20% перед восстановлением: +50% регенерации на 3 конца раунда. Повтор — после достижения 20% и нового падения ниже порога."},
        # Особые (активируемые, раз в день/отдых)
        "ritual_black_flame": {"name":"Ритуал Чёрного Пламени","type":"special","used":False,"desc":"Следующее Пламя души: +40% прямого урона, совместимо с критом и Пеплом. Усиление сохраняется между боями; восстановление — долгим отдыхом."},
        "cold_calculation": {"name":"Холодный расчёт","type":"special","used":False,"desc":"До боя или в первый ход Калисты: +10 процентных пунктов крита до конца боя. Снова доступно в следующем бою."},
        "memory_of_house": {"name":"Память Дома Клиф","type":"special","used":False,"desc":"Раз в долгий отдых: преимущество на проверку знаний о запретной магии."},
    },
    "mana_reserve_ticks": 0,
    "mana_reserve_armed": True,
    "soul_flame_boost": False,
    "crit_boost_active": False,
    "player_turns_started": 0,
    "pepel_empower": False,   # следующее огненное игнор 30% fire resist
    "ten_invis": False,       # до начала третьего хода Калисты
    "ten_invis_turn_starts_left": 0,  # два следующих начала её хода после активации
    "ten_resist_boost": 0,    # начал хода Калисты до окончания +20 к сопротивлениям
    "status_effects": [],     # [{"name","duration","desc"}]
    "portrait_url": "",
    "crit_chance": 0.065,
    "quests": [
        {"id":1,"name":"Пепел старого дома","status":"В процессе","desc":""},
        {"id":2,"name":"Кристалл пустоты","status":"Активен","desc":""},
        {"id":3,"name":"Долг Серому","status":"Ожидание","desc":""},
    ],
    "notes": "Контроль важнее силы.",
    "scenes": [], "npcs": [], "active_scene_id": "", "gm_notes": "",
    "combat_log": [],
    "resists": {"Огонь":75,"Земля":5,"Вода":10,"Воздух":5,"Тьма":95,"Свет":15},
    # Очередь
    "round": 1,
    "turn_order": [],       # [{"kind":"player"/"ally"/"enemy","id":...,"name":...}]
    "current_turn": 0,
    "combat_active": False,
}


def absorb(val):
    return val / (val + 800) if val and val > 0 else 0.0


def real_dmg(raw, resist):
    return max(0, round(raw * (1 - absorb(resist))))


def total_stat(d, n):
    return d["base_stats"].get(n,0) + d["equip_bonuses"].get(n,0)


def recalc_equip(d):
    eq = d.get("equipment", {})
    b = {k:0 for k in ["Сила","Выносливость","Ловкость","Мудрость","Интеллект","Харизма","Дух"]}
    arm = atk = 0
    resists = {e:0 for e in ELEMENTS}
    for it in eq.values():
        b["Интеллект"] += it.get("int",0)
        b["Мудрость"] += it.get("wis",0)
        b["Дух"] += it.get("spi",0)
        arm += it.get("armor",0)
        atk += it.get("attack",0)
        resists["Огонь"] += it.get("fire",0)
        resists["Тьма"] += it.get("dark",0)
        resists["Земля"] += it.get("earth",0)
        resists["Вода"] += it.get("water",0)
        resists["Воздух"] += it.get("air",0)
        resists["Свет"] += it.get("light",0)
    b["Выносливость"] = 25
    for key, value in d.get("stat_adjustments", {}).items():
        b[key] = b.get(key, 0) + value
    d["equip_bonuses"] = b
    d["armor"] = max(0, arm + d.get("armor_adjustment", 0))
    d["phys_attack"] = max(0, 5 + atk + d.get("attack_adjustment", 0))
    # базовые + экип
    base_r = {"Огонь":5,"Земля":5,"Вода":10,"Воздух":5,"Тьма":40,"Свет":15}
    d["resists"] = {e: max(0, min(95, base_r[e] + resists[e] + d.get("resist_adjustments", {}).get(e, 0))) for e in ELEMENTS}


def recalc(d):
    if d.get("xp_curve_version")==1:advance_levels(d)
    if "equipment" in d: recalc_equip(d)
    intel=total_stat(d,"Интеллект"); wis=total_stat(d,"Мудрость"); cha=total_stat(d,"Харизма")
    spi=total_stat(d,"Дух"); end=total_stat(d,"Выносливость"); agi=total_stat(d,"Ловкость")
    d["mana_max"]=intel*10
    d["hp_max"]=d["level"]*20 + end*10
    d["spell_power"]=intel/5/100
    d["mana_regen"]=round(spi*0.5)
    d["initiative"]=round(agi/2 + wis/4)
    d["control_resist"]=min(0.9, wis/4/100)
    d["evasion_chance"]=min(.5,max(0,agi*.005))
    d["ritual_bonus"]=wis/5/100
    d["fear_power"]=cha/3/100


def gen_enemy(level, size, elite):
    sm = {"Мелкий":0.6,"Обычный":1.0,"Крупный":1.5,"Огромный":2.2}.get(size,1.0)
    em = 1.7 if elite else 1.0
    m = sm * em
    hp = int((40+level*18)*m*random.uniform(0.9,1.15))
    armor = int((5+level*4)*m*random.uniform(0.85,1.15))
    atk = int((8+level*3.5)*m*random.uniform(0.9,1.1))
    resists = {}
    for e in ELEMENTS:
        resists[e] = min(90, max(0, int(level*2.0*m*random.uniform(0.6,1.3))))
    # чуть сильнее в одной стихии
    main = random.choice(ELEMENTS)
    resists[main] = min(90, resists[main] + 15)
    return {
        "hp":hp,"hp_max":hp,"armor":armor,"attack_damage":atk,
        "attack_type": random.choice(["Физический"]+ELEMENTS),
        "resists": resists,
        "dots": [],
        "initiative": int(8 + level*0.6 + random.randint(-3,5)),
    }


def merge_defaults(default, saved):
    """Дополняем вложенные поля, сохраняя пользовательские списки и значения."""
    if isinstance(default, dict) and isinstance(saved, dict):
        result = deepcopy(default)
        for key, value in saved.items():
            result[key] = merge_defaults(default[key], value) if key in default else deepcopy(value)
        return result
    return deepcopy(saved)


def validate_tree(value, template, path="сохранение"):
    if path.endswith(".gives") and value is None:
        return
    if isinstance(template, dict):
        if not isinstance(value, dict):
            raise ValueError(f"{path}: ожидается объект")
        for key in template.keys() & value.keys():
            validate_tree(value[key], template[key], f"{path}.{key}")
    elif isinstance(template, list):
        if not isinstance(value, list):
            raise ValueError(f"{path}: ожидается список")
        if template:
            for i, item in enumerate(value):
                validate_tree(item, template[0], f"{path}[{i}]")
    elif isinstance(template, bool):
        if not isinstance(value, bool):
            raise ValueError(f"{path}: ожидается логическое значение")
    elif isinstance(template, (int, float)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{path}: ожидается конечное число")
        if isinstance(template, int) and not isinstance(value, int):
            raise ValueError(f"{path}: ожидается целое число")
    elif isinstance(template, str) and not isinstance(value, str):
        raise ValueError(f"{path}: ожидается текст")


def migrate(saved):
    validate_tree(saved, DEFAULT)
    if saved.get("schema_version", 5) not in (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22):
        raise ValueError("Версия сохранения не поддерживается")
    data = merge_defaults(DEFAULT, saved)
    if data["name"] in ("Калист", "Калист Клиф"):
        data["name"] = "Калиста Клиф" if data["name"].endswith("Клиф") else "Калиста"
    if saved.get('schema_version',5)<18:
        for _, target in participants(data):
            target['element_defense_mode']='percent'
            target['resists']={el:max(-100,min(95,v)) for el,v in target.get('resists',{}).items()}
        for spell in data['spells']:
            if spell['name']=='Покров тьмы':spell['action']='shield'
            if spell['name']=='Теневой укол':
                spell['cd_max']=2
                spell['desc']='Чистый урон: игнорирует броню и сопротивления; щиты поглощают урон.'
    if saved.get('schema_version',5)<19:
        for _,target in participants(data):target['action_limit']=2
        ally=data['ally']
        if ally.get('sheet_profile'):
            removed={'Когти','Кислотные брызги','Газовое облако','Десница Ока','Совершенная контратака'}
            ally['actions']=[a for a in ally.get('actions',[]) if a['name'].strip() not in removed]
            existing={a['name'] for a in ally['actions']}
            ally['actions'] += [a for a in warrior_actions() if a['name'] not in existing]
            ally['counterattack_enabled']=True
            ally['sheet_profile']['abilities']='Видящий — позволяет видеть суть вещей.\nСкорострел — две атаки мечом за одно действие.\nКонтратака — 65% после потери HP от прямого ближнего удара; обычный удар мечом без расхода действий.\nДесница Ока — активная способность, +100% урона до конца текущего хода, один раз за бой.'
            fill_warrior_equipment(ally)
        invalidate_player_requests(data,'Правила боя обновились; предложи действие заново')
    data.setdefault('distances',{})
    known={token for token,_ in participants(data)}
    if not isinstance(data['distances'],dict):raise ValueError('Повреждены дистанции')
    for key,value in data['distances'].items():
        if len(key.split('|'))!=2 or value not in ('Ближняя','Дальняя'):raise ValueError('Неверная дистанция')
    data['distances']={k:v for k,v in data['distances'].items() if all(t in known for t in k.split('|'))}
    for actor in data.get("turn_order", []):
        if actor.get("kind") == "player": actor["name"] = data["name"]
    for _, target in participants(data):
        target.setdefault("heal_amount", 0)
        nonnegative_int(target["heal_amount"], "Сила лечения")
        validate_tree(target, {"description": ""})
        if target.get('element_defense_mode', 'rating') not in ('rating', 'percent'):
            raise ValueError('Неизвестный способ расчёта сопротивлений')
        if target.get('element_defense_mode') == 'percent':
            if any(not isinstance(v, (int,float)) or isinstance(v,bool) or not math.isfinite(v) or not -100 <= v <= 95 for v in target['resists'].values()):
                raise ValueError('Сопротивления в процентах должны быть от −100 до 95')
        if 'sheet_profile' in target:
            ensure_player_sheet(target)
            profile = target['sheet_profile']
            template = imported_friend()['sheet_profile']
            validate_tree(profile, {key:value for key,value in template.items() if key not in ('equipment','inventory','formula_adjustments','stat_adjustments','resist_adjustments','quests')})
            if not template.keys() <= profile.keys(): raise ValueError('Неполный лист персонажа друга')
            for field in ('attack','critical_damage','critical_chance','level','free_points'):
                if profile[field] < 0: raise ValueError('Боевые параметры листа не могут быть отрицательными')
            if profile['critical_chance'] > 100: raise ValueError('Шанс крита должен быть не выше 100%')
    if saved.get("schema_version", 5) < 13:
        for key in ("dark_resist", "water_sense", "double_flame", "ritual_black_flame", "cold_calculation"):
            data["passives"][key]["desc"] = DEFAULT["passives"][key]["desc"]
        if data["combat_active"]:
            player_index = next((i for i, actor in enumerate(data["turn_order"]) if actor.get("kind") == "player"), None)
            data["player_turns_started"] = max(0, data["round"] - 1) + int(player_index is not None and player_index <= data["current_turn"])
        else:
            data["player_turns_started"] = 0
            if not data["crit_boost_active"]: data["passives"]["cold_calculation"]["used"] = False
    if saved.get("schema_version", 5) < 12:
        data["passives"]["shadow_child"]["desc"] = DEFAULT["passives"]["shadow_child"]["desc"]
    if saved.get("schema_version", 5) < 10:
        data["passives"]["shadow_child"]["desc"] = DEFAULT["passives"]["shadow_child"]["desc"]
        # Старые сохранения не содержат момента активации: даём два будущих начала хода.
        data["ten_invis_turn_starts_left"] = 2 if data["ten_invis"] else 0
    if saved.get("schema_version", 5) < 9:
        data["passives"]["mana_reserve"]["desc"] = DEFAULT["passives"]["mana_reserve"]["desc"]
    for enemy in data["enemies"]:
        enemy.setdefault("resists", {el: enemy.get("resist_" + code, 0)
                                    for el, code in zip(ELEMENTS, ["fire", "earth", "water", "air", "dark", "light"])})
        enemy.setdefault("dots", [])
        enemy.setdefault("initiative", 10)
        for key in ("id", "name", "hp", "hp_max", "armor"):
            if key not in enemy:
                raise ValueError(f"У противника отсутствует поле {key}")
        validate_tree(enemy, {"id": 0, "name": "", "hp": 0, "hp_max": 1, "armor": 0,
                              "resists": {el: 0 for el in ELEMENTS}, "initiative": 0,
                              "attack_damage": 0, "attack_type": "", "dots": []})
    ids = [enemy["id"] for enemy in data["enemies"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Повторяющиеся ID противников")
    data["next_enemy_id"] = max([data.get("next_enemy_id", 1)] + [i + 1 for i in ids])
    for spell in data["spells"]:
        spell.setdefault("cd_max", 0)
        spell.setdefault("cd_left", 0)
        spell.setdefault("dot", None)
        spell.setdefault("reach", "Дальняя")
        if spell["reach"] not in ("Ближняя","Дальняя","Любая"):raise ValueError("Неверная дальность заклинания")
    if len({sp["id"] for sp in data["spells"]}) != len(data["spells"]):
        raise ValueError("Повторяющиеся ID заклинаний")
    data.setdefault("dots", [])
    for target in [data, data["ally"]] + data["enemies"]:
        for dot in target.get("dots", []):
            validate_tree(dot, {"name": "", "damage": 0, "duration": 1, "element": ""})
            if not {"name", "damage", "duration"} <= dot.keys():
                raise ValueError("Неполные данные периодического эффекта")
    # Сохраняем исходные итоговые значения вместо незаметного изменения баланса.
    if "armor_adjustment" not in data:
        reference = deepcopy(data)
        recalc_equip(reference)
        data["armor_adjustment"] = data["armor"] - reference["armor"]
        data["attack_adjustment"] = data["phys_attack"] - reference["phys_attack"]
        data["stat_adjustments"] = {k: data["equip_bonuses"].get(k, 0) - v
                                    for k, v in reference["equip_bonuses"].items()}
        data["resist_adjustments"] = {k: data["resists"].get(k, 0) - v
                                      for k, v in reference["resists"].items()}
    validate_tree(data, {"armor_adjustment": 0, "attack_adjustment": 0,
                         "stat_adjustments": {k: 0 for k in data["base_stats"]},
                         "resist_adjustments": {el: 0 for el in ELEMENTS},
                         "dots": [{"name": "", "damage": 0, "duration": 1, "element": ""}]})
    for spell in data["spells"]:
        descriptions={'DoT 3 раунда':'Горение: шанс 50%, 6% Интеллекта × (1 + сила заклинаний), 3 срабатывания.','Слабость + DoT':'Проклятие: шанс 50%, 4% Интеллекта × (1 + сила заклинаний), 3 срабатывания. Слабость: шанс 35%, −35% физического урона на 2 хода.','Игнор части брони':'Чистый урон: игнорирует броню и сопротивления; щиты поглощают урон.','Шанс страха':'Страх: шанс 50% с учётом сопротивления контролю, пропуск 2 ходов.'}
        if spell.get('desc') in descriptions:spell['desc']=descriptions[spell['desc']]
        if not {"id", "name", "base", "mana", "school"} <= spell.keys():
            raise ValueError("Неполные данные заклинания")
        if spell["mana"] < 0 or spell["base"] < 0 or spell["cd_max"] < 0 or spell["cd_left"] < 0:
            raise ValueError("Урон, стоимость и перезарядка не могут быть отрицательными")
        if spell.get("dot") is not None:
            dot = spell["dot"]
            if not isinstance(dot, dict) or not {"name", "damage", "duration"} <= dot.keys():
                raise ValueError("Неполные данные эффекта заклинания")
            validate_tree(dot, {"name": "", "damage": 0, "duration": 1, "element": ""})
    for token, target in participants(data):
        effects = target.setdefault("effects", [])
        if not isinstance(effects, list):
            raise ValueError("Список эффектов повреждён")
        for index, dot in enumerate(target.get("dots", [])):
            if dot["duration"] <= 0:
                continue
            effects.append({"id": f"legacy-dot-{index}", "kind": "dot", "name": dot["name"],
                            "value": dot["damage"], "element": dot.get("element", "Огонь"),
                            "duration": dot["duration"], "source": "legacy", "desc": "",
                            "applied_round": 0})
        target["dots"] = []
        for index, status in enumerate(target.get("status_effects", [])):
            validate_tree(status, {"name": "", "duration": 1, "desc": ""})
            if not {"name", "duration"} <= status.keys():
                raise ValueError("Неполные данные статуса")
            if status["duration"] <= 0:
                continue
            effects.append({"id": f"legacy-status-{index}", "kind": "note", "name": status["name"],
                            "value": 0, "duration": status["duration"], "source": "legacy",
                            "desc": status.get("desc", ""), "applied_round": 0})
        if "status_effects" in target:
            target["status_effects"] = []
        for index, effect in enumerate(effects):
            effect.setdefault("id", f"effect-{index}")
            effect.setdefault("value", 0)
            effect.setdefault("duration", None)
            effect.setdefault("element", "Огонь")
            effect.setdefault("source", "Ведущий")
            effect.setdefault("desc", "")
            effect.setdefault("applied_round", 0)
            validate_effect(effect)
        if len({effect["id"] for effect in effects}) != len(effects):
            raise ValueError(f"Повторяющиеся ID эффектов: {token}")
        hp_key, maximum_key = hp_fields(target)
        nonnegative_int(target[hp_key], "HP")
        if target[maximum_key] < 1:
            raise ValueError("Максимум HP должен быть выше 0")
    for spell in data["spells"]:
        spell.setdefault("action", "shield" if spell["name"] == "Покров тьмы" and spell["base"] == 0 else "damage")
        if spell["action"] not in ("damage", "heal", "shield", "note"):
            raise ValueError("Неизвестное действие заклинания")
        nonnegative_int(spell.get("effect_value", 0), "Сила эффекта заклинания")
        nonnegative_int(spell.get("effect_duration", 0), "Длительность эффекта заклинания")
    for item in data["inventory"]:
        if "use" not in item:
            # Только известные предметы с известными числами; новые названия не угадываем.
            known = {"Зелье маны (большое)": {"kind": "mana", "value": 400},
                     "Зелье лечения": {"kind": "heal", "value": 250},
                     "Свиток «Щит теней»": {"kind": "shield", "value": 300}}
            item["use"] = deepcopy(known.get(item["name"]))
        validate_item_use(item.get("use"))
        nonnegative_int(item["qty"], "Количество предметов")
    for spell in data["spells"]:
        if spell.get("dot"):
            dot = spell["dot"]
            validate_effect({"kind": "dot", "name": dot["name"], "value": dot["damage"],
                             "duration": dot["duration"], "element": dot.get("element", "Огонь")})
    data.setdefault("initiative_overrides", {})
    data.setdefault("turn_excluded", [])
    if not isinstance(data["initiative_overrides"], dict) or not isinstance(data["turn_excluded"], list):
        raise ValueError("Настройки очереди повреждены")
    known_tokens = {token for token, _ in participants(data)}
    for token, value in data["initiative_overrides"].items():
        if not isinstance(token, str): raise ValueError("Неверный участник очереди")
        nonnegative_int(value, "Инициатива")
    if any(not isinstance(token, str) for token in data["turn_excluded"]):
        raise ValueError("Неверный список исключений из очереди")
    data["initiative_overrides"] = {token: value for token, value in data["initiative_overrides"].items() if token in known_tokens}
    data["turn_excluded"] = list(dict.fromkeys(token for token in data["turn_excluded"] if token in known_tokens))
    if not 0 <= data["mana_reserve_ticks"] <= 3:
        raise ValueError("Остаток тиков резерва должен быть от 0 до 3")
    if not 0 <= data["ten_invis_turn_starts_left"] <= 2:
        raise ValueError("Остаток начал хода невидимости должен быть от 0 до 2")
    if data["ten_invis"] != (data["ten_invis_turn_starts_left"] > 0):
        raise ValueError("Состояние невидимости не соответствует её длительности")
    nonnegative_int(data["ten_resist_boost"], "Длительность сопротивлений Тени")
    if data["ten_resist_boost"] > 2:
        raise ValueError("Остаток начал хода сопротивлений Тени должен быть от 0 до 2")
    nonnegative_int(data["player_turns_started"], "Число начатых ходов Калисты")
    validate_campaign(data)
    validate_action_state(data)
    for enemy in data["enemies"]:
        if "side" in enemy and enemy["side"] not in ("Враг", "Союзник", "Нейтральный"):
            raise ValueError("Неизвестная сторона участника боя")
    if saved.get('schema_version',5)<21:
        invalidate_player_requests(data,'Правила эффектов обновлены; предложи действие заново')
    for _,target in participants(data):
        nonnegative_int(target.get('fear_immunity_turns',0),'Иммунитет к страху')
    for spell in data['spells']:
        if spell.get('dot',{}):
            if spell['dot'].get('name') in ('Горение','Проклятие'):
                kind='burn' if spell['dot']['name']=='Горение' else 'curse'
                spell['dot']['damage']=kalista_dot_damage(data,kind)
        spell['desc']=spell.get('desc','').replace('18 урона','6% Интеллекта × (1 + сила заклинаний)').replace('10 урона','4% Интеллекта × (1 + сила заклинаний)')
    initialize_progress(data)
    if data["ally"].get("sheet_profile"):initialize_progress(data["ally"]["sheet_profile"])
    data["schema_version"] = 22
    return data


def spell_raw(base, power, dual=False, soul=False):
    d=round(base*(1+power))
    if dual: d=round(d*1.05)
    if soul: d=round(d*1.40)
    return d


EFFECT_KINDS = {
    "note": "Статус / заметка", "shield": "Щит", "dot": "Периодический урон",
    "weakness": "Слабость", "fear": "Страх", "hot": "Периодическое лечение", "armor": "Поправка к броне", "resist": "Поправка к сопротивлению",
}


DAMAGE_TYPES = ["Физический"] + ELEMENTS


def nonnegative_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label}: требуется целое число от 0")
    return value


def hp_fields(target):
    return ("hp_current", "hp_max") if "hp_current" in target else ("hp", "hp_max")


def participant(data, token):
    if token.startswith('npc:'):
        npc=npc_record(data,token.split(':',1)[1])
        if npc: return npc['combat']
        raise ValueError('NPC больше не существует')
    if token == "player":
        return data
    if token == "ally":
        return data["ally"]
    if isinstance(token, str) and token.startswith("enemy:"):
        for enemy in data["enemies"]:
            if token == f"enemy:{enemy['id']}":
                return enemy
    raise ValueError("Цель больше не существует")


def participants(data):
    return [("player", data), ("ally", data["ally"])] + [
        (f"enemy:{enemy['id']}", enemy) for enemy in data["enemies"]]


def participant_label(data, token):
    target = participant(data, token)
    suffix = f" · #{target['id']}" if token.startswith("enemy:") else ""
    return target["name"] + suffix


def validate_effect(effect):
    if not isinstance(effect, dict):
        raise ValueError("Эффект должен быть объектом")
    if effect.get("kind") not in EFFECT_KINDS:
        raise ValueError("Неизвестный вид эффекта")
    if not isinstance(effect.get("name"), str) or not effect["name"].strip():
        raise ValueError("Эффекту нужно название")
    kind = effect["kind"]
    value = effect.get("value", 0)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Величина эффекта должна быть целым числом")
    if kind in ("shield", "dot", "hot") and value < 0:
        raise ValueError("Щит, урон и лечение не могут быть отрицательными")
    duration = effect.get("duration")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration, int) or duration < 1):
        raise ValueError("Длительность должна быть положительной или бессрочной")
    if kind in ("dot", "hot", "weakness", "fear") and duration is None:
        raise ValueError("Периодическому эффекту нужно количество срабатываний")
    if kind in ("dot", "resist") and effect.get("element", "Огонь") not in DAMAGE_TYPES:
        raise ValueError("Неизвестный тип урона или сопротивления")
    if kind == "resist" and effect.get("element", "Огонь") == "Физический":
        raise ValueError("Физическую защиту задавай поправкой к броне")
    if "id" in effect and (not isinstance(effect["id"], str) or not effect["id"]):
        raise ValueError("Неверный ID эффекта")
    if "applied_round" in effect:
        nonnegative_int(effect["applied_round"], "Раунд применения")
    for key in ("source", "desc"):
        if key in effect and not isinstance(effect[key], str):
            raise ValueError(f"{key}: ожидается текст")


def add_effect(target, effect, round_number=0, stack=False):
    validate_effect(effect)
    if effect["kind"] == "fear" and target.get("fear_immunity_turns", 0) > 0:
        return None
    entry = deepcopy(effect)
    entry.setdefault("value", 0)
    entry.setdefault("duration", None)
    entry.setdefault("element", "Огонь")
    entry.setdefault("source", "Ведущий")
    entry.setdefault("desc", "")
    entry["id"] = uuid4().hex
    entry["applied_round"] = round_number
    effects = target.setdefault("effects", [])
    if not stack:
        # Разные источники могут действовать независимо. Повтор того же эффекта
        # заменяет величину и длительность, а не суммирует их скрыто.
        for index, old in enumerate(effects):
            if (old["kind"], old["name"], old.get("source", ""), old.get("element", "Огонь")) == (
                    entry["kind"], entry["name"], entry["source"], entry["element"]):
                entry["id"] = old["id"]
                effects[index] = entry
                return entry
    effects.append(entry)
    return entry


def effective_defense(target, damage_type):
    if damage_type not in DAMAGE_TYPES:
        raise ValueError("Неизвестный тип урона")
    if damage_type == "Физический":
        return max(0, target.get("armor", 0) + sum(
            effect["value"] for effect in target.get("effects", []) if effect["kind"] == "armor"))
    resist = target.get("resists", {}).get(damage_type, 0)
    # Сохраняем прежнее числовое правило Тени: +20 пунктов, с пределом 95.
    if target.get("ten_resist_boost", 0) > 0:
        resist = min(95, resist + 20)
    return max(-100,min(95,resist + sum(effect["value"] for effect in target.get("effects", [])
                              if effect["kind"] == "resist" and effect["element"] == damage_type)))


def damage_preview(target, amount, damage_type="Физический", final=False,
                   bypass_shields=False, defense_factor=1.0, apply_stance=True):
    nonnegative_int(amount, "Урон")
    if not isinstance(defense_factor, (int, float)) or not math.isfinite(defense_factor) or not 0 <= defense_factor <= 1:
        raise ValueError("Неверная доля сопротивления")
    defense = effective_defense(target, damage_type) * defense_factor
    if not final and damage_type != "Физический":
        incoming=max(0,round(amount*(1-defense/100)))
    else:
        incoming=amount if final else real_dmg(amount,defense)
    racial_reduction = 0
    if not final and damage_type == "Тьма" and "dark_resist" in target.get("passives", {}):
        protected = round(incoming * .9)
        racial_reduction = incoming - protected
        incoming = protected
    if apply_stance and target.get('defensive_stance'):incoming=round(incoming*.7)
    capacity = sum(effect["value"] for effect in target.get("effects", []) if effect["kind"] == "shield")
    absorbed = 0 if bypass_shields else min(incoming, capacity)
    hp_key, _ = hp_fields(target)
    hp_loss = min(max(0, target[hp_key]), incoming - absorbed)
    return {"raw":amount,"damage_type":damage_type,"final":final,"stance":bool(apply_stance and target.get("defensive_stance")),"incoming": incoming, "absorbed": absorbed, "hp_loss": hp_loss, "racial_reduction": racial_reduction,
            "overkill": incoming - absorbed - hp_loss, "defense": defense,
            "hp_after": max(0, target[hp_key] - hp_loss)}


def apply_damage(target, amount, damage_type="Физический", final=False,
                 bypass_shields=False, defense_factor=1.0, apply_stance=True):
    result = damage_preview(target, amount, damage_type, final, bypass_shields, defense_factor, apply_stance)
    remaining = result["absorbed"]
    if remaining:
        # Порядок наложения виден в списке эффектов; щиты расходуются в том же порядке.
        for effect in target.get("effects", []):
            if effect["kind"] == "shield" and remaining:
                used = min(effect["value"], remaining)
                effect["value"] -= used
                remaining -= used
        target["effects"] = [effect for effect in target.get("effects", [])
                             if effect["kind"] != "shield" or effect["value"] > 0]
    target[hp_fields(target)[0]] = result["hp_after"]
    return result


def apply_healing(target, amount):
    nonnegative_int(amount, "Лечение")
    hp_key, maximum_key = hp_fields(target)
    before = max(0, target[hp_key])
    restored = min(amount, max(0, target[maximum_key] - before))
    target[hp_key] = before + restored
    return {"restored": restored, "excess": amount - restored, "hp_after": target[hp_key]}


def restore_mana(target, amount):
    nonnegative_int(amount, "Мана")
    if "mana_current" not in target or "mana_max" not in target:
        raise ValueError("У этой цели нет отдельного ресурса маны")
    restored = min(amount, max(0, target["mana_max"] - target["mana_current"]))
    target["mana_current"] += restored
    observe_mana_reserve(target)
    return restored


def observe_mana_reserve(data):
    """Достижение порога разрешает следующую активацию после падения маны."""
    if data.get("mana_max", 0) > 0 and data["mana_current"] * 5 >= data["mana_max"]:
        data["mana_reserve_armed"] = True


def tick_mana_regeneration(data):
    """Один тик в конце полного раунда; порог проверяется до восстановления."""
    observe_mana_reserve(data)
    ticks = data.get("mana_reserve_ticks", 0)
    messages = []
    if (ticks == 0 and data.get("mana_reserve_armed", True)
            and data["mana_max"] > 0 and data["mana_current"] * 5 < data["mana_max"]):
        ticks = 3
        data["mana_reserve_armed"] = False
        messages.append("Магический резерв активирован: 3 усиленных восстановления")
    amount = round(data["mana_regen"] * 1.5) if ticks else data["mana_regen"]
    restored = restore_mana(data, amount)
    data["mana_reserve_ticks"] = max(0, ticks - 1)
    messages.append(f"Регенерация маны: +{restored} MP" +
                    (f" · резерв: оставшихся восстановлений — {data['mana_reserve_ticks']}" if ticks else ""))
    if ticks == 1:
        messages.append("Магический резерв завершён")
    return messages


def damage_message(name, result):
    detail=f"{result.get('raw',result['incoming'])} урона → после защиты {result['incoming']} → щит −{result['absorbed']} → HP −{result['hp_loss']} (осталось {result['hp_after']})"
    if result.get('components_detail'):
        detail=' + '.join(f"{x['element']}: {x['raw']:g} → {x['after']:g}" for x in result['components_detail'])+' → '+detail
    if result.get('racial_reduction'):detail+=f" · защита от Тьмы −{result['racial_reduction']}"
    if result.get('stance'):detail+=' · стойка −30% учтена'
    if result.get('overkill'):detail+=f" · избыточный урон {result['overkill']}"
    return name+': '+detail


def tick_periodic(target):
    """Каждый периодический эффект тикает один раз в конце хода цели."""
    messages = []
    if target.get("fear_immunity_turns", 0) > 0:
        target["fear_immunity_turns"] -= 1
        if target["fear_immunity_turns"] == 0:
            messages.append(f"Иммунитет к страху завершён: {target['name']}")
    for effect in list(target.get("effects", [])):
        if effect['kind'] in ('weakness','fear'):
            effect['duration']-=1
            if effect['duration']<=0:
                if effect['kind']=='fear':
                    target['fear_immunity_turns']=1
                    messages.append(f"Иммунитет к страху: до конца следующего личного хода — {target['name']}")
                target['effects']=[item for item in target['effects'] if item['id']!=effect['id']]
                messages.append(f"«{effect['name']}» завершён: {target['name']}")
            continue
        if effect["kind"] not in ("dot", "hot"):
            continue
        if effect["kind"] == "dot":
            result = apply_damage(target, effect["value"], effect["element"])
            messages.append(f"«{effect['name']}»: " + damage_message(target["name"], result))
        else:
            result = apply_healing(target, effect["value"])
            messages.append(f"«{effect['name']}»: {target['name']} +{result['restored']} HP")
        effect["duration"] -= 1
        if effect["duration"] <= 0:
            target["effects"] = [item for item in target["effects"] if item["id"] != effect["id"]]
            messages.append(f"«{effect['name']}» завершён: {target['name']}")
    return messages


def tick_round_effects(target, completed_round):
    messages = []
    kept = []
    for effect in target.get("effects", []):
        if (effect["kind"] not in ("dot", "hot", "weakness", "fear") and effect["duration"] is not None
                and effect.get("applied_round", 0) < completed_round):
            effect["duration"] -= 1
        if effect["duration"] is None or effect["duration"] > 0:
            kept.append(effect)
        else:
            messages.append(f"«{effect['name']}» истёк: {target['name']}")
    target["effects"] = kept
    return messages


def actor_target(data, actor):
    if actor is None:
        return None
    token = f"enemy:{actor['id']}" if actor["kind"] == "enemy" else actor["kind"]
    try:
        return participant(data, token)
    except ValueError:
        return None


def activate_shadow_invisibility(data):
    """Ход активации — первый; заканчиваем на втором следующем начале хода."""
    if data["ten"] < 5:
        raise ValueError("Для невидимости нужно 5 Тени")
    data["ten"] = 0
    data["ten_invis"] = True
    data["ten_invis_turn_starts_left"] = 2
    record_turn_action(data,'player','Невидимость',data['name'],'До начала третьего хода после активации',counts=False)
    return "Тень: невидимость до начала 3-го хода Калисты (ход активации — 1-й)"


def activate_shadow_resistance(data):
    if data["ten"] < 5:
        raise ValueError("Для сопротивлений нужно 5 Тени")
    data["ten"] = 0
    data["ten_resist_boost"] = 2
    record_turn_action(data,'player','Сопротивления Тени',data['name'],'+20 до начала третьего хода после активации',counts=False)
    return "Тень: +20 к сопротивлениям до начала 3-го хода Калисты (ход активации — 1-й)"


def begin_actor_turn(data):
    """Считаем только настоящее начало хода Калисты при продвижении очереди."""
    actor = get_current_actor(data)
    data["turn_serial"] = data.get("turn_serial", 0) + 1
    data["turn_actions"] = []
    invalidate_player_requests(data,'Ход завершён; предложи действие в актуальном ходе')
    if actor:
        combatant = actor_target(data, actor)
        if combatant:
            combatant['movement_used']=False
            combatant['defensive_stance']=False
        for ability in (combatant or {}).get("actions", []):
            ability["cooldown_left"] = max(0, ability.get("cooldown_left", 0) - 1)
    messages=[]
    if actor and actor['kind']=='player':
        data['player_turns_started']=data.get('player_turns_started',0)+1
        if data.get('ten_invis'):
            data['ten_invis_turn_starts_left']-=1
            if data['ten_invis_turn_starts_left']==0:
                data['ten_invis']=False
                messages.append('Невидимость спала: начало 3-го хода Калисты после активации')
        if data.get('ten_resist_boost',0)>0:
            data['ten_resist_boost']-=1
            if data['ten_resist_boost']==0:messages.append('Сопротивления Тени истекли: начало 3-го хода Калисты после активации')
    if actor and any(e['kind']=='fear' for e in (combatant or {}).get('effects',[])):
        message=f"{combatant['name']}: пропускает ход — Страх"
        record_turn_action(data,actor_token(actor),'Страх',combatant['name'],message,counts=False)
        return messages+[message]+advance_turn(data)
    return messages


def finish_round(data):
    completed = data["round"]
    messages = tick_mana_regeneration(data)
    for _, target in participants(data):
        messages.extend(tick_round_effects(target, completed))
    for spell in data["spells"]:
        if spell["cd_left"] > 0:
            spell["cd_left"] -= 1
    data["round"] += 1
    data["turn_order"] = build_turn_order(data)
    data["current_turn"] = 0
    messages.append(f"=== Раунд {data['round']} ===")
    messages.extend(begin_actor_turn(data))
    return messages


def advance_turn(data):
    if not data["combat_active"]:
        raise ValueError("Бой не начат")
    messages = []
    if not data["turn_order"]:
        messages.append("Нет участников с HP выше 0; восстанови HP и начни бой заново.")
        return messages
    target = actor_target(data, get_current_actor(data))
    if target is not None:target['eye_damage_boost']=False
    if target is not None and target[hp_fields(target)[0]] > 0:
        messages.extend(tick_periodic(target))
    data["current_turn"] += 1
    # Удалённые и поверженные участники не получают пустые ходы.
    while data["current_turn"] < len(data["turn_order"]):
        target = actor_target(data, data["turn_order"][data["current_turn"]])
        if target is not None and target[hp_fields(target)[0]] > 0:
            messages.extend(begin_actor_turn(data))
            return messages
        data["current_turn"] += 1
    messages.extend(finish_round(data))
    return messages


def spell_action(spell):
    return spell.get("action", "damage")


def shadow_shield_amount(data):
    return round(total_stat(data,'Интеллект')*(1+data.get('spell_power',0)))


def outgoing_damage(source,amount,damage_type):
    amount=round(amount*2) if source.get('eye_damage_boost') else amount
    return round(amount*.65) if damage_type=='Физический' and any(e['kind']=='weakness' for e in source.get('effects',[])) else amount


def kalista_dot_damage(data, kind):
    coefficient = {"burn": .06, "curse": .04}[kind]
    return round(total_stat(data, "Интеллект") * (1 + data.get("spell_power", 0)) * coefficient)


def roll_spell_effects(data,spell,target):
    if spell_action(spell)!='damage' or target[hp_fields(target)[0]]<=0:return []
    rolls=[]
    if 'Огонь' in spell['school']:
        rolls.append(('dot','Горение',kalista_dot_damage(data,'burn'),'Огонь',3,.5,'burn'))
    if 'Тьма' in spell['school']:
        rolls.extend([('dot','Проклятие',kalista_dot_damage(data,'curse'),'Тьма',3,.5,'curse'),('weakness','Слабость',35,'Тьма',2,.35,'weakness')])
    if spell['name'] in ('Разряд бездны','Пламя души'):
        chance=.5*(1-min(.9,max(0,target.get('control_resist',0))))
        rolls.append(('fear','Страх',0,'Тьма',2,chance,'fear'))
    messages=[]
    for kind,name,value,element,duration,chance,key in rolls:
        if kind=="fear" and target.get("fear_immunity_turns",0)>0:
            messages.append("Страх: цель защищена иммунитетом до конца следующего личного хода")
            continue
        roll=random.random()
        if roll<chance:
            # All Kalista spells refresh this status rather than stacking it.
            if kind=='dot':
                value=max([value]+[e['value'] for e in target.get('effects',[]) if e['kind']==kind and e['name']==name and (e.get('source','').startswith('spell:') or e.get('source','').startswith('kalista:'))])
            target['effects']=[e for e in target.get('effects',[]) if not (e['kind']==kind and e['name']==name and (e.get('source','').startswith('spell:') or e.get('source','').startswith('kalista:')))]
            add_effect(target,dict(kind=kind,name=name,value=value,element=element,duration=duration,source='kalista:'+key),data['round'] if data['combat_active'] else 0)
            messages.append(f'{name}: наложено на {duration} хода цели (бросок {roll*100:.1f}% < {chance*100:.1f}%)')
        else:messages.append(f'{name}: не наложено (бросок {roll*100:.1f}% ≥ {chance*100:.1f}%)')
    return messages


def spell_damage_preview(data,spell,target,raw,final_damage=None):
    if final_damage is not None:return damage_preview(target,final_damage,final=True)
    if spell['name']=='Теневой укол':return damage_preview(target,raw,final=True)
    schools=['Огонь','Тьма'] if spell['school']=='Огонь+Тьма' else ['Огонь' if 'Огонь' in spell['school'] else 'Тьма']
    incoming=0.0
    racial_reduction=0.0
    details=[]
    for element in schools:
        part=raw/len(schools)
        defense=effective_defense(target,element)
        if element=='Огонь' and data.get('pepel_empower'):defense*=.7
        reduced=max(0,part*(1-defense/100))
        if element=='Тьма' and 'dark_resist' in target.get('passives',{}):
            racial_reduction+=reduced*.1;reduced*=.9
        details.append(dict(element=element,raw=part,after=round(reduced,2)))
        incoming+=reduced
    result=damage_preview(target,round(incoming),final=True)
    result['raw']=raw
    result['components_detail']=details
    result['racial_reduction']=round(racial_reduction)
    result['components']=[{'element':el,'share':1/len(schools)} for el in schools]
    return result


def spell_damage_apply(data,spell,target,raw,final_damage=None):
    preview=spell_damage_preview(data,spell,target,raw,final_damage)
    result=apply_damage(target,preview['incoming'],final=True,apply_stance=False)
    for key in ('raw','components_detail','stance','racial_reduction'): 
        if key in preview:result[key]=preview[key]
    return result


def cast_spell(data, spell, target, crit=False, final_damage=None, shield_amount=None):
    if crit:raise ValueError("Крит определяется автоматически, назначать его вручную нельзя")
    """Проверяем всё до расходования ресурсов. Решения о целях/крите принимает UI."""
    check_action_limit(data, "player")
    if data['hp_current']<=0: raise ValueError('У Калисты 0 HP')
    action = spell_action(spell)
    if action not in ("damage", "heal", "shield", "note"):
        raise ValueError("Неизвестное действие заклинания")
    if spell["mana"] > data["mana_current"]:
        raise ValueError("Не хватает маны")
    if spell.get("cd_left", 0) > 0:
        raise ValueError("Заклинание ещё на перезарядке")
    if action in ("heal", "shield", "damage"):
        if target is None:
            raise ValueError("Выбери цель")
    target_token=next((t for t,v in participants(data) if v is target),None)
    if action=='damage' and target_token:
        check_reach(data,'player',dict(kind='damage',damage_type='Тьма',reach=spell.get('reach','Дальняя')),target_token)
    amount = spell["base"]
    if action == "shield":
        amount = shadow_shield_amount(data) if spell["name"]=="Покров тьмы" else (spell.get("effect_value", 0) if shield_amount is None else shield_amount)
        nonnegative_int(amount, "Сила щита")
        if amount == 0:
            raise ValueError("Укажи силу щита: в исходных правилах её значение не задано")
    if action == "heal":
        amount = spell.get("effect_value", 0)
        nonnegative_int(amount, "Лечение")
        if amount == 0:
            raise ValueError("Укажи величину лечения выше 0")
    if final_damage is not None:
        nonnegative_int(final_damage, "Итоговый урон")
    effect = None
    if action in ("heal", "shield", "note"):
        effect = {"kind": "shield" if action == "shield" else "note", "name": spell["name"],
                  "value": amount if action == "shield" else 0,
                  "duration": spell.get("effect_duration") or None,
                  "source": f"spell:{spell['id']}", "desc": spell.get("desc", "")}
        validate_effect(effect)
    dual, soul = spell_bonuses(data, spell)
    raw = spell_raw(amount, data.get("spell_power", 0), dual, soul) if action == "damage" else amount
    if crit and action == "damage":
        raw = round(raw * 1.5)
    empowered=bool(data.get('pepel_empower') and 'Огонь' in spell['school'] and action=='damage' and raw>0 and spell['name']!='Теневой укол')
    if target is not None and action=='damage' and raw>0:
        spell_damage_preview(data,spell,target,raw,final_damage)
    observe_mana_reserve(data)
    data["mana_current"] -= spell["mana"]
    data["last_school"] = spell["school"]
    spell["cd_left"] = spell.get("cd_max", 0)
    if spell.get("gives") in ("pepel", "both"):
        data["pepel"] = min(5, data["pepel"] + 1)
    if spell.get("gives") in ("ten", "both"):
        data["ten"] = min(5, data["ten"] + 1)
    if soul and action == "damage":
        data["soul_flame_boost"] = False
    messages = [f"«{spell['name']}» (−{spell['mana']} MP)" + (" · КРИТ" if crit and action == "damage" else "")]
    if target is not None and action == "damage":
        missed=bool(target_token and ranged_miss_chance(data,'player',spell,target_token) and random.random()<.5)
        if missed:
            messages.append('Промах: дальнее заклинание в ближнем бою (шанс промаха 50%)')
            if empowered:data['pepel_empower']=False
        elif raw > 0:
            if final_damage is None and random.random()<effective_crit_chance(data):
                raw=round(raw*1.5)
                messages.append('КРИТ: автоматический бросок по шансу Калисты · урон ×1,5')
            result=spell_damage_apply(data,spell,target,raw,final_damage)
            messages.append(damage_message(target['name'],result))
            target_token=next(t for t,v in participants(data) if v is target)
            messages.extend(counterattack(data,'player',target_token,result))
            if final_damage is not None:messages.append('Урон назначен ведущим; щит учтён')
            if empowered:data['pepel_empower']=False
        if not missed:messages.extend(roll_spell_effects(data,spell,target))
    elif action == "heal":
        result = apply_healing(target, amount)
        messages.append(f"{target['name']}: +{result['restored']} HP (избыток {result['excess']})")
    elif action in ("shield", "note"):
        recipient = target if target is not None else data
        add_effect(recipient, effect, data["round"] if data["combat_active"] else 0)
        messages.append(f"{recipient['name']}: {spell['name']}" + (f" · щит {amount}" if action == "shield" else ""))
    record_turn_action(data, "player", spell["name"], target["name"] if target else data["name"], " · ".join(messages))
    return messages


def build_turn_order(data):
    order = []
    for token, target in participants(data):
        if token in data.get("turn_excluded", []) or target[hp_fields(target)[0]] <= 0:
            continue
        kind = "enemy" if token.startswith("enemy:") else token
        order.append({"kind": kind, "id": target["id"] if kind == "enemy" else 0,
                      "name": target["name"],
                      "init": data.get("initiative_overrides", {}).get(token, target.get("initiative", 10))})
    order.sort(key=lambda actor: -actor["init"])
    return order


def refresh_turn_order(data):
    """Добавление участника не должно переключать текущий ход."""
    actor = get_current_actor(data)
    order = build_turn_order(data)
    # Новые участники вступают после текущего хода; порядок следующего раунда
    # снова строится по инициативе.
    if actor:
        old = data["turn_order"]
        latest = {(item["kind"], item["id"]): item for item in order}
        for item in old:
            replacement = latest.get((item["kind"], item["id"]))
            if replacement:
                item["name"] = replacement["name"]
                item["init"] = replacement["init"]
        known = {(item["kind"], item["id"]) for item in old}
        old.extend(item for item in order if (item["kind"], item["id"]) not in known)
    else:
        data["turn_order"] = order
        data["current_turn"] = 0


def get_current_actor(data):
    if not data["turn_order"]: return None
    idx=data["current_turn"] % len(data["turn_order"])
    return data["turn_order"][idx]


def validate_item_use(use):
    if use is None:
        return
    if not isinstance(use, dict) or use.get("kind") not in ("heal", "mana", "shield"):
        raise ValueError("Неизвестное действие предмета")
    nonnegative_int(use.get("value"), "Величина действия предмета")
    nonnegative_int(use.get("duration", 0), "Длительность действия предмета")


def use_item(data, item):
    use = item.get("use")
    validate_item_use(use)
    if not use or item["qty"] <= 0:
        raise ValueError("Предмет недоступен")
    amount = use["value"]
    if amount <= 0:
        raise ValueError("Укажи величину действия предмета выше 0")
    if use["kind"] == "heal":
        result = apply_healing(data, amount)
        actual = result["restored"]
        message = f"{item['name']}: +{actual} HP (избыток {result['excess']})"
    elif use["kind"] == "mana":
        actual = restore_mana(data, amount)
        message = f"{item['name']}: +{actual} MP"
    else:
        add_effect(data, {"kind": "shield", "name": item["name"], "value": amount,
                          "duration": use.get("duration") or None, "source": f"item:{item['name']}"},
                   data["round"] if data["combat_active"] else 0)
        actual = amount
        message = f"{item['name']}: щит {amount}"
    if actual > 0:
        item["qty"] -= 1
        record_turn_action(data,'player',item['name'],data['name'],message,counts=False)
        return message + " · использован 1 предмет"
    return message + " · предмет сохранён, ресурс уже заполнен"


def actor_token(actor):
    return f"enemy:{actor['id']}" if actor["kind"] == "enemy" else actor["kind"]


def set_initiative(data, token, value):
    participant(data, token)
    nonnegative_int(value, "Инициатива")
    data.setdefault("initiative_overrides", {})[token] = value
    # Уже сыгранные ходы и текущий актёр остаются на месте.
    if data["combat_active"] and data["turn_order"]:
        current = data["current_turn"]
        prefix = data["turn_order"][:current + 1]
        tail = data["turn_order"][current + 1:]
        for actor in data["turn_order"]:
            if actor_token(actor) == token:
                actor["init"] = value
        tail.sort(key=lambda actor: -actor["init"])
        data["turn_order"] = prefix + tail


def move_in_queue(data, token, offset):
    if offset not in (-1, 1):
        raise ValueError("Разрешён сдвиг на одну позицию")
    order = data["turn_order"]
    selected = next((i for i, actor in enumerate(order) if actor_token(actor) == token), None)
    if selected is None:
        raise ValueError("Участника нет в очереди")
    destination = selected + offset
    if not 0 <= destination < len(order):
        return False
    current = get_current_actor(data)
    order[selected], order[destination] = order[destination], order[selected]
    if current:
        data["current_turn"] = next(i for i, actor in enumerate(order) if actor_token(actor) == actor_token(current))
    return True


def exclude_from_queue(data, token):
    participant(data, token)
    excluded = data.setdefault("turn_excluded", [])
    if token not in excluded: excluded.append(token)
    current = get_current_actor(data)
    index = data["current_turn"]
    data["turn_order"] = [actor for actor in data["turn_order"] if actor_token(actor) != token]
    if not data["turn_order"]:
        data["current_turn"] = 0
        return []
    if current and actor_token(current) != token:
        data["current_turn"] = next(i for i, actor in enumerate(data["turn_order"]) if actor_token(actor) == actor_token(current))
    else:
        data["current_turn"] = index
        if index >= len(data["turn_order"]):
            return finish_round(data)
        return begin_actor_turn(data)
    return []


def return_to_queue(data, token):
    target = participant(data, token)
    data["turn_excluded"] = [item for item in data.get("turn_excluded", []) if item != token]
    if target[hp_fields(target)[0]] > 0 and data["combat_active"]:
        refresh_turn_order(data)


def add_history(history, before, after, label, limit=20):
    if before == after:
        return False
    history.append({"data": deepcopy(before), "label": label})
    del history[:-limit]
    return True


def special_availability(data, key):
    passive = data["passives"][key]
    if passive["used"]: return False, "Уже использовано"
    if key == "cold_calculation" and data["combat_active"]:
        actor = get_current_actor(data)
        if data.get("player_turns_started", 0) != 1 or not actor or actor["kind"] != "player":
            return False, "Доступно до боя или в первый ход Калисты"
    return True, ""


def activate_special(data, key):
    allowed, reason = special_availability(data, key)
    if not allowed: raise ValueError(reason)
    data["passives"][key]["used"] = True
    if key == "ritual_black_flame": data["soul_flame_boost"] = True
    if key == "cold_calculation": data["crit_boost_active"] = True
    record_turn_action(data,'player',data['passives'][key]['name'],data['name'],'Усиление активировано',counts=False)
    return f"Особое умение: {data['passives'][key]['name']}"


def effective_crit_chance(data):
    return min(1.0, max(0.0, data.get("crit_chance", .065) + (.10 if data.get("crit_boost_active") else 0)))


def start_combat(data):
    begin_rewards(data)
    for _,target in participants(data):
        target['eye_damage_boost']=False;target['defensive_stance']=False;target['eye_used']=False;target['movement_used']=False
    data["combat_active"] = True
    for _, target in participants(data):
        for effect in target.get("effects", []): effect["applied_round"] = 0
    data["round"] = 1
    data["player_turns_started"] = 0
    data["turn_order"] = build_turn_order(data)
    data["current_turn"] = 0
    return ["=== Бой начат. Раунд 1 ==="] + begin_actor_turn(data)


def _end_combat(data):
    reward=settle_rewards(data)
    data["combat_active"] = False
    for _,target in participants(data):
        target['eye_damage_boost']=False;target['defensive_stance']=False;target['movement_used']=False
        target['effects']=[effect for effect in target.get('effects',[]) if effect['kind']!='shield']
    fallen=[enemy for enemy in data['enemies'] if enemy['hp']<=0 and enemy.get('side','Враг')=='Враг']
    if fallen:
        data.setdefault('defeated_enemies',[]).extend(deepcopy(fallen))
        data['enemies']=[enemy for enemy in data['enemies'] if enemy not in fallen]
        tokens={t for t,_ in participants(data)}
        data['distances']={key:value for key,value in data.get('distances',{}).items() if set(key.split('|'))<=tokens}
        data['initiative_overrides']={key:value for key,value in data.get('initiative_overrides',{}).items() if key in tokens}
        data['turn_excluded']=[key for key in data.get('turn_excluded',[]) if key in tokens]
    data["turn_order"] = []
    data["current_turn"] = 0
    data["player_turns_started"] = 0
    data["crit_boost_active"] = False
    data["passives"]["cold_calculation"]["used"] = False
    data['turn_serial']=data.get('turn_serial',0)+1
    data['turn_actions']=[]
    invalidate_player_requests(data,'Бой завершён')
    suffix=""
    if reward:
        suffix=" · Опыт: "+"; ".join(f"{h['name']} +{h['xp']} XP"+(f" · уровень {h['level_before']} → {h['level_after']} · +{h['free_points']} очков" if h['free_points'] else "") for h in reward['heroes'])
    return "=== Бой окончен ==="+suffix


def end_combat(data):
    candidate=deepcopy(data)
    message=_end_combat(candidate)
    data.clear();data.update(candidate)
    return message


def spell_bonuses(data, spell):
    # Одна функция для предпросмотра и применения; периодический урон не усиливаем.
    damage = spell_action(spell) == "damage"
    dual = damage and {data.get("last_school"), spell["school"]} == {"Огонь", "Тьма"}
    soul = bool(damage and data.get("soul_flame_boost") and spell["name"] == "Пламя души")
    return dual, soul


def exclude_from_queue_after_delete(data, token):
    # Удаляем запись из очереди тем же способом, без требования существующей цели.
    data.setdefault("turn_excluded", [])
    current = get_current_actor(data)
    index = data["current_turn"]
    data["turn_order"] = [actor for actor in data["turn_order"] if actor_token(actor) != token]
    data["initiative_overrides"].pop(token, None)
    data["turn_excluded"] = [item for item in data["turn_excluded"] if item != token]
    if not data["turn_order"]: data["current_turn"] = 0
    elif current and actor_token(current) != token:
        data["current_turn"] = next(i for i, actor in enumerate(data["turn_order"]) if actor_token(actor) == actor_token(current))
    elif index >= len(data["turn_order"]):
        return finish_round(data)
    else:
        data["current_turn"] = index
        return begin_actor_turn(data)
    return []


def combatant_heal(data, healer_token, recipient_token, amount):
    """Лечение по решению ведущего; неизвестные стоимость и кулдаун не добавляем."""
    nonnegative_int(amount, "Сила лечения")
    healer = participant(data, healer_token)
    recipient = participant(data, recipient_token)
    if healer[hp_fields(healer)[0]] <= 0:
        raise ValueError("У лечащего участника 0 HP")
    if amount <= 0:
        raise ValueError("Укажи силу лечения выше 0")
    result = apply_healing(recipient, amount)
    record_turn_action(data, healer_token, "Лечение", recipient["name"], f"+{result['restored']} HP")
    if data["combat_active"]: refresh_turn_order(data)
    return (f"{participant_label(data, healer_token)} → {participant_label(data, recipient_token)}: "
            f"лечение +{result['restored']} HP (избыток {result['excess']})")


SHEOGARATH_REFERENCE = {'name': 'Шеогарат', 'race': 'Драконит', 'class': 'Вне класса', 'texts': {'traits': 'Видящий - возможность видеть суть вещей (трансформируемый)\nСкорострел - возможность нанести две атаки одновременно (рукопашка трансформируемый)\nДесница Ока - раз в три хода пробитие +10 +урон 1к6 игнорирует Крит неудачу (Кул даун 7 дней)\nСовершенная контр атака - всякий раз контратакую атаку ближнего боя ', 'attacks': '', 'notes-1': 'Грогор - кент крутой \nЭван - торгаш зерна кент грогора', 'items': 'Бездонная сумка:', 'equipment': 'Двуручный меч холода (уникальный) 🔵\nГрозовой меч 🔵\nСапоги ниргхала  (🟠 1/8) (невозможно сбить с ног)', 'allies': 'Китис УВАЖЕЕЕЕЕНИЕ', 'notes-2': 'Элиза - богиня смерти\nГрегор - бог мучений и страданий \nМилитара - богиня воинов\nРевиронг - бог меткости и леса\nХарт - бог авантюр, лжи и хитрости\nСата - богиня удачи \nФералис - бог жизни и света'}, 'attacks': [{'name': 'Кислотные брызги', 'formula': '1d8+[con]', 'notes': '30 м\nТикающий дэбафф 3х -2 брони стак до 5', 'type': ''}, {'name': 'Когти', 'formula': '1d6+[dex]', 'notes': '\n', 'type': 'Коо'}, {'name': 'Газовое облако ', 'formula': '1d10+[con]', 'notes': 'Область применения 10х10', 'type': ''}, {'name': 'Двуручный меч', 'formula': '2d6+[str]+2', 'notes': '', 'type': 'Режущий'}], 'resources': [{'name': 'Лагерь истинного авантюриста', 'qty': 1, 'max': 1}, {'name': 'Голова кельтузада', 'qty': 1, 'max': 1}, {'name': 'Первородная эссенция', 'qty': 9, 'max': 1}], 'coins': {'gp': 4837, 'total': 4959.43, 'sp': 1089, 'cp': 1754, 'pp': 0, 'ep': 0}, 'bonuses': [{'target': 'weapon.weapon-1789683947798.attack', 'formula': '2', 'label': ''}, {'target': 'weapon.weapon-1789683947798.damage', 'formula': '1d8', 'label': 'Холод'}], 'speed': '60'}


def imported_friend():
    ally = {"name":"Персонаж друга", "hp":440, "hp_max":690, "armor":185,
            "initiative":12, "attack_damage":302, "attack_type":"Физический", "heal_amount":0,
            "effects":[], "dots":[], "element_defense_mode":"percent",
            "description":"Уровень 17 · Ледяная скорбь",
            "resists":{"Огонь":10,"Земля":95,"Вода":10,"Воздух":10,"Тьма":50,"Свет":-50},
            "sheet_profile":{"source":"Лист_персонажа_тест_заебло.xlsx", "level":17, "race":"", "class":"", "free_points":64,
                "stats":{"Сила":60,"Выносливость":35,"Ловкость":35,"Мудрость":10,"Интеллект":10,"Харизма":0},
                "base_stats":{"Сила":10,"Выносливость":10,"Ловкость":10,"Мудрость":10,"Интеллект":10,"Харизма":10},
                "attack":302.4,"critical_damage":654.8,"critical_chance":13.75,
                "equipment":[{"slot":"Оружие 1","name":"Ледяная скорбь","description":"0/100", "bonuses":{"Сила":50,"Выносливость":25,"Ловкость":25,"Харизма":-10,"Атака":270,"Критический урон":50,"Шанс крита":7,"Тьма":50,"Свет":-50}}],
                "abilities":"", "notes":"Имя, раса, класс и способности не заполнены в исходном листе. Инициатива не указана; её можно задать вручную."}}


    reference = deepcopy(SHEOGARATH_REFERENCE)
    ally['name'] = reference['name']
    ally['description'] = ''
    profile = ally['sheet_profile']
    profile.update(race=reference['race'], **{'class':reference['class']}, reference=reference)
    profile['abilities'] = reference['texts']['traits']
    profile['notes'] = '\n\n'.join(reference['texts'][k] for k in ('notes-1','allies','notes-2') if reference['texts'][k])
    profile['source'] += ' + Шеогарат — Long Story Short.json'
    profile['equipment_note'] = reference['texts']['equipment']
    ally['actions'] = friend_actions()
    ally['counterattack_enabled']=True
    ensure_player_sheet(ally)
    fill_warrior_equipment(ally)
    profile['abilities']='Видящий — позволяет видеть суть вещей.\nСкорострел — две атаки мечом за одно действие.\nКонтратака — 65% после потери HP от прямого ближнего удара; обычный удар мечом без расхода действий.\nДесница Ока — +100% урона до конца текущего хода, один раз за бой.'
    return ally


def scene_record(data, scene_id):
    return next((item for item in data['scenes'] if item['id'] == scene_id), None)


def npc_record(data, npc_id):
    return next((item for item in data['npcs'] if item['id'] == npc_id), None)


def validate_campaign(data):
    scene_template = dict(id='', name='', location='', summary='', gm_notes='', result='', status='', npc_ids=[])
    npc_template = dict(id='', name='', role='', location='', description='', public_notes='', gm_notes='', side='',
                        combat=dict(hp=0, hp_max=1, armor=0, attack_damage=0, attack_type='', heal_amount=0,
                                    initiative=0, resists={e:0 for e in ELEMENTS}))
    for records, template in ((data['scenes'], scene_template), (data['npcs'], npc_template)):
        ids = []
        for record in records:
            validate_tree(record, template)
            if not set(template) <= record.keys(): raise ValueError('Неполные данные сцены или NPC')
            if not record['id'].strip() or not record['name'].strip(): raise ValueError('У сцены или NPC должны быть ID и имя')
            ids.append(record['id'])
        if len(ids) != len(set(ids)): raise ValueError('Повторяющиеся ID сцен или NPC')
    npc_ids = {npc['id'] for npc in data['npcs']}
    for scene in data['scenes']:
        if scene['status'] not in ('Подготовка', 'Идёт', 'На паузе', 'Завершена'): raise ValueError('Неизвестный статус сцены')
        if any(not isinstance(npc_id, str) or npc_id not in npc_ids for npc_id in scene['npc_ids']):
            raise ValueError('Сцена ссылается на неизвестного NPC')
        if len(scene['npc_ids']) != len(set(scene['npc_ids'])): raise ValueError('NPC повторяется в сцене')
    for npc in data['npcs']:
        if npc['side'] not in ('Враг', 'Союзник', 'Нейтральный'): raise ValueError('Неизвестная сторона NPC')
        combat = npc['combat']
        if not set(npc_template['combat']) <= combat.keys(): raise ValueError('Неполные боевые характеристики NPC')
        for key in ('hp', 'hp_max', 'armor', 'attack_damage', 'heal_amount', 'initiative'):
            nonnegative_int(combat[key], 'Характеристика NPC')
        if combat['hp_max'] < 1 or combat['hp'] > combat['hp_max']: raise ValueError('HP NPC должны быть в пределах максимума')
        if combat['attack_type'] not in DAMAGE_TYPES: raise ValueError('Неизвестный тип атаки NPC')
        if not set(ELEMENTS) <= combat['resists'].keys(): raise ValueError('Неполные сопротивления NPC')
        for element in ELEMENTS: nonnegative_int(combat['resists'][element], 'Сопротивление NPC')
    if not isinstance(data['active_scene_id'], str): raise ValueError('Неверный ID текущей сцены')
    if data['active_scene_id'] and not scene_record(data, data['active_scene_id']): raise ValueError('Текущая сцена отсутствует')
    active = [scene['id'] for scene in data['scenes'] if scene['status'] == 'Идёт']
    if active != ([data['active_scene_id']] if data['active_scene_id'] else []):
        raise ValueError('Текущая сцена и её статус не совпадают')


def create_scene(data, name, location=''):
    if not name.strip(): raise ValueError('Укажи название сцены')
    scene = dict(id=uuid4().hex, name=name.strip(), location=location.strip(), summary='', gm_notes='', result='',
                 status='Подготовка', npc_ids=[])
    data['scenes'].append(scene)
    return scene


def create_npc(data, name, role=''):
    if not name.strip(): raise ValueError('Укажи имя NPC')
    npc = dict(id=uuid4().hex, name=name.strip(), role=role.strip(), location='', description='', public_notes='', gm_notes='', side='Нейтральный',
               combat=dict(hp=100, hp_max=100, armor=0, attack_damage=0, attack_type='Физический', heal_amount=0,
                           initiative=10, resists={e:0 for e in ELEMENTS}))
    data['npcs'].append(npc)
    return npc


def activate_scene(data, scene_id):
    scene = scene_record(data, scene_id)
    if scene is None: raise ValueError('Сцена больше не существует')
    for other in data['scenes']:
        if other['id'] != scene_id and other['status'] == 'Идёт': other['status'] = 'На паузе'
    scene['status'] = 'Идёт'
    data['active_scene_id'] = scene_id


def update_scene(data, scene_id, changes):
    if scene_record(data, scene_id) is None: raise ValueError('Сцена больше не существует')
    candidate = deepcopy(data)
    scene = scene_record(candidate, scene_id)
    scene.update(changes)
    scene['id'] = scene_id
    scene['name'] = scene['name'].strip()
    if scene['status'] == 'Идёт': activate_scene(candidate, scene_id)
    elif candidate['active_scene_id'] == scene_id: candidate['active_scene_id'] = ''
    validate_campaign(candidate)
    data['scenes'] = candidate['scenes']
    data['active_scene_id'] = candidate['active_scene_id']


def update_npc(data, npc_id, changes):
    if npc_record(data, npc_id) is None: raise ValueError('NPC больше не существует')
    candidate = deepcopy(data)
    npc = npc_record(candidate, npc_id)
    npc.update(changes)
    npc['id'] = npc_id
    npc['name'] = npc['name'].strip()
    validate_campaign(candidate)
    data['npcs'] = candidate['npcs']


def delete_scene(data, scene_id):
    if scene_record(data, scene_id) is None: raise ValueError('Сцена больше не существует')
    data['scenes'] = [scene for scene in data['scenes'] if scene['id'] != scene_id]
    if data['active_scene_id'] == scene_id: data['active_scene_id'] = ''


def delete_npc(data, npc_id):
    if npc_record(data, npc_id) is None: raise ValueError('NPC больше не существует')
    data['npcs'] = [npc for npc in data['npcs'] if npc['id'] != npc_id]
    for scene in data['scenes']: scene['npc_ids'] = [linked for linked in scene['npc_ids'] if linked != npc_id]
    for enemy in data['enemies']:
        if enemy.get('source_npc_id') == npc_id: enemy.pop('source_npc_id')


def npc_battle_token(data, npc_id):
    return next((f"enemy:{enemy['id']}" for enemy in data['enemies'] if enemy.get('source_npc_id') == npc_id), None)


def add_npc_to_battle(data, npc_id):
    npc = npc_record(data, npc_id)
    if npc is None: raise ValueError('NPC больше не существует')
    if npc_battle_token(data, npc_id): raise ValueError('Этот NPC уже среди участников боя')
    validate_campaign(data)
    enemy_id = data['next_enemy_id']
    stats = {key:deepcopy(npc['combat'][key]) for key in ('hp','hp_max','armor','attack_damage','attack_type','heal_amount','initiative')}
    stats['resists'] = {element:npc['combat']['resists'][element] for element in ELEMENTS}
    stats['actions']=deepcopy(npc['combat'].get('actions',[]))
    stats['action_limit']=npc['combat'].get('action_limit',0)
    for key in ('mana_current','mana_max'):
        if key in npc['combat']: stats[key]=npc['combat'][key]
    fighter = dict(id=enemy_id, name=npc['name'], description=npc['description'] or npc['role'], side=npc['side'],
                   source_npc_id=npc_id, effects=[], dots=[], **stats)
    fighter['level']=npc['combat'].get('level')
    fighter['is_boss']=npc['combat'].get('is_boss',False)
    fighter['is_elite']=npc['combat'].get('is_elite',False)
    data['enemies'].append(fighter)
    if data['combat_active']:register_enemy(data,fighter)
    data['next_enemy_id'] += 1
    if data['combat_active']: refresh_turn_order(data)
    return f'enemy:{enemy_id}'


def scene_player_text(data, scene_id):
    scene = scene_record(data, scene_id)
    if scene is None: raise ValueError('Сцена больше не существует')
    lines = [f"# {scene['name']}"]
    if scene['location']: lines.extend(['', f"Место: {scene['location']}"])
    if scene['summary']: lines.extend(['', scene['summary']])
    linked = [npc_record(data, npc_id) for npc_id in scene['npc_ids']]
    if linked: lines.extend(['', '## Участники'])
    for npc in linked:
        lines.extend(['', f"### {npc['name']}"])
        for field in ('role', 'description', 'public_notes'):
            if npc[field]: lines.extend(['', npc[field]])
    return '\n'.join(lines)


def combat_side(data, token):
    if token == 'player': return 'Героиня'
    if token == 'ally': return 'Союзник'
    return participant(data, token).get('side', 'Враг')


def visible_battle_participants(data):
    return [(token,target) for token,target in participants(data) if not (token.startswith('enemy:') and target[hp_fields(target)[0]]<=0 and combat_side(data,token)=='Враг')]


def default_opponent(data, source_token):
    tokens = [token for token, target in participants(data) if token != source_token and target[hp_fields(target)[0]] > 0]
    if combat_side(data, source_token) == 'Враг': return 'player' if 'player' in tokens else tokens[0] if tokens else source_token
    return next((token for token in tokens if combat_side(data, token) == 'Враг'), tokens[0] if tokens else source_token)


def action_template(name, kind='damage', amount=0, hits=1, **changes):
    action = dict(id=uuid4().hex, name=name, kind=kind, amount=amount, hits=hits,
                  damage_type='Физический', cooldown=0, cooldown_left=0, duration=0,
                  effect_kind='note', effect_value=0, effect_element='Огонь', max_stacks=1,
                  description='', needs_setup=False, shared_attack=False, manual_recharge=False, spent=False,
                  mana_cost=0,charges_max=0,charges_left=0)
    action.update(changes)
    return action


def warrior_actions():
    return [action_template('Десница Ока',kind='note',rule='eye',description='Один раз за бой: +100% исходящего урона до конца текущего хода. Активация расходует одно действие.'),
            action_template('Мощный удар',shared_attack=True,multiplier=1.5,cooldown=2,description='150% обычного урона меча. Одно действие; КД 2 личных хода.'),
            action_template('Защитная стойка',kind='note',rule='stance',cooldown=1,description='Входящий урон −30% до начала следующего личного хода. Одно действие; КД 1 личный ход.')]


def movement_actions():
    return [action_template('Сближение',kind='note',rule='move_close',reach='Любая',description='Сблизиться с выбранной целью. Одно перемещение за ход, без расхода действий.'),action_template('Отступление',kind='note',rule='move_far',reach='Любая',description='Отойти от всех целей рядом. Одно перемещение за ход, без расхода действий.')]


def friend_actions():
    return [action_template('Удар оружием',shared_attack=True),action_template('Скорострел',hits=2,shared_attack=True,description='Две атаки мечом за одно действие; отдельные проверки уклонения, защиты и щитов.'),action_template('Видящий',kind='note',description='Позволяет видеть суть вещей. Числовой боевой эффект не задан.')] + warrior_actions() + movement_actions()


def fill_warrior_equipment(ally):
    from kalista_player_model import ensure_player_sheet
    ensure_player_sheet(ally)
    p=ally['sheet_profile']
    if p.get('warrior_equipment_filled'):return
    for item in p['equipment']:
        if 'Грозовой меч' in item['name'] and not any(x['equipped'] and x['slot']=='Оружие 2' for x in p['equipment']):item.update(slot='Оружие 2',equipped=True)
        if 'ниргхала' in item['name'].lower() and 'сапоги' in item['name'].lower():
            item.update(slot='Сапоги',equipped=True)
            item['description']+='\nЛегендарная часть комплекта Ниргхала. Числовой бонус комплекта не задан.'
        if item['slot'].startswith(('Кольцо','Ожерелье','Серьга')):item['equipped']=False
    names={'Шлем':'Обычный шлем','Наплечники':'Обычные наплечники','Перчатки':'Обычные перчатки','Нагрудник':'Кираса Ниргхала','Пояс':'Обычный пояс','Штаны':'Обычные поножи'}
    for slot,name in names.items():
        if not any(x['equipped'] and x['slot']==slot for x in p['equipment']):
            p['equipment'].append(dict(id=uuid4().hex,name=name,slot=slot,equipped=True,bonuses={},description='Легендарная часть комплекта Ниргхала. Числовой бонус комплекта не задан.' if slot=='Нагрудник' else 'Обычная экипировка. Текущая защита уже учтена в характеристиках.'))
    p['warrior_equipment_filled']=True


def distance_between(data,first,second):
    return data.get('distances',{}).get('|'.join(sorted((first,second))),'Дальняя' if 'player' in (first,second) and first!=second else 'Ближняя')


def reach_label(ability):
    reach=ability.get('reach','Ближняя' if ability.get('damage_type')=='Физический' else 'Дальняя')
    return {'Ближняя':'⚔ Ближняя','Дальняя':'🏹 Дальняя','Любая':'⚔ 🏹 Любая'}[reach]


def ranged_miss_chance(data,source_token,ability,target_token):
    if not data.get('combat_active') or ability.get('reach','Ближняя' if ability.get('damage_type')=='Физический' else 'Дальняя')!='Дальняя':return 0.0
    source_side=combat_side(data,source_token)
    for token,target in participants(data):
        if token!=source_token and (combat_side(data,token)=='Враг')!=(source_side=='Враг') and target[hp_fields(target)[0]]>0 and distance_between(data,source_token,token)=='Ближняя':
            return .5
    return 0.0


def check_reach(data,source_token,action,target_token):
    if action['kind']=='damage' and action.get('reach','Ближняя' if action['damage_type']=='Физический' else 'Дальняя')=='Ближняя' and distance_between(data,source_token,target_token)!='Ближняя':
        raise ValueError('Цель далеко: сначала сблизься; ближняя атака не проходит')


def evasion_chance(target):
    dex=target.get('sheet_profile',{}).get('stats',{}).get('Ловкость',target.get('base_stats',{}).get('Ловкость',target.get('agility',0)))
    if 'base_stats' in target and not target.get('sheet_profile'):dex=total_stat(target,'Ловкость')
    return round(min(.5,max(0,dex*.005)),8)


def counterattack(data,source_token,target_token,result):
    target=participant(data,target_token);source=participant(data,source_token)
    if not target.get('counterattack_enabled') or result['hp_loss']<=0 or distance_between(data,source_token,target_token)!='Ближняя':return []
    if target[hp_fields(target)[0]]<=0 or source[hp_fields(source)[0]]<=0 or any(e['kind']=='fear' for e in target.get('effects',[])):return []
    roll=random.random()
    if roll>=.65:return [f"{target['name']}: контратака не сработала ({roll*100:.1f}% ≥ 65%)"]
    if random.random()<evasion_chance(source):return [f"{source['name']}: уклонение от контратаки"]
    if source is data and data.get('ten_invis'):return [f"{source['name']}: контратака не попала — невидимость"]
    amount=round(target.get('sheet_profile',{}).get('attack',target.get('attack_damage',0)))
    amount=outgoing_damage(target,amount,'Физический')
    answer=apply_damage(source,amount,'Физический')
    message='Контратака: '+damage_message(source['name'],answer)
    record_turn_action(data,target_token,'Контратака',source['name'],message,counts=False)
    return [message]


def validate_action_state(data):
    data.setdefault('turn_serial', 0)
    data.setdefault('turn_actions', [])
    nonnegative_int(data['turn_serial'], 'Номер хода')
    if not isinstance(data['turn_actions'], list): raise ValueError('Повреждена история хода')
    for entry in data['turn_actions']:
        validate_tree(entry, dict(source='',name='',target='',result='',counts=True))
        if not {'source','name','target','result','counts'} <= entry.keys(): raise ValueError('Неполная запись хода')
    data.setdefault('player_requests', [])
    if not isinstance(data['player_requests'],list): raise ValueError('Повреждены предложения игрока')
    request_ids=set()
    for request in data['player_requests']:
        validate_tree(request,dict(id='',action_id='',action_name='',victims=[''],critical=False,turn_serial=0,status='',message=''))
        if not {'id','action_id','action_name','victims','critical','turn_serial','status','message'} <= request.keys(): raise ValueError('Неполное предложение игрока')
        if request['status'] not in ('pending','accepted','rejected') or request['id'] in request_ids: raise ValueError('Неверное предложение игрока')
        request_ids.add(request['id'])
    for token, target in participants(data) + [('npc:'+npc['id'],npc['combat']) for npc in data['npcs']]:
        if 'mana_current' in target or 'mana_max' in target:
            nonnegative_int(target.get('mana_current',-1),'Мана участника')
            nonnegative_int(target.get('mana_max',-1),'Максимум маны участника')
            if target['mana_current']>target['mana_max']: raise ValueError('Мана выше максимума')
        target['action_limit']=2
        nonnegative_int(target['action_limit'], 'Лимит действий')
        if target.get('sheet_profile'):
            target.setdefault('actions', friend_actions())
            target['attack_damage'] = round(target['sheet_profile']['attack'])
            # Old imported description repeated immutable identity fields.
            if target.get('description', '').endswith('Уровень 17'): target['description'] = ''
        target.setdefault('actions', [])
        if not isinstance(target['actions'], list): raise ValueError('Действия должны быть списком')
        if not token.startswith('npc:'):
            if not target['actions'] and token!='player':
                target['actions']=[action_template('Атака',shared_attack=True,damage_type=target.get('attack_type','Физический')),action_template('Лечение',kind='heal',amount=target.get('heal_amount',0),needs_setup=not bool(target.get('heal_amount',0)))]
            existing={a.get('rule') for a in target['actions']}
            target['actions'] += [a for a in movement_actions() if a['rule'] not in existing]
        ids = set()
        for action in target['actions']:
            for field in ('mana_cost','charges_max','charges_left'): action.setdefault(field,0)
            for field in ('armor_penetration','extra_dice_count','extra_dice_sides'): action.setdefault(field,0)
            action.setdefault('reach','Ближняя' if action['damage_type']=='Физический' else 'Дальняя')
            if action.get('rule')=='move_far':action['description']='Отойти от всех участников рядом. Одно перемещение за ход, без расхода действий.'
            action.setdefault('multiplier',1.0)
            if action['reach'] not in ('Ближняя','Дальняя','Любая'):raise ValueError('Неверная дальность атаки')
            if not isinstance(action['multiplier'],(int,float)) or not math.isfinite(action['multiplier']) or action['multiplier']<=0:raise ValueError('Неверный множитель урона')
            if action.get('rule','') not in ('','eye','stance','move_close','move_far'):raise ValueError('Неизвестное правило способности')
            action.setdefault('reaction',False)
            if not isinstance(action['reaction'],bool): raise ValueError('Неверный признак реакции')
            validate_tree(action, action_template(''))
            if not action_template('').keys() <= action.keys(): raise ValueError('Неполные данные действия')
            if not action['name'].strip() or not action['id'] or action['id'] in ids: raise ValueError('Неверное название или ID действия')
            ids.add(action['id'])
            if action['kind'] not in ('damage','heal','shield','note'): raise ValueError('Неизвестное действие')
            if action['damage_type'] not in DAMAGE_TYPES: raise ValueError('Неизвестный тип урона действия')
            for field in ('amount','cooldown','cooldown_left','duration','max_stacks','mana_cost','charges_max','charges_left'): nonnegative_int(action[field], field)
            if action['charges_left']>action['charges_max']: raise ValueError('Осталось больше зарядов, чем максимум')
            for field in ('armor_penetration','extra_dice_count','extra_dice_sides'): nonnegative_int(action[field],field)
            if action['extra_dice_count']>10 or action['extra_dice_sides']>1000: raise ValueError('Слишком большой бросок')
            if action['extra_dice_count'] and action['extra_dice_sides']<2: raise ValueError('Кубику нужно минимум 2 грани')
            if not 1 <= action['hits'] <= 10 or isinstance(action['hits'], bool): raise ValueError('Нужно от 1 до 10 попаданий')
            if not 1 <= action['max_stacks'] <= 20: raise ValueError('Нужно от 1 до 20 стаков')
            validate_effect(dict(kind=action['effect_kind'], name=action['name'], value=action['effect_value'],
                                 duration=action['duration'] or None, element=action['effect_element']))


def action_amount(source, action, critical=False):
    if critical:
        if action['kind'] != 'damage' or not source.get('sheet_profile') or not action['shared_attack']:
            raise ValueError('Критический урон для этого действия не задан')
        return round(source['sheet_profile']['critical_damage'])
    if action['shared_attack']:
        return round(source['sheet_profile']['attack']) if source.get('sheet_profile') else source.get('attack_damage',0)
    return action['amount']


def check_action_limit(data, source_token, reaction=False):
    source = participant(data, source_token)
    if any(e['kind']=='fear' for e in source.get('effects',[])):raise ValueError('Страх: персонаж не может действовать до окончания эффекта')
    if not data.get('combat_active') or reaction: return
    limit = 2
    count = sum(entry['source'] == source_token and entry.get('counts', True) for entry in data.get('turn_actions', []))
    if limit and count >= limit: raise ValueError('Лимит действий этого хода исчерпан')


def record_turn_action(data, source_token, name, target, result, counts=True):
    data.setdefault('turn_actions', []).append(dict(source=source_token, name=name, target=target, result=result, counts=counts))
    data['turn_actions'] = data['turn_actions'][-50:]


def action_damage_factor(target, action):
    if action['damage_type']=='Физический' and action.get('armor_penetration'):
        armor=effective_defense(target,'Физический')
        return max(0,armor-action['armor_penetration'])/armor if armor else 1.0
    return 1.0


def preview_action(data, source_token, action, token, critical=False, manual_amount=None):
    target=participant(data,token)
    amount=action_amount(participant(data,source_token),action,critical) if manual_amount is None else manual_amount
    check_reach(data,source_token,action,token)
    amount=round(amount*action.get('multiplier',1))
    count=action.get('extra_dice_count',0);sides=action.get('extra_dice_sides',0)
    values=[]
    for bonus in (count,count*sides):
        copy=deepcopy(target);loss=absorbed=0
        if token=='player' and data.get('ten_invis'): values.append((0,0));continue
        for hit in range(action['hits']):
            result=apply_damage(copy,outgoing_damage(participant(data,source_token),amount+bonus,action['damage_type']),action['damage_type'],defense_factor=action_damage_factor(copy,action))
            loss+=result['hp_loss'];absorbed+=result['absorbed']
        values.append((loss,absorbed))
    dodge=evasion_chance(target) if action['damage_type']=='Физический' else 0
    miss=ranged_miss_chance(data,source_token,action,token) if action['kind']=='damage' else 0
    return dict(hp_min=0 if dodge or miss else values[0][0],hp_max=values[1][0],shield=values[0][1],dodge=dodge,miss=miss)


def perform_action(data, source_token, action_id, victims, critical=False, reaction=False, manual_amount=None, simulation=False):
    if critical:raise ValueError("Крит определяется автоматически, назначать его вручную нельзя")
    # Execute on a copy so a missing target or invalid rule cannot partly spend resources.
    candidate = deepcopy(data)
    source = participant(candidate, source_token)
    action = next((a for a in source['actions'] if a['id'] == action_id), None)
    if action is None: raise ValueError('Действие больше не существует')
    reaction=bool(reaction or action.get('reaction',False))
    if action['needs_setup']: raise ValueError('Сначала настрой действие у ведущего')
    if action['cooldown_left'] or action['spent']: raise ValueError('Действие ещё не восстановилось')
    if action['charges_max'] and action['charges_left']==0: raise ValueError('Закончились заряды')
    if action['mana_cost']>source.get('mana_current',0): raise ValueError('Не хватает маны')
    rule=action.get('rule','')
    moving=rule in ('move_close','move_far')
    check_action_limit(candidate, source_token, reaction or moving)
    if moving and source.get('movement_used') and candidate['combat_active']:raise ValueError('Перемещение этого хода уже использовано')
    if rule=='eye' and (not candidate['combat_active'] or source.get('eye_used')):raise ValueError('Десница Ока доступна один раз в текущем бою')
    if source[hp_fields(source)[0]] <= 0: raise ValueError('У действующего персонажа 0 HP')
    if not victims or len(victims) != len(set(victims)): raise ValueError('Выбери разные цели')
    if len(victims) > 20: raise ValueError('Слишком много целей')
    targets = [(token, participant(candidate, token)) for token in victims]
    for token,_ in targets:check_reach(candidate,source_token,action,token)
    if rule in ('eye','stance') and (len(targets)!=1 or targets[0][0]!=source_token):raise ValueError('Эта способность применяется только к себе')
    if moving and (len(targets)!=1 or targets[0][0]==source_token):raise ValueError('Выбери другого участника для перемещения')
    amount = action_amount(source, action, critical)
    if manual_amount is not None:
        nonnegative_int(manual_amount, 'Ручная величина')
        if critical: raise ValueError('Ручной урон и крит нельзя применить одновременно')
        amount = manual_amount
    if action['kind'] != 'note' and amount <= 0: raise ValueError('Задай величину выше 0')
    messages=[]
    extra_bonus=0
    if action.get('extra_dice_count'):
        rolls=[random.randint(1,action['extra_dice_sides']) for _ in range(action['extra_dice_count'])]
        extra_bonus=sum(rolls)
        amount+=extra_bonus
        messages.append(f"Дополнительный бросок: {rolls} = +{sum(rolls)}")
    if action['kind']=='damage':
        amount=round(amount*action.get('multiplier',1))
        weakened=outgoing_damage(source,amount,action['damage_type'])
        if weakened!=amount:messages.append(f'Слабость: физический урон {amount} → {weakened} (−35%)')
        amount=weakened
    for token, target in targets:
        landed=False
        if action['kind'] == 'damage':
            if target[hp_fields(target)[0]] <= 0: raise ValueError('У цели 0 HP')
            if target is candidate and candidate.get('ten_invis'):
                messages.append(f"{target['name']}: промах — невидимость")
                continue
            for hit in range(action['hits']):
                if target[hp_fields(target)[0]] <= 0 or source[hp_fields(source)[0]]<=0: break
                if not simulation and ranged_miss_chance(candidate,source_token,action,token) and random.random()<.5:
                    messages.append(f'Попадание {hit+1}: промах — дальняя атака в ближнем бою (50%)');continue
                if not simulation and action['damage_type']=='Физический' and random.random()<evasion_chance(target):
                    messages.append(f"Попадание {hit+1}: {target['name']} уклонился");continue
                landed=True
                hit_amount=amount
                if not simulation and manual_amount is None and action['shared_attack'] and source.get('sheet_profile'):
                    chance=min(.95,max(0,source['sheet_profile']['critical_chance']/100))
                    if chance>0 and random.random()<chance:
                        hit_amount=outgoing_damage(source,round((action_amount(source,action,True)+extra_bonus)*action.get('multiplier',1)),action['damage_type'])
                        messages.append(f'Попадание {hit+1}: КРИТ — автоматический бросок {chance*100:g}%')
                result=apply_damage(target, hit_amount, action['damage_type'],defense_factor=action_damage_factor(target,action))
                messages.append(f"Попадание {hit+1}: " + damage_message(target['name'], result))
                if not simulation and not reaction:messages.extend(counterattack(candidate,source_token,token,result))
        elif action['kind'] == 'heal':
            result=apply_healing(target, amount);messages.append(f"{target['name']}: +{result['restored']} HP")
        elif action['kind'] == 'shield':
            add_effect(target, dict(kind='shield',name=action['name'],value=amount,duration=action['duration'] or None,source=source_token), candidate['round'] if candidate['combat_active'] else 0)
            messages.append(f"{target['name']}: щит {amount}")
        else:
            if moving:
                if rule=='move_far':
                    for other,_ in participants(candidate):
                        if other!=source_token:
                            candidate.setdefault('distances',{})['|'.join(sorted((source_token,other)))]= 'Дальняя'
                    messages.append(f"{source['name']}: отступает от всех участников рядом")
                else:
                    candidate.setdefault('distances',{})['|'.join(sorted((source_token,token)))]= 'Ближняя'
                source['movement_used']=True
            elif rule=='eye':source['eye_used']=True;source['eye_damage_boost']=True
            elif rule=='stance':source['defensive_stance']=True
            messages.append(f"{source['name']} → {target['name']}: {action['name']}")
        if not rule and (action['kind']!='damage' or landed) and (action['kind'] == 'note' or action['effect_kind'] != 'note'):
            kind=action['effect_kind']
            existing=[e for e in target['effects'] if e.get('source') == action['id']]
            if kind=='fear' and target.get('fear_immunity_turns',0)>0:
                messages.append(f"{target['name']}: страх не наложен — иммунитет")
            elif len(existing) < action['max_stacks']:
                add_effect(target, dict(kind=kind,name=action['name'],value=action['effect_value'],duration=action['duration'] or None,
                                       element=action['effect_element'],source=action['id'],desc=action['description']), candidate['round'] if candidate['combat_active'] else 0, stack=True)
                messages.append(f"{target['name']}: эффект {action['name']}")
            else: messages.append(f"{target['name']}: достигнут предел стаков")
    # Own-turn cooldown N permits reuse after N subsequent starts, no reduction on rerun.
    action['cooldown_left'] = action['cooldown']
    action['spent'] = action['manual_recharge']
    if action['charges_max']: action['charges_left']-=1
    if action['mana_cost']: source['mana_current']-=action['mana_cost']
    record_turn_action(candidate, source_token, action['name'], ', '.join(t['name'] for _,t in targets), ' · '.join(messages), counts=not (reaction or moving))
    if candidate['combat_active']: refresh_turn_order(candidate)
    validate_action_state(candidate)
    data.clear();data.update(candidate)
    return messages


def effect_lifetime(effect):
    duration=effect.get('duration')
    if duration is None: return effect['name']+' · бессрочно'
    when='Осталось ходов цели' if effect['kind'] in ('dot','hot','weakness','fear') else 'Осталось полных раундов'
    return f"{effect['name']} · {when}: {duration}"


def public_player_state(data):
    # Whitelist public fields; never render the GM save, notes or hidden NPC records.
    result={key:deepcopy(data[key]) for key in ('combat_active','round','current_turn','turn_order','turn_serial','turn_actions')}
    result['ally']=deepcopy(data['ally'])
    result['hero']={key:deepcopy(data.get(key)) for key in ('name','hp_current','hp_max','mana_current','mana_max')}
    result['fighters']=[{'token':token,'name':target['name'],'hp':target[hp_fields(target)[0]],'hp_max':target[hp_fields(target)[1]],'side':combat_side(data,token)} for token,target in participants(data)]
    scene=scene_record(data,data['active_scene_id'])
    result['scene']=scene_player_text(data,scene['id']) if scene else ''
    # Turn results are authored combat summaries; exclude action descriptions / NPC secrets.
    result['requests']=[{key:r.get(key) for key in ('id','action_name','status','message')} for r in data.get('player_requests',[])][-10:]
    return result


def invalidate_player_requests(data,message):
    for request in data.get('player_requests',[]):
        if request['status']=='pending': request.update(status='rejected',message=message)


def set_manual_turn(data,index):
    if not data['combat_active'] or not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(data['turn_order']):
        raise ValueError('Неверный ход')
    data['current_turn']=index
    data['turn_serial']=data.get('turn_serial',0)+1
    data['turn_actions']=[]
    invalidate_player_requests(data,'Ведущий изменил текущий ход')


def resolve_player_request(data,request_id,accept):
    request=next((r for r in data.get('player_requests',[]) if r['id']==request_id),None)
    if not request or request['status']!='pending': raise ValueError('Предложение уже обработано')
    if not accept:
        request.update(status='rejected',message='Ведущий отклонил действие');return ['Предложение игрока отклонено']
    if request['turn_serial']!=data['turn_serial']: raise ValueError('Предложение относится к прошедшему ходу')
    action=next((a for a in data['ally']['actions'] if a['id']==request['action_id']),None)
    if data['combat_active'] and actor_token(get_current_actor(data))!='ally' and not (action or {}).get('reaction'): raise ValueError('Сейчас ход другого участника')
    messages=perform_action(data,'ally',request['action_id'],request['victims'],False,reaction=False)
    request=next(r for r in data['player_requests'] if r['id']==request_id)
    request.update(status='accepted',message='Действие применено')
    return messages


__all__ = ['register_enemy','xp_needed','MAX_LEVEL','visible_battle_participants','reach_label','ranged_miss_chance','kalista_dot_damage','distance_between','evasion_chance','check_reach','warrior_actions','movement_actions','fill_warrior_equipment','shadow_shield_amount', 'outgoing_damage', 'roll_spell_effects', 'spell_damage_preview', 'spell_damage_apply', 'invalidate_player_requests', 'set_manual_turn', 'preview_action', 'action_damage_factor', 'ELEMENTS', 'DEFAULT', 'absorb', 'real_dmg', 'total_stat', 'recalc_equip', 'recalc', 'gen_enemy', 'merge_defaults', 'validate_tree', 'migrate', 'spell_raw', 'EFFECT_KINDS', 'DAMAGE_TYPES', 'nonnegative_int', 'hp_fields', 'participant', 'participants', 'participant_label', 'validate_effect', 'add_effect', 'effective_defense', 'damage_preview', 'apply_damage', 'apply_healing', 'restore_mana', 'observe_mana_reserve', 'tick_mana_regeneration', 'damage_message', 'tick_periodic', 'tick_round_effects', 'actor_target', 'activate_shadow_invisibility', 'activate_shadow_resistance', 'begin_actor_turn', 'finish_round', 'advance_turn', 'spell_action', 'cast_spell', 'build_turn_order', 'refresh_turn_order', 'get_current_actor', 'validate_item_use', 'use_item', 'actor_token', 'set_initiative', 'move_in_queue', 'exclude_from_queue', 'return_to_queue', 'add_history', 'special_availability', 'activate_special', 'effective_crit_chance', 'start_combat', 'end_combat', 'spell_bonuses', 'exclude_from_queue_after_delete', 'combatant_heal', 'SHEOGARATH_REFERENCE', 'imported_friend', 'scene_record', 'npc_record', 'validate_campaign', 'create_scene', 'create_npc', 'activate_scene', 'update_scene', 'update_npc', 'delete_scene', 'delete_npc', 'npc_battle_token', 'add_npc_to_battle', 'scene_player_text', 'combat_side', 'default_opponent', 'action_template', 'friend_actions', 'validate_action_state', 'action_amount', 'check_action_limit', 'record_turn_action', 'perform_action', 'effect_lifetime', 'public_player_state', 'resolve_player_request']
