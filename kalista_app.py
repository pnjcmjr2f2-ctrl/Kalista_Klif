#!/usr/bin/env python3
"""
Калист Клиф — Интерактивный лист персонажа v2
Исправленная и расширенная версия
"""

import streamlit as st
import json
import random
from datetime import datetime
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "kalista_save.json"

st.set_page_config(
    page_title="✧ Калист Клиф ✧",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Quattrocento+Sans:wght@400;700&display=swap');
    
    .main-title {
        font-family: 'Cinzel', serif;
        font-size: 2.2rem;
        color: #E8DAEF;
        text-align: center;
        text-shadow: 0 0 12px #4A235A;
        margin-bottom: 0.1rem;
    }
    .subtitle {
        text-align: center;
        color: #BB8FCE;
        font-size: 1rem;
        margin-bottom: 1rem;
    }
    .section-header {
        font-family: 'Cinzel', serif;
        color: #D7BDE2;
        font-size: 1.25rem;
        border-bottom: 2px solid #7D3C98;
        padding-bottom: 4px;
        margin: 1rem 0 0.7rem 0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.45rem; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ===================== ДЕФОЛТНЫЕ ДАННЫЕ =====================
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
        "Сила": 10,
        "Выносливость": 15,
        "Ловкость": 14,
        "Мудрость": 10,
        "Интеллект": 60,
        "Харизма": 10,
        "Дух": 35,
    },
    "equip_bonuses": {
        "Сила": 0,
        "Выносливость": 25,
        "Ловкость": 0,
        "Мудрость": 85,
        "Интеллект": 235,
        "Харизма": 0,
        "Дух": 175,
    },

    "armor": 535,
    "phys_attack": 55,

    "pepel": 0,
    "ten": 0,
    "buffs": "",
    "debuffs": "",
    "concentration": "",
    "last_school": None,

    "gold": 84,
    "silver": 34,
    "copper": 0,

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
         "desc": "Быстрый сгусток огня. Низкая стоимость.", "gives": "pepel"},
        {"id": 2, "name": "Огненный шар", "base": 80, "mana": 35, "range": "Средняя", "school": "Огонь",
         "desc": "Классический шар пламени.", "gives": "pepel"},
        {"id": 3, "name": "Язык пламени", "base": 55, "mana": 28, "range": "Ближняя", "school": "Огонь",
         "desc": "Полоса огня перед заклинателем.", "gives": "pepel"},
        {"id": 4, "name": "Пепел и тлен", "base": 40, "mana": 22, "range": "Средняя", "school": "Огонь",
         "desc": "DoT: поджигает на 3 хода.", "gives": "pepel"},
        {"id": 5, "name": "Адское дыхание", "base": 120, "mana": 55, "range": "Ближняя", "school": "Огонь",
         "desc": "Мощный конус огня.", "gives": "pepel"},
        {"id": 6, "name": "Теневой укол", "base": 45, "mana": 20, "range": "Ближняя", "school": "Тьма",
         "desc": "Тёмный шип. Игнорирует часть брони.", "gives": "ten"},
        {"id": 7, "name": "Покров тьмы", "base": 0, "mana": 30, "range": "На себя", "school": "Тьма",
         "desc": "Щит +10% сопр. тьме.", "gives": None},
        {"id": 8, "name": "Проклятие слабости", "base": 25, "mana": 25, "range": "Средняя", "school": "Тьма",
         "desc": "Снижает силу и атаку на 3 хода.", "gives": "ten"},
        {"id": 9, "name": "Разряд бездны", "base": 95, "mana": 45, "range": "Дальняя", "school": "Тьма",
         "desc": "Мощный разряд. Шанс страха.", "gives": "ten"},
        {"id": 10, "name": "Пламя души", "base": 150, "mana": 70, "range": "Средняя", "school": "Огонь+Тьма",
         "desc": "Ультиматив. Долгий каст.", "gives": "both"},
    ],

    "combat_log": [],
    "resists": {"Огонь": 75, "Земля": 5, "Вода": 10, "Воздух": 5, "Тьма": 95, "Свет": 15},
}

def total_stat(data, name):
    return data["base_stats"].get(name, 0) + data["equip_bonuses"].get(name, 0)

def recalc_derived(data):
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
    data["mana_regen"] = spi * 0.5
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
            data = DEFAULT.copy()
            data.update(saved)
            for key in ["base_stats", "equip_bonuses", "resists"]:
                if key in saved:
                    data[key] = {**DEFAULT.get(key, {}), **saved[key]}
            return data
        except Exception:
            pass
    return DEFAULT.copy()

