#!/usr/bin/env python3
"""
Калист Клиф — v6 · первый этап
Очередь ходов, ИИ врагов, DoT, кулдауны, 6 стихий
"""

import streamlit as st
import json
import random
import os
import tempfile
import shutil
import math
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
        "shadow_child": {"name":"Дитя тени","type":"class","used":False,"desc":"Тёмные заклинания дают Тень. При 5 — активация: невидимость 1 ход ИЛИ +20% сопротивления на 2 хода."},
        "mana_reserve": {"name":"Магический резерв","type":"class","used":False,"desc":"Когда мана <20%, реген маны +50% на 3 тика. Автоматически."},
        # Особые (активируемые, раз в день/отдых)
        "ritual_black_flame": {"name":"Ритуал Чёрного Пламени","type":"special","used":False,"desc":"Раз в день: следующее Пламя души +40% урона без долгого каста."},
        "cold_calculation": {"name":"Холодный расчёт","type":"special","used":False,"desc":"В начале боя (1 ход): +10% шанса крита до конца боя."},
        "memory_of_house": {"name":"Память Дома Клиф","type":"special","used":False,"desc":"Раз в долгий отдых: преимущество на проверку знаний о запретной магии."},
    },
    "soul_flame_boost": False,
    "crit_boost_active": False,
    "pepel_empower": False,   # следующее огненное игнор 30% fire resist
    "ten_invis": False,       # невидимость 1 ход
    "ten_resist_boost": 0,    # раундов +20% сопротивления осталось
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
                              "resists": {el: 0 for el in ELEMENTS}, "initiative": 0})
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
    data["schema_version"] = 6
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

def process_dots(target, name_for_log):
    """Тикает DoT’ы, возвращает список сообщений"""
    msgs=[]
    new_dots=[]
    for dot in target.get("dots",[]):
        el=dot.get("element","Огонь")
        if "resists" in target:
            res=target["resists"].get(el,0)
        elif name_for_log=="Калист":
            res=st.session_state.data["resists"].get(el,0)
        else:  # ally
            res=0
        dmg=real_dmg(dot["damage"], res) if el!="Физический" else real_dmg(dot["damage"], target.get("armor",0))
        hp_key = "hp_current" if "hp_current" in target else "hp"
        target[hp_key]=max(0, target[hp_key]-dmg)
        msgs.append(f"DoT «{dot['name']}» по {name_for_log}: {dmg} ({el})")
        dot["duration"]-=1
        if dot["duration"]>0: new_dots.append(dot)
        else: msgs.append(f"«{dot['name']}» спал с {name_for_log}")
    target["dots"]=new_dots
    return msgs

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
    """Простой ИИ: бьёт более слабую цель"""
    targets=[]
    if data["hp_current"]>0:
        targets.append(("player", data["hp_current"], data["armor"], data["resists"]))
    if data["ally"]["hp"]>0:
        targets.append(("ally", data["ally"]["hp"], data["ally"]["armor"], data["ally"].get("resists", {})))
    if not targets: return
    # предпочитаем меньшее HP
    targets.sort(key=lambda t: t[1])
    kind, _, armor_or_res, resists = targets[0]
    raw=enemy.get("attack_damage",10)
    atype=enemy.get("attack_type","Физический")
    if atype=="Физический":
        dmg=real_dmg(raw, armor_or_res if kind=="ally" else data["armor"])
    else:
        res = resists.get(atype, 0)
        dmg=real_dmg(raw, res)
    if kind=="player":
        data["hp_current"]=max(0, data["hp_current"]-dmg)
        log(f"🤖 {enemy['name']} бьёт Калисту ({atype} {raw}) → {dmg} · HP {data['hp_current']}")
    else:
        data["ally"]["hp"]=max(0, data["ally"]["hp"]-dmg)
        log(f"🤖 {enemy['name']} бьёт {data['ally']['name']} ({atype} {raw}) → {dmg} · HP {data['ally']['hp']}")

def persist_and_rerun():
    # HP союзника меняется боевыми кнопками вне его редактора.
    st.session_state.pop("ah", None)
    if save(st.session_state.data):
        st.rerun()


# ===================== INIT =====================
if "data" not in st.session_state:
    st.session_state.data=load()
    recalc(st.session_state.data)
