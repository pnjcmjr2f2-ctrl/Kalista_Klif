#!/usr/bin/env python3
"""
Калист Клиф — v7 · эффекты, щиты и лечение
Ручное ведение НРИ, очередь ходов, эффекты, щиты, лечение и 6 стихий
"""

import streamlit as st
import json
import random
import os
import tempfile
import shutil
import math
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from copy import deepcopy

SAVE_FILE = Path(__file__).parent / "kalista_save.json"
ELEMENTS = ["Огонь", "Земля", "Вода", "Воздух", "Тьма", "Свет"]

st.set_page_config(page_title="✧ Калист Клиф ✧", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Quattrocento+Sans:wght@400;700&display=swap');
.main-title{font-family:'Cinzel',serif;font-size:2rem;color:#E8DAEF;text-align:center;text-shadow:0 0 12px #4A235A;margin-bottom:.1rem}
.subtitle{text-align:center;color:#BB8FCE;margin-bottom:.8rem}
.section-h{font-family:'Cinzel',serif;color:#D7BDE2;font-size:1.1rem;border-bottom:2px solid #7D3C98;padding-bottom:2px;margin:.8rem 0 .4rem}
div[data-testid="stMetricValue"]{font-size:1.25rem}
.stButton>button{border-radius:8px;font-weight:600}
.turn-now{background:#3D1A5C;border:2px solid #BB8FCE;border-radius:10px;padding:8px 12px;margin-bottom:6px}
</style>
""", unsafe_allow_html=True)

# ===================== DEFAULT =====================
DEFAULT = {
    "name": "Калист Клиф", "race": "Тёмный эльф (Дроу)", "class": "Маг огня и тьмы",
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
        # Расовые (справочные)
        "darkvision": {"name":"Зрение в темноте","type":"racial","used":False,"desc":"Видит в полной темноте на 36м. Яркий свет может ослепить на 1 ход."},
        "dark_resist": {"name":"Сопротивление тьме","type":"racial","used":False,"desc":"Базовое сопр. Тьме +35, доп. +10% к сопротивлению магии тьмы."},
        "water_sense": {"name":"Чувствительность к воде","type":"racial","used":False,"desc":"Бонус к сопр. Воде. Долгий дождь вызывает дискомфорт."},
        "drow_grace": {"name":"Дроу-грация","type":"racial","used":False,"desc":"+2 к скрытности и акробатике в темноте/слабом свете."},
        # Классовые
        "double_flame": {"name":"Двойное пламя","type":"class","used":False,"desc":"+5% урона, если предыдущее заклинание было другой школы (Огонь↔Тьма). Работает автоматически."},
        "ash_lady": {"name":"Повелительница пепла","type":"class","used":False,"desc":"Огненные заклинания дают Пепел. При 5 — активация: след. огненное игнор 30% сопр. огню."},
        "shadow_child": {"name":"Дитя тени","type":"class","used":False,"desc":"Тёмные заклинания дают Тень. При 5 — активация: невидимость 1 ход ИЛИ +20 к сопротивлениям (предел 95) на 2 раунда."},
        "mana_reserve": {"name":"Магический резерв","type":"class","used":False,"desc":"Когда мана <20%, реген маны +50% на 3 тика. Пока учитывается ведущим вручную."},
        # Особые (активируемые, раз в день/отдых)
        "ritual_black_flame": {"name":"Ритуал Чёрного Пламени","type":"special","used":False,"desc":"Раз в день: следующее Пламя души +40% урона без долгого каста."},
        "cold_calculation": {"name":"Холодный расчёт","type":"special","used":False,"desc":"В начале боя (1 ход): +10% шанса крита до конца боя."},
        "memory_of_house": {"name":"Память Дома Клиф","type":"special","used":False,"desc":"Раз в долгий отдых: преимущество на проверку знаний о запретной магии."},
    },
    "soul_flame_boost": False,
    "crit_boost_active": False,
    "pepel_empower": False,   # следующее огненное игнор 30% fire resist
    "ten_invis": False,       # невидимость 1 ход
    "ten_resist_boost": 0,    # раундов +20 к сопротивлениям осталось
    "status_effects": [],     # [{"name","duration","desc"}]
    "portrait_url": "",
    "crit_chance": 0.065,
    "quests": [
        {"id":1,"name":"Пепел старого дома","status":"В процессе","desc":""},
        {"id":2,"name":"Кристалл пустоты","status":"Активен","desc":""},
        {"id":3,"name":"Долг Серому","status":"Ожидание","desc":""},
    ],
    "notes": "Контроль важнее силы.",
    "combat_log": [],
    "resists": {"Огонь":75,"Земля":5,"Вода":10,"Воздух":5,"Тьма":95,"Свет":15},
    # Очередь
    "round": 1,
    "turn_order": [],       # [{"kind":"player"/"ally"/"enemy","id":...,"name":...}]
    "current_turn": 0,
    "combat_active": False,
}

# ===================== ФОРМУЛЫ =====================
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
    d["resists"] = {e: max(0, min(95, base_r[e] + resists[e]) + d.get("resist_adjustments", {}).get(e, 0)) for e in ELEMENTS}

def recalc(d):
    if "equipment" in d: recalc_equip(d)
    intel=total_stat(d,"Интеллект"); wis=total_stat(d,"Мудрость"); cha=total_stat(d,"Харизма")
    spi=total_stat(d,"Дух"); end=total_stat(d,"Выносливость"); agi=total_stat(d,"Ловкость")
    d["mana_max"]=intel*10
    d["hp_max"]=d["level"]*20 + end*10
    d["spell_power"]=intel/5/100
    d["mana_regen"]=round(spi*0.5)
    d["initiative"]=round(agi/2 + wis/4)
    d["control_resist"]=min(0.9, wis/4/100)
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
    if saved.get("schema_version", 5) not in (5, 6, 7):
        raise ValueError("Версия сохранения не поддерживается")
    data = merge_defaults(DEFAULT, saved)
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
    data["schema_version"] = 7
    return data


def load():
    if not SAVE_FILE.exists():
        return migrate(deepcopy(DEFAULT))
    try:
        return migrate(json.loads(SAVE_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error(f"Сохранение не загружено: {exc}. Исходный файл оставлен без изменений.")
        st.info("Восстанови kalista_save.json из kalista_save.json.bak либо исправь файл и перезапусти приложение.")
        st.stop()


def save(d):
    """Атомарная запись; предыдущая корректная версия хранится рядом в .bak."""
    temporary = None
    try:
        migrate(d)
        payload = json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False)
        if SAVE_FILE.exists() and SAVE_FILE.read_text(encoding="utf-8") == payload:
            return True
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=SAVE_FILE.parent,
                                         prefix=".kalista-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if SAVE_FILE.exists():
            migrate(json.loads(SAVE_FILE.read_text(encoding="utf-8")))
            shutil.copy2(SAVE_FILE, SAVE_FILE.with_suffix(".json.bak"))
        os.replace(temporary, SAVE_FILE)
        return True
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error(f"Не удалось сохранить: {exc}. Предыдущее сохранение не перезаписано.")
        return False
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def log(msg):
    ts=datetime.now().strftime("%H:%M:%S")
    st.session_state.data["combat_log"].insert(0,f"[{ts}] {msg}")
    st.session_state.data["combat_log"]=st.session_state.data["combat_log"][:80]

def spell_raw(base, power, dual=False, soul=False):
    d=round(base*(1+power))
    if dual: d=round(d*1.05)
    if soul: d=round(d*1.40)
    return d

# ===================== ОБЩАЯ МЕХАНИКА =====================
# Эти функции работают с данными, не зависят от Streamlit и имени персонажа.
EFFECT_KINDS = {
    "note": "Статус / заметка", "shield": "Щит", "dot": "Периодический урон",
    "hot": "Периодическое лечение", "armor": "Поправка к броне", "resist": "Поправка к сопротивлению",
}
DAMAGE_TYPES = ["Физический"] + ELEMENTS


def nonnegative_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label}: требуется целое число от 0")
    return value


def hp_fields(target):
    return ("hp_current", "hp_max") if "hp_current" in target else ("hp", "hp_max")


def participant(data, token):
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
    if kind in ("dot", "hot") and duration is None:
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
    return max(0, resist + sum(effect["value"] for effect in target.get("effects", [])
                              if effect["kind"] == "resist" and effect["element"] == damage_type))


def damage_preview(target, amount, damage_type="Физический", final=False,
                   bypass_shields=False, defense_factor=1.0):
    nonnegative_int(amount, "Урон")
    if not isinstance(defense_factor, (int, float)) or not math.isfinite(defense_factor) or not 0 <= defense_factor <= 1:
        raise ValueError("Неверная доля сопротивления")
    defense = effective_defense(target, damage_type) * defense_factor
    incoming = amount if final else real_dmg(amount, defense)
    capacity = sum(effect["value"] for effect in target.get("effects", []) if effect["kind"] == "shield")
    absorbed = 0 if bypass_shields else min(incoming, capacity)
    hp_key, _ = hp_fields(target)
    hp_loss = min(max(0, target[hp_key]), incoming - absorbed)
    return {"incoming": incoming, "absorbed": absorbed, "hp_loss": hp_loss,
            "overkill": incoming - absorbed - hp_loss, "defense": defense,
            "hp_after": max(0, target[hp_key] - hp_loss)}


def apply_damage(target, amount, damage_type="Физический", final=False,
                 bypass_shields=False, defense_factor=1.0):
    result = damage_preview(target, amount, damage_type, final, bypass_shields, defense_factor)
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
    return restored


def damage_message(name, result):
    return (f"{name}: после защиты {result['incoming']} · щит −{result['absorbed']} · "
            f"HP −{result['hp_loss']} → {result['hp_after']}")


def tick_periodic(target):
    """Каждый периодический эффект тикает один раз в конце хода цели."""
    messages = []
    for effect in list(target.get("effects", [])):
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
        if (effect["kind"] not in ("dot", "hot") and effect["duration"] is not None
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


def finish_round(data):
    completed = data["round"]
    messages = []
    for _, target in participants(data):
        messages.extend(tick_round_effects(target, completed))
    for spell in data["spells"]:
        if spell["cd_left"] > 0:
            spell["cd_left"] -= 1
    if data.get("ten_resist_boost", 0) > 0:
        data["ten_resist_boost"] -= 1
        if data["ten_resist_boost"] == 0:
            messages.append("Бонус сопротивления от Тени истёк")
    if data.get("ten_invis"):
        data["ten_invis"] = False
        messages.append("Невидимость спала")
    data["round"] += 1
    data["turn_order"] = build_turn_order(data)
    data["current_turn"] = 0
    messages.append(f"=== Раунд {data['round']} ===")
    return messages


def advance_turn(data):
    if not data["combat_active"]:
        raise ValueError("Бой не начат")
    messages = []
    if not data["turn_order"]:
        messages.append("Нет участников с HP выше 0; восстанови HP и начни бой заново.")
        return messages
    target = actor_target(data, get_current_actor(data))
    if target is not None and target[hp_fields(target)[0]] > 0:
        messages.extend(tick_periodic(target))
    data["current_turn"] += 1
    # Удалённые и поверженные участники не получают пустые ходы.
    while data["current_turn"] < len(data["turn_order"]):
        target = actor_target(data, data["turn_order"][data["current_turn"]])
        if target is not None and target[hp_fields(target)[0]] > 0:
            return messages
        data["current_turn"] += 1
    messages.extend(finish_round(data))
    return messages


def spell_action(spell):
    return spell.get("action", "damage")


def cast_spell(data, spell, target, crit=False, final_damage=None, shield_amount=None):
    """Проверяем всё до расходования ресурсов. Решения о целях/крите принимает UI."""
    action = spell_action(spell)
    if action not in ("damage", "heal", "shield", "note"):
        raise ValueError("Неизвестное действие заклинания")
    if spell["mana"] > data["mana_current"]:
        raise ValueError("Не хватает маны")
    if spell.get("cd_left", 0) > 0:
        raise ValueError("Заклинание ещё на перезарядке")
    if action in ("heal", "shield") or (action == "damage" and (spell["base"] > 0 or spell.get("dot"))):
        if target is None:
            raise ValueError("Выбери цель")
    amount = spell["base"]
    if action == "shield":
        amount = spell.get("effect_value", 0) if shield_amount is None else shield_amount
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
    dot_effect = None
    if action == "damage" and spell.get("dot") and target is not None:
        dot = spell["dot"]
        dot_effect = {"kind": "dot", "name": dot["name"], "value": dot["damage"],
                      "element": dot.get("element", "Огонь"), "duration": dot["duration"],
                      "source": f"spell:{spell['id']}"}
        validate_effect(dot_effect)
    effect = None
    if action in ("heal", "shield", "note"):
        effect = {"kind": "shield" if action == "shield" else "note", "name": spell["name"],
                  "value": amount if action == "shield" else 0,
                  "duration": spell.get("effect_duration") or None,
                  "source": f"spell:{spell['id']}", "desc": spell.get("desc", "")}
        validate_effect(effect)
    dual = {data.get("last_school"), spell["school"]} == {"Огонь", "Тьма"}
    soul = bool(data.get("soul_flame_boost") and spell["name"] == "Пламя души")
    raw = spell_raw(amount, data.get("spell_power", 0), dual, soul) if action == "damage" else amount
    if crit and action == "damage":
        raw = round(raw * 1.5)
    dtype = "Огонь" if "Огонь" in spell["school"] else "Тьма"
    empowered = bool(data.get("pepel_empower") and dtype == "Огонь" and action == "damage" and raw > 0)
    # До изменения данных проверяем расчёт и цель.
    if target is not None and action == "damage" and raw > 0:
        damage_preview(target, raw if final_damage is None else final_damage, dtype,
                       final=final_damage is not None, defense_factor=0.7 if empowered else 1.0)
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
        if raw > 0:
            result = apply_damage(target, raw if final_damage is None else final_damage, dtype,
                                  final=final_damage is not None, defense_factor=0.7 if empowered else 1.0)
            messages.append(damage_message(target["name"], result))
            if final_damage is not None:
                messages.append("Урон назначен ведущим; щит учтён")
            if empowered:
                data["pepel_empower"] = False
        if dot_effect is not None:
            # В прежней версии повторные касты складывали DoT. Сохраняем это правило.
            add_effect(target, dot_effect, data["round"] if data["combat_active"] else 0, stack=True)
            messages.append(f"+ «{dot_effect['name']}» ({dot_effect['duration']} срабатывания)")
    elif action == "heal":
        result = apply_healing(target, amount)
        messages.append(f"{target['name']}: +{result['restored']} HP (избыток {result['excess']})")
    elif action in ("shield", "note"):
        recipient = target if target is not None else data
        add_effect(recipient, effect, data["round"] if data["combat_active"] else 0)
        messages.append(f"{recipient['name']}: {spell['name']}" + (f" · щит {amount}" if action == "shield" else ""))
    return messages


def build_turn_order(data):
    order=[]
    if data["hp_current"] > 0:
        order.append({"kind":"player","id":0,"name":data["name"],"init":data["initiative"]})
    if data["ally"]["hp"] > 0:
        order.append({"kind":"ally","id":0,"name":data["ally"]["name"],"init":data["ally"].get("initiative",12)})
    for e in data["enemies"]:
        if e["hp"]>0:
            order.append({"kind":"enemy","id":e["id"],"name":e["name"],"init":e.get("initiative",10)})
    order.sort(key=lambda x: -x["init"])
    return order

def refresh_turn_order(data):
    """Добавление участника не должно переключать текущий ход."""
    actor = get_current_actor(data)
    order = build_turn_order(data)
    # Новые участники вступают после текущего хода; порядок следующего раунда
    # снова строится по инициативе.
    if actor:
        old = data["turn_order"]
        known = {(item["kind"], item["id"]) for item in old}
        old.extend(item for item in order if (item["kind"], item["id"]) not in known)
    else:
        data["turn_order"] = order
        data["current_turn"] = 0


def get_current_actor(data):
    if not data["turn_order"]: return None
    idx=data["current_turn"] % len(data["turn_order"])
    return data["turn_order"][idx]

def enemy_ai_act(data, enemy):
    """Вспомогательное действие; интерфейс не запускает ИИ самостоятельно."""
    targets = [target for token, target in participants(data) if token in ("player", "ally")
               and target[hp_fields(target)[0]] > 0]
    if not targets:
        return
    target = min(targets, key=lambda item: item[hp_fields(item)[0]])
    if target is data and data.get("ten_invis"):
        data["ten_invis"] = False
        log(f"{enemy['name']}: атака отменена невидимостью")
        return
    result = apply_damage(target, enemy.get("attack_damage", 10), enemy.get("attack_type", "Физический"))
    log(f"{enemy['name']} → " + damage_message(target["name"], result))


def persist_and_rerun():
    # HP союзника меняется боевыми кнопками вне его редактора.
    st.session_state["_reset_resource_widgets"] = True
    if save(st.session_state.data):
        st.rerun()


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
        return message + " · использован 1 предмет"
    return message + " · предмет сохранён, ресурс уже заполнен"


def show_effect_summary(target):
    effects = target.get("effects", [])
    if effects:
        capacity = sum(effect["value"] for effect in effects if effect["kind"] == "shield")
        if capacity:
            st.caption(f"🛡 Щит: {capacity}")
        st.caption("Эффекты: " + ", ".join(effect["name"] for effect in effects))


def render_gm_tools(data):
    with st.expander("Управление ведущего: урон, лечение, щиты и эффекты", expanded=False):
        tokens = [token for token, _ in participants(data)]
        token = st.selectbox("Участник", tokens, format_func=lambda item: participant_label(data, item), key="gm_target")
        target = participant(data, token)
        st.caption("Сопротивление → щит → HP. Лечение ограничено максимумом HP. "
                   "Повтор одного эффекта обновляет его; сложение можно включить явно.")
        a1, a2 = st.columns(2)
        operation = a1.selectbox("Действие", ["Урон", "Лечение", "Мана", "Щит"], key="gm_action")
        amount = a2.number_input("Величина", min_value=0, value=0, key="gm_amount")
        dtype = "Физический"
        final = bypass = False
        duration = 0
        shield_name = "Щит ведущего"
        if operation == "Урон":
            dtype = st.selectbox("Тип урона", DAMAGE_TYPES, key="gm_damage_type")
            mode = st.selectbox("Как применить", ["Рассчитать по защите", "Готовый урон — учесть щит", "Снять HP напрямую"], key="gm_damage_mode")
            final = mode != "Рассчитать по защите"
            bypass = mode == "Снять HP напрямую"
            preview = damage_preview(target, amount, dtype, final=final, bypass_shields=bypass)
            st.info("Предпросмотр: " + damage_message(target["name"], preview))
        elif operation == "Лечение":
            hp_key, maximum_key = hp_fields(target)
            st.info(f"Восстановится {min(amount, max(0, target[maximum_key] - target[hp_key]))} HP")
        elif operation == "Мана" and "mana_current" not in target:
            st.caption("У этой цели мана пока не задана. Её можно вести в заметке.")
        elif operation == "Щит":
            shield_name = st.text_input("Название щита", value="Щит ведущего", key="gm_shield_name")
            duration = st.number_input("Полных раундов щита (0 — бессрочно)", min_value=0, value=0, key="gm_shield_duration")
        disabled = amount <= 0 or (operation == "Мана" and "mana_current" not in target)
        if st.button("Применить действие", disabled=disabled, key="gm_apply"):
            try:
                if operation == "Урон":
                    result = apply_damage(target, amount, dtype, final=final, bypass_shields=bypass)
                    log("Ведущий: " + damage_message(target["name"], result))
                elif operation == "Лечение":
                    result = apply_healing(target, amount)
                    log(f"Ведущий: {target['name']} +{result['restored']} HP (избыток {result['excess']})")
                    if data["combat_active"]: refresh_turn_order(data)
                elif operation == "Мана":
                    actual = restore_mana(target, amount)
                    log(f"Ведущий: {target['name']} +{actual} MP")
                else:
                    add_effect(target, {"kind": "shield", "name": shield_name.strip(), "value": amount,
                                        "duration": duration or None, "source": "Ведущий"},
                               data["round"] if data["combat_active"] else 0)
                    log(f"Ведущий: {target['name']} — щит {amount}")
                persist_and_rerun()
            except ValueError as exc:
                st.error(str(exc))
        st.markdown("**Эффекты выбранного участника**")
        st.caption("Урон и лечение: срабатывания в конце хода цели. Остальные: полные раунды; "
                   "раунд наложения не сокращает длительность. Вне боя эффекты меняются вручную.")
        if not target.get("effects"):
            st.caption("Нет активных эффектов")
        for effect in list(target.get("effects", [])):
            count = effect["duration"]
            unit = "срабатыв." if effect["kind"] in ("dot", "hot") else "полных р."
            lifetime = "бессрочно" if count is None else f"{count} {unit}"
            numeric = f" · {effect['value']}" if effect["kind"] != "note" else ""
            element = f" ({effect['element']})" if effect["kind"] in ("dot", "resist") else ""
            st.write(f"{effect['name']} — {EFFECT_KINDS[effect['kind']]}{numeric}{element} · {lifetime}")
            if effect.get("desc"): st.caption(effect["desc"])
            if st.button("Снять эффект", key=f"remove_effect_{token}_{effect['id']}"):
                target["effects"] = [entry for entry in target["effects"] if entry["id"] != effect["id"]]
                log(f"Ведущий снял «{effect['name']}»: {target['name']}")
                persist_and_rerun()
        with st.form("gm_add_effect"):
            kind = st.selectbox("Вид эффекта", list(EFFECT_KINDS), format_func=lambda value: EFFECT_KINDS[value])
            name = st.text_input("Название эффекта")
            # В форме вид не обновляется до отправки, поэтому поля остаются общими.
            value = st.number_input("Величина (отрицательная допустима для поправок)", value=0, step=1)
            element = st.selectbox("Стихия / тип периодического урона", DAMAGE_TYPES)
            duration = st.number_input("Длительность / число срабатываний (0 — бессрочно)", min_value=0, value=3)
            description = st.text_input("Описание эффекта")
            stack = st.checkbox("Добавить отдельно, даже если такой эффект уже есть")
            if st.form_submit_button("Наложить эффект"):
                try:
                    entry = {"kind": kind, "name": name.strip(), "value": value, "element": element,
                             "duration": duration or None, "source": "Ведущий", "desc": description}
                    add_effect(target, entry, data["round"] if data["combat_active"] else 0, stack=stack)
                    log(f"Ведущий: «{name.strip()}» → {target['name']}")
                    persist_and_rerun()
                except ValueError as exc:
                    st.error(str(exc))
        c1, c2 = st.columns(2)
        if c1.button("Один тик урона / лечения вручную", key="gm_tick_periodic"):
            for message in tick_periodic(target): log("Ручной тик: " + message)
            if data["combat_active"]: refresh_turn_order(data)
            persist_and_rerun()
        if c2.button("Уменьшить длительности на раунд", key="gm_tick_duration"):
            for message in tick_round_effects(target, data["round"] + 1): log("Ведущий: " + message)
            persist_and_rerun()


# ===================== INIT =====================
if "data" not in st.session_state:
    st.session_state.data=load()
    recalc(st.session_state.data)
data=st.session_state.data
if st.session_state.pop("_reset_resource_widgets", False):
    st.session_state.pop("ah", None)
    for key in list(st.session_state):
        if str(key).startswith("q") and str(key)[1:].isdigit():
            del st.session_state[key]
recalc(data)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("<div class='main-title' style='font-size:1.35rem'>✧ Калист</div>", unsafe_allow_html=True)
    st.caption(f"Ур.{data['level']} · {data['class']}")
    st.progress(min(data["hp_current"]/max(data["hp_max"],1),1.0), text=f"HP {data['hp_current']}/{data['hp_max']}")
    st.progress(min(data["mana_current"]/max(data["mana_max"],1),1.0), text=f"MP {data['mana_current']}/{data['mana_max']}")
    if data.get("combat_active"):
        st.markdown(f"**Раунд {data['round']}**")
        actor=get_current_actor(data)
        if actor: st.info(f"Ход: {actor['name']}")
    st.divider()
    page=st.radio("Меню",["Обзор","Бой","Экипировка","Характеристики","Инвентарь","Заклинания","Квесты","Кубики","Биография"],label_visibility="collapsed")
    st.divider()
    if st.button("💾 Сохранить",use_container_width=True):
        if save(data): st.success("Сохранено")
    st.download_button("📥 Экспорт сохранения", json.dumps(data, ensure_ascii=False, indent=2),
                       file_name="kalista_save.json", mime="application/json", use_container_width=True)
    imported = st.file_uploader("Импорт сохранения", type=["json"])
    if imported is not None and st.button("Применить импорт"):
        try:
            restored = migrate(json.loads(imported.getvalue().decode("utf-8-sig")))
            recalc(restored)
            if save(restored):
                st.session_state.data = restored
                for key in list(st.session_state):
                    if key != "data": del st.session_state[key]
                persist_and_rerun()
        except (ValueError, TypeError, KeyError) as exc:
            st.error(f"Импорт отменён: {exc}")
    reset_confirm = st.checkbox("Подтверждаю сброс к исходной Калисте")
    if st.button("🔄 Сброс",use_container_width=True, disabled=not reset_confirm):
        restored = migrate(deepcopy(DEFAULT)); recalc(restored)
        if save(restored):
            st.session_state.data = restored
            for key in list(st.session_state):
                if key != "data": del st.session_state[key]
            persist_and_rerun()

# ===================== ОБЗОР =====================
if page=="Обзор":
    st.markdown(f"<div class='main-title'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{data['race']} · {data['class']} · Ур.{data['level']}</div>", unsafe_allow_html=True)
    data["portrait_url"] = st.text_input("URL портрета (картинка)", value=data.get("portrait_url",""), key="portrait")
    if data.get("portrait_url"):
        try:
            st.image(data["portrait_url"], width=200)
        except Exception:
            st.caption("Не удалось загрузить изображение")
    c1,c2=st.columns(2)
    c1.progress(min(data["hp_current"]/max(data["hp_max"],1),1.0),text=f"HP {data['hp_current']}/{data['hp_max']}")
    c2.progress(min(data["mana_current"]/max(data["mana_max"],1),1.0),text=f"MP {data['mana_current']}/{data['mana_max']}")
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Сила закл.",f"+{data['spell_power']*100:.0f}%")
    m2.metric("Броня",data["armor"])
    m3.metric("Иниц.",data["initiative"])
    m4.metric("Очки",data["free_points"])
    st.markdown("<div class='section-h'>Сопротивления</div>", unsafe_allow_html=True)
    rc=st.columns(6)
    for i,e in enumerate(ELEMENTS):
        rc[i].metric(e, data["resists"].get(e,0))
    st.markdown("<div class='section-h'>Характеристики</div>", unsafe_allow_html=True)
    cols=st.columns(4)
    for i,n in enumerate(["Сила","Выносливость","Ловкость","Мудрость","Интеллект","Харизма","Дух"]):
        cols[i%4].metric(n, total_stat(data,n))
    st.markdown("<div class='section-h'>Опыт</div>", unsafe_allow_html=True)
    x1,x2,x3=st.columns([2,1,1])
    ax=x1.number_input("XP",0,value=100,step=50)
    if x2.button("➕ XP"): data["xp"]+=ax; data["xp_to_next"]=max(0,data["xp_to_next"]-ax); persist_and_rerun()
    if x3.button("⬆ Ур.+1"):
        data["level"]+=1; data["free_points"]+=4; data["xp_to_next"]=data["level"]*1000; recalc(data); persist_and_rerun()

# ===================== БОЙ =====================
elif page=="Бой":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Бой</div>", unsafe_allow_html=True)

    # Управление боем
    c1,c2,c3=st.columns(3)
    if c1.button("▶️ Начать бой", disabled=data["combat_active"]):
        data["combat_active"]=True
        for _, target in participants(data):
            for effect in target.get("effects", []): effect["applied_round"] = 0
        data["round"]=1
        data["turn_order"]=build_turn_order(data)
        data["current_turn"]=0
        # Начало боя не является отдыхом: перезарядки сохраняются.
        log(f"=== Бой начат. Раунд 1 ===")
        persist_and_rerun()
    if c2.button("⏹ Закончить бой"):
        data["combat_active"]=False
        data["turn_order"]=[]
        data["crit_boost_active"] = False
        log("=== Бой окончен ===")
        persist_and_rerun()
    if c3.button("⏭ Следующий ход", disabled=not data["combat_active"]):
        for message in advance_turn(data):
            log(message)
        persist_and_rerun()

    # Текущий ход
    if data["combat_active"] and data["turn_order"]:
        actor=get_current_actor(data)
        st.markdown(f"<div class='turn-now'>Раунд <b>{data['round']}</b> · Сейчас ходит: <b>{actor['name'] if actor else '?'}</b></div>", unsafe_allow_html=True)
        order_str=" → ".join([("▶"+t["name"] if t==actor else t["name"]) for t in data["turn_order"]])
        st.caption(order_str)

    # Ресурсы
    r1,r2,r3,r4=st.columns(4)
    r1.metric("Калист HP", f"{data['hp_current']}/{data['hp_max']}")
    r2.metric("Мана", f"{data['mana_current']}/{data['mana_max']}")
    r3.metric("Броня", data["armor"])
    r4.metric("Пепел/Тень", f"{data['pepel']}/5 · {data['ten']}/5")

    render_gm_tools(data)
    show_effect_summary(data)

    # Союзник
    st.markdown("<div class='section-h'>Союзник</div>", unsafe_allow_html=True)
    ally=data["ally"]
    a1,a2,a3,a4,a5=st.columns(5)
    ally["name"]=a1.text_input("Имя", ally["name"])
    ally["hp"]=a2.number_input("HP",0,value=int(ally["hp"]),key="ah")
    ally["hp_max"]=a3.number_input("Макс",1,value=int(ally["hp_max"]),key="ahm")
    ally["armor"]=a4.number_input("Броня",0,value=int(ally["armor"]),key="aa")
    ally["initiative"]=a5.number_input("Иниц.",0,value=int(ally.get("initiative",12)),key="ai")
    
    # Атака союзника
    b1,b2=st.columns(2)
    ally["attack_damage"]=b1.number_input("Урон атаки",0,value=int(ally.get("attack_damage",40)),key="aad")
    ally["attack_type"]=b2.selectbox("Тип атаки",["Физический"]+ELEMENTS, index=(["Физический"]+ELEMENTS).index(ally.get("attack_type","Физический")) if ally.get("attack_type","Физический") in ["Физический"]+ELEMENTS else 0, key="aat")
    
    # Сопротивления союзника
    st.caption("Сопротивления стихиям")
    rc=st.columns(6)
    if "resists" not in ally:
        ally["resists"]={e:10 for e in ELEMENTS}
    for i,el in enumerate(ELEMENTS):
        ally["resists"][el]=rc[i].number_input(el[:3],0,value=int(ally["resists"].get(el,10)),key=f"ar_{el}")
    
    st.progress(min(ally["hp"]/max(ally["hp_max"],1),1.0))
    show_effect_summary(ally)


    with st.expander("🔥 Пепел / 🌑 Тень", expanded=False):
        p1, p2 = st.columns(2)
        with p1:
            st.progress(data["pepel"]/5, text=f"Пепел {data['pepel']}/5")
            b1, b2 = st.columns(2)
            if b1.button("+1 Пепел", key="pep_plus"):
                data["pepel"] = min(5, data["pepel"]+1); persist_and_rerun()
            if b2.button("Активировать", key="pep_act", disabled=data["pepel"]<5):
                data["pepel"] = 0
                data["pepel_empower"] = True
                log("Пепел → след. огонь игнор 30% сопр.")
                persist_and_rerun()
            if data.get("pepel_empower"):
                st.success("Усиление огня активно")
        with p2:
            st.progress(data["ten"]/5, text=f"Тень {data['ten']}/5")
            b1, b2, b3 = st.columns(3)
            if b1.button("+1 Тень", key="ten_plus"):
                data["ten"] = min(5, data["ten"]+1); persist_and_rerun()
            if b2.button("Невид.", key="ten_inv", disabled=data["ten"]<5):
                data["ten"] = 0
                data["ten_invis"] = True
                log("Тень: невидимость 1 ход")
                persist_and_rerun()
            if b3.button("+20 сопр.", key="ten_res", disabled=data["ten"]<5):
                data["ten"] = 0
                data["ten_resist_boost"] = 2
                log("Тень: +20 к сопротивлениям на 2 раунда")
                persist_and_rerun()
            if data.get("ten_invis"):
                st.success("Невидима")
            elif data.get("ten_resist_boost", 0) > 0:
                st.success(f"+20 к сопротивлениям ({data['ten_resist_boost']} р.)")

    with st.expander("Статусы и отдых", expanded=False):
        o1, o2 = st.columns(2)
        if o1.button("🌙 Короткий отдых"):
            restored = restore_mana(data, data["mana_regen"] * 3)
            log(f"Короткий отдых: +{restored} MP"); persist_and_rerun()
        if o2.button("🌅 Длинный отдых"):
            data["hp_current"] = data["hp_max"]
            data["mana_current"] = data["mana_max"]
            data["pepel"] = 0; data["ten"] = 0
            data["soul_flame_boost"] = False; data["crit_boost_active"] = False
            data["pepel_empower"] = False; data["ten_invis"] = False; data["ten_resist_boost"] = 0
            data["status_effects"] = []
            data["dots"] = []
            data["effects"] = []
            for p in data["passives"].values():
                if p.get("type") == "special":
                    p["used"] = False
            for s in data["spells"]:
                s["cd_left"] = 0
            log("Длинный отдых"); persist_and_rerun()

    st.divider()

    # ===== ВРАГИ =====
    st.markdown("<div class='section-h'>Враги</div>", unsafe_allow_html=True)
    for i,e in enumerate(data["enemies"]):
        elite="⭐ " if e.get("is_elite") else ""
        st.markdown(f"**{elite}{e['name']}** · ур.{e.get('level',1)} · {e.get('size','?')} · иниц.{e.get('initiative',10)}")
        st.progress(min(e["hp"]/max(e["hp_max"],1),1.0), text=f"HP {e['hp']}/{e['hp_max']}")
        res=e.get("resists",{})
        st.caption(f"Броня {e.get('armor',0)} · Атака {e.get('attack_damage',0)} ({e.get('attack_type','?')}) · " +
                   " · ".join(f"{el[:1]}{res.get(el,0)}" for el in ELEMENTS))
        show_effect_summary(e)

        b1,b2,b3=st.columns(3)
        if b1.button("⚔→Калист", key=f"ek{e['id']}", disabled=e["hp"] <= 0):
            if data.get("ten_invis"):
                log(f"{e['name']} промахнулся — Калист невидима")
                data["ten_invis"] = False
                persist_and_rerun()
            result = apply_damage(data, e.get("attack_damage", 10), e.get("attack_type", "Физический"))
            log(f"{e['name']} → " + damage_message(data["name"], result))
            persist_and_rerun()
        if b2.button("⚔→Союзник", key=f"ea{e['id']}", disabled=e["hp"] <= 0):
            result = apply_damage(ally, e.get("attack_damage", 10), e.get("attack_type", "Физический"))
            log(f"{e['name']} → " + damage_message(ally["name"], result))
            persist_and_rerun()
        if b3.button("🗑", key=f"ed{e['id']}"):
            data["enemies"].pop(i); persist_and_rerun()

        # ручной урон
        rc1,rc2,rc3=st.columns([1.4,1.2,1])
        dt=rc1.selectbox("Тип",["Физический"]+ELEMENTS, key=f"edt{e['id']}")
        rw=rc2.number_input("Урон",0,value=40,step=5, key=f"erw{e['id']}")
        if rc3.button("Урон", key=f"eh{e['id']}"):
            result = apply_damage(e, rw, dt)
            log(damage_message(e["name"], result))
            if e["hp"]<=0: log(f"{e['name']} повержен")
            persist_and_rerun()
        st.divider()

    # Добавить врага
    with st.form("adden"):
        st.markdown("**Новый враг**")
        f1,f2,f3,f4=st.columns(4)
        nm=f1.text_input("Имя","Враг")
        lv=f2.number_input("Ур.",1,60,10)
        sz=f3.selectbox("Размер",["Мелкий","Обычный","Крупный","Огромный"])
        el=f4.checkbox("Элитный")
        if st.form_submit_button("Сгенерировать"):
            stt=gen_enemy(lv,sz,el)
            data["enemies"].append({"id":data["next_enemy_id"],"name":nm,"level":lv,"size":sz,"is_elite":el,**stt})
            data["next_enemy_id"]+=1
            log(f"+ {nm} (ур.{lv} {sz}{'⭐' if el else ''}) HP{stt['hp']}")
            if data["combat_active"]:
                refresh_turn_order(data)
            persist_and_rerun()

    st.divider()

    # Урон от союзника
    st.markdown("<div class='section-h'>Урон от союзника</div>", unsafe_allow_html=True)
    alive=[e for e in data["enemies"] if e["hp"]>0]
    if alive:
        t1,t2,t3,t4=st.columns([2,1.3,1.2,1])
        tgt=t1.selectbox("Цель",[e["id"] for e in alive],
                          format_func=lambda eid: next(f"{e['name']} · #{eid}" for e in alive if e["id"] == eid),key="atgt")
        default_type = ally.get("attack_type","Физический")
        type_opts = ["Физический"]+ELEMENTS
        dt=t2.selectbox("Тип", type_opts, index=type_opts.index(default_type) if default_type in type_opts else 0, key="adt")
        rw=t3.number_input("Урон",0,value=int(ally.get("attack_damage",40)),step=5,key="arw")
        if t4.button("Ударить"):
            for e in data["enemies"]:
                if e["id"]==tgt and e["hp"]>0:
                    result = apply_damage(e, rw, dt)
                    log(f"{ally['name']} → " + damage_message(e["name"], result))
                    if e["hp"]<=0: log(f"{e['name']} повержен")
                    break
            persist_and_rerun()

    st.divider()

    # Заклинания

    with st.expander("📜 Заклинания Калисты", expanded=True):
        if data.get("last_school"):
            st.caption(f"Прошлая школа: {data['last_school']}")
        if data.get("soul_flame_boost"):
            st.warning("Ритуал: Пламя души +40%")
        if data.get("pepel_empower"):
            st.success("Пепел: след. огонь игнор 30% сопр.")

        targets = [None] + [token for token, _ in participants(data)]
        stgt = st.selectbox("Цель", targets, key="spell_target_v7",
                           format_func=lambda token: "—" if token is None else participant_label(data, token))
        crit_mode = st.selectbox("Критический удар", ["Без крита", "Крит по решению ведущего", "Бросок при применении"])
        override_damage = st.checkbox("Назначить итоговый урон вручную")
        gm_damage = st.number_input("Готовый урон (щит будет учтён)", min_value=0, value=0, disabled=not override_damage)
        st.caption("Каст применяет выбранное действие, расход маны, перезарядку и эффекты. "
                   "Для лечения и щитов сила задаётся явно, без множителей урона.")
        for sp in data["spells"]:
            action = spell_action(sp)
            dual = {data.get("last_school"), sp["school"]} == {"Огонь", "Тьма"}
            soul = data.get("soul_flame_boost") and sp["name"] == "Пламя души"
            raw = spell_raw(sp.get("base", 0), data.get("spell_power", 0), dual, soul) if action == "damage" else sp.get("effect_value", 0)
            target = participant(data, stgt) if stgt is not None else None
            shield_amount = None
            if action == "shield":
                shield_amount = st.number_input(f"Сила щита · {sp['name']}", min_value=0,
                                                 value=sp.get("effect_value", 0), key=f"cast_shield_{sp['id']}")
                if shield_amount == 0:
                    st.caption("Укажи силу щита перед кастом. Её также можно сохранить на странице «Заклинания».")
            cd = sp.get("cd_left", 0)
            needs_target = action in ("shield", "heal") or (action == "damage" and (raw > 0 or sp.get("dot")))
            can = data["mana_current"] >= sp.get("mana", 0) and cd <= 0 and (not needs_target or target is not None)
            if action == "shield": can = can and shield_amount > 0
            if action == "heal": can = can and raw > 0
            if target is not None and action == "damage" and raw > 0:
                can = can and target[hp_fields(target)[0]] > 0
                dtype = "Огонь" if "Огонь" in sp["school"] else "Тьма"
                preview_raw = round(raw * 1.5) if crit_mode == "Крит по решению ведущего" else raw
                preview = damage_preview(target, gm_damage if override_damage else preview_raw, dtype,
                                         final=override_damage,
                                         defense_factor=0.7 if data.get("pepel_empower") and dtype == "Огонь" else 1.0)
                st.caption(f"{sp['name']}: " + damage_message(target["name"], preview) +
                           (" · до броска крита" if crit_mode == "Бросок при применении" and not override_damage else ""))
            elif target is not None and action == "heal":
                hp_key, maximum_key = hp_fields(target)
                st.caption(f"{sp['name']}: восстановится {min(raw, max(0, target[maximum_key] - target[hp_key]))} HP")
            cols = st.columns([2.8, 0.8, 0.7, 0.7, 1.1])
            icon = "🛡" if action == "shield" else "💚" if action == "heal" else "🔥" if "Огонь" in sp["school"] else "🌑"
            cols[0].markdown(f"**{icon} {sp['name']}**")
            cols[0].caption((sp.get("desc") or "") + (" · DoT" if action == "damage" and sp.get("dot") else ""))
            cols[1].write(f"**{shield_amount if action == 'shield' else raw or '—'}**")
            cols[2].write(f"{sp.get('mana', 0)} MP")
            cols[3].write(f"КД {cd}/{sp.get('cd_max', 0)}" if sp.get("cd_max") else "—")
            if cols[4].button("Каст", key=f"cast_{sp['id']}", disabled=not can):
                chance = min(1.0, max(0.0, data.get("crit_chance", 0.065) + (0.10 if data.get("crit_boost_active") else 0)))
                is_crit = action == "damage" and not override_damage and (
                    crit_mode == "Крит по решению ведущего" or
                    (crit_mode == "Бросок при применении" and random.random() < chance))
                try:
                    messages = cast_spell(data, sp, target, crit=is_crit,
                                          final_damage=gm_damage if override_damage and action == "damage" else None,
                                          shield_amount=shield_amount)
                    for message in messages: log(message)
                    if data["combat_active"]: refresh_turn_order(data)
                    persist_and_rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.divider()
    st.markdown("<div class='section-h'>Лог</div>", unsafe_allow_html=True)
    for entry in data["combat_log"][:20]: st.text(entry)
    lc1, lc2 = st.columns(2)
    if lc1.button("Очистить лог"):
        data["combat_log"]=[]; persist_and_rerun()
    if lc2.button("📋 Копировать лог"):
        log_text = "\n".join(data["combat_log"])
        st.code(log_text, language=None)
        st.caption("Выдели и скопируй текст выше")

# ===================== ЭКИПИРОВКА =====================
elif page=="Экипировка":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Экипировка</div>", unsafe_allow_html=True)
    for slot,it in data["equipment"].items():
        with st.expander(f"{'🔹' if it.get('name') else '▫️'} {slot}: {it.get('name') or '—'}"):
            it["name"]=st.text_input("Имя",it.get("name",""),key=f"n{slot}")
            c=st.columns(4)
            it["armor"]=c[0].number_input("Броня",0,value=int(it.get("armor",0)),key=f"a{slot}")
            it["attack"]=c[1].number_input("Атака",0,value=int(it.get("attack",0)),key=f"t{slot}")
            it["int"]=c[2].number_input("Инт",0,value=int(it.get("int",0)),key=f"i{slot}")
            it["wis"]=c[3].number_input("Мудр",0,value=int(it.get("wis",0)),key=f"w{slot}")
            c2=st.columns(4)
            it["spi"]=c2[0].number_input("Дух",0,value=int(it.get("spi",0)),key=f"s{slot}")
            it["fire"]=c2[1].number_input("Огонь",0,value=int(it.get("fire",0)),key=f"f{slot}")
            it["dark"]=c2[2].number_input("Тьма",0,value=int(it.get("dark",0)),key=f"d{slot}")
            it["earth"]=c2[3].number_input("Земля",0,value=int(it.get("earth",0)),key=f"e{slot}")
            c3=st.columns(3)
            it["water"]=c3[0].number_input("Вода",0,value=int(it.get("water",0)),key=f"wa{slot}")
            it["air"]=c3[1].number_input("Воздух",0,value=int(it.get("air",0)),key=f"ai{slot}")
            it["light"]=c3[2].number_input("Свет",0,value=int(it.get("light",0)),key=f"l{slot}")
    if st.button("🔄 Пересчитать",type="primary"):
        recalc_equip(data); recalc(data); st.success(f"Броня {data['armor']}"); persist_and_rerun()

# ===================== ХАРАКТЕРИСТИКИ =====================
elif page=="Характеристики":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Характеристики</div>", unsafe_allow_html=True)
    st.info(f"Свободные очки: **{data['free_points']}** · Уровень **{data['level']}**")

    with st.expander("Характеристики", expanded=True):
        for n in ["Сила","Выносливость","Ловкость","Мудрость","Интеллект","Харизма","Дух"]:
            cols = st.columns([2,1,1,1,1])
            cols[0].write(f"**{n}**")
            cols[1].write(f"База {data['base_stats'][n]}")
            cols[2].write(f"+{data['equip_bonuses'][n]}")
            cols[3].write(f"**{total_stat(data,n)}**")
            if cols[4].button("＋", key=f"u{n}", disabled=data["free_points"]<=0):
                data["base_stats"][n] += 1
                data["free_points"] -= 1
                recalc(data)
                persist_and_rerun()
        st.markdown("**Производные**")
        d1,d2,d3 = st.columns(3)
        d1.metric("Сила закл.", f"+{data['spell_power']*100:.0f}%")
        d1.metric("Реген маны", data["mana_regen"])
        d2.metric("Сопр. контролю", f"{data.get('control_resist',0)*100:.1f}%")
        d2.metric("Инициатива", data["initiative"])
        d3.metric("Броня", data["armor"])
        d3.metric("Крит", f"{data.get('crit_chance',0.065)*100:.1f}%")

    with st.expander("Сопротивления стихиям"):
        rc = st.columns(6)
        for i, e in enumerate(ELEMENTS):
            rc[i].metric(e, data["resists"].get(e, 0))

    with st.expander("Пассивки (расовые и классовые)"):
        for k, p in data["passives"].items():
            if p.get("type") in ("racial", "class"):
                st.markdown(f"**{p['name']}** — {p['desc']}")
                if k == "mana_reserve":
                    st.caption("Пока справочное правило: бонус к регенерации назначает ведущий. Автоматический триггер ещё не подключён.")
                if k == "shadow_child":
                    st.caption("Текущий расчёт: +20 пунктов сопротивления с пределом 95; это сохранённая формула программы.")

    with st.expander("Особые умения"):
        for k, p in data["passives"].items():
            if p.get("type") != "special":
                continue
            c1, c2 = st.columns([3.5, 1])
            status = "✅ использовано" if p["used"] else "🟢 доступно"
            c1.markdown(f"**{p['name']}** — {status}<br>{p['desc']}", unsafe_allow_html=True)
            if not p["used"]:
                if c2.button("Использовать", key=f"pas_{k}"):
                    p["used"] = True
                    if k == "ritual_black_flame":
                        data["soul_flame_boost"] = True
                        log("Ритуал: Пламя души усилено")
                    elif k == "cold_calculation":
                        data["crit_boost_active"] = True
                        log("Холодный расчёт: +10% крита")
                    else:
                        log(f"Использовано: {p['name']}")
                    persist_and_rerun()
            else:
                c2.write("—")

elif page=="Инвентарь":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Инвентарь</div>", unsafe_allow_html=True)
    g,s,c=st.columns(3)
    data["gold"]=g.number_input("Золото",0,value=data["gold"])
    data["silver"]=s.number_input("Серебро",0,value=data["silver"])
    data["copper"]=c.number_input("Медь",0,value=data["copper"])
    for i,it in enumerate(data["inventory"]):
        cols=st.columns([3,1,1,1])
        cols[0].write(f"**{it['name']}** · {it['type']}")
        it["qty"]=cols[1].number_input("Кол",0,value=it["qty"],key=f"q{i}",label_visibility="collapsed")
        use = it.get("use")
        if use:
            cols[0].caption(f"Применение: { {'heal': 'лечение', 'mana': 'мана', 'shield': 'щит'}[use['kind']]} · {use['value']}")
            if cols[2].button("Применить", key=f"use_item_{i}", disabled=it["qty"] <= 0 or use["value"] <= 0):
                message = use_item(data, it)
                log(message)
                persist_and_rerun()
        with st.expander(f"Действие предмета · {it['name']} · #{i + 1}"):
            with st.form(f"item_use_{i}"):
                options = ["none", "heal", "mana", "shield"]
                current = use["kind"] if use else "none"
                kind = st.selectbox("Действие", options, index=options.index(current),
                                    format_func=lambda v: {"none": "Справочный предмет", "heal": "Лечение", "mana": "Восстановление маны", "shield": "Щит"}[v])
                amount = st.number_input("Величина", min_value=0, value=use["value"] if use else 0)
                duration = st.number_input("Полных раундов (0 — бессрочно)", min_value=0, value=use.get("duration", 0) if use else 0)
                if st.form_submit_button("Сохранить действие"):
                    it["use"] = None if kind == "none" else {"kind": kind, "value": amount, "duration": duration}
                    persist_and_rerun()
        if cols[3].button("🗑",key=f"x{i}"): data["inventory"].pop(i); persist_and_rerun()
    with st.form("ai"):
        st.markdown("**Добавить предмет**")
        nn = st.text_input("Название")
        nt = st.selectbox("Тип", ["Расходник", "Реагент", "Свиток", "Оружие", "Броня", "Реликвия", "Инструмент", "Книга", "Валюта", "Прочее"])
        nq = st.number_input("Количество", min_value=1, value=1)
        nd = st.text_input("Описание")
        if st.form_submit_button("Добавить") and nn.strip():
            data["inventory"].append({"name": nn.strip(), "type": nt, "qty": int(nq), "desc": nd, "use": None})
            persist_and_rerun()


elif page=="Заклинания":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Заклинания</div>", unsafe_allow_html=True)
    st.caption("Кулдауны в раундах. 0 = без кулдауна. Каст — на странице «Бой».")

    for i, sp in enumerate(list(data["spells"])):
        with st.expander(f"{sp.get('name','?')} (КД {sp.get('cd_max',0)})"):
            sp["name"] = st.text_input("Название", sp.get("name",""), key=f"sn{sp['id']}")
            c1, c2, c3, c4 = st.columns(4)
            sp["base"] = c1.number_input("Базовый урон", min_value=0, value=int(sp.get("base",0) or 0), key=f"sb{sp['id']}")
            sp["mana"] = c2.number_input("Мана", min_value=0, value=int(sp.get("mana",0) or 0), key=f"sm{sp['id']}")
            sp["cd_max"] = c3.number_input("Кулдаун", min_value=0, value=int(sp.get("cd_max",0) or 0), key=f"sc{sp['id']}")
            schools = ["Огонь", "Тьма", "Огонь+Тьма"]
            cur = sp.get("school", "Огонь")
            sp["school"] = c4.selectbox("Школа", schools, index=schools.index(cur) if cur in schools else 0, key=f"ss{sp['id']}")
            sp["desc"] = st.text_input("Описание", sp.get("desc",""), key=f"sd{sp['id']}")
            actions = ["damage", "heal", "shield", "note"]
            sp["action"] = st.selectbox("Действие", actions, index=actions.index(spell_action(sp)),
                                        format_func=lambda v: {"damage": "Урон", "heal": "Лечение", "shield": "Щит", "note": "Статус / заметка"}[v], key=f"sa{sp['id']}")
            if sp["action"] in ("heal", "shield"):
                sp["effect_value"] = st.number_input("Лечение / сила щита (без множителей)", min_value=0,
                                                      value=sp.get("effect_value", 0), key=f"sev{sp['id']}")
            if sp["action"] in ("shield", "note"):
                sp["effect_duration"] = st.number_input("Полных раундов (0 — бессрочно)", min_value=0,
                                                         value=sp.get("effect_duration", 0), key=f"sed{sp['id']}")
            if sp["action"] == "damage":
                with st.form(f"dot_settings_{sp['id']}"):
                    existing = sp.get("dot") or {}
                    enabled = st.checkbox("Периодический урон", value=bool(existing))
                    dot_name = st.text_input("Название эффекта", value=existing.get("name", "Горение"))
                    dot_amount = st.number_input("Урон за срабатывание", min_value=0, value=existing.get("damage", 0))
                    dot_duration = st.number_input("Срабатываний", min_value=1, value=max(1, existing.get("duration", 3)))
                    dot_element = st.selectbox("Тип урона эффекта", DAMAGE_TYPES,
                                               index=DAMAGE_TYPES.index(existing.get("element", "Огонь")))
                    if st.form_submit_button("Сохранить периодический эффект"):
                        if enabled and not dot_name.strip():
                            st.error("Укажи название эффекта")
                        else:
                            sp["dot"] = {"name": dot_name.strip(), "damage": dot_amount,
                                         "duration": dot_duration, "element": dot_element} if enabled else None
                            persist_and_rerun()

            gives_opts = [None, "pepel", "ten", "both"]
            cur_g = sp.get("gives")
            gi = gives_opts.index(cur_g) if cur_g in gives_opts else 0
            sp["gives"] = st.selectbox("Даёт ресурс", gives_opts, index=gi,
                format_func=lambda x: {None:"Ничего","pepel":"Пепел","ten":"Тень","both":"Оба"}[x], key=f"sg{sp['id']}")
            if st.button("Удалить заклинание", key=f"sdel{sp['id']}"):
                data["spells"].pop(i)
                persist_and_rerun()

    with st.form("asp"):
        st.markdown("**Новое заклинание**")
        sn = st.text_input("Название")
        c1, c2, c3 = st.columns(3)
        sb = c1.number_input("Урон", min_value=0, value=50)
        sm = c2.number_input("Мана", min_value=0, value=30)
        sc = c3.number_input("Кулдаун", min_value=0, value=0)
        ss = st.selectbox("Школа", ["Огонь", "Тьма", "Огонь+Тьма"])
        sd = st.text_input("Описание")
        sg = st.selectbox("Даёт", [None, "pepel", "ten", "both"],
            format_func=lambda x: {None:"Ничего","pepel":"Пепел","ten":"Тень","both":"Оба"}[x])
        if st.form_submit_button("Добавить") and sn.strip():
            nid = max((s.get("id",0) for s in data["spells"]), default=0) + 1
            data["spells"].append({
                "id": nid, "name": sn.strip(), "base": sb, "mana": sm,
                "school": ss, "desc": sd, "gives": sg,
                "cd_max": sc, "cd_left": 0, "dot": None, "range": "Средняя"
            })
            persist_and_rerun()


# ===================== КВЕСТЫ =====================
elif page=="Квесты":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Квесты и заметки</div>", unsafe_allow_html=True)

    if not data.get("quests"):
        st.caption("Квестов пока нет")

    for i, q in enumerate(list(data.get("quests", []))):
        title = f"{q.get('name','Без имени')} — {q.get('status','?')}"
        with st.expander(title):
            q["name"] = st.text_input("Название", q.get("name",""), key=f"qn{i}")
            statuses = ["Активен", "В процессе", "Ожидание", "Выполнен", "Провален"]
            cur_st = q.get("status", "Активен")
            q["status"] = st.selectbox("Статус", statuses,
                index=statuses.index(cur_st) if cur_st in statuses else 0, key=f"qs{i}")
            q["desc"] = st.text_area("Описание", q.get("desc",""), key=f"qdesc{i}")
            if st.button("Удалить квест", key=f"qdel{i}"):
                data["quests"].pop(i)
                persist_and_rerun()

    with st.form("aq"):
        st.markdown("**Новый квест**")
        qn = st.text_input("Название")
        qs = st.selectbox("Статус", ["Активен", "В процессе", "Ожидание"])
        qd = st.text_area("Описание")
        if st.form_submit_button("Добавить") and qn.strip():
            nid = max((q.get("id",0) for q in data.get("quests",[])), default=0) + 1
            data.setdefault("quests", []).append({"id": nid, "name": qn.strip(), "status": qs, "desc": qd})
            persist_and_rerun()

    st.markdown("---")
    st.markdown("**Личные заметки**")
    data["notes"] = st.text_area("Заметки", value=data.get("notes",""), height=150, key="notes_area")


# ===================== КУБИКИ =====================
elif page=="Кубики":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Кубики</div>", unsafe_allow_html=True)
    cols=st.columns(7)
    for i,s in enumerate([4,6,8,10,12,20,100]):
        with cols[i]:
            if st.button(f"d{s}",key=f"d{s}",use_container_width=True):
                r=random.randint(1,s); st.session_state[f"r{s}"]=r; log(f"d{s}:{r}")
            if f"r{s}" in st.session_state:
                st.markdown(f"<h2 style='text-align:center;color:#E8DAEF'>{st.session_state[f'r{s}']}</h2>",unsafe_allow_html=True)

# ===================== БИО =====================
elif page=="Биография":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Биография</div>", unsafe_allow_html=True)
    st.markdown("""
### Внешность
Высокая даже для дроу (около 178 см), стройная, с грациозной, почти хищной осанкой.
Кожа цвета глубокой ночи с лёгким пепельным оттенком. Волосы — длинные, **чёрные как ночь**, обычно собраны в небрежный высокий хвост или спрятаны под капюшоном.
Глаза ярко-фиолетовые, почти светящиеся в темноте. На левой щеке тонкий шрам от старого ритуального клинка.
Одевается исключительно в чёрное и тёмно-фиолетовое. Движения точные, экономные, без лишних жестов.

### Характер
Холодная, сдержанная, крайне наблюдательная. Редко повышает голос — предпочитает, чтобы за неё говорили последствия.
Обладает сухим, иногда язвительным чувством юмора. К тем, кого считает «своими», проявляет неожиданную (хоть и сдержанную) заботу.
Глубоко амбициозна, но не ради власти над другими, а ради понимания и контроля над силами, которые большинство считают запретными.
Ненавидит слабость в себе и презирает тех, кто сдаётся. При этом сама боится потерять контроль над собственной магией.

### Предыстория
Калист родилась в **Доме Клиф** — большом и гордом матриархальном доме дроу, известном своими экспериментами на стыке огня и тьмы.
Её мать, матриарх **Ильраэль Клиф**, была одержима идеей создать «чистое пламя бездны» — огонь, питаемый самой пустотой.
В возрасте шестнадцати лет Калист стала свидетельницей падения своего дома: во время особо опасного ритуала что-то пошло не так.
Чёрное пламя вырвалось из-под контроля и уничтожило почти весь Дом Клиф за одну ночь.
Выжила только она — потому что в последний момент мать затолкала её в защитный круг и сама приняла основной удар.

С тех пор Калист странствует. Сначала по Подземью, потом — на поверхность.
Она продолжает исследования матери, но уже более осторожно и методично.
Носит с собой единственную реликвию дома — **Фамильный Амулет** — и клянётся, что либо доведёт работу до конца, либо погибнет, пытаясь.
На поверхности её часто принимают за обычную тёмную эльфийку-отшельницу. Мало кто догадывается, насколько глубоко она погружена в запретные знания.

### Цели и мотивация
- Завершить работу матери и создать стабильное «Пламя Души»
- Найти или воссоздать знания, утерянные вместе с Домом Клиф
- Доказать себе, что падение дома было не приговором, а ценой за нечто большее
- Достичь равновесия огня и тьмы внутри себя

### Страхи и слабости
- Потеря контроля (повторить судьбу матери)
- Одиночество
- Светлые маги и «чистые» жрецы
- Привязанность

### Важные связи
- **Ильраэль Клиф** (мать, погибла) — источник и боли, и силы
- **Вэрин Т’лаас** — бывший соратник, расстались на плохой ноте
- **«Серый»** — контрабандист с поверхности, знает часть правды
""")



save(data)
