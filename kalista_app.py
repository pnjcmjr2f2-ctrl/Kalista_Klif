#!/usr/bin/env python3
"""
Калист Клиф — Интерактивный лист персонажа
Полноценный помощник для игры
"""

import streamlit as st
import json
import os
import random
from datetime import datetime
from pathlib import Path

# ===================== КОНФИГ =====================
SAVE_FILE = Path(__file__).parent / "kalista_save.json"
PAGE_TITLE = "✧ Калист Клиф ✧"
PAGE_ICON = "🔥"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== СТИЛИ =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Quattrocento+Sans:wght@400;700&display=swap');
    
    .main-title {
        font-family: 'Cinzel', serif;
        font-size: 2.4rem;
        color: #E8DAEF;
        text-align: center;
        text-shadow: 0 0 12px #4A235A, 0 0 24px #7D3C98;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-family: 'Quattrocento Sans', sans-serif;
        text-align: center;
        color: #BB8FCE;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        background: linear-gradient(145deg, #2C003E, #1A0026);
        border: 1px solid #7D3C98;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
        box-shadow: 0 4px 12px rgba(74, 35, 90, 0.4);
    }
    .stat-label {
        color: #BB8FCE;
        font-size: 0.85rem;
        margin-bottom: 2px;
    }
    .stat-value {
        color: #F5EEF8;
        font-size: 1.4rem;
        font-weight: 700;
    }
    .section-header {
        font-family: 'Cinzel', serif;
        color: #D7BDE2;
        font-size: 1.3rem;
        border-bottom: 2px solid #7D3C98;
        padding-bottom: 4px;
        margin: 1.2rem 0 0.8rem 0;
    }
    .spell-card {
        background: #1C0029;
        border-left: 4px solid #922B21;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .hp-bar > div > div > div {
        background: linear-gradient(90deg, #922B21, #C0392B) !important;
    }
    .mana-bar > div > div > div {
        background: linear-gradient(90deg, #1A5276, #5DADE2) !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
</style>
""", unsafe_allow_html=True)

# ===================== ДАННЫЕ ПЕРСОНАЖА (базовые) =====================
DEFAULT_DATA = {
    "name": "Калист Клиф",
    "race": "Тёмный эльф (Дроу)",
    "class": "Маг огня и тьмы",
    "level": 21,
    "xp": 18450,
    "xp_to_next": 2150,
    
    # Текущие ресурсы
    "hp_current": 420,
    "hp_max": 820,
    "mana_current": 2950,
    "mana_max": 2950,
    
    # Базовые характеристики
    "stats": {
        "Сила": 10,
        "Выносливость": 40,
        "Ловкость": 14,
        "Мудрость": 95,
        "Интеллект": 295,
        "Харизма": 10,
        "Дух": 210,
    },
    
    # Производные (считаются)
    "spell_power": 0.59,          # 59%
    "crit_chance": 0.06475,
    "mana_regen": 105,
    "control_resist": 0.2375,     # ~23.75%
    "ritual_bonus": 0.19,
    "fear_power": 0.0333,
    "armor": 535,
    "phys_absorb": 0.4007,
    "phys_attack": 55,
    "initiative": 31,             # 14/2 + 95/4 ≈ 7+23.75
    "dodge": 0.028,
    
    # Сопротивления
    "resists": {
        "Огонь": 75,
        "Земля": 5,
        "Вода": 10,
        "Воздух": 5,
        "Тьма": 95,
        "Свет": 15,
    },
    
    # Боевой трекер
    "pepel": 0,
    "ten": 0,
    "buffs": "",
    "debuffs": "",
    "concentration": "",
    "backlash_risk": "Низкий",
    
    # Валюта
    "gold": 84,
    "silver": 34,
    "copper": 0,
    
    # Инвентарь
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
    
    # Заклинания
    "spells": [
        {"id": 1, "name": "Искровой заряд", "base": 35, "mana": 18, "range": "Ближняя", "school": "Огонь",
         "desc": "Быстрый сгусток огня. Низкая стоимость."},
        {"id": 2, "name": "Огненный шар", "base": 80, "mana": 35, "range": "Средняя", "school": "Огонь",
         "desc": "Классический шар пламени. Хороший урон."},
        {"id": 3, "name": "Язык пламени", "base": 55, "mana": 28, "range": "Ближняя", "school": "Огонь",
         "desc": "Полоса огня перед заклинателем."},
        {"id": 4, "name": "Пепел и тлен", "base": 40, "mana": 22, "range": "Средняя", "school": "Огонь",
         "desc": "DoT: поджигает цель на 3 хода. +1 Пепел"},
        {"id": 5, "name": "Адское дыхание", "base": 120, "mana": 55, "range": "Ближняя", "school": "Огонь",
         "desc": "Мощный конус огня. Высокий расход. +1 Пепел"},
        {"id": 6, "name": "Теневой укол", "base": 45, "mana": 20, "range": "Ближняя", "school": "Тьма",
         "desc": "Быстрый тёмный шип. Игнорирует часть брони. +1 Тень"},
        {"id": 7, "name": "Покров тьмы", "base": 0, "mana": 30, "range": "На себя", "school": "Тьма",
         "desc": "Щит: поглощает урон, +10% сопр. тьме."},
        {"id": 8, "name": "Проклятие слабости", "base": 25, "mana": 25, "range": "Средняя", "school": "Тьма",
         "desc": "Снижает силу и атаку цели на 3 хода. +1 Тень"},
        {"id": 9, "name": "Разряд бездны", "base": 95, "mana": 45, "range": "Дальняя", "school": "Тьма",
         "desc": "Мощный тёмный разряд. Шанс страха. +1 Тень"},
        {"id": 10, "name": "Пламя души", "base": 150, "mana": 70, "range": "Средняя", "school": "Огонь+Тьма",
         "desc": "Ультиматив: огонь, питаемый тьмой. Долгий каст."},
    ],
    
    "combat_log": [],
    "last_school": None,  # для пассивки Двойное пламя
}

# ===================== УТИЛИТЫ =====================
def calc_spell_damage(base: int, spell_power: float) -> int:
    return round(base * (1 + spell_power))

def load_save():
    if SAVE_FILE.exists():
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Мержим с дефолтом на случай новых полей
            merged = DEFAULT_DATA.copy()
            merged.update(data)
            return merged
        except Exception:
            return DEFAULT_DATA.copy()
    return DEFAULT_DATA.copy()

def save_data(data: dict):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.data["combat_log"].insert(0, f"[{ts}] {msg}")
    st.session_state.data["combat_log"] = st.session_state.data["combat_log"][:40]

def roll_dice(sides: int) -> int:
    return random.randint(1, sides)

# ===================== ИНИЦИАЛИЗАЦИЯ =====================
if "data" not in st.session_state:
    st.session_state.data = load_save()

data = st.session_state.data

# ===================== САЙДБАР =====================
with st.sidebar:
    st.markdown(f"<div class='main-title' style='font-size:1.6rem'>✧ Калист</div>", unsafe_allow_html=True)
    st.caption("Маг огня и тьмы · Ур. 21")
    
    st.divider()
    
    page = st.radio(
        "Навигация",
        ["Обзор", "Заклинания", "Бой", "Инвентарь", "Кубики", "Биография"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if st.button("💾 Сохранить", use_container_width=True):
        save_data(data)
        st.success("Сохранено!")
    
    if st.button("🔄 Сбросить к исходному", use_container_width=True):
        st.session_state.data = DEFAULT_DATA.copy()
        save_data(st.session_state.data)
        st.rerun()
    
    st.caption("Состояние сохраняется в kalista_save.json")

# ===================== СТРАНИЦА: ОБЗОР =====================
if page == "Обзор":
    st.markdown(f"<div class='main-title'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{data['race']} · {data['class']} · Уровень {data['level']}</div>", unsafe_allow_html=True)
    
    # HP / Mana
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**❤️ Здоровье**")
        hp_pct = data["hp_current"] / data["hp_max"]
        st.progress(min(hp_pct, 1.0), text=f"{data['hp_current']} / {data['hp_max']}")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("−50 HP", key="hp_m50"):
                data["hp_current"] = max(0, data["hp_current"] - 50)
                add_log("Получено 50 урона")
                st.rerun()
        with c2:
            if st.button("+50 HP", key="hp_p50"):
                data["hp_current"] = min(data["hp_max"], data["hp_current"] + 50)
                add_log("Восстановлено 50 HP")
                st.rerun()
        with c3:
            if st.button("Полное", key="hp_full"):
                data["hp_current"] = data["hp_max"]
                add_log("HP полностью восстановлено")
                st.rerun()
    
    with col2:
        st.markdown("**💧 Мана**")
        mana_pct = data["mana_current"] / data["mana_max"]
        st.progress(min(mana_pct, 1.0), text=f"{data['mana_current']} / {data['mana_max']}")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("−100 MP", key="mp_m100"):
                data["mana_current"] = max(0, data["mana_current"] - 100)
                st.rerun()
        with c2:
            if st.button("+105 MP (реген)", key="mp_regen"):
                data["mana_current"] = min(data["mana_max"], data["mana_current"] + data["mana_regen"])
                add_log(f"Регенерация маны +{data['mana_regen']}")
                st.rerun()
        with c3:
            if st.button("Полная", key="mp_full"):
                data["mana_current"] = data["mana_max"]
                add_log("Мана полностью восстановлена")
                st.rerun()
    
    st.divider()
    
    # Основные статы
    st.markdown("<div class='section-header'>Характеристики</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    stat_list = list(data["stats"].items())
    for i, (name, val) in enumerate(stat_list):
        with cols[i % 4]:
            st.metric(name, val)
    
    st.markdown("<div class='section-header'>Магические параметры</div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Сила заклинаний", f"+{data['spell_power']*100:.0f}%")
        st.metric("Сопр. контролю", f"{data['control_resist']*100:.1f}%")
    with m2:
        st.metric("Шанс крита", f"{data['crit_chance']*100:.2f}%")
        st.metric("Бонус ритуалов", f"+{data['ritual_bonus']*100:.0f}%")
    with m3:
        st.metric("Реген маны", f"{data['mana_regen']}/тик")
        st.metric("Сила страха", f"{data['fear_power']*100:.1f}%")
    
    st.markdown("<div class='section-header'>Боевые характеристики</div>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.metric("Броня", data["armor"])
        st.metric("Поглощение", f"{data['phys_absorb']*100:.1f}%")
    with b2:
        st.metric("Физ. атака", data["phys_attack"])
        st.metric("Инициатива", data["initiative"])
    with b3:
        st.metric("Уклонение", f"{data['dodge']*100:.1f}%")
    with b4:
        st.metric("Опыт", f"{data['xp']}")
        st.caption(f"до следующего: {data['xp_to_next']}")
    
    st.markdown("<div class='section-header'>Сопротивления стихиям</div>", unsafe_allow_html=True)
    rcols = st.columns(6)
    for i, (el, val) in enumerate(data["resists"].items()):
        with rcols[i]:
            color = "#E74C3C" if el == "Огонь" else "#8E44AD" if el == "Тьма" else "#5DADE2"
            st.markdown(f"**{el}**")
            st.markdown(f"<span style='color:{color};font-size:1.3rem;font-weight:700'>{val}</span>", unsafe_allow_html=True)

# ===================== СТРАНИЦА: ЗАКЛИНАНИЯ =====================
elif page == "Заклинания":
    st.markdown("<div class='main-title' style='font-size:1.8rem'>Заклинания</div>", unsafe_allow_html=True)
    st.caption(f"Сила заклинаний: +{data['spell_power']*100:.0f}% · Мана: {data['mana_current']}/{data['mana_max']}")
    
    # Пассивка Двойное пламя
    if data.get("last_school"):
        st.info(f"🔥 Последняя школа: **{data['last_school']}** → следующее заклинание другой школы получит +5% урона")
    
    for spell in data["spells"]:
        dmg = calc_spell_damage(spell["base"], data["spell_power"])
        # Бонус двойного пламени
        dual = False
        if data.get("last_school") and data["last_school"] != spell["school"] and spell["school"] in ("Огонь", "Тьма", "Огонь+Тьма"):
            if "Огонь" in spell["school"] or "Тьма" in spell["school"]:
                dmg = round(dmg * 1.05)
                dual = True
        
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                school_icon = "🔥" if "Огонь" in spell["school"] else "🌑"
                st.markdown(f"**{school_icon} {spell['name']}** · {spell['school']} · {spell['range']}")
                st.caption(spell["desc"])
            with c2:
                st.metric("Урон", dmg if spell["base"] > 0 else "—")
                if dual:
                    st.caption("+5% двойное пламя")
            with c3:
                st.metric("Мана", spell["mana"])
                can_cast = data["mana_current"] >= spell["mana"]
                if st.button("Каст", key=f"cast_{spell['id']}", disabled=not can_cast, type="primary"):
                    data["mana_current"] -= spell["mana"]
                    data["last_school"] = spell["school"]
                    
                    # Пепел / Тень
                    if "Огонь" in spell["school"] and spell["base"] > 0:
                        data["pepel"] = min(5, data["pepel"] + 1)
                    if "Тьма" in spell["school"] and spell["id"] != 7:
                        data["ten"] = min(5, data["ten"] + 1)
                    
                    log_msg = f"Каст «{spell['name']}» → {dmg} урона (−{spell['mana']} маны)"
                    if dual:
                        log_msg += " [Двойное пламя]"
                    add_log(log_msg)
                    st.rerun()
            st.divider()

# ===================== СТРАНИЦА: БОЙ =====================
elif page == "Бой":
    st.markdown("<div class='main-title' style='font-size:1.8rem'>Боевой трекер</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Инициатива", data["initiative"])
    with c2:
        st.metric("❤️ HP", f"{data['hp_current']}/{data['hp_max']}")
    with c3:
        st.metric("💧 Мана", f"{data['mana_current']}/{data['mana_max']}")
    
    st.divider()
    
    # Пепел и Тень
    st.markdown("### 🔥 Пепел и 🌑 Тень")
    p1, p2 = st.columns(2)
    with p1:
        st.progress(data["pepel"] / 5, text=f"Пепел: {data['pepel']} / 5")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("+1 Пепел"):
                data["pepel"] = min(5, data["pepel"] + 1)
                st.rerun()
        with b2:
            if st.button("Сбросить Пепел", disabled=data["pepel"] < 5):
                data["pepel"] = 0
                add_log("Активирован Пепел: следующее огненное заклинание игнорирует 30% сопротивления огню")
                st.rerun()
        if data["pepel"] >= 5:
            st.success("Готово к активации! Следующее огненное заклинание игнорирует 30% сопр. огню")
    
    with p2:
        st.progress(data["ten"] / 5, text=f"Тень: {data['ten']} / 5")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("+1 Тень"):
                data["ten"] = min(5, data["ten"] + 1)
                st.rerun()
        with b2:
            if st.button("Сбросить Тень", disabled=data["ten"] < 5):
                data["ten"] = 0
                add_log("Активирована Тень: невидимость на 1 ход ИЛИ +20% сопротивления на 2 хода")
                st.rerun()
        if data["ten"] >= 5:
            st.success("Готово! Невидимость 1 ход или +20% сопротивления на 2 хода")
    
    st.divider()
    
    # Баффы / дебаффы
    st.markdown("### Состояния")
    data["buffs"] = st.text_area("Баффы", value=data.get("buffs", ""), height=80)
    data["debuffs"] = st.text_area("Дебаффы", value=data.get("debuffs", ""), height=80)
    data["concentration"] = st.text_input("Концентрация", value=data.get("concentration", ""))
    
    st.divider()
    
    # Лог
    st.markdown("### Лог боя")
    if data["combat_log"]:
        for entry in data["combat_log"][:15]:
            st.text(entry)
        if st.button("Очистить лог"):
            data["combat_log"] = []
            st.rerun()
    else:
        st.caption("Пока пусто — кастуйте заклинания или получайте урон")

# ===================== СТРАНИЦА: ИНВЕНТАРЬ =====================
elif page == "Инвентарь":
    st.markdown("<div class='main-title' style='font-size:1.8rem'>Инвентарь и валюта</div>", unsafe_allow_html=True)
    
    # Валюта
    st.markdown("### 💰 Валюта")
    g, s, c = st.columns(3)
    with g:
        data["gold"] = st.number_input("Золото", min_value=0, value=data["gold"], step=1)
    with s:
        data["silver"] = st.number_input("Серебро", min_value=0, value=data["silver"], step=1)
    with c:
        data["copper"] = st.number_input("Медь", min_value=0, value=data["copper"], step=1)
    
    st.divider()
    
    st.markdown("### 🎒 Сумка")
    for i, item in enumerate(data["inventory"]):
        cols = st.columns([3, 1, 1, 2])
        with cols[0]:
            st.markdown(f"**{item['name']}**")
            st.caption(item["desc"])
        with cols[1]:
            st.caption(item["type"])
        with cols[2]:
            new_qty = st.number_input("Кол-во", min_value=0, value=item["qty"], key=f"qty_{i}", label_visibility="collapsed")
            item["qty"] = new_qty
        with cols[3]:
            if item["type"] == "Расходник" and item["qty"] > 0:
                if "мана" in item["name"].lower():
                    if st.button("Выпить", key=f"use_{i}"):
                        item["qty"] -= 1
                        data["mana_current"] = min(data["mana_max"], data["mana_current"] + 400)
                        add_log(f"Использовано: {item['name']} (+400 маны)")
                        st.rerun()
                elif "лечен" in item["name"].lower():
                    if st.button("Выпить", key=f"use_{i}"):
                        item["qty"] -= 1
                        data["hp_current"] = min(data["hp_max"], data["hp_current"] + 250)
                        add_log(f"Использовано: {item['name']} (+250 HP)")
                        st.rerun()

# ===================== СТРАНИЦА: КУБИКИ =====================
elif page == "Кубики":
    st.markdown("<div class='main-title' style='font-size:1.8rem'>Кубики</div>", unsafe_allow_html=True)
    
    dice_types = [4, 6, 8, 10, 12, 20, 100]
    cols = st.columns(len(dice_types))
    
    for i, sides in enumerate(dice_types):
        with cols[i]:
            if st.button(f"d{sides}", key=f"dice_{sides}", use_container_width=True):
                result = roll_dice(sides)
                st.session_state[f"last_roll_{sides}"] = result
                add_log(f"Бросок d{sides}: **{result}**")
            
            if f"last_roll_{sides}" in st.session_state:
                st.markdown(f"<div style='text-align:center;font-size:2rem;color:#E8DAEF'>{st.session_state[f'last_roll_{sides}']}</div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### Свой бросок")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        custom_sides = st.number_input("Грани", min_value=2, max_value=1000, value=20)
    with c2:
        num_dice = st.number_input("Количество", min_value=1, max_value=20, value=1)
    with c3:
        modifier = st.number_input("Модификатор", value=0)
    
    if st.button("Бросить", type="primary"):
        rolls = [roll_dice(custom_sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        rolls_str = " + ".join(map(str, rolls))
        if modifier:
            rolls_str += f" + ({modifier})" if modifier > 0 else f" − ({abs(modifier)})"
        st.success(f"Результат: **{total}**  ({rolls_str})")
        add_log(f"Бросок {num_dice}d{custom_sides}{modifier:+d if modifier else ''}: {total}")

# ===================== СТРАНИЦА: БИОГРАФИЯ =====================
elif page == "Биография":
    st.markdown("<div class='main-title' style='font-size:1.8rem'>Биография</div>", unsafe_allow_html=True)
    
    st.markdown("""
### Внешность
Высокая даже для дроу (около 178 см), стройная, с грациозной, почти хищной осанкой.  
Кожа цвета глубокой ночи с лёгким пепельным оттенком. Волосы — длинные, **чёрные как ночь**, обычно собраны в небрежный высокий хвост или спрятаны под капюшоном.  
Глаза ярко-фиолетовые, почти светящиеся в темноте. На левой щеке тонкий шрам от старого ритуального клинка.  
Одевается исключительно в чёрное и тёмно-фиолетовое.

### Характер
Холодная, сдержанная, крайне наблюдательная. Редко повышает голос — предпочитает, чтобы за неё говорили последствия.  
Обладает сухим, иногда язвительным чувством юмора. К тем, кого считает «своими», проявляет неожиданную (хоть и сдержанную) заботу.  
Глубоко амбициозна, но не ради власти над другими, а ради понимания и контроля над силами, которые большинство считают запретными.

### Предыстория
Калист родилась в **Доме Клиф** — большом и гордом матриархальном доме дроу, известном своими экспериментами на стыке огня и тьмы.  
Её мать, матриарх **Ильраэль Клиф**, была одержима идеей создать «чистое пламя бездны».  
В возрасте шестнадцати лет Калист стала свидетельницей падения своего дома: чёрное пламя вырвалось из-под контроля и уничтожило почти весь Дом Клиф за одну ночь.  
Выжила только она — потому что в последний момент мать затолкала её в защитный круг.

С тех пор Калист странствует. Продолжает исследования матери, но уже более осторожно. Носит с собой единственную реликвию дома — **Фамильный Амулет** — и клянётся довести работу до конца.

### Цели
- Создать стабильное «Пламя Души»
- Найти утерянные знания Дома Клиф
- Достичь равновесия огня и тьмы внутри себя

### Страхи
- Потеря контроля (повторить судьбу матери)
- Одиночество
- Светлые маги и «чистые» жрецы
- Привязанность
    """)

# Автосохранение при изменениях (лёгкое)
save_data(data)