def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    data = st.session_state.data
    data["combat_log"].insert(0, f"[{ts}] {msg}")
    data["combat_log"] = data["combat_log"][:50]

def calc_dmg(base, spell_power, dual=False):
    dmg = round(base * (1 + spell_power))
    if dual:
        dmg = round(dmg * 1.05)
    return dmg

# ===================== INIT =====================
if "data" not in st.session_state:
    st.session_state.data = load_save()
    recalc_derived(st.session_state.data)

data = st.session_state.data
recalc_derived(data)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("<div class='main-title' style='font-size:1.5rem'>✧ Калист</div>", unsafe_allow_html=True)
    st.caption(f"Ур. {data['level']} · {data['class']}")
    st.divider()

    page = st.radio(
        "Навигация",
        ["Обзор", "Бой", "Характеристики", "Инвентарь", "Заклинания (все)", "Кубики", "Биография"],
        label_visibility="collapsed"
    )

    st.divider()
    if st.button("💾 Сохранить", use_container_width=True):
        save_data(data)
        st.success("Сохранено")
    if st.button("🔄 Сбросить всё", use_container_width=True):
        st.session_state.data = DEFAULT.copy()
        recalc_derived(st.session_state.data)
        save_data(st.session_state.data)
        st.rerun()

# ===================== ОБЗОР =====================
if page == "Обзор":
    st.markdown(f"<div class='main-title'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{data['race']} · {data['class']} · Уровень {data['level']}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**❤️ Здоровье**")
        st.progress(min(data["hp_current"] / max(data["hp_max"], 1), 1.0),
                    text=f"{data['hp_current']} / {data['hp_max']}")
    with c2:
        st.markdown("**💧 Мана**")
        st.progress(min(data["mana_current"] / max(data["mana_max"], 1), 1.0),
                    text=f"{data['mana_current']} / {data['mana_max']}")

    st.divider()

    st.markdown("<div class='section-header'>Ключевые параметры</div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Сила заклинаний", f"+{data['spell_power']*100:.0f}%")
    m2.metric("Броня", data["armor"])
    m3.metric("Инициатива", data["initiative"])
    m4.metric("Свободные очки", data["free_points"])

    st.markdown("<div class='section-header'>Характеристики (итого)</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, name in enumerate(["Сила", "Выносливость", "Ловкость", "Мудрость", "Интеллект", "Харизма", "Дух"]):
        with cols[i % 4]:
            st.metric(name, total_stat(data, name))

    st.markdown("<div class='section-header'>Опыт</div>", unsafe_allow_html=True)
    st.write(f"**Текущий опыт:** {data['xp']}  ·  **До следующего уровня:** {data['xp_to_next']}")

    colx1, colx2, colx3 = st.columns([2, 1, 1])
    with colx1:
        add_xp = st.number_input("Добавить опыт", min_value=0, value=100, step=50, key="xp_add")
    with colx2:
        if st.button("➕ Добавить XP"):
            data["xp"] += add_xp
            data["xp_to_next"] = max(0, data["xp_to_next"] - add_xp)
            add_log(f"Получено {add_xp} опыта")
            if data["xp_to_next"] <= 0:
                st.warning("Пора повышать уровень! Перейди в «Характеристики»")
            st.rerun()
    with colx3:
        if st.button("⬆ Уровень +1"):
            data["level"] += 1
            data["free_points"] += 4
            data["xp_to_next"] = data["level"] * 1000
            recalc_derived(data)
            add_log(f"Уровень повышен до {data['level']}! +4 свободных очка")
            st.rerun()

# ===================== БОЙ =====================
elif page == "Бой":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Бой</div>", unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("❤️ HP", f"{data['hp_current']}/{data['hp_max']}")
    r2.metric("💧 Мана", f"{data['mana_current']}/{data['mana_max']}")
    r3.metric("🛡 Броня", data["armor"])
    r4.metric("⚡ Инициатива", data["initiative"])

    st.markdown("##### Получить / восстановить")
    d1, d2, d3, d4 = st.columns([2, 1, 2, 1])
    with d1:
        dmg_in = st.number_input("Урон по мне", min_value=0, value=0, step=10, key="dmg_in")
    with d2:
        if st.button("Нанести урон"):
            data["hp_current"] = max(0, data["hp_current"] - dmg_in)
            add_log(f"Получено {dmg_in} урона (HP → {data['hp_current']})")
            st.rerun()
    with d3:
        heal_in = st.number_input("Восстановить HP", min_value=0, value=0, step=10, key="heal_in")
    with d4:
        if st.button("Вылечить"):
            data["hp_current"] = min(data["hp_max"], data["hp_current"] + heal_in)
            add_log(f"Восстановлено {heal_in} HP")
            st.rerun()

    m1, m2, m3 = st.columns([2, 1, 1])
    with m1:
        mana_change = st.number_input("Изменить ману (+/-)", value=0, step=50, key="mana_ch")
    with m2:
        if st.button("Применить ману"):
            data["mana_current"] = max(0, min(data["mana_max"], data["mana_current"] + mana_change))
            st.rerun()
    with m3:
        if st.button("Полная мана"):
            data["mana_current"] = data["mana_max"]
            st.rerun()

    st.divider()

    st.markdown("##### 🔥 Пепел & 🌑 Тень")
    p1, p2 = st.columns(2)
    with p1:
        st.progress(data["pepel"] / 5, text=f"Пепел {data['pepel']}/5")
        c1, c2 = st.columns(2)
        if c1.button("+1 Пепел"):
            data["pepel"] = min(5, data["pepel"] + 1)
            st.rerun()
        if c2.button("Активировать Пепел", disabled=data["pepel"] < 5):
            data["pepel"] = 0
            add_log("Пепел активирован → следующее огненное игнорирует 30% сопр. огню")
            st.rerun()
    with p2:
        st.progress(data["ten"] / 5, text=f"Тень {data['ten']}/5")
        c1, c2 = st.columns(2)
        if c1.button("+1 Тень"):
            data["ten"] = min(5, data["ten"] + 1)
            st.rerun()
        if c2.button("Активировать Тень", disabled=data["ten"] < 5):
            data["ten"] = 0
            add_log("Тень активирована → невидимость 1 ход или +20% сопротивления")
            st.rerun()

    st.divider()

    st.markdown("##### Быстрый каст")
    if data.get("last_school"):
        st.caption(f"Последняя школа: **{data['last_school']}** (Двойное пламя активно)")

    for spell in data["spells"]:
        dual = bool(data.get("last_school") and data["last_school"] != spell["school"]
                    and ("Огонь" in spell["school"] or "Тьма" in spell["school"]))
        dmg = calc_dmg(spell["base"], data["spell_power"], dual) if spell["base"] else 0

        cols = st.columns([3.2, 1, 1, 1.2])
        with cols[0]:
            icon = "🔥" if "Огонь" in spell["school"] else "🌑"
            st.markdown(f"**{icon} {spell['name']}** · {spell['school']}")
            st.caption(spell["desc"])
        with cols[1]:
            st.write(f"**{dmg if dmg else '—'}**")
            if dual:
                st.caption("+5%")
        with cols[2]:
            st.write(f"{spell['mana']} MP")
        with cols[3]:
            can = data["mana_current"] >= spell["mana"]
            if st.button("Каст", key=f"c_{spell['id']}", disabled=not can):
                data["mana_current"] -= spell["mana"]
                data["last_school"] = spell["school"]
                if spell.get("gives") in ("pepel", "both"):
                    data["pepel"] = min(5, data["pepel"] + 1)
                if spell.get("gives") in ("ten", "both"):
                    data["ten"] = min(5, data["ten"] + 1)
                msg = f"«{spell['name']}» → {dmg} урона (−{spell['mana']} MP)"
                if dual:
                    msg += " [Двойное пламя]"
                add_log(msg)
                st.rerun()

    st.divider()

    st.markdown("##### Состояния")
    data["buffs"] = st.text_input("Баффы", value=data.get("buffs", ""))
    data["debuffs"] = st.text_input("Дебаффы", value=data.get("debuffs", ""))
    data["concentration"] = st.text_input("Концентрация", value=data.get("concentration", ""))

    st.markdown("##### Лог")
    for entry in data["combat_log"][:12]:
        st.text(entry)
    if st.button("Очистить лог"):
        data["combat_log"] = []
        st.rerun()

# ===================== ХАРАКТЕРИСТИКИ =====================
elif page == "Характеристики":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Характеристики</div>", unsafe_allow_html=True)

    st.info(f"Свободные очки: **{data['free_points']}**  ·  Уровень: **{data['level']}**")

    st.markdown("##### Базовые характеристики (можно повышать очками)")
    for name in ["Сила", "Выносливость", "Ловкость", "Мудрость", "Интеллект", "Харизма", "Дух"]:
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.write(f"**{name}**")
        with cols[1]:
            st.write(f"База: {data['base_stats'][name]}")
        with cols[2]:
            st.write(f"Экип: +{data['equip_bonuses'][name]}")
        with cols[3]:
            st.write(f"**Итого: {total_stat(data, name)}**")
        with cols[4]:
            if st.button("＋", key=f"up_{name}", disabled=data["free_points"] <= 0):
                data["base_stats"][name] += 1
                data["free_points"] -= 1
                recalc_derived(data)
                add_log(f"Повышена {name}")
                st.rerun()

    st.divider()
    st.markdown("##### Броня и физ. атака (ручные)")
    c1, c2 = st.columns(2)
    with c1:
        data["armor"] = st.number_input("Броня", min_value=0, value=int(data["armor"]), step=5)
    with c2:
        data["phys_attack"] = st.number_input("Физ. атака", min_value=0, value=int(data["phys_attack"]), step=1)

    st.divider()
    st.markdown("##### Производные (считаются автоматически)")
    d1, d2, d3 = st.columns(3)
    d1.metric("Сила заклинаний", f"+{data['spell_power']*100:.0f}%")
    d1.metric("Реген маны", f"{data['mana_regen']:.0f}")
    d2.metric("Сопр. контролю", f"{data['control_resist']*100:.1f}%")
    d2.metric("Бонус ритуалов", f"+{data['ritual_bonus']*100:.0f}%")
    d3.metric("Сила страха", f"{data['fear_power']*100:.1f}%")
    d3.metric("Инициатива", data["initiative"])

# ===================== ИНВЕНТАРЬ =====================
elif page == "Инвентарь":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Инвентарь</div>", unsafe_allow_html=True)

    st.markdown("##### 💰 Валюта")
    g, s, c = st.columns(3)
    data["gold"] = g.number_input("Золото", min_value=0, value=data["gold"])
    data["silver"] = s.number_input("Серебро", min_value=0, value=data["silver"])
    data["copper"] = c.number_input("Медь", min_value=0, value=data["copper"])

    st.divider()
    st.markdown("##### 🎒 Сумка")

    for i, item in enumerate(data["inventory"]):
        cols = st.columns([3, 1.2, 1, 1.5])
        with cols[0]:
            st.markdown(f"**{item['name']}**")
            st.caption(f"{item['type']} · {item['desc']}")
        with cols[1]:
            item["qty"] = st.number_input("Кол-во", min_value=0, value=item["qty"], key=f"q_{i}", label_visibility="collapsed")
        with cols[2]:
            if item["type"] == "Расходник" and item["qty"] > 0:
                if "мана" in item["name"].lower():
                    if st.button("Выпить", key=f"use_{i}"):
                        item["qty"] -= 1
                        data["mana_current"] = min(data["mana_max"], data["mana_current"] + 400)
                        add_log(f"Выпито: {item['name']} (+400 MP)")
                        st.rerun()
                elif "лечен" in item["name"].lower() or "здоров" in item["name"].lower():
                    if st.button("Выпить", key=f"use_{i}"):
                        item["qty"] -= 1
                        data["hp_current"] = min(data["hp_max"], data["hp_current"] + 250)
                        add_log(f"Выпито: {item['name']} (+250 HP)")
                        st.rerun()
        with cols[3]:
            if st.button("🗑", key=f"del_{i}"):
                data["inventory"].pop(i)
                st.rerun()

    st.divider()
    st.markdown("##### ➕ Добавить предмет")
    with st.form("add_item"):
        n1, n2 = st.columns(2)
        new_name = n1.text_input("Название")
        new_type = n2.selectbox("Тип", ["Расходник", "Реагент", "Свиток", "Оружие", "Броня", "Реликвия", "Инструмент", "Прочее"])
        new_qty = st.number_input("Количество", min_value=1, value=1)
        new_desc = st.text_input("Описание")
        if st.form_submit_button("Добавить"):
            if new_name.strip():
                data["inventory"].append({
                    "name": new_name.strip(),
                    "type": new_type,
                    "qty": new_qty,
                    "desc": new_desc.strip()
                })
                st.success(f"Добавлено: {new_name}")
                st.rerun()

# ===================== ЗАКЛИНАНИЯ (редактирование) =====================
elif page == "Заклинания (все)":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Заклинания</div>", unsafe_allow_html=True)
    st.caption("Здесь можно редактировать и добавлять заклинания. Каст удобнее делать на странице «Бой».")

    for i, spell in enumerate(data["spells"]):
        with st.expander(f"{spell['name']}  ({spell['school']})"):
            spell["name"] = st.text_input("Название", spell["name"], key=f"sn_{i}")
            c1, c2, c3 = st.columns(3)
            spell["base"] = c1.number_input("Базовый урон", value=spell["base"], key=f"sb_{i}")
            spell["mana"] = c2.number_input("Мана", value=spell["mana"], key=f"sm_{i}")
            spell["range"] = c3.text_input("Дистанция", spell["range"], key=f"sr_{i}")
            spell["school"] = st.selectbox("Школа", ["Огонь", "Тьма", "Огонь+Тьма"],
                                           index=["Огонь", "Тьма", "Огонь+Тьма"].index(spell["school"]) if spell["school"] in ["Огонь", "Тьма", "Огонь+Тьма"] else 0,
                                           key=f"ss_{i}")
            spell["desc"] = st.text_input("Описание", spell["desc"], key=f"sd_{i}")
            if st.button("Удалить заклинание", key=f"sdel_{i}"):
                data["spells"].pop(i)
                st.rerun()

    st.divider()
    st.markdown("##### ➕ Новое заклинание")
    with st.form("add_spell"):
        sn = st.text_input("Название")
        c1, c2, c3 = st.columns(3)
        sb = c1.number_input("Базовый урон", min_value=0, value=50)
        sm = c2.number_input("Мана", min_value=0, value=30)
        sr = c3.text_input("Дистанция", value="Средняя")
        ss = st.selectbox("Школа", ["Огонь", "Тьма", "Огонь+Тьма"])
        sd = st.text_input("Описание")
        gives = st.selectbox("Даёт ресурс", [None, "pepel", "ten", "both"], format_func=lambda x: {None: "Ничего", "pepel": "Пепел", "ten": "Тень", "both": "Оба"}[x])
        if st.form_submit_button("Добавить заклинание"):
            if sn.strip():
                new_id = max([s["id"] for s in data["spells"]], default=0) + 1
                data["spells"].append({
                    "id": new_id, "name": sn.strip(), "base": sb, "mana": sm,
                    "range": sr, "school": ss, "desc": sd, "gives": gives
                })
                st.success(f"Добавлено: {sn}")
                st.rerun()

# ===================== КУБИКИ =====================
elif page == "Кубики":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Кубики</div>", unsafe_allow_html=True)

    dice = [4, 6, 8, 10, 12, 20, 100]
    cols = st.columns(len(dice))
    for i, sides in enumerate(dice):
        with cols[i]:
            if st.button(f"d{sides}", key=f"d{sides}", use_container_width=True):
                res = random.randint(1, sides)
                st.session_state[f"roll_{sides}"] = res
                add_log(f"d{sides}: {res}")
            if f"roll_{sides}" in st.session_state:
                st.markdown(f"<h2 style='text-align:center;color:#E8DAEF'>{st.session_state[f'roll_{sides}']}</h2>", unsafe_allow_html=True)

    st.divider()
    st.markdown("##### Свой бросок")
    c1, c2, c3 = st.columns(3)
    sides = c1.number_input("Грани", 2, 1000, 20)
    num = c2.number_input("Кол-во", 1, 20, 1)
    mod = c3.number_input("Модификатор", value=0)
    if st.button("Бросить", type="primary"):
        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls) + mod
        st.success(f"Результат: **{total}**  ({' + '.join(map(str, rolls))}{f' {mod:+d}' if mod else ''})")
        add_log(f"{num}d{sides}{mod:+d if mod else ''}: {total}")

# ===================== БИОГРАФИЯ =====================
elif page == "Биография":
    st.markdown("<div class='main-title' style='font-size:1.7rem'>Биография</div>", unsafe_allow_html=True)
    st.markdown("""
### Внешность
Высокая (≈178 см), стройная, грациозная. Кожа цвета глубокой ночи. Волосы длинные, **чёрные как ночь**.  
Глаза ярко-фиолетовые. Шрам на левой щеке. Одежда — чёрное и тёмно-фиолетовое.

### Характер
Холодная, сдержанная, наблюдательная. Сухой язвительный юмор. Амбициозна ради понимания запретных сил.  
Боится потери контроля над магией.

### Предыстория
Родилась в **Доме Клиф**. Мать — матриарх Ильраэль — пыталась создать «пламя бездны».  
Ритуал вышел из-под контроля, дом почти полностью погиб. Калист спасла мать, затолкав в защитный круг.  
С тех пор странствует, продолжает исследования и носит **Фамильный Амулет**.

### Цели
- Создать стабильное «Пламя Души»
- Восстановить знания Дома Клиф
- Достичь равновесия огня и тьмы

### Страхи
Потеря контроля · Одиночество · Светлые маги · Привязанность
    """)

# Автосохранение
save_data(data)
