#!/usr/bin/env python3
"""
Калиста Клиф — v15 · компактный боевой стол
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
from html import escape
from datetime import datetime
from pathlib import Path
from copy import deepcopy

SAVE_FILE = Path(__file__).parent / "kalista_save.json"
PORTRAIT_FILE = Path(__file__).parent / "assets" / "kalista-portrait.png"
ELEMENTS = ["Огонь", "Земля", "Вода", "Воздух", "Тьма", "Свет"]

st.set_page_config(page_title="✧ Калиста Клиф ✧", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Quattrocento+Sans:wght@400;700&display=swap');
.main-title{font-family:'Cinzel',serif;font-size:2rem;color:#E8DAEF;text-align:center;text-shadow:0 0 12px #4A235A;margin-bottom:.1rem}
.subtitle{text-align:center;color:#BB8FCE;margin-bottom:.8rem}
.section-h{font-family:'Cinzel',serif;color:#D7BDE2;font-size:1.1rem;border-bottom:2px solid #7D3C98;padding-bottom:2px;margin:.8rem 0 .4rem}
div[data-testid="stMetricValue"]{font-size:1.25rem}
.stButton>button{border-radius:8px;font-weight:600}
.turn-now{background:#3D1A5C;border:2px solid #BB8FCE;border-radius:10px;padding:8px 12px;margin-bottom:6px}

[data-testid="stLayoutWrapper"]:has(>.st-key-battle_header){position:sticky;top:3.5rem;z-index:50;background:#18121f}
.st-key-battle_header{background:#18121f;padding:0 0 .35rem;border-bottom:1px solid #704080;gap:.35rem}
[data-testid="stMainBlockContainer"]:has(.st-key-battle_header){padding-top:4rem;padding-bottom:2rem}
[data-testid="stMainBlockContainer"]:has(.st-key-battle_header)>[data-testid="stVerticalBlock"]{gap:.65rem}
.st-key-battle_header [data-testid="stRadio"] p{color:#e0d3ec}
.st-key-battle_header [data-testid="stButton"] button{background:#30213c;color:#f0e5f6;border:1px solid #60456f}
.st-key-battle_header [data-testid="stButton"] button:disabled{background:#211a29;color:#746980}
.battle-card{background:#261531;border:1px solid #7d5291;border-radius:10px;padding:8px 12px;margin-bottom:6px}
.battle-name{font-weight:700;color:#ecdff3;display:flex;justify-content:space-between;gap:8px;font-size:1rem}
.battle-name span{font-weight:400;color:#cbb5d4;font-size:.85rem}
.battle-values{display:flex;gap:12px;flex-wrap:wrap;margin-top:5px;font-size:.9rem;color:#ecdff3}
.st-key-battle_header [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.35rem}
.st-key-battle_header [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}
.st-key-battle_header button{padding:.35rem .25rem;min-height:2.4rem;font-size:.9rem}
.st-key-battle_header [role="radiogroup"]{gap:.3rem .7rem;flex-wrap:wrap}
@media(max-width:640px){.block-container{padding-left:1rem;padding-right:1rem}.battle-name{flex-direction:column;gap:2px}.battle-values{gap:4px 12px}.battle-values b{font-size:.82rem}.st-key-battle_header button{font-size:.78rem}.st-key-battle_header [role="radiogroup"] label{font-size:.85rem}[data-testid="stLayoutWrapper"]:has(>.st-key-battle_header){top:3.5rem}}

.battle-strip{padding:.5rem .65rem;color:#ede2f4;display:flex;flex-direction:column;gap:.15rem}
.battle-strip strong{font-size:1rem}.battle-strip span{font-size:.78rem;color:#b9a7c5}
.combatant-card{border:1px solid #564062;border-radius:14px;padding:12px 16px;background:#211928;color:#eee3f5;margin-bottom:8px}
.combatant-card.acting{border-left:4px solid #b680d5;background:linear-gradient(110deg,#35213f,#211928)}
.combat-eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:.67rem;color:#c39eda;font-weight:700}
.combatant-name{font-size:1.25rem;font-weight:700;margin-top:2px}.combat-identity{color:#b8a5c5;font-size:.78rem;margin:2px 0 8px}
.combat-health-label{display:flex;justify-content:space-between;font-size:.8rem}.combat-health{height:6px;background:#49354f;border-radius:9px;overflow:hidden;margin:5px 0 8px}
.combat-health>div{height:100%;background:#87b59b;border-radius:9px;transition:width .2s}
.combat-details{font-size:.8rem;color:#b9a7c5}.combat-badges{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}
.combat-badge{font-size:.7rem;background:#473053;color:#dbc0eb;padding:2px 7px;border-radius:20px}
[data-testid="stMainBlockContainer"]:has(.st-key-battle_header) [data-testid="stVerticalBlock"]{gap:.65rem}
@media(max-width:640px){.combatant-card{padding:9px 12px}.combatant-name{font-size:1.05rem}.combat-identity{margin-bottom:5px}.combat-details{font-size:.75rem}}


.st-key-turn_action [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.65rem}
.st-key-turn_action [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}
@media(max-width:640px){.st-key-battle_header [role="radiogroup"]{gap:.2rem .4rem}.st-key-battle_header [data-testid="stRadio"] p{font-size:.75rem}.battle-strip{padding:.3rem .5rem}}

[data-testid="stMainBlockContainer"]:has(.st-key-gm_table){padding-top:3.5rem;padding-bottom:2rem}
.st-key-gm_table [data-testid="stVerticalBlock"]{gap:.6rem}
.st-key-gm_table h3{padding-top:.3rem;padding-bottom:.3rem}
@media(max-width:640px){.st-key-gm_table .main-title{text-align:left}.st-key-gm_table button{font-size:.85rem}}

.st-key-gm_filter [data-testid="stHorizontalBlock"],.st-key-gm_scene_actions [data-testid="stHorizontalBlock"],.st-key-gm_roster [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.6rem}
.st-key-gm_filter [data-testid="stColumn"],.st-key-gm_scene_actions [data-testid="stColumn"],.st-key-gm_roster [data-testid="stColumn"]{min-width:0!important}
@media(max-width:640px){.st-key-gm_scene_actions [data-testid="stColumn"]{flex:1 1 0!important}.st-key-gm_roster button{font-size:.78rem}}

.st-key-overview_hero [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.75rem}
.st-key-overview_hero [data-testid="stColumn"]{min-width:0!important}
.st-key-overview_hero [data-testid="stImage"] img{border-radius:14px;border:1px solid #624173;max-width:100%;height:auto}
@media(max-width:640px){.st-key-overview_hero [data-testid="stMetricValue"]{font-size:1.1rem}.st-key-overview_hero [data-testid="stVerticalBlock"]{gap:.5rem}}
</style>
""", unsafe_allow_html=True)