data=st.session_state.data
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
        # тикаем DoT текущего
        actor=get_current_actor(data)
        if actor:
            if actor["kind"]=="player":
                for m in process_dots(data, data["name"]): log(m)
            elif actor["kind"]=="ally":
                for m in process_dots(data["ally"], data["ally"]["name"]): log(m)
            elif actor["kind"]=="enemy":
                for e in data["enemies"]:
                    if e["id"]==actor["id"]:
                        for m in process_dots(e, e["name"]): log(m)
                        break
        # уменьшаем кулдауны в конце полного круга
        data["current_turn"]+=1
        if data["current_turn"] % max(len(data["turn_order"]),1) == 0:
            data["round"]+=1
            for s in data["spells"]:
                if s["cd_left"]>0: s["cd_left"]-=1
            # тик статусов Калисты
            new_se = []
            for se in data.get("status_effects", []):
                se["duration"] -= 1
                if se["duration"] > 0:
                    new_se.append(se)
                else:
                    log(f"Статус «{se['name']}» истёк")
            data["status_effects"] = new_se
            if data.get("ten_resist_boost", 0) > 0:
                data["ten_resist_boost"] -= 1
                if data["ten_resist_boost"] <= 0:
                    log("Бонус +20% сопротивления от Тени истёк")
            if data.get("ten_invis"):
                data["ten_invis"] = False
                log("Невидимость спала")
            log(f"=== Раунд {data['round']} ===")
            # пересобираем порядок (на случай смертей)
            data["turn_order"]=build_turn_order(data)
            data["current_turn"]=0
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
    if ally.get("dots"):
        st.caption("DoT: "+", ".join(f"{d['name']}({d['duration']})" for d in ally["dots"]))


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
            if b3.button("+20% сопр.", key="ten_res", disabled=data["ten"]<5):
                data["ten"] = 0
                data["ten_resist_boost"] = 2
                log("Тень: +20% сопр. на 2 хода")
                persist_and_rerun()
            if data.get("ten_invis"):
                st.success("Невидима")
            elif data.get("ten_resist_boost", 0) > 0:
                st.success(f"+20% сопр. ({data['ten_resist_boost']} р.)")

    with st.expander("Статусы и отдых", expanded=False):
        if data.get("status_effects"):
            for i, se in enumerate(data["status_effects"]):
                st.write(f"• {se['name']} ({se['duration']} р.) — {se.get('desc','')}")
                if st.button("Снять", key=f"rm_se_{i}"):
                    data["status_effects"].pop(i); persist_and_rerun()
        with st.form("add_status"):
            s1, s2 = st.columns(2)
            sn = s1.text_input("Статус")
            sd = s2.number_input("Раунды", 1, 20, 3)
            if st.form_submit_button("Добавить") and sn.strip():
                data.setdefault("status_effects", []).append({"name": sn.strip(), "duration": int(sd), "desc": ""})
                persist_and_rerun()
        o1, o2 = st.columns(2)
        if o1.button("🌙 Короткий отдых"):
            data["mana_current"] = min(data["mana_max"], data["mana_current"] + data["mana_regen"]*3)
            log("Короткий отдых"); persist_and_rerun()
        if o2.button("🌅 Длинный отдых"):
            data["hp_current"] = data["hp_max"]
            data["mana_current"] = data["mana_max"]
            data["pepel"] = 0; data["ten"] = 0
            data["soul_flame_boost"] = False; data["crit_boost_active"] = False
            data["pepel_empower"] = False; data["ten_invis"] = False; data["ten_resist_boost"] = 0
            data["status_effects"] = []
            data["dots"] = []
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
        if e.get("dots"):
            st.caption("DoT: "+", ".join(f"{d['name']}({d['duration']})" for d in e["dots"]))

        b1,b2,b3=st.columns(3)
        if b1.button("⚔→Калист", key=f"ek{e['id']}"):
            if data.get("ten_invis"):
                log(f"{e['name']} промахнулся — Калист невидима")
                data["ten_invis"] = False
                persist_and_rerun()
            raw=e.get("attack_damage",10); at=e.get("attack_type","Физический")
            if at=="Физический":
                dmg=real_dmg(raw, data["armor"])
            else:
                resist = data["resists"].get(at,0)
                if data.get("ten_resist_boost", 0) > 0:
                    resist = min(95, resist + 20)
                dmg=real_dmg(raw, resist)
            data["hp_current"]=max(0,data["hp_current"]-dmg)
            log(f"{e['name']}→Калист ({at} {raw})={dmg}"); persist_and_rerun()
        if b2.button("⚔→Союзник", key=f"ea{e['id']}"):
            raw=e.get("attack_damage",10)
            at=e.get("attack_type","Физический")
            if at=="Физический":
                dmg=real_dmg(raw, ally.get("armor",0))
            else:
                dmg=real_dmg(raw, ally.get("resists",{}).get(at,0))
            ally["hp"]=max(0,ally["hp"]-dmg)
            log(f"{e['name']}→{ally['name']} ({at} {raw})={dmg}"); persist_and_rerun()
        if b3.button("🗑", key=f"ed{e['id']}"):
            data["enemies"].pop(i); persist_and_rerun()

        # ручной урон
        rc1,rc2,rc3=st.columns([1.4,1.2,1])
        dt=rc1.selectbox("Тип",["Физический"]+ELEMENTS, key=f"edt{e['id']}")
        rw=rc2.number_input("Урон",0,value=40,step=5, key=f"erw{e['id']}")
        if rc3.button("Урон", key=f"eh{e['id']}"):
            if dt=="Физический": dmg=real_dmg(rw, e.get("armor",0))
            else: dmg=real_dmg(rw, e.get("resists",{}).get(dt,0))
            e["hp"]=max(0,e["hp"]-dmg)
            log(f"По {e['name']}: {dt} {rw}→{dmg} (HP {e['hp']})")
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
                    if dt=="Физический": dmg=real_dmg(rw,e.get("armor",0))
                    else: dmg=real_dmg(rw,e.get("resists",{}).get(dt,0))
                    e["hp"]=max(0,e["hp"]-dmg)
                    log(f"{ally['name']}→{e['name']} ({dt} {rw})={dmg}")
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

        targets = [None] + [e["id"] for e in data["enemies"] if e.get("hp", 0) > 0]
        stgt = st.selectbox("Цель", targets, key="stgt",
                           format_func=lambda eid: "—" if eid is None else next(f"{e['name']} · #{eid}" for e in data["enemies"] if e["id"] == eid))
        crit_mode = st.selectbox("Критический удар", ["Без крита", "Крит по решению ведущего", "Бросок при применении"])
        override_damage = st.checkbox("Назначить итоговый урон вручную")
        gm_damage = st.number_input("Итоговый урон (без сопротивления и множителя крита)", min_value=0, value=0, disabled=not override_damage)
        st.caption("Каст применяет расход маны, перезарядку и эффекты. Щиты и прочие описательные эффекты пока назначай вручную.")

        for sp in data["spells"]:
            dual = {data.get("last_school"), sp["school"]} == {"Огонь", "Тьма"}
            soul = data.get("soul_flame_boost") and sp["name"] == "Пламя души"
            raw = spell_raw(sp.get("base", 0), data.get("spell_power", 0), dual, soul) if sp.get("base") else 0
            cd = sp.get("cd_left", 0)
            can = data["mana_current"] >= sp.get("mana", 0) and cd <= 0 and (raw == 0 or stgt is not None)
            if stgt is not None and raw > 0:
                target = next(e for e in data["enemies"] if e["id"] == stgt)
                dtype_preview = "Огонь" if "Огонь" in sp["school"] else "Тьма"
                resist_preview = target.get("resists", {}).get(dtype_preview, 0)
                if data.get("pepel_empower") and dtype_preview == "Огонь": resist_preview *= 0.7
                preview_raw = round(raw * 1.5) if crit_mode == "Крит по решению ведущего" else raw
                preview = gm_damage if override_damage else real_dmg(preview_raw, resist_preview)
                st.caption(f"{sp['name']}: расчёт по цели {preview}" + (" · до броска крита" if crit_mode == "Бросок при применении" and not override_damage else ""))

            cols = st.columns([2.8, 0.8, 0.7, 0.7, 1.1])
            icon = "🔥" if "Огонь" in sp.get("school", "") else "🌑"
            cols[0].markdown(f"**{icon} {sp['name']}**")
            cols[0].caption((sp.get("desc") or "") + (" · DoT" if sp.get("dot") else ""))
            cols[1].write(f"**{raw or '—'}**")
            cols[2].write(f"{sp.get('mana', 0)}MP")
            cols[3].write(f"КД {cd}/{sp.get('cd_max', 0)}" if sp.get("cd_max") else "—")
            if cols[4].button("Каст", key=f"cast_{sp['id']}", disabled=not can):
                data["mana_current"] -= sp["mana"]
                data["last_school"] = sp["school"]
                if sp.get("cd_max", 0) > 0:
                    sp["cd_left"] = sp["cd_max"]
                if sp.get("gives") in ("pepel", "both"):
                    data["pepel"] = min(5, data["pepel"] + 1)
                if sp.get("gives") in ("ten", "both"):
                    data["ten"] = min(5, data["ten"] + 1)
                if soul:
                    data["soul_flame_boost"] = False

                if "Огонь" in sp["school"]:
                    dtype = "Огонь"
                else:
                    dtype = "Тьма"

                crit_chance = data.get("crit_chance", 0.065)
                if data.get("crit_boost_active"):
                    crit_chance += 0.10
                is_crit = (crit_mode == "Крит по решению ведущего" or
                           (crit_mode == "Бросок при применении" and random.random() < crit_chance))
                if is_crit:
                    raw = round(raw * 1.5)

                msg = f"«{sp['name']}» сырой {raw}"
                if is_crit:
                    msg += " ⚡КРИТ"

                if stgt is not None and raw > 0:
                    for e in data["enemies"]:
                        if e["id"] == stgt and e.get("hp", 0) > 0:
                            resist = e.get("resists", {}).get(dtype, 0)
                            if data.get("pepel_empower") and dtype == "Огонь":
                                resist = resist * 0.7
                                data["pepel_empower"] = False
                                msg += " [Пепел]"
                            dmg = gm_damage if override_damage else real_dmg(raw, resist)
                            if override_damage: msg += " [решение ведущего]"
                            e["hp"] = max(0, e["hp"] - dmg)
                            msg += f" → {e['name']}={dmg} (HP {e['hp']})"
                            if sp.get("dot"):
                                from copy import deepcopy as _dc
                                e.setdefault("dots", []).append(_dc(sp["dot"]))
                                msg += f" +DoT"
                            if e["hp"] <= 0:
                                msg += " [мертв]"
                            break
                log(msg + f" (−{sp['mana']}MP)")
                persist_and_rerun()

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
        if it["type"]=="Расходник" and it["qty"]>0:
            if "мана" in it["name"].lower() and cols[2].button("Выпить",key=f"u{i}"):
                it["qty"]-=1; data["mana_current"]=min(data["mana_max"],data["mana_current"]+400); persist_and_rerun()
            if "лечен" in it["name"].lower() and cols[2].button("Выпить",key=f"h{i}"):
                it["qty"]-=1; data["hp_current"]=min(data["hp_max"],data["hp_current"]+250); persist_and_rerun()
        if cols[3].button("🗑",key=f"x{i}"): data["inventory"].pop(i); persist_and_rerun()
    with st.form("ai"):
        st.markdown("**Добавить предмет**")
        nn = st.text_input("Название")
        nt = st.selectbox("Тип", ["Расходник", "Реагент", "Свиток", "Оружие", "Броня", "Реликвия", "Инструмент", "Книга", "Валюта", "Прочее"])
        nq = st.number_input("Количество", min_value=1, value=1)
        nd = st.text_input("Описание")
        if st.form_submit_button("Добавить") and nn.strip():
            data["inventory"].append({"name": nn.strip(), "type": nt, "qty": int(nq), "desc": nd})
            persist_and_rerun()


