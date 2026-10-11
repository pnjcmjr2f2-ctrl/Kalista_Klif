#!/usr/bin/env python3
"""
Калист Клиф — Интерактивный помощник v3
Полная версия: бой с врагами, пассивки, отдых, квесты, экипировка
"""

import streamlit as st
import json
import random
from datetime import datetime
from pathlib import Path
from copy import deepcopy

SAVE_FILE = Path(__file__).parent / "kalista_save.json"

st.set_page_config(
    page_title="✧ Калист Клиф ✧",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== СТИЛИ =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Quattrocento+Sans:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Quattrocento Sans', sans-serif; }
    .main-title {
        font-family: 'Cinzel', serif;
        font-size: 2.1rem;
        color: #E8DAEF;
        text-align: center;
        text-shadow: 0 0 14px #4A235A;
        margin-bottom: 0.15rem;
    }
    .subtitle { text-align: center; color: #BB8FCE; margin-bottom: 1rem; }
    .section-h {
        font-family: 'Cinzel', serif;
        color: #D7BDE2;
        font-size: 1.2rem;
        border-bottom: 2px solid #7D3C98;
        padding-bottom: 3px;
        margin: 1rem 0 0.6rem 0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.35rem; }
    .stButton > button { border-radius: 8px; font-weight: 600; }
    .enemy-card {
        background: #1a0a22;
        border: 1px solid #5B2C6F;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ===================== ДЕФОЛТ =====================
DEFAULT = {
    "name": "Калист Клиф",
    "race": "Тёмный эльф (Дроу)",
    "class": "Маг огня и тьмы",
    "level": 21,
    "xp": 18450,
    "xp_to_next": 2150,
    "free_points": 0,

    "hp_current": 420,
    "hp_max": 820,
    "mana_current": 0,
    "mana_max": 2950,

    "base_stats": {
        "Сила": 10, "Выносливость": 15, "Ловкость": 14,
        "Мудрость": 10, "Интеллект": 60, "Харизма": 10, "Дух": 35
    },
    "equip_bonuses": {
        "Сила": 0, "Выносливость": 25, "Ловкость": 0,
        "Мудрость": 85, "Интеллект": 235, "Харизма": 0, "Дух": 175
    },

    "armor": 535,
    "phys_attack": 55,

    "pepel": 0,
    "ten": 0,
    "buffs": "",
    "debuffs": "",
    "concentration": "",
    "last_school": None,

    "gold": 84, "silver": 34, "copper": 0,

    "inventory": [
        {"name": "Зелье маны (большое)", "type": "Расходник", "qty": 3, "desc": "Восстанавливает 400 маны"},
        {"name": "Зелье лечения", "type": "Расходник", "qty": 2, "desc": "Восстанавливает 250 здоровья"},
        {"name": "Свиток «Щит теней»", "type": "Свиток", "qty": 1, "desc": "Щит на 300 урона"},
        {"name": "Кристалл пустоты", "type": "Реагент", "qty": 5, "desc": "Для ритуалов тьмы"},
        {"name": "Пепел древнего костра", "type": "Реагент", "qty": 4, "desc": "Усиливает огонь"},
        {"name": "Чёрный дневник", "type": "Книга", "qty": 1, "desc": "Личные записи"},
        {"name": "Амулет старого дома", "type": "Реликвия", "qty": 1, "desc": "Реликвия Дома Клиф"},
        {"name": "Набор алхимика", "type": "Инструмент", "qty": 1, "desc": "Полевая алхимия"},
        {"name": "Факел вечного огня", "type": "Инструмент", "qty": 1, "desc": "Чёрное пламя"},
    ],

    "spells": [
        {"id": 1, "name": "Искровой заряд", "base": 35, "mana": 18, "range": "Ближняя", "school": "Огонь",
         "desc": "Быстрый сгусток огня.", "gives": "pepel"},
        {"id": 2, "name": "Огненный шар", "base": 80, "mana": 35, "range": "Средняя", "school": "Огонь",
         "desc": "Классический шар пламени.", "gives": "pepel"},
        {"id": 3, "name": "Язык пламени", "base": 55, "mana": 28, "range": "Ближняя", "school": "Огонь",
         "desc": "Полоса огня.", "gives": "pepel"},
        {"id": 4, "name": "Пепел и тлен", "base": 40, "mana": 22, "range": "Средняя", "school": "Огонь",
         "desc": "DoT на 3 хода.", "gives": "pepel"},
        {"id": 5, "name": "Адское дыхание", "base": 120, "mana": 55, "range": "Ближняя", "school": "Огонь",
         "desc": "Мощный конус огня.", "gives": "pepel"},
        {"id": 6, "name": "Теневой укол", "base": 45, "mana": 20, "range": "Ближняя", "school": "Тьма",
         "desc": "Игнорирует часть брони.", "gives": "ten"},
        {"id": 7, "name": "Покров тьмы", "base": 0, "mana": 30, "range": "На себя", "school": "Тьма",
         "desc": "Щит +10% сопр. тьме.", "gives": None},
        {"id": 8, "name": "Проклятие слабости", "base": 25, "mana": 25, "range": "Средняя", "school": "Тьма",
         "desc": "Снижает силу и атаку.", "gives": "ten"},
        {"id": 9, "name": "Разряд бездны", "base": 95, "mana": 45, "range": "Дальняя", "school": "Тьма",
         "desc": "Шанс страха.", "gives": "ten"},
        {"id": 10, "name": "Пламя души", "base": 150, "mana": 70, "range": "Средняя", "school": "Огонь+Тьма",
         "desc": "Ультиматив.", "gives": "both"},
    ],

    "equipment": {
        "Оружие 1 (посох)": {"name": "Посох Магистра Огня и Тьмы", "armor": 0, "attack": 50, "int": 60, "wis": 15, "spi": 60, "fire": 50, "dark": 50, "desc": "Чёрное пламя внутри"},
        "Оружие 2": {"name": "", "armor": 0, "attack": 0, "int": 0, "wis": 0, "spi": 0, "fire": 0, "dark": 0, "desc": ""},
        "Шлем": {"name": "Капюшон тьмы", "armor": 15, "attack": 0, "int": 20, "wis": 10, "spi": 10, "fire": 0, "dark": 0, "desc": ""},
        "Наплечники": {"name": "Наплечники тьмы", "armor": 5, "attack": 0, "int": 20, "wis": 10, "spi": 10, "fire": 0, "dark": 5, "desc": ""},
        "Перчатки": {"name": "Перчатки тьмы", "armor": 5, "attack": 0, "int": 10, "wis": 5, "spi": 15, "fire": 0, "dark": 5, "desc": ""},
        "Нагрудник": {"name": "Нагрудник тьмы", "armor": 50, "attack": 0, "int": 40, "wis": 0, "spi": 30, "fire": 0, "dark": 5, "desc": ""},
        "Пояс": {"name": "Пояс тьмы", "armor": 10, "attack": 0, "int": 10, "wis": 5, "spi": 5, "fire": 0, "dark": 5, "desc": ""},
        "Штаны": {"name": "Поножи тьмы", "armor": 25, "attack": 0, "int": 15, "wis": 0, "spi": 5, "fire": 0, "dark": 5, "desc": ""},
        "Сапоги": {"name": "Сапоги тьмы", "armor": 15, "attack": 0, "int": 10, "wis": 0, "spi": 10, "fire": 0, "dark": 5, "desc": ""},
        "Серьга 1": {"name": "", "armor": 0, "attack": 0, "int": 0, "wis": 0, "spi": 0, "fire": 0, "dark": 0, "desc": ""},
        "Серьга 2": {"name": "", "armor": 0, "attack": 0, "int": 0, "wis": 0, "spi": 0, "fire": 0, "dark": 0, "desc": ""},
        "Ожерелье": {"name": "Фамильный Амулет", "armor": 0, "attack": 0, "int": 0, "wis": 40, "spi": 0, "fire": 0, "dark": 0, "desc": "Шёпот дома"},
        "Кольцо 1": {"name": "Кольцо разрушения", "armor": 0, "attack": 0, "int": 25, "wis": 0, "spi": 30, "fire": 20, "dark": 0, "desc": ""},
        "Кольцо 2": {"name": "Кольцо сосредоточения", "armor": 0, "attack": 0, "int": 25, "wis": 0, "spi": 0, "fire": 0, "dark": 0, "desc": ""},
        "Кольцо 3": {"name": "", "armor": 0, "attack": 0, "int": 0, "wis": 0, "spi": 0, "fire": 0, "dark": 0, "desc": ""},
        "Кольцо 4": {"name": "", "armor": 0, "attack": 0, "int": 0, "wis": 0, "spi": 0, "fire": 0, "dark": 0, "desc": ""},
    },

    # --- Новые системы ---
    "enemies": [],
    "next_enemy_id": 1,

    "passives": {
        "ritual_black_flame": {"name": "Ритуал Чёрного Пламени", "used": False, "desc": "Раз в день: следующее Пламя души +40% урона и без долгого каста"},
        "cold_calculation": {"name": "Холодный расчёт", "used": False, "desc": "В начале боя (1 ход): +10% шанса крита до конца боя"},
        "memory_of_house": {"name": "Память Дома Клиф", "used": False, "desc": "Раз в долгий отдых: преимущество на проверку знаний о запретной магии"},
    },
    "soul_flame_boost": False,   # флаг от Ритуала
    "crit_boost_active": False,  # от Холодного расчёта

    "quests": [
        {"id": 1, "name": "Пепел старого дома", "status": "В процессе", "desc": "Найти записи/артефакты Дома Клиф. Форпост на границе Подземья."},
        {"id": 2, "name": "Кристалл пустоты", "status": "Активен", "desc": "Добыть стабильный кристалл пустоты. Руины под Серым Утёсом."},
        {"id": 3, "name": "Долг Серому", "status": "Ожидание", "desc": "Серый попросит об услуге. Быть готовой."},
    ],
    "notes": "Никогда не использовать Пламя души рядом с теми, кого не готова потерять.\nКонтроль важнее силы. Всегда.",

    "combat_log": [],
    "resists": {"Огонь": 75, "Земля": 5, "Вода": 10, "Воздух": 5, "Тьма": 95, "Свет": 15},
}

# ===================== УТИЛИТЫ =====================
def total_stat(data, name):
    return data["base_stats"].get(name, 0) + data["equip_bonuses"].get(name, 0)

def recalc_equip_bonuses(data):
    eq = data.get("equipment", {})
    bonuses = {k: 0 for k in ["Сила", "Выносливость", "Ловкость", "Мудрость", "Интеллект", "Харизма", "Дух"]}
    total_armor = 0
    total_attack = 0
    for item in eq.values():
        bonuses["Интеллект"] += item.get("int", 0)
        bonuses["Мудрость"] += item.get("wis", 0)
        bonuses["Дух"] += item.get("spi", 0)
        total_armor += item.get("armor", 0)
        total_attack += item.get("attack", 0)
    # Кольцо сосредоточения даёт Выносливость 25 (зашито)
    bonuses["Выносливость"] = 25
    data["equip_bonuses"] = bonuses
    data["armor"] = total_armor
    data["phys_attack"] = 5 + total_attack

def recalc_derived(data):
    if "equipment" in data:
        recalc_equip_bonuses(data)
    intel = total_stat(data, "Интеллект")
    wis = total_stat(data, "Мудрость")
    cha = total_stat(data, "Харизма")
    spi = total_stat(data, "Дух")
    end = total_stat(data, "Выносливость")
    agi = total_stat(data, "Ловкость")

    data["mana_max"] = intel * 10
    data["hp_max"] = data["level"] * 20 + end * 10
    data["spell_power"] = intel / 5 / 100
    data["crit_chance"] = min(0.95, 0.05 + intel * 0.00005)
    data["mana_regen"] = round(spi * 0.5)
    data["control_resist"] = min(0.90, wis / 4 / 100)
    data["ritual_bonus"] = wis / 5 / 100
    data["fear_power"] = cha / 3 / 100
    data["initiative"] = round(agi / 2 + wis / 4)
    data["dodge"] = min(0.40, agi / 5 / 100)

def load_save():
    if SAVE_FILE.exists():
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            data = deepcopy(DEFAULT)
            # аккуратно мержим
            for k, v in saved.items():
                if k in data and isinstance(data[k], dict) and isinstance(v, dict):
                    data[k].update(v)
                else:
                    data[k] = v
            return data
        except Exception:
            pass
    return deepcopy(DEFAULT)

def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.data["combat_log"].insert(0, f"[{ts}] {msg}")
    st.session_state.data["combat_log"] = st.session_state.data["combat_log"][:60]

def calc_dmg(base, power, dual=False, soul_boost=False):
    dmg = round(base * (1 + power))
    if dual:
        dmg = round(dmg * 1.05)
    if soul_boost:
        dmg = round(dmg * 1.40)
    return dmg

# ===================== INIT =====================
if "data" not in st.session_state:
    st.session_state.data = load_save()
    recalc_derived(st.session_state.data)

data = st.session_state.data
recalc_derived(data)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("<div class='main-title' style='font-size:1.45rem'>✧ Калист</div>", unsafe_allow_html=True)
    st.caption(f"Ур. {data['level']} · {data['class']}")
    st.progress(min(data["hp_current"] / max(data["hp_max"], 1), 1.0), text=f"HP {data['hp_current']}/{data['hp_max']}")
    st.progress(min(data["mana_current"] / max(data["mana_max"], 1), 1.0), text=f"MP {data['mana_current']}/{data['mana_max']}")
    st.divider()

    page = st.radio(
        "Меню",
        ["Обзор", "Бой", "Экипировка", "Характеристики", "Инвентарь",
         "Заклинания", "Квесты", "Кубики", "Биография"],
        label_visibility="collapsed"
    )
    st.divider()
    if st.button("💾 Сохранить", use_container_width=True):
        save_data(data)
        st.success("Сохранено")
    if st.button("🔄 Сбросить всё", use_container_width=True):
        st.session_state.data = deepcopy(DEFAULT)
        recalc_derived(st.session_state.data)
        save_data(st.session_state.data)
        st.rerun()

# ===================== ОБЗОР =====================
if page == "Обзор":
    st.markdown(f"<div class='main-title'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{data['race']} · {data['class']} · Ур. {data['level']}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**❤️ Здоровье**")
        st.progress(min(data["hp_current"] / max(data["hp_max"], 1), 1.0), text=f"{data['hp_current']} / {data['hp_max']}")
    with c2:
        st.markdown("**💧 Мана**")
        st.progress(min(data["mana_current"] / max(data["mana_max"], 1), 1.0), text=f"{data['mana_current']} / {data['mana_max']}")

    st.markdown("<div class='section-h'>Ключевые параметры</div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Сила заклинаний", f"+{data['spell_power']*100:.0f}%")
    m2.metric("Броня", data["armor"])
    m3.metric("Инициатива", data["initiative"])
    m4.metric("Свободные очки", data["free_points"])

    st.markdown("<div class='section-h'>Характеристики</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, name in enumerate(["Сила", "Выносливость", "Ловкость", "Мудрость", "Интеллект", "Харизма", "Дух"]):
        cols[i % 4].metric(name, total_stat(data, name))

    st.markdown("<div class='section-h'>Опыт</div>", unsafe_allow_html=True)
    st.write(f"Текущий: **{data['xp']}** · До следующего уровня: **{data['xp_to_next']}**")
    x1, x2, x3 = st.columns([2, 1, 1])
    add_xp = x1.number_input("Добавить опыт", min_value=0, value=100, step=50)
    if x2.button("➕ XP"):
        data["xp"] += add_xp
        data["xp_to_next"] = max(0, data["xp_to_next"] - add_xp)
        log(f"+{add_xp} опыта")
        st.rerun()
    if x3.button("⬆ Уровень +1"):
        data["level"] += 1
        data["free_points"] += 4
        data["xp_to_next"] = data["level"] * 1000
        recalc_derived(data)
        log(f"Уровень {data['level']}! +4 очка")
        st.rerun()

# ===================== БОЙ =====================
elif page == "Бой":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Бой</div>", unsafe_allow_html=True)

    # Ресурсы
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("❤️ HP", f"{data['hp_current']}/{data['hp_max']}")
    r2.metric("💧 Мана", f"{data['mana_current']}/{data['mana_max']}")
    r3.metric("🛡 Броня", data["armor"])
    r4.metric("⚡ Иниц.", data["initiative"])

    # Урон / лечение / мана
    with st.expander("Получить урон / восстановить", expanded=False):
        d1, d2, d3, d4 = st.columns([2, 1, 2, 1])
        dmg_in = d1.number_input("Урон по мне", min_value=0, value=0, step=10)
        if d2.button("Нанести"):
            data["hp_current"] = max(0, data["hp_current"] - dmg_in)
            log(f"Получено {dmg_in} урона → HP {data['hp_current']}")
            st.rerun()
        heal_in = d3.number_input("Лечение", min_value=0, value=0, step=10)
        if d4.button("Вылечить"):
            data["hp_current"] = min(data["hp_max"], data["hp_current"] + heal_in)
            log(f"+{heal_in} HP")
            st.rerun()
        m1, m2, m3 = st.columns([2, 1, 1])
        mana_ch = m1.number_input("Мана (+/-)", value=0, step=50)
        if m2.button("Применить"):
            data["mana_current"] = max(0, min(data["mana_max"], data["mana_current"] + mana_ch))
            st.rerun()
        if m3.button("Полная мана"):
            data["mana_current"] = data["mana_max"]
            st.rerun()

    # Пепел / Тень
    st.markdown("<div class='section-h'>Пепел и Тень</div>", unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        st.progress(data["pepel"] / 5, text=f"🔥 Пепел {data['pepel']}/5")
        b1, b2 = st.columns(2)
        if b1.button("+1 Пепел"):
            data["pepel"] = min(5, data["pepel"] + 1)
            st.rerun()
        if b2.button("Активировать", disabled=data["pepel"] < 5, key="act_pepel"):
            data["pepel"] = 0
            log("Пепел активирован → следующее огненное игнорирует 30% сопр. огню")
            st.rerun()
    with p2:
        st.progress(data["ten"] / 5, text=f"🌑 Тень {data['ten']}/5")
        b1, b2 = st.columns(2)
        if b1.button("+1 Тень"):
            data["ten"] = min(5, data["ten"] + 1)
            st.rerun()
        if b2.button("Активировать", disabled=data["ten"] < 5, key="act_ten"):
            data["ten"] = 0
            log("Тень активирована → невидимость 1 ход или +20% сопротивления")
            st.rerun()

    # Пассивки
    st.markdown("<div class='section-h'>Особые умения</div>", unsafe_allow_html=True)
    for key, p in data["passives"].items():
        cols = st.columns([3, 1.2])
        with cols[0]:
            status = "✅ использовано" if p["used"] else "🟢 доступно"
            st.markdown(f"**{p['name']}** — {status}")
            st.caption(p["desc"])
        with cols[1]:
            if not p["used"]:
                if st.button("Использовать", key=f"pas_{key}"):
                    p["used"] = True
                    if key == "ritual_black_flame":
                        data["soul_flame_boost"] = True
                        log("Ритуал Чёрного Пламени: следующее Пламя души усилено")
                    elif key == "cold_calculation":
                        data["crit_boost_active"] = True
                        log("Холодный расчёт: +10% крита до конца боя")
                    else:
                        log(f"Использовано: {p['name']}")
                    st.rerun()

    # Отдых
    st.markdown("<div class='section-h'>Отдых</div>", unsafe_allow_html=True)
    o1, o2 = st.columns(2)
    if o1.button("🌙 Короткий отдых"):
        data["mana_current"] = min(data["mana_max"], data["mana_current"] + data["mana_regen"] * 3)
        data["concentration"] = ""
        log("Короткий отдых: мана +реген×3, концентрация сброшена")
        st.rerun()
    if o2.button("🌅 Длинный отдых"):
        data["hp_current"] = data["hp_max"]
        data["mana_current"] = data["mana_max"]
        data["pepel"] = 0
        data["ten"] = 0
        data["buffs"] = ""
        data["debuffs"] = ""
        data["concentration"] = ""
        data["last_school"] = None
        data["soul_flame_boost"] = False
        data["crit_boost_active"] = False
        for p in data["passives"].values():
            p["used"] = False
        log("Длинный отдых: всё восстановлено, пассивки сброшены")
        st.rerun()

    st.divider()

    # ===== ВРАГИ =====
    st.markdown("<div class='section-h'>Враги</div>", unsafe_allow_html=True)

    if not data["enemies"]:
        st.caption("Пока нет врагов. Добавь ниже.")
    else:
        for i, enemy in enumerate(data["enemies"]):
            with st.container():
                c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.2, 0.8])
                with c1:
                    st.markdown(f"**{enemy['name']}**")
                    st.progress(min(enemy["hp"] / max(enemy["hp_max"], 1), 1.0),
                                text=f"HP {enemy['hp']}/{enemy['hp_max']}")
                    if enemy.get("statuses"):
                        st.caption(f"Статусы: {enemy['statuses']}")
                with c2:
                    dmg_e = st.number_input("Урон", min_value=0, value=0, step=10, key=f"edmg_{enemy['id']}")
                with c3:
                    if st.button("Ударить", key=f"ehit_{enemy['id']}"):
                        enemy["hp"] = max(0, enemy["hp"] - dmg_e)
                        log(f"{enemy['name']} получил {dmg_e} урона → {enemy['hp']} HP")
                        if enemy["hp"] <= 0:
                            log(f"{enemy['name']} повержен!")
                        st.rerun()
                with c4:
                    if st.button("🗑", key=f"edel_{enemy['id']}"):
                        data["enemies"].pop(i)
                        st.rerun()
                enemy["statuses"] = st.text_input("Статусы врага", value=enemy.get("statuses", ""), key=f"est_{enemy['id']}", label_visibility="collapsed")

    with st.form("add_enemy"):
        st.markdown("**Добавить врага**")
        e1, e2, e3 = st.columns(3)
        ename = e1.text_input("Имя", value="Враг")
        ehp = e2.number_input("HP", min_value=1, value=100)
        earm = e3.number_input("Броня", min_value=0, value=0)
        if st.form_submit_button("Добавить"):
            data["enemies"].append({
                "id": data["next_enemy_id"],
                "name": ename,
                "hp": ehp,
                "hp_max": ehp,
                "armor": earm,
                "statuses": ""
            })
            data["next_enemy_id"] += 1
            log(f"В бой вступает: {ename} ({ehp} HP)")
            st.rerun()

    st.divider()

    # ===== БЫСТРЫЙ КАСТ =====
    st.markdown("<div class='section-h'>Быстрый каст</div>", unsafe_allow_html=True)
    if data.get("last_school"):
        st.caption(f"Последняя школа: **{data['last_school']}** → Двойное пламя активно")
    if data.get("soul_flame_boost"):
        st.warning("Ритуал активен: следующее «Пламя души» усилено на +40%")

    # Выбор цели для урона
    enemy_names = ["— по площади / без цели —"] + [e["name"] for e in data["enemies"] if e["hp"] > 0]
    target = st.selectbox("Цель заклинания", enemy_names)

    for spell in data["spells"]:
        dual = bool(data.get("last_school") and data["last_school"] != spell["school"]
                    and ("Огонь" in spell["school"] or "Тьма" in spell["school"]))
        soul = data.get("soul_flame_boost") and spell["name"] == "Пламя души"
        dmg = calc_dmg(spell["base"], data["spell_power"], dual, soul) if spell["base"] else 0

        cols = st.columns([3.0, 0.9, 0.9, 1.1])
        with cols[0]:
            icon = "🔥" if "Огонь" in spell["school"] else "🌑"
            st.markdown(f"**{icon} {spell['name']}**")
            st.caption(f"{spell['school']} · {spell['desc']}")
        with cols[1]:
            st.write(f"**{dmg if dmg else '—'}**")
            extras = []
            if dual: extras.append("+5%")
            if soul: extras.append("+40%")
            if extras: st.caption(" ".join(extras))
        with cols[2]:
            st.write(f"{spell['mana']} MP")
        with cols[3]:
            can = data["mana_current"] >= spell["mana"]
            if st.button("Каст", key=f"cast_{spell['id']}", disabled=not can):
                data["mana_current"] -= spell["mana"]
                data["last_school"] = spell["school"]
                if spell.get("gives") in ("pepel", "both"):
                    data["pepel"] = min(5, data["pepel"] + 1)
                if spell.get("gives") in ("ten", "both"):
                    data["ten"] = min(5, data["ten"] + 1)
                if soul:
                    data["soul_flame_boost"] = False
                msg = f"«{spell['name']}» → {dmg} урона (−{spell['mana']} MP)"
                if dual: msg += " [Двойное пламя]"
                if soul: msg += " [Ритуал]"
                # урон по цели
                if target != "— по площади / без цели —" and dmg > 0:
                    for e in data["enemies"]:
                        if e["name"] == target and e["hp"] > 0:
                            e["hp"] = max(0, e["hp"] - dmg)
                            msg += f" → {target} ({e['hp']} HP)"
                            if e["hp"] <= 0:
                                msg += " [повержен]"
                            break
                log(msg)
                st.rerun()

    st.divider()
    st.markdown("<div class='section-h'>Состояния и лог</div>", unsafe_allow_html=True)
    data["buffs"] = st.text_input("Баффы", value=data.get("buffs", ""))
    data["debuffs"] = st.text_input("Дебаффы", value=data.get("debuffs", ""))
    data["concentration"] = st.text_input("Концентрация", value=data.get("concentration", ""))

    for entry in data["combat_log"][:15]:
        st.text(entry)
    if st.button("Очистить лог"):
        data["combat_log"] = []
        st.rerun()

# ===================== ЭКИПИРОВКА =====================
elif page == "Экипировка":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Экипировка</div>", unsafe_allow_html=True)
    st.caption("Меняй предметы и бонусы. После изменений нажми «Пересчитать».")

    for slot, item in data["equipment"].items():
        with st.expander(f"{'🔹' if item.get('name') else '▫️'} {slot}: {item.get('name') or 'пусто'}"):
            item["name"] = st.text_input("Название", value=item.get("name", ""), key=f"n_{slot}")
            item["desc"] = st.text_input("Описание", value=item.get("desc", ""), key=f"d_{slot}")
            c1, c2, c3, c4 = st.columns(4)
            item["armor"] = c1.number_input("Броня", 0, value=int(item.get("armor", 0)), key=f"a_{slot}")
            item["attack"] = c2.number_input("Атака", 0, value=int(item.get("attack", 0)), key=f"at_{slot}")
            item["int"] = c3.number_input("Интеллект", 0, value=int(item.get("int", 0)), key=f"i_{slot}")
            item["wis"] = c4.number_input("Мудрость", 0, value=int(item.get("wis", 0)), key=f"w_{slot}")
            c5, c6, c7 = st.columns(3)
            item["spi"] = c5.number_input("Дух", 0, value=int(item.get("spi", 0)), key=f"s_{slot}")
            item["fire"] = c6.number_input("Огонь", 0, value=int(item.get("fire", 0)), key=f"f_{slot}")
            item["dark"] = c7.number_input("Тьма", 0, value=int(item.get("dark", 0)), key=f"dk_{slot}")

    if st.button("🔄 Пересчитать бонусы", type="primary"):
        recalc_equip_bonuses(data)
        recalc_derived(data)
        st.success(f"Броня: {data['armor']} · Физ. атака: {data['phys_attack']} · Инт от шмота: {data['equip_bonuses']['Интеллект']}")
        st.rerun()

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Броня", data["armor"])
    t2.metric("Физ. атака", data["phys_attack"])
    t3.metric("Инт от шмота", data["equip_bonuses"].get("Интеллект", 0))
    t4.metric("Дух от шмота", data["equip_bonuses"].get("Дух", 0))

# ===================== ХАРАКТЕРИСТИКИ =====================
elif page == "Характеристики":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Характеристики</div>", unsafe_allow_html=True)
    st.info(f"Свободные очки: **{data['free_points']}** · Уровень: **{data['level']}**")

    for name in ["Сила", "Выносливость", "Ловкость", "Мудрость", "Интеллект", "Харизма", "Дух"]:
        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].write(f"**{name}**")
        cols[1].write(f"База {data['base_stats'][name]}")
        cols[2].write(f"Экип +{data['equip_bonuses'][name]}")
        cols[3].write(f"**Итого {total_stat(data, name)}**")
        if cols[4].button("＋", key=f"up_{name}", disabled=data["free_points"] <= 0):
            data["base_stats"][name] += 1
            data["free_points"] -= 1
            recalc_derived(data)
            log(f"+1 {name}")
            st.rerun()

    st.divider()
    st.markdown("<div class='section-h'>Производные</div>", unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    d1.metric("Сила заклинаний", f"+{data['spell_power']*100:.0f}%")
    d1.metric("Реген маны", data["mana_regen"])
    d2.metric("Сопр. контролю", f"{data['control_resist']*100:.1f}%")
    d2.metric("Бонус ритуалов", f"+{data['ritual_bonus']*100:.0f}%")
    d3.metric("Сила страха", f"{data['fear_power']*100:.1f}%")
    d3.metric("Инициатива", data["initiative"])

# ===================== ИНВЕНТАРЬ =====================
elif page == "Инвентарь":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Инвентарь</div>", unsafe_allow_html=True)
    g, s, c = st.columns(3)
    data["gold"] = g.number_input("Золото", 0, value=data["gold"])
    data["silver"] = s.number_input("Серебро", 0, value=data["silver"])
    data["copper"] = c.number_input("Медь", 0, value=data["copper"])

    st.divider()
    for i, item in enumerate(data["inventory"]):
        cols = st.columns([3, 1, 1, 1])
        cols[0].markdown(f"**{item['name']}**  \n{item['type']} · {item['desc']}")
        item["qty"] = cols[1].number_input("Кол", 0, value=item["qty"], key=f"q{i}", label_visibility="collapsed")
        with cols[2]:
            if item["type"] == "Расходник" and item["qty"] > 0:
                if "мана" in item["name"].lower() and st.button("Выпить", key=f"u{i}"):
                    item["qty"] -= 1
                    data["mana_current"] = min(data["mana_max"], data["mana_current"] + 400)
                    log(f"Выпито {item['name']} (+400 MP)")
                    st.rerun()
                elif ("лечен" in item["name"].lower() or "здоров" in item["name"].lower()) and st.button("Выпить", key=f"u{i}"):
                    item["qty"] -= 1
                    data["hp_current"] = min(data["hp_max"], data["hp_current"] + 250)
                    log(f"Выпито {item['name']} (+250 HP)")
                    st.rerun()
        if cols[3].button("🗑", key=f"di{i}"):
            data["inventory"].pop(i)
            st.rerun()

    with st.form("add_item"):
        st.markdown("**Добавить предмет**")
        n1, n2 = st.columns(2)
        nn = n1.text_input("Название")
        nt = n2.selectbox("Тип", ["Расходник", "Реагент", "Свиток", "Оружие", "Броня", "Реликвия", "Инструмент", "Прочее"])
        nq = st.number_input("Кол-во", 1, value=1)
        nd = st.text_input("Описание")
        if st.form_submit_button("Добавить") and nn.strip():
            data["inventory"].append({"name": nn.strip(), "type": nt, "qty": nq, "desc": nd.strip()})
            st.rerun()

# ===================== ЗАКЛИНАНИЯ =====================
elif page == "Заклинания":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Заклинания</div>", unsafe_allow_html=True)
    st.caption("Редактирование. Каст — на странице «Бой».")

    for i, spell in enumerate(data["spells"]):
        with st.expander(f"{spell['name']} ({spell['school']})"):
            spell["name"] = st.text_input("Название", spell["name"], key=f"sn{i}")
            c1, c2, c3 = st.columns(3)
            spell["base"] = c1.number_input("Урон", value=spell["base"], key=f"sb{i}")
            spell["mana"] = c2.number_input("Мана", value=spell["mana"], key=f"sm{i}")
            spell["range"] = c3.text_input("Дистанция", spell["range"], key=f"sr{i}")
            spell["school"] = st.selectbox("Школа", ["Огонь", "Тьма", "Огонь+Тьма"],
                index=["Огонь", "Тьма", "Огонь+Тьма"].index(spell["school"]) if spell["school"] in ["Огонь", "Тьма", "Огонь+Тьма"] else 0, key=f"ss{i}")
            spell["desc"] = st.text_input("Описание", spell["desc"], key=f"sd{i}")
            if st.button("Удалить", key=f"sdel{i}"):
                data["spells"].pop(i)
                st.rerun()

    with st.form("add_spell"):
        st.markdown("**Новое заклинание**")
        sn = st.text_input("Название")
        c1, c2, c3 = st.columns(3)
        sb = c1.number_input("Урон", 0, value=50)
        sm = c2.number_input("Мана", 0, value=30)
        sr = c3.text_input("Дистанция", value="Средняя")
        ss = st.selectbox("Школа", ["Огонь", "Тьма", "Огонь+Тьма"])
        sd = st.text_input("Описание")
        sg = st.selectbox("Даёт", [None, "pepel", "ten", "both"], format_func=lambda x: {None: "Ничего", "pepel": "Пепел", "ten": "Тень", "both": "Оба"}[x])
        if st.form_submit_button("Добавить") and sn.strip():
            nid = max([s["id"] for s in data["spells"]], default=0) + 1
            data["spells"].append({"id": nid, "name": sn.strip(), "base": sb, "mana": sm, "range": sr, "school": ss, "desc": sd, "gives": sg})
            st.rerun()

# ===================== КВЕСТЫ =====================
elif page == "Квесты":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Квесты и заметки</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-h'>Активные задания</div>", unsafe_allow_html=True)
    for i, q in enumerate(data["quests"]):
        with st.expander(f"{q['name']} — {q['status']}"):
            q["name"] = st.text_input("Название", q["name"], key=f"qn{i}")
            q["status"] = st.selectbox("Статус", ["Активен", "В процессе", "Ожидание", "Выполнен", "Провален"],
                                       index=["Активен", "В процессе", "Ожидание", "Выполнен", "Провален"].index(q["status"]) if q["status"] in ["Активен", "В процессе", "Ожидание", "Выполнен", "Провален"] else 0,
                                       key=f"qs{i}")
            q["desc"] = st.text_area("Описание", q["desc"], key=f"qd{i}")
            if st.button("Удалить квест", key=f"qdel{i}"):
                data["quests"].pop(i)
                st.rerun()

    with st.form("add_quest"):
        st.markdown("**Новый квест**")
        qn = st.text_input("Название")
        qs = st.selectbox("Статус", ["Активен", "В процессе", "Ожидание"])
        qd = st.text_area("Описание")
        if st.form_submit_button("Добавить") and qn.strip():
            nid = max([q["id"] for q in data["quests"]], default=0) + 1
            data["quests"].append({"id": nid, "name": qn.strip(), "status": qs, "desc": qd})
            st.rerun()

    st.divider()
    st.markdown("<div class='section-h'>Личные заметки</div>", unsafe_allow_html=True)
    data["notes"] = st.text_area("Заметки", value=data.get("notes", ""), height=150)

# ===================== КУБИКИ =====================
elif page == "Кубики":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Кубики</div>", unsafe_allow_html=True)
    dice = [4, 6, 8, 10, 12, 20, 100]
    cols = st.columns(len(dice))
    for i, s in enumerate(dice):
        with cols[i]:
            if st.button(f"d{s}", key=f"d{s}", use_container_width=True):
                res = random.randint(1, s)
                st.session_state[f"r{s}"] = res
                log(f"d{s}: {res}")
            if f"r{s}" in st.session_state:
                st.markdown(f"<h2 style='text-align:center;color:#E8DAEF'>{st.session_state[f'r{s}']}</h2>", unsafe_allow_html=True)

    st.divider()
    c1, c2, c3 = st.columns(3)
    sides = c1.number_input("Грани", 2, 1000, 20)
    num = c2.number_input("Кол-во", 1, 20, 1)
    mod = c3.number_input("Модификатор", value=0)
    if st.button("Бросить", type="primary"):
        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls) + mod
        st.success(f"**{total}** ({' + '.join(map(str, rolls))}{f' {mod:+d}' if mod else ''})")
        log(f"{num}d{sides}{mod:+d if mod else ''}: {total}")

# ===================== БИОГРАФИЯ =====================
elif page == "Биография":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Биография</div>", unsafe_allow_html=True)
    st.markdown("""
### Внешность
Высокая (≈178 см), стройная. Кожа глубокой ночи. Волосы **чёрные как ночь**. Глаза ярко-фиолетовые. Шрам на левой щеке.

### Характер
Холодная, сдержанная, наблюдательная. Сухой юмор. Амбициозна ради понимания запретных сил. Боится потери контроля.

### Предыстория
Дом Клиф. Мать Ильраэль пыталась создать «пламя бездны». Ритуал уничтожил дом. Калист спасена матерью. Странствует, продолжает исследования, носит Фамильный Амулет.

### Цели
Создать «Пламя Души» · Восстановить знания дома · Равновесие огня и тьмы

### Страхи
Потеря контроля · Одиночество · Светлые маги · Привязанность
    """)

# Автосохранение
save_data(data)