# ===================== DEFAULT =====================
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
    if saved.get("schema_version", 5) not in (5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
        raise ValueError("Версия сохранения не поддерживается")
    data = merge_defaults(DEFAULT, saved)
    if data["name"] in ("Калист", "Калист Клиф"):
        data["name"] = "Калиста Клиф" if data["name"].endswith("Клиф") else "Калиста"
    for actor in data.get("turn_order", []):
        if actor.get("kind") == "player": actor["name"] = data["name"]
    for _, target in participants(data):
        target.setdefault("heal_amount", 0)
        nonnegative_int(target["heal_amount"], "Сила лечения")
        validate_tree(target, {"description": ""})
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
    for enemy in data["enemies"]:
        if "side" in enemy and enemy["side"] not in ("Враг", "Союзник", "Нейтральный"):
            raise ValueError("Неизвестная сторона участника боя")
    data["schema_version"] = 14
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
    racial_reduction = 0
    if not final and damage_type == "Тьма" and "dark_resist" in target.get("passives", {}):
        protected = round(incoming * .9)
        racial_reduction = incoming - protected
        incoming = protected
    capacity = sum(effect["value"] for effect in target.get("effects", []) if effect["kind"] == "shield")
    absorbed = 0 if bypass_shields else min(incoming, capacity)
    hp_key, _ = hp_fields(target)
    hp_loss = min(max(0, target[hp_key]), incoming - absorbed)
    return {"incoming": incoming, "absorbed": absorbed, "hp_loss": hp_loss, "racial_reduction": racial_reduction,
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
        messages.append("Магический резерв активирован: 3 усиленных тика")
    amount = round(data["mana_regen"] * 1.5) if ticks else data["mana_regen"]
    restored = restore_mana(data, amount)
    data["mana_reserve_ticks"] = max(0, ticks - 1)
    messages.append(f"Регенерация маны: +{restored} MP" +
                    (f" · резерв: осталось {data['mana_reserve_ticks']} тика" if ticks else ""))
    if ticks == 1:
        messages.append("Магический резерв завершён")
    return messages


def damage_message(name, result):
    return (f"{name}: после защиты {result['incoming']} · щит −{result['absorbed']} · "
            f"HP −{result['hp_loss']} → {result['hp_after']}" +
            (f" · защита от Тьмы −{result['racial_reduction']}" if result.get("racial_reduction") else ""))


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


def activate_shadow_invisibility(data):
    """Ход активации — первый; заканчиваем на втором следующем начале хода."""
    if data["ten"] < 5:
        raise ValueError("Для невидимости нужно 5 Тени")
    data["ten"] = 0
    data["ten_invis"] = True
    data["ten_invis_turn_starts_left"] = 2
    return "Тень: невидимость до начала 3-го хода Калисты (ход активации — 1-й)"


def activate_shadow_resistance(data):
    if data["ten"] < 5:
        raise ValueError("Для сопротивлений нужно 5 Тени")
    data["ten"] = 0
    data["ten_resist_boost"] = 2
    return "Тень: +20 к сопротивлениям до начала 3-го хода Калисты (ход активации — 1-й)"


def begin_actor_turn(data):
    """Считаем только настоящее начало хода Калисты при продвижении очереди."""
    actor = get_current_actor(data)
    if not actor or actor["kind"] != "player":
        return []
    data["player_turns_started"] = data.get("player_turns_started", 0) + 1
    messages = []
    if data.get("ten_invis"):
        data["ten_invis_turn_starts_left"] -= 1
        if data["ten_invis_turn_starts_left"] == 0:
            data["ten_invis"] = False
            messages.append("Невидимость спала: начало 3-го хода Калисты после активации")
    if data.get("ten_resist_boost", 0) > 0:
        data["ten_resist_boost"] -= 1
        if data["ten_resist_boost"] == 0:
            messages.append("Сопротивления Тени истекли: начало 3-го хода Калисты после активации")
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
    dual, soul = spell_bonuses(data, spell)
    raw = spell_raw(amount, data.get("spell_power", 0), dual, soul) if action == "damage" else amount
    if crit and action == "damage":
        raw = round(raw * 1.5)
    dtype = "Огонь" if "Огонь" in spell["school"] else "Тьма"
    empowered = bool(data.get("pepel_empower") and dtype == "Огонь" and action == "damage" and raw > 0)
    # До изменения данных проверяем расчёт и цель.
    if target is not None and action == "damage" and raw > 0:
        damage_preview(target, raw if final_damage is None else final_damage, dtype,
                       final=final_damage is not None, defense_factor=0.7 if empowered else 1.0)
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

def enemy_ai_act(data, enemy):
    """Вспомогательное действие; интерфейс не запускает ИИ самостоятельно."""
    targets = [target for token, target in participants(data) if token in ("player", "ally")
               and target[hp_fields(target)[0]] > 0]
    if not targets:
        return
    target = min(targets, key=lambda item: item[hp_fields(item)[0]])
    if target is data and data.get("ten_invis"):
        log(f"{enemy['name']}: атака отменена невидимостью")
        return
    result = apply_damage(target, enemy.get("attack_damage", 10), enemy.get("attack_type", "Физический"))
    log(f"{enemy['name']} → " + damage_message(target["name"], result))


def persist_and_rerun(label=None):
    st.session_state["_reset_resource_widgets"] = True
    if commit_current(label):
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


def render_quick_action(data, token):
    target = participant(data, token)
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


def render_effect_editor(data, token):
    target = participant(data, token)
    st.markdown("**Эффекты выбранного участника**")
    st.caption("Урон и лечение: срабатывания в конце хода цели. Остальные: полные раунды; "
               "раунд наложения не сокращает длительность. Вне боя эффекты меняются вручную.")
    if not target.get("effects"):
        st.caption("Нет активных эффектов")
    visible = list(target.get("effects", []))
    if len(visible) > 6:
        query = st.text_input("Найти эффект", key="effect_search")
        visible = [effect for effect in visible if query.casefold() in (effect["name"] + " " + effect.get("desc", "")).casefold()]
        if len(visible) > 6:
            pages = list(range((len(visible) + 5) // 6))
            page_index = remembered_select("Страница эффектов", pages, f"effect_page_{token}", default=0,
                                            format_func=lambda value: f"{value + 1} / {len(pages)}")
            visible = visible[page_index * 6:(page_index + 1) * 6]
        if not visible: st.caption("По запросу ничего не найдено")
    for effect in visible:
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


def commit_current(label=None):
    data = st.session_state.data
    recalc(data)
    observe_mana_reserve(data)
    previous = st.session_state.get("_committed_data", deepcopy(data))
    if not save(data):
        return False
    if label is None:
        old_log = previous.get("combat_log", [])
        new_log = data.get("combat_log", [])
        label = new_log[0].split("] ", 1)[-1] if new_log and new_log != old_log else "Редактирование"
    add_history(st.session_state.setdefault("_undo_history", []), previous, data, label)
    st.session_state["_committed_data"] = deepcopy(data)
    return True


def undo_last_action():
    history = st.session_state.get("_undo_history", [])
    if not history:
        return False
    entry = history[-1]
    restored = migrate(deepcopy(entry["data"]))
    recalc(restored)
    restored["combat_log"].insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] Отменено: {entry['label']}")
    restored["combat_log"] = restored["combat_log"][:80]
    if not save(restored):
        return False
    history.pop()
    st.session_state.data = restored
    st.session_state["_committed_data"] = deepcopy(restored)
    # Иначе значения созданных ранее полей могут немедленно вернуть отменённое действие.
    keep = {"data", "_committed_data", "_undo_history", "page", "battle_section", "gm_section", "_battle_preferences"}
    for key in list(st.session_state):
        if key not in keep: del st.session_state[key]
    st.rerun()


def remembered_select(label, options, key, default=None, **kwargs):
    """Сохраняем выбор между экранами, даже когда Streamlit удаляет скрытый виджет."""
    prefs = st.session_state.setdefault("_battle_preferences", {})
    candidate = st.session_state.get(key, prefs.get(key, default))
    if candidate not in options:
        candidate = default if default in options else options[0]
    if st.session_state.get(key) not in options:
        st.session_state[key] = candidate
    value = st.selectbox(label, options, key=key, **kwargs)
    prefs[key] = value
    return value


def reset_participant_widgets():
    st.session_state["_reset_resource_widgets"] = True


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
    return f"Особое умение: {data['passives'][key]['name']}"


def effective_crit_chance(data):
    return min(1.0, max(0.0, data.get("crit_chance", .065) + (.10 if data.get("crit_boost_active") else 0)))


def start_combat(data):
    data["combat_active"] = True
    for _, target in participants(data):
        for effect in target.get("effects", []): effect["applied_round"] = 0
    data["round"] = 1
    data["player_turns_started"] = 0
    data["turn_order"] = build_turn_order(data)
    data["current_turn"] = 0
    return ["=== Бой начат. Раунд 1 ==="] + begin_actor_turn(data)


def end_combat(data):
    data["combat_active"] = False
    data["turn_order"] = []
    data["current_turn"] = 0
    data["player_turns_started"] = 0
    data["crit_boost_active"] = False
    data["passives"]["cold_calculation"]["used"] = False
    return "=== Бой окончен ==="


def spell_bonuses(data, spell):
    # Одна функция для предпросмотра и применения; периодический урон не усиливаем.
    damage = spell_action(spell) == "damage"
    dual = damage and {data.get("last_school"), spell["school"]} == {"Огонь", "Тьма"}
    soul = bool(damage and data.get("soul_flame_boost") and spell["name"] == "Пламя души")
    return dual, soul


def render_battle_header(data):
    actor = get_current_actor(data) if data["combat_active"] else None
    turn = f"Раунд {data['round']} · {actor['name']}" if actor else "Бой не начат" if not data["combat_active"] else "Нет активных участников"
    shield = sum(effect["value"] for effect in data.get("effects", []) if effect["kind"] == "shield")
    active_scene = scene_record(data, data['active_scene_id'])
    if active_scene: turn += ' · ' + active_scene['name']
    with st.container(key="battle_header"):
        st.markdown(f"""<div class="battle-strip"><strong>{escape(turn)}</strong>
        <span>{escape(data['name'])} · HP {data['hp_current']}/{data['hp_max']} · MP {data['mana_current']}/{data['mana_max']} · Щит {shield} · Пепел {data['pepel']}/5 · Тень {data['ten']}/5</span></div>""", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("Начать", disabled=data["combat_active"], key="battle_start", use_container_width=True):
            for message in start_combat(data): log(message)
            persist_and_rerun("Начало боя")
        if b2.button("Далее", disabled=not data["combat_active"] or not data["turn_order"], key="battle_next", use_container_width=True):
            for message in advance_turn(data): log(message)
            persist_and_rerun("Следующий ход")
        history = st.session_state.get("_undo_history", [])
        hint = f"Отменить: {history[-1]['label']}" if history else "Нет действий для отмены"
        if b3.button("Отмена", disabled=not history, key="battle_undo", help=hint, use_container_width=True):
            undo_last_action()
        if b4.button("Стоп", disabled=not data["combat_active"], key="battle_stop", use_container_width=True):
            log(end_combat(data))
            persist_and_rerun("Завершение боя")
        prefs = st.session_state.setdefault("_battle_preferences", {})
        if "battle_section" not in st.session_state:
            st.session_state["battle_section"] = prefs.get("battle_section", "Ход")
        if st.session_state["battle_section"] == "Калиста":
            st.session_state["battle_section"] = "Ход"
        selected = st.radio("Раздел боя", ["Ход", "Участники", "Эффекты", "Очередь", "Журнал"],
                            key="battle_section", horizontal=True, label_visibility="collapsed")
        prefs["battle_section"] = selected


def render_selected_spell(data, target):
    if not data["spells"]:
        st.info("Заклинаний пока нет. Добавь их на странице «Заклинания».")
        return
    spells = {spell["id"]: spell for spell in data["spells"]}
    sid = remembered_select("Способность", list(spells), "battle_spell", default=data["spells"][0]["id"],
                            format_func=lambda value: f"{spells[value]['name']} · {spells[value]['mana']} MP" +
                            (f" · КД {spells[value]['cd_left']}" if spells[value]['cd_left'] else ""))
    spell = spells[sid]
    action = spell_action(spell)
    dual, soul = spell_bonuses(data, spell)
    raw = spell_raw(spell["base"], data.get("spell_power", 0), dual, soul) if action == "damage" else spell.get("effect_value", 0)
    st.caption(f"{spell.get('desc', '')} · Мана {spell['mana']} · КД {spell.get('cd_left', 0)}/{spell.get('cd_max', 0)}")
    bonuses = (["Двойное пламя +5%"] if dual else []) + (["Ритуал +40%"] if soul else [])
    if bonuses: st.caption("Прямой урон: " + " · ".join(bonuses))
    if action == "damage": st.caption(f"Шанс крита: {effective_crit_chance(data)*100:.1f}%")
    shield_amount = None
    if action == "shield":
        shield_amount = st.number_input("Сила щита", min_value=0, value=spell.get("effect_value", 0), key=f"cast_shield_{sid}")
        if not shield_amount: st.caption("Сила щита в правилах не задана — укажи её перед применением.")
    crit_mode = "Без крита"
    override = False
    final_damage = 0
    if action == "damage":
        with st.expander("Крит и ручной урон", expanded=False):
            crit_mode = remembered_select("Крит", ["Без крита", "Крит ведущего", "Бросок"], "battle_crit", default="Без крита")
            override = st.checkbox("Назначить итоговый урон вручную", key="battle_override")
            final_damage = st.number_input("Готовый урон (щит будет учтён)", min_value=0, value=0,
                                           disabled=not override, key="battle_final_damage")
        dtype = "Огонь" if "Огонь" in spell["school"] else "Тьма"
        preview_raw = round(raw * 1.5) if crit_mode == "Крит ведущего" else raw
        if raw > 0:
            preview = damage_preview(target, final_damage if override else preview_raw, dtype, final=override,
                                     defense_factor=0.7 if data.get("pepel_empower") and dtype == "Огонь" else 1.0)
            st.info(damage_message(target["name"], preview) + (" · до броска крита" if crit_mode == "Бросок" and not override else ""))
        if spell.get("dot"):
            dot = spell["dot"]
            st.caption(f"+ {dot['name']}: {dot['damage']} {dot.get('element', 'Огонь')} × {dot['duration']} срабатывания")
    elif action == "heal":
        hp_key, maximum_key = hp_fields(target)
        st.info(f"{target['name']}: восстановится {min(raw, max(0, target[maximum_key] - target[hp_key]))} HP")
    elif action == "shield":
        st.info(f"{target['name']}: щит {shield_amount} · " + (f"{spell['effect_duration']} полных раундов" if spell.get("effect_duration") else "бессрочно"))
    else:
        st.info(f"{target['name']}: статус «{spell['name']}»")
    can = data["mana_current"] >= spell["mana"] and spell.get("cd_left", 0) == 0
    if action == "shield": can = can and shield_amount > 0
    if action == "heal": can = can and raw > 0
    if action == "damage": can = can and target[hp_fields(target)[0]] > 0
    if st.button("Применить способность", key=f"cast_{sid}", disabled=not can, type="primary", use_container_width=True):
        chance = effective_crit_chance(data)
        crit = action == "damage" and not override and (crit_mode == "Крит ведущего" or (crit_mode == "Бросок" and random.random() < chance))
        try:
            for message in cast_spell(data, spell, target, crit=crit,
                                      final_damage=final_damage if override and action == "damage" else None,
                                      shield_amount=shield_amount): log(message)
            if data["combat_active"]: refresh_turn_order(data)
            persist_and_rerun(f"Способность: {spell['name']}")
        except ValueError as exc:
            st.error(str(exc))
    if not can:
        reasons = []
        if data["mana_current"] < spell["mana"]: reasons.append("не хватает маны")
        if spell.get("cd_left", 0): reasons.append("способность на перезарядке")
        if action == "damage" and target[hp_fields(target)[0]] == 0: reasons.append("у цели 0 HP")
        if action in ("shield", "heal") and (shield_amount if action == "shield" else raw) == 0: reasons.append("не задана сила эффекта")
        st.caption("Применение недоступно: " + ", ".join(reasons))
    with st.expander("Предметы Калисты", expanded=False):
        usable = [(i, item) for i, item in enumerate(data["inventory"]) if item.get("use") and item["qty"] > 0 and item["use"]["value"] > 0]
        if not usable:
            st.caption("Нет доступных расходников. Действия предметов настраиваются в инвентаре.")
        else:
            indices = [i for i, _ in usable]
            index = remembered_select("Предмет", indices, "battle_item", default=indices[0],
                                      format_func=lambda i: f"{data['inventory'][i]['name']} ×{data['inventory'][i]['qty']}")
            if st.button("Применить к Калисте", key="battle_use_item", use_container_width=True):
                log(use_item(data, data["inventory"][index]))
                persist_and_rerun(f"Предмет: {data['inventory'][index]['name']}")
    with st.expander("Пепел, Тень и особые умения", expanded=False):
        p1, p2 = st.columns(2)
        if p1.button("🔥 Усилить огонь", key="pep_act", disabled=data["pepel"] < 5, use_container_width=True):
            data["pepel"] = 0; data["pepel_empower"] = True
            log("Пепел: следующее огненное заклинание игнорирует 30% сопротивления")
            persist_and_rerun()
        if p2.button("🌑 Невидимость", key="ten_inv", disabled=data["ten"] < 5, use_container_width=True):
            log(activate_shadow_invisibility(data))
            persist_and_rerun()
        if st.button("🌑 +20 к сопротивлениям", key="ten_res", disabled=data["ten"] < 5, use_container_width=True):
            log(activate_shadow_resistance(data))
            persist_and_rerun()
        st.caption(f"Регенерация: {data['mana_regen']} MP в конце раунда · резерв: {data.get('mana_reserve_ticks', 0)} усиленных тика осталось")
        if data.get("pepel_empower"): st.caption("🔥 Усиление огня готово")
        if data.get("ten_invis"): st.caption(f"🌑 Невидимость: до начала 3-го хода; осталось {data['ten_invis_turn_starts_left']} начала хода Калисты")
        if data.get("ten_resist_boost"): st.caption(f"🌑 +20 к сопротивлениям: осталось {data['ten_resist_boost']} начала хода Калисты")
        if data.get("soul_flame_boost"): st.caption("Ритуал: Пламя души +40%")
        for key, passive in data["passives"].items():
            if passive.get("type") == "special":
                allowed, reason = special_availability(data, key)
                if st.button(passive["name"], key=f"battle_passive_{key}", disabled=not allowed, help=passive["desc"], use_container_width=True):
                    log(activate_special(data, key))
                    persist_and_rerun()
                if reason and not passive["used"]: st.caption(reason)
        p1, p2 = st.columns(2)
        if p1.button("+1 Пепел", key="pep_plus", use_container_width=True):
            data["pepel"] = min(5, data["pepel"] + 1); persist_and_rerun("Добавлен Пепел")
        if p2.button("+1 Тень", key="ten_plus", use_container_width=True):
            data["ten"] = min(5, data["ten"] + 1); persist_and_rerun("Добавлена Тень")
    with st.expander("Отдых", expanded=False):
        c1, c2 = st.columns(2)
        if c1.button("Короткий отдых", key="battle_short_rest", use_container_width=True):
            restored = restore_mana(data, data["mana_regen"] * 3)
            log(f"Короткий отдых: +{restored} MP"); persist_and_rerun()
        if c2.button("Долгий отдых", key="battle_long_rest", use_container_width=True):
            data["hp_current"] = data["hp_max"]; data["mana_current"] = data["mana_max"]
            data["mana_reserve_ticks"] = 0; data["mana_reserve_armed"] = True
            data["ten_invis_turn_starts_left"] = 0
            data["pepel"] = data["ten"] = data["ten_resist_boost"] = 0
            for flag in ("soul_flame_boost", "crit_boost_active", "pepel_empower", "ten_invis"): data[flag] = False
            data["effects"] = []; data["dots"] = []; data["status_effects"] = []
            for passive in data["passives"].values():
                if passive.get("type") == "special": passive["used"] = False
            for spell in data["spells"]: spell["cd_left"] = 0
            if data["combat_active"]: refresh_turn_order(data)
            log("Долгий отдых"); persist_and_rerun()


def render_participant_editor(data, token):
    target = participant(data, token)
    hp_key, maximum_key = hp_fields(target)
    with st.expander("Изменить характеристики участника", expanded=False):
        with st.form(f"edit_participant_{token}"):
            name = st.text_input("Имя", value=target["name"])
            description = st.text_input("Кто это / заметка", value=target.get("description", ""))
            c1, c2 = st.columns(2)
            hp = c1.number_input("HP", min_value=0, value=target[hp_key])
            maximum = c2.number_input("Максимум HP", min_value=1, value=target[maximum_key], disabled=token == "player")
            armor = st.number_input("Броня без временных эффектов", min_value=0, value=target.get("armor", 0))
            attack = st.number_input("Урон атаки", min_value=0, value=target.get("attack_damage", target.get("phys_attack", 0)))
            heal_amount = st.number_input("Сила лечения", min_value=0, value=target.get("heal_amount", 0), disabled=token == "player")
            attack_type = st.selectbox("Тип атаки", DAMAGE_TYPES, index=DAMAGE_TYPES.index(target.get("attack_type", "Физический")))
            resists = {}
            cols = st.columns(2)
            for i, element in enumerate(ELEMENTS):
                resists[element] = cols[i % 2].number_input(element, min_value=0, value=target.get("resists", {}).get(element, 0))
            if token == "player": st.caption("Максимум HP Калисты рассчитывается из уровня и характеристик.")
            if st.form_submit_button("Сохранить участника"):
                if not name.strip(): st.error("Укажи имя")
                else:
                    target["name"] = name.strip(); target[hp_key] = hp
                    target["description"] = description.strip()
                    if token != "player": target[maximum_key] = maximum
                    if token == "player":
                        data["armor_adjustment"] += armor - data["armor"]
                        data["attack_adjustment"] += attack - data["phys_attack"]
                        for element in ELEMENTS:
                            data["resist_adjustments"][element] += resists[element] - data["resists"].get(element, 0)
                    else:
                        target["armor"] = armor; target["attack_damage"] = attack
                        target["attack_type"] = attack_type; target["resists"] = resists
                        target["heal_amount"] = heal_amount
                    if data["combat_active"]: refresh_turn_order(data)
                    log(f"Изменён участник: {name.strip()}")
                    persist_and_rerun()
    if token.startswith("enemy:"):
        with st.expander("Удалить участника", expanded=False):
            confirm = st.checkbox("Подтверждаю удаление", key=f"confirm_delete_{token}")
            if st.button("Удалить врага", disabled=not confirm, key=f"delete_{token}"):
                data["enemies"] = [enemy for enemy in data["enemies"] if f"enemy:{enemy['id']}" != token]
                for message in exclude_from_queue_after_delete(data, token): log(message)
                log(f"Удалён враг: {target['name']}")
                persist_and_rerun()


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
    if data["combat_active"]: refresh_turn_order(data)
    return (f"{participant_label(data, healer_token)} → {participant_label(data, recipient_token)}: "
            f"лечение +{result['restored']} HP (избыток {result['excess']})")


def render_combatant_action(data, source_token, victim_token):
    source = participant(data, source_token)
    victim = participant(data, victim_token)
    operation = st.radio("Действие участника", ["Атака", "Лечение"], horizontal=True,
                         key=f"actor_action_{source_token}", label_visibility="collapsed")
    if operation == "Лечение":
        amount = st.number_input("Восстановить HP", min_value=0, value=source.get("heal_amount", 0),
                                 key=f"actor_heal_amount_{source_token}")
        hp_key, maximum_key = hp_fields(victim)
        restored = min(amount, max(0, victim[maximum_key] - victim[hp_key]))
        st.caption(f"{participant_label(data, source_token)} → {participant_label(data, victim_token)} · +{restored} HP · после лечения {victim[hp_key] + restored}/{victim[maximum_key]}")
        if st.button("Вылечить цель", key=f"actor_heal_{source_token}", type="primary", use_container_width=True,
                     disabled=amount <= 0 or restored == 0 or source[hp_fields(source)[0]] <= 0):
            log(combatant_heal(data, source_token, victim_token, amount))
            persist_and_rerun(f"Лечение: {source['name']}")
        st.caption("Силу лечения задаёт ведущий; обычное лечение ограничено максимумом HP.")
    else:
        c1, c2 = st.columns(2)
        amount = c1.number_input("Урон атаки", min_value=0, value=source.get("attack_damage", 0), key=f"actor_attack_amount_{source_token}")
        dtype = c2.selectbox("Тип урона", DAMAGE_TYPES, index=DAMAGE_TYPES.index(source.get("attack_type", "Физический")), key=f"actor_attack_type_{source_token}")
        result = damage_preview(victim, amount, dtype)
        invisible = victim is data and data.get("ten_invis")
        st.caption("Цель невидима — атака не нанесёт урона" if invisible else damage_message(victim["name"], result))
        if st.button("Атаковать цель", key=f"attack_{source_token}", disabled=source[hp_fields(source)[0]] <= 0 or victim[hp_fields(victim)[0]] <= 0 or amount <= 0,
                     type="primary", use_container_width=True):
            if invisible:
                log(f"{participant_label(data, source_token)}: промах — {victim['name']} невидима")
            else:
                result = apply_damage(victim, amount, dtype)
                log(f"{participant_label(data, source_token)} → " + damage_message(participant_label(data, victim_token), result))
            persist_and_rerun("Атака: " + source["name"])


def render_attack(data, token):
    if token == "player": return
    with st.expander(f"Действия вне очереди · {participant_label(data, token)}", expanded=False):
        tokens = [candidate for candidate, _ in participants(data)]
        default = default_opponent(data, token)
        victim = remembered_select("Цель действия", tokens, f"attack_victim_{token}", default=default,
                                   format_func=lambda value: participant_label(data, value))
        render_combatant_action(data, token, victim)


def render_combatant_card(data, token, title, active=False):
    target = participant(data, token)
    hp_key, maximum_key = hp_fields(target)
    shield = sum(effect["value"] for effect in target.get("effects", []) if effect["kind"] == "shield")
    role = combat_side(data, token) + (f" #{target['id']}" if token.startswith("enemy:") else "")
    identity = [role]
    if target.get("level"): identity.append(f"Уровень {target['level']}")
    if token == "player": identity.extend([target.get("race", ""), target.get("class", "")])
    elif target.get("size"): identity.append(target["size"])
    if target.get("is_elite"): identity.append("Элитный")
    if target.get("description"): identity.append(target["description"][:160])
    ratio = min(100, max(0, 100 * target[hp_key] / max(1, target[maximum_key])))
    details = [f"Броня {effective_defense(target, 'Физический')}", f"Щит {shield}"]
    if "mana_current" in target: details.append(f"MP {target['mana_current']}/{target['mana_max']}")
    elif active: details.append(f"Атака {target.get('attack_damage', 0)} · {target.get('attack_type', 'Физический')}")
    if active and target.get("heal_amount", 0): details.append(f"Лечение {target['heal_amount']}")
    if active: details.append(f"Инициатива {data.get('initiative_overrides', {}).get(token, target.get('initiative', 10))}")
    effects = [effect['name'] for effect in target.get('effects', [])]
    if target is data and data.get('ten_invis'): effects.append('Невидимость')
    if target is data and data.get('ten_resist_boost'): effects.append('Сопротивления Тени')
    badges = ''.join(f'<span class="combat-badge">{escape(name)}</span>' for name in effects[:4])
    if len(effects) > 4: badges += f'<span class="combat-badge">ещё {len(effects)-4}</span>'
    if not active:
        st.markdown(f"""<div class="combatant-card combat-target"><div class="combat-eyebrow">{escape(title)} · {escape(role)}</div>
        <div class="combat-health-label"><strong>{escape(participant_label(data, token))}</strong><span>HP {target[hp_key]} / {target[maximum_key]}</span></div>
        <div class="combat-health"><div style="width:{ratio:.2f}%"></div></div>
        <div class="combat-details">{escape(' · '.join(details))}</div><div class="combat-badges">{badges}</div></div>""", unsafe_allow_html=True)
        return
    st.markdown(f"""<div class="combatant-card {'acting' if active else ''}">
    <div class="combat-eyebrow">{escape(title)}</div><div class="combatant-name">{escape(participant_label(data, token))}</div>
    <div class="combat-identity">{escape(' · '.join(filter(None, identity)))}</div>
    <div class="combat-health-label">HP <strong>{target[hp_key]} / {target[maximum_key]}</strong></div>
    <div class="combat-health"><div style="width:{ratio:.2f}%"></div></div>
    <div class="combat-details">{escape(' · '.join(details))}</div><div class="combat-badges">{badges}</div></div>""", unsafe_allow_html=True)


def render_new_enemy(data):
    with st.expander("Добавить врага / подкрепление", expanded=False):
        with st.form("adden"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Имя нового врага", value="Враг")
            level = c2.number_input("Уровень", min_value=1, max_value=60, value=10)
            size = st.selectbox("Размер", ["Мелкий", "Обычный", "Крупный", "Огромный"])
            elite = st.checkbox("Элитный")
            if st.form_submit_button("Добавить врага"):
                if not name.strip(): st.error("Укажи имя")
                else:
                    eid = data["next_enemy_id"]
                    data["enemies"].append({"id": eid, "name": name.strip(), "level": level, "size": size,
                                            "is_elite": elite, "effects": [], **gen_enemy(level, size, elite)})
                    data["next_enemy_id"] += 1
                    if data["combat_active"]: refresh_turn_order(data)
                    st.session_state["_next_battle_target"] = f"enemy:{eid}"
                    log(f"Добавлен враг: {name.strip()}")
                    persist_and_rerun()


def render_queue(data, token):
    target = participant(data, token)
    current = get_current_actor(data)
    if data["turn_order"]:
        visible_order = list(enumerate(data["turn_order"]))
        if len(visible_order) > 10:
            pages = list(range((len(visible_order) + 9) // 10))
            page_index = remembered_select("Страница очереди", pages, "queue_page", default=data["current_turn"] // 10,
                                            format_func=lambda value: f"{value + 1} / {len(pages)}")
            visible_order = visible_order[page_index * 10:(page_index + 1) * 10]
        for i, actor in visible_order:
            prefix = "▶" if i == data["current_turn"] else "✓" if i < data["current_turn"] else "·"
            st.write(f"{prefix} {i + 1}. {actor['name']} · {actor.get('init', 0)}")
    else:
        st.caption("Очередь появится после начала боя")
    st.caption("Перестановка действует в текущем круге. Следующий круг строится по инициативе.")
    default_init = data.get("initiative_overrides", {}).get(token, target.get("initiative", 10))
    initiative = st.number_input("Инициатива выбранного участника", min_value=0, value=default_init, key=f"queue_init_{token}")
    if st.button("Применить инициативу", key="queue_apply_init"):
        set_initiative(data, token, initiative)
        log(f"Инициатива: {target['name']} → {initiative}")
        persist_and_rerun()
    order_tokens = [actor_token(actor) for actor in data["turn_order"]]
    if token in order_tokens:
        pos = order_tokens.index(token)
        c1, c2 = st.columns(2)
        if c1.button("↑ Раньше", disabled=pos == 0, key="queue_up", use_container_width=True):
            move_in_queue(data, token, -1); log(f"{target['name']}: раньше в очереди"); persist_and_rerun()
        if c2.button("↓ Позже", disabled=pos == len(order_tokens) - 1, key="queue_down", use_container_width=True):
            move_in_queue(data, token, 1); log(f"{target['name']}: позже в очереди"); persist_and_rerun()
        if st.button("Назначить его ход сейчас", disabled=current is not None and actor_token(current) == token, key="queue_jump", use_container_width=True):
            data["current_turn"] = pos
            log(f"Ведущий назначил ход: {target['name']}")
            persist_and_rerun()
        st.caption("Назначение хода вручную не вызывает тики эффектов.")
    if token in data.get("turn_excluded", []):
        if st.button("Вернуть в очередь", key="queue_return", use_container_width=True):
            return_to_queue(data, token); log(f"{target['name']}: возвращён в очередь"); persist_and_rerun()
    elif st.button("Исключить из очереди", key="queue_exclude", use_container_width=True):
        for message in exclude_from_queue(data, token): log(message)
        log(f"{target['name']}: исключён из очереди")
        persist_and_rerun()
    if token in data.get("initiative_overrides", {}):
        if st.button("Вернуть обычную инициативу", key="queue_clear_override"):
            set_initiative(data, token, target.get("initiative", 10))
            data["initiative_overrides"].pop(token)
            log(f"{target['name']}: обычная инициатива восстановлена"); persist_and_rerun()


def render_battle(data):
    render_battle_header(data)
    section = st.session_state["battle_section"]
    current = get_current_actor(data) if data["combat_active"] else None
    active_token = actor_token(current) if current else None
    if section != "Ход" and active_token and actor_target(data, current) is not None:
        render_combatant_card(data, active_token, "Сейчас ходит", active=True)
    if section == "Журнал":
        st.caption("История отмены хранится в текущей сессии; состояние игры сохраняется в файл.")
        search = st.text_input("Найти в журнале", key="battle_log_search")
        entries = [entry for entry in data["combat_log"] if search.casefold() in entry.casefold()]
        for entry in entries[:20]: st.text(entry)
        if not entries: st.caption("Записей нет")
        st.download_button("Скачать журнал", "\n".join(reversed(data["combat_log"])), file_name="kalista_combat_log.txt", mime="text/plain")
        return
    tokens = [token for token, _ in participants(data)]
    if section == "Ход":
        if not active_token:
            active_token = remembered_select("Кто действует", tokens, "battle_manual_actor", default="player",
                                             format_func=lambda value: participant_label(data, value))
        default = default_opponent(data, active_token)
        with st.container(key="turn_cards"):
            acting_column, target_column = st.columns(2)
            with acting_column:
                render_combatant_card(data, active_token, "Сейчас ходит" if current else "Действие вне боя", active=True)
            with target_column:
                token = remembered_select("Цель действия", tokens, f"turn_target_{active_token}", default=default,
                                          format_func=lambda value: participant_label(data, value))
                render_combatant_card(data, token, "Цель")
        if active_token == "player": render_selected_spell(data, participant(data, token))
        else:
            with st.container(key="turn_action"):
                render_combatant_action(data, active_token, token)
        if data["combat_log"]: st.caption("Последнее: " + data["combat_log"][0])
        return
    default = active_token or "player"
    token = remembered_select("Выбранный участник", tokens, "battle_target", default=default,
                              format_func=lambda value: participant_label(data, value))
    target = participant(data, token)
    hp_key, maximum_key = hp_fields(target)
    shield = sum(effect["value"] for effect in target.get("effects", []) if effect["kind"] == "shield")
    st.caption(f"HP {target[hp_key]}/{target[maximum_key]} · Щит {shield} · Броня {effective_defense(target, 'Физический')} · Эффектов {len(target.get('effects', []))}")
    if section == "Участники":
        with st.expander("Ручная правка: урон, лечение, мана и щит", expanded=False):
            render_quick_action(data, token)
        render_attack(data, token)
        render_participant_editor(data, token)
        render_new_enemy(data)
    elif section == "Эффекты":
        render_effect_editor(data, token)
    elif section == "Очередь":
        render_queue(data, token)
    if data["combat_log"]:
        st.caption("Последнее: " + data["combat_log"][0])


# ===================== СЦЕНЫ И NPC =====================
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
    fighter = dict(id=enemy_id, name=npc['name'], description=npc['description'] or npc['role'], side=npc['side'],
                   source_npc_id=npc_id, effects=[], dots=[], **stats)
    data['enemies'].append(fighter)
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


def render_npc_roster(data, scene):
    if not scene['npc_ids']:
        st.caption('Добавь участников в настройках сцены. Карточки NPC создаются в соседнем разделе.')
    with st.container(key='gm_roster'):
        for npc_id in scene['npc_ids']:
            npc = npc_record(data, npc_id)
            c1, c2 = st.columns([3, 2])
            c1.markdown(f"**{escape(npc['name'])}** · {escape(npc['role']) or npc['side']}")
            existing = npc_battle_token(data, npc_id)
            if c2.button('В бою' if existing else 'Добавить в бой', key=f'scene_battle_{scene["id"]}_{npc_id}', disabled=bool(existing), use_container_width=True):
                add_npc_to_battle(data, npc_id)
                log(f"NPC добавлен в бой: {npc['name']} ({npc['side']})")
                persist_and_rerun(f"В бой: {npc['name']}")


def render_scene_editor(data):
    with st.expander('Новая сцена', expanded=not data['scenes']):
        with st.form('gm_new_scene'):
            name = st.text_input('Название сцены', key='gm_new_scene_name')
            location = st.text_input('Место', key='gm_new_scene_location')
            if st.form_submit_button('Создать сцену'):
                try:
                    scene = create_scene(data, name, location)
                    st.session_state['_gm_select_scene'] = scene['id']
                    persist_and_rerun(f"Создана сцена: {scene['name']}")
                except ValueError as exc: st.error(str(exc))
    if not data['scenes']: return
    with st.container(key='gm_filter'):
        search_column, select_column = st.columns([1, 2])
        search = search_column.text_input('Найти сцену', key='gm_scene_search')
        matches = [scene for scene in data['scenes'] if search.casefold() in (scene['name']+' '+scene['location']+' '+scene['summary']+' '+scene['gm_notes']).casefold()]
        if not matches:
            st.info('Подходящих сцен нет. Измени поиск.'); return
        with select_column:
            scene_id = remembered_select('Сцена', [scene['id'] for scene in matches], 'gm_scene_selected', default=data['active_scene_id'] or matches[0]['id'],
                                         format_func=lambda ident: f"{'▶ ' if ident == data['active_scene_id'] else ''}{scene_record(data, ident)['name']} · {scene_record(data, ident)['status']}")
    scene = scene_record(data, scene_id)
    st.subheader(scene['name'])
    st.caption(f"{scene['location'] or 'Место не задано'} · {scene['status']}")
    if scene['summary']: st.write(scene['summary'])
    with st.container(key='gm_scene_actions'):
        b1, b2 = st.columns(2)
        if b1.button('Сделать текущей', key=f'gm_scene_activate_{scene_id}', disabled=data['active_scene_id'] == scene_id, use_container_width=True):
            activate_scene(data, scene_id)
            st.session_state['_gm_select_scene'] = scene_id
            persist_and_rerun(f"Текущая сцена: {scene['name']}")
        if b2.button('Завершить сцену', key=f'gm_scene_finish_{scene_id}', disabled=scene['status'] == 'Завершена', use_container_width=True):
            update_scene(data, scene_id, {'status':'Завершена'})
            st.session_state['_gm_select_scene'] = scene_id
            persist_and_rerun(f"Завершена сцена: {scene['name']}")
    with st.expander('Содержание и участники', expanded=not scene['summary'] and not scene['gm_notes']):
        with st.form(f'gm_scene_form_{scene_id}'):
            name = st.text_input('Название', value=scene['name'])
            location = st.text_input('Место сцены', value=scene['location'])
            statuses = ['Подготовка', 'Идёт', 'На паузе', 'Завершена']
            status = st.selectbox('Статус сцены', statuses, index=statuses.index(scene['status']))
            npcs = st.multiselect('NPC в сцене', [npc['id'] for npc in data['npcs']], default=scene['npc_ids'], format_func=lambda ident:f"{npc_record(data, ident)['name']} · №{next(i+1 for i,npc in enumerate(data['npcs']) if npc['id']==ident)}", key=f'gm_scene_npcs_{scene_id}')
            summary = st.text_area('Что видят игроки', value=scene['summary'], height=100)
            notes = st.text_area('Заметки и секреты ведущего', value=scene['gm_notes'], height=130)
            result = st.text_area('Итог сцены — для ведущего', value=scene['result'], height=80)
            if st.form_submit_button('Сохранить сцену', type='primary'):
                try:
                    update_scene(data, scene_id, dict(name=name, location=location, status=status, npc_ids=npcs, summary=summary, gm_notes=notes, result=result))
                    st.session_state['_gm_select_scene'] = scene_id
                    persist_and_rerun(f"Сцена: {name.strip()}")
                except ValueError as exc: st.error(str(exc))
    render_npc_roster(data, scene)
    if scene['gm_notes']:
        with st.expander('Подсказки ведущему', expanded=True): st.write(scene['gm_notes'])
    if scene['result']:
        with st.expander('Итог сцены', expanded=False): st.write(scene['result'])
    with st.expander('Текст для игроков', expanded=False):
        public = scene_player_text(data, scene_id)
        st.markdown(public)
        st.download_button('Скачать текст для игроков', public, file_name='scene_for_players.md', mime='text/markdown', key=f'gm_export_scene_{scene_id}')
    with st.expander('Удалить сцену', expanded=False):
        confirm = st.checkbox('Подтверждаю удаление сцены', key=f'gm_scene_delete_confirm_{scene_id}')
        if st.button('Удалить сцену', disabled=not confirm, key=f'gm_scene_delete_{scene_id}'):
            delete_scene(data, scene_id); persist_and_rerun(f"Удалена сцена: {scene['name']}")


def render_npc_editor(data):
    with st.expander('Новый NPC', expanded=not data['npcs']):
        with st.form('gm_new_npc'):
            name = st.text_input('Имя NPC', key='gm_new_npc_name')
            role = st.text_input('Роль / занятие, известное игрокам', key='gm_new_npc_role')
            if st.form_submit_button('Создать NPC'):
                try:
                    npc = create_npc(data, name, role)
                    st.session_state['_gm_select_npc'] = npc['id']
                    persist_and_rerun(f"Создан NPC: {npc['name']}")
                except ValueError as exc: st.error(str(exc))
    if not data['npcs']: return
    with st.container(key='gm_filter'):
        search_column, select_column = st.columns([1, 2])
        search = search_column.text_input('Найти NPC', key='gm_npc_search')
        matches = [npc for npc in data['npcs'] if search.casefold() in ' '.join(npc[field] for field in ('name','role','location','description','public_notes','gm_notes')).casefold()]
        if not matches:
            st.info('Подходящих NPC нет. Измени поиск.'); return
        with select_column:
            npc_id = remembered_select('Карточка NPC', [npc['id'] for npc in matches], 'gm_npc_selected', default=matches[0]['id'], format_func=lambda ident:f"{npc_record(data, ident)['name']} · {npc_record(data, ident)['role'] or npc_record(data, ident)['side']} · №{next(i+1 for i,npc in enumerate(data['npcs']) if npc['id']==ident)}")
    npc = npc_record(data, npc_id)
    st.subheader(npc['name'])
    st.caption(f"{npc['role'] or 'Роль не задана'} · {npc['side']} · {npc['location'] or 'Место не задано'}")
    if npc['description']: st.write(npc['description'])
    if npc['gm_notes']:
        with st.expander('Секреты NPC', expanded=False): st.write(npc['gm_notes'])
    with st.expander('Изменить карточку NPC', expanded=not npc['description'] and not npc['gm_notes']):
        with st.form(f'gm_npc_form_{npc_id}'):
            name = st.text_input('Имя', value=npc['name'])
            c1, c2 = st.columns(2)
            role = c1.text_input('Роль / занятие', value=npc['role'])
            location = c2.text_input('Где находится', value=npc['location'])
            sides = ['Враг', 'Союзник', 'Нейтральный']
            side = st.selectbox('Сторона в бою', sides, index=sides.index(npc['side']))
            description = st.text_area('Внешность и характер — для игроков', value=npc['description'], height=100)
            public = st.text_area('Известное игрокам', value=npc['public_notes'], height=100)
            private = st.text_area('Секреты и заметки ведущего', value=npc['gm_notes'], height=120)
            with st.expander('Характеристики для добавления в бой', expanded=False):
                c1, c2, c3 = st.columns(3)
                hp = c1.number_input('HP NPC', min_value=0, value=npc['combat']['hp'])
                maximum = c2.number_input('Максимум HP NPC', min_value=1, value=npc['combat']['hp_max'])
                armor = c3.number_input('Броня NPC', min_value=0, value=npc['combat']['armor'])
                c1, c2, c3 = st.columns(3)
                attack = c1.number_input('Урон атаки NPC', min_value=0, value=npc['combat']['attack_damage'])
                healing = c2.number_input('Лечение NPC', min_value=0, value=npc['combat']['heal_amount'])
                initiative = c3.number_input('Инициатива NPC', min_value=0, value=npc['combat']['initiative'])
                dtype = st.selectbox('Тип атаки NPC', DAMAGE_TYPES, index=DAMAGE_TYPES.index(npc['combat']['attack_type']))
                resists = {}
                cols = st.columns(2)
                for i, element in enumerate(ELEMENTS):
                    resists[element] = cols[i%2].number_input(f'Сопротивление: {element}', min_value=0, value=npc['combat']['resists'][element])
            if st.form_submit_button('Сохранить NPC', type='primary'):
                try:
                    update_npc(data, npc_id, dict(name=name, role=role, location=location, side=side, description=description, public_notes=public, gm_notes=private,
                                                combat=dict(hp=hp, hp_max=maximum, armor=armor, attack_damage=attack, heal_amount=healing, initiative=initiative, attack_type=dtype, resists=resists)))
                    st.session_state['_gm_select_npc'] = npc_id
                    persist_and_rerun(f"NPC: {name.strip()}")
                except ValueError as exc: st.error(str(exc))
    existing = npc_battle_token(data, npc_id)
    if st.button('Уже среди участников боя' if existing else 'Добавить NPC в бой', key=f'gm_npc_battle_{npc_id}', disabled=bool(existing), use_container_width=True):
        add_npc_to_battle(data, npc_id)
        log(f"NPC добавлен в бой: {npc['name']} ({npc['side']})")
        persist_and_rerun(f"В бой: {npc['name']}")
    st.caption('В бой попадут HP и характеристики из сохранённой карточки NPC.')
    linked = [scene['name'] for scene in data['scenes'] if npc_id in scene['npc_ids']]
    if linked: st.caption('Сцены: ' + ', '.join(linked))
    with st.expander('Удалить NPC', expanded=False):
        confirm = st.checkbox('Подтверждаю удаление NPC', key=f'gm_npc_delete_confirm_{npc_id}')
        if st.button('Удалить NPC', key=f'gm_npc_delete_{npc_id}', disabled=not confirm):
            delete_npc(data, npc_id); persist_and_rerun(f"Удалён NPC: {npc['name']}")


def render_gm(data):
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Стол ведущего</div>", unsafe_allow_html=True)
    history = st.session_state.get('_undo_history', [])
    if st.button('Отменить последнее действие', key='gm_undo', disabled=not history, help=history[-1]['label'] if history else 'Нет действий для отмены'):
        undo_last_action()
    prefs = st.session_state.setdefault('_battle_preferences', {})
    if 'gm_section' not in st.session_state: st.session_state['gm_section'] = prefs.get('gm_section', 'Сцены')
    section = st.radio('Раздел ведущего', ['Сцены','NPC','Записная книжка'], key='gm_section', horizontal=True, label_visibility='collapsed')
    prefs['gm_section'] = section
    if section == 'Сцены': render_scene_editor(data)
    elif section == 'NPC': render_npc_editor(data)
    else:
        with st.form('gm_notebook'):
            notes = st.text_area('Общие заметки ведущего', value=data['gm_notes'], height=260)
            if st.form_submit_button('Сохранить заметки', type='primary'):
                data['gm_notes'] = notes
                persist_and_rerun('Заметки ведущего')
        current = scene_record(data, data['active_scene_id'])
        if current: st.caption('Текущая сцена: ' + current['name'])
        st.download_button('Скачать записную книжку', data['gm_notes'], file_name='gm_notes.md', mime='text/markdown')


def combat_side(data, token):
    if token == 'player': return 'Героиня'
    if token == 'ally': return 'Союзник'
    return participant(data, token).get('side', 'Враг')


def default_opponent(data, source_token):
    tokens = [token for token, target in participants(data) if token != source_token and target[hp_fields(target)[0]] > 0]
    if combat_side(data, source_token) == 'Враг': return 'player' if 'player' in tokens else tokens[0] if tokens else source_token
    return next((token for token in tokens if combat_side(data, token) == 'Враг'), tokens[0] if tokens else source_token)


# ===================== INIT =====================
if "data" not in st.session_state:
    st.session_state.data=load()
    recalc(st.session_state.data)
data=st.session_state.data
if data.get("schema_version", 5) < 14:
    data = migrate(data)
    st.session_state.data = data
if st.session_state.pop("_reset_resource_widgets", False):
    st.session_state.pop("ah", None)
    for key in list(st.session_state):
        if (str(key).startswith("q") and str(key)[1:].isdigit()) or str(key).startswith("queue_init_"):
            del st.session_state[key]
recalc(data)
if "_committed_data" not in st.session_state:
    st.session_state["_committed_data"] = deepcopy(data)
st.session_state.setdefault("_undo_history", [])
if "_next_battle_target" in st.session_state:
    st.session_state["battle_target"] = st.session_state.pop("_next_battle_target")

for pending, selected, search in (("_gm_select_scene", "gm_scene_selected", "gm_scene_search"), ("_gm_select_npc", "gm_npc_selected", "gm_npc_search")):
    if pending in st.session_state:
        st.session_state[selected] = st.session_state.pop(pending)
        st.session_state[search] = ""
        # Перезагружаем значения формы после сохранения или смены статуса.
        prefix = "gm_scene_npcs_" if selected == "gm_scene_selected" else ""
        if prefix:
            for widget_key in list(st.session_state):
                if str(widget_key).startswith(prefix): del st.session_state[widget_key]

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("<div class='main-title' style='font-size:1.35rem'>✧ Калиста</div>", unsafe_allow_html=True)
    st.caption(f"Ур.{data['level']} · {data['class']}")
    st.progress(min(data["hp_current"]/max(data["hp_max"],1),1.0), text=f"HP {data['hp_current']}/{data['hp_max']}")
    st.progress(min(data["mana_current"]/max(data["mana_max"],1),1.0), text=f"MP {data['mana_current']}/{data['mana_max']}")
    if data.get("combat_active"):
        st.markdown(f"**Раунд {data['round']}**")
        actor=get_current_actor(data)
        if actor: st.info(f"Ход: {actor['name']}")
    active_scene = scene_record(data, data['active_scene_id'])
    if active_scene: st.caption('Сцена: ' + active_scene['name'])
    st.divider()
    page=st.radio("Меню",["Обзор","Бой","Экипировка","Характеристики","Инвентарь","Заклинания","Квесты","Ведущий","Кубики","Биография"],label_visibility="collapsed", key="page")
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
    with st.expander("Настройки портрета", expanded=False):
        data["portrait_url"] = st.text_input("URL своего портрета (пусто — портрет Калисты)", value=data.get("portrait_url", ""), key="portrait")
    with st.container(key="overview_hero"):
        portrait_column, info_column = st.columns([1, 2])
        with portrait_column:
            source = data.get("portrait_url") or (str(PORTRAIT_FILE) if PORTRAIT_FILE.is_file() else None)
            if source:
                try:
                    st.image(source, width=220)
                except Exception:
                    st.caption("Не удалось загрузить выбранный портрет")
                    if PORTRAIT_FILE.is_file(): st.image(str(PORTRAIT_FILE), width=220)
            else:
                st.caption("Портрет хранится в assets/kalista-portrait.png рядом с приложением.")
        with info_column:
            st.progress(min(data["hp_current"]/max(data["hp_max"],1),1.0),text=f"HP {data['hp_current']}/{data['hp_max']}")
            st.progress(min(data["mana_current"]/max(data["mana_max"],1),1.0),text=f"MP {data['mana_current']}/{data['mana_max']}")
            m1,m2=st.columns(2)
            m1.metric("Сила закл.",f"+{data['spell_power']*100:.0f}%")
            m2.metric("Броня",data["armor"])
            m3,m4=st.columns(2)
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
    render_battle(data)

# ===================== ЭКИПИРОВКА =====================
elif page=="Ведущий":
    with st.container(key="gm_table"):
        render_gm(data)

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
        d3.metric("Крит", f"{effective_crit_chance(data)*100:.1f}%")

    with st.expander("Сопротивления стихиям"):
        rc = st.columns(6)
        for i, e in enumerate(ELEMENTS):
            rc[i].metric(e, data["resists"].get(e, 0))

    with st.expander("Пассивки (расовые и классовые)"):
        for k, p in data["passives"].items():
            if p.get("type") in ("racial", "class"):
                st.markdown(f"**{p['name']}** — {p['desc']}")
                if k == "mana_reserve":
                    st.caption("Мана восстанавливается в конце полного раунда. Резерв проверяется до восстановления и усиливает три тика, даже после выхода выше 20%.")
                if k == "shadow_child":
                    st.caption("Текущий расчёт: +20 пунктов сопротивления с пределом 95; это сохранённая формула программы.")

    with st.expander("Особые умения"):
        for k, p in data["passives"].items():
            if p.get("type") != "special":
                continue
            c1, c2 = st.columns([3.5, 1])
            allowed, reason = special_availability(data, k)
            status = "✅ использовано" if p["used"] else "🟢 доступно" if allowed else "⏳ сейчас недоступно"
            c1.markdown(f"**{p['name']}** — {status}<br>{p['desc']}", unsafe_allow_html=True)
            if c2.button("Использовать", key=f"pas_{k}", disabled=not allowed):
                log(activate_special(data, k))
                persist_and_rerun()
            if reason and not p["used"]: c1.caption(reason)


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
Калиста родилась в **Доме Клиф** — большом и гордом матриархальном доме дроу, известном своими экспериментами на стыке огня и тьмы.
Её мать, матриарх **Ильраэль Клиф**, была одержима идеей создать «чистое пламя бездны» — огонь, питаемый самой пустотой.
В возрасте шестнадцати лет Калиста стала свидетельницей падения своего дома: во время особо опасного ритуала что-то пошло не так.
Чёрное пламя вырвалось из-под контроля и уничтожило почти весь Дом Клиф за одну ночь.
Выжила только она — потому что в последний момент мать затолкала её в защитный круг и сама приняла основной удар.

С тех пор Калиста странствует. Сначала по Подземью, потом — на поверхность.
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



commit_current()