elif page=="Заклинания":
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Заклинания</div>", unsafe_allow_html=True)
    st.caption("Кулдауны в раундах. 0 = без кулдауна. Каст — на странице «Бой».")

    for i, sp in enumerate(list(data["spells"])):
        with st.expander(f"{sp.get('name','?')} (КД {sp.get('cd_max',0)})"):
            sp["name"] = st.text_input("Название", sp.get("name",""), key=f"sn{i}")
            c1, c2, c3, c4 = st.columns(4)
            sp["base"] = c1.number_input("Базовый урон", min_value=0, value=int(sp.get("base",0) or 0), key=f"sb{i}")
            sp["mana"] = c2.number_input("Мана", min_value=0, value=int(sp.get("mana",0) or 0), key=f"sm{i}")
            sp["cd_max"] = c3.number_input("Кулдаун", min_value=0, value=int(sp.get("cd_max",0) or 0), key=f"sc{i}")
            schools = ["Огонь", "Тьма", "Огонь+Тьма"]
            cur = sp.get("school", "Огонь")
            sp["school"] = c4.selectbox("Школа", schools, index=schools.index(cur) if cur in schools else 0, key=f"ss{i}")
            sp["desc"] = st.text_input("Описание", sp.get("desc",""), key=f"sd{i}")
            gives_opts = [None, "pepel", "ten", "both"]
            cur_g = sp.get("gives")
            gi = gives_opts.index(cur_g) if cur_g in gives_opts else 0
            sp["gives"] = st.selectbox("Даёт ресурс", gives_opts, index=gi,
                format_func=lambda x: {None:"Ничего","pepel":"Пепел","ten":"Тень","both":"Оба"}[x], key=f"sg{i}")
            if st.button("Удалить заклинание", key=f"sdel{i}"):
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
