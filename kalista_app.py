#!/usr/bin/env python3
"""
Калиста Клиф — v46 · полный лист игрока
Ручное ведение НРИ, очередь ходов, эффекты, щиты, лечение и 6 стихий
"""

import streamlit as st
from kalista_view import editing,gm_view
from kalista_map import separation,ability_range
from kalista_shape_ui import edit_shape
from kalista_shapes import is_area,check_area_aim,shape_targets,area_label
from kalista_loot import settings as loot_settings,assign_loot,equip_root_reserve,DEFAULT_CHANCES
import json
import random
import math
from html import escape
from datetime import datetime
from pathlib import Path
from copy import deepcopy
import hmac
import time
from kalista_storage import read_state, write_state, StaleState, create_snapshot, list_snapshots, restore_snapshot, undo_entries
from kalista_engine import (
    DAMAGE_TYPES, DEFAULT, EFFECT_KINDS, ELEMENTS, MAX_LEVEL,
    RARITIES, action_amount, action_template, activate_scene, activate_shadow_invisibility,
    activate_shadow_resistance, activate_special, actor_target, actor_token, add_effect,
    add_history, add_npc_to_battle, advance_turn, apply_damage, apply_healing,
    cast_spell, check_reach, combat_side, create_npc, create_scene,
    damage_message, damage_preview, default_opponent, delete_npc, delete_scene,
    distance_between, effect_lifetime, effective_crit_chance, effective_defense, end_combat,
    evasion_chance, exclude_from_queue, exclude_from_queue_after_delete, gen_enemy, get_current_actor,
    hp_fields, imported_friend, invalidate_player_requests, kalista_dot_damage, migrate,
    move_in_queue, npc_battle_token, npc_record, observe_mana_reserve, participant,
    participant_label, participants, perform_action, preview_action, public_player_state,
    ranged_miss_chance, rarity_badge, rarity_label, reach_label, recalc,
    recalc_equip, refresh_turn_order, register_enemy, restore_mana,
    return_to_queue, scene_player_text, scene_record, set_initiative, set_manual_turn,
    shadow_shield_amount, special_availability, spell_action, spell_bonuses, spell_damage_preview,
    spell_raw, start_combat, tick_periodic, tick_round_effects, total_stat,
    update_npc, update_scene, use_item, validate_action_state, visible_battle_participants,
    xp_needed
)
from kalista_theme import THEME
from kalista_text import readable_rules
from kalista_battle_readout import effect_label,render_recent_results
from kalista_player_ui import render_section as render_player_sheet_section, SECTIONS as PLAYER_SECTIONS

SAVE_FILE = Path(__file__).parent / "kalista_save.json"
PORTRAIT_FILE = Path(__file__).parent / "assets" / "kalista-portrait.png"

st.set_page_config(page_title="✧ Калиста Клиф ✧", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")
st.markdown(THEME, unsafe_allow_html=True)

# ===================== DEFAULT =====================

# ===================== ФОРМУЛЫ =====================


def load():
    try:
        saved, revision = read_state(SAVE_FILE)
        st.session_state["_save_revision"] = revision
        if saved is None: return migrate(deepcopy(DEFAULT))
        return migrate(saved)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error(f"Сохранение не загружено: {exc}. Исходный файл оставлен без изменений.")
        st.info("Восстанови kalista_save.json из kalista_save.json.bak либо исправь файл и перезапусти приложение.")
        st.stop()


def save(d):
    try:
        st.session_state['_save_revision'] = write_state(SAVE_FILE, d, st.session_state.get('_save_revision', read_state(SAVE_FILE)[1]), migrate)
        return True
    except StaleState:
        st.session_state['_sync_notice'] = 'Игра обновилась на другом экране. Твоё действие не применено; повтори его с актуальными данными.'
        for key in list(st.session_state):
            if key not in ('_role', '_save_revision', '_sync_notice'): del st.session_state[key]
        st.rerun()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error(f'Не удалось сохранить: {exc}. Предыдущее сохранение не перезаписано.')
        return False


def log(msg):
    ts=datetime.now().strftime("%H:%M:%S")
    st.session_state.data["combat_log"].insert(0,f"[{ts}] {msg}")
    st.session_state.data["combat_log"]=st.session_state.data["combat_log"][:80]


# ===================== ОБЩАЯ МЕХАНИКА =====================
# Эти функции работают с данными, не зависят от Streamlit и имени персонажа.


def persist_and_rerun(label=None):
    st.session_state["_reset_resource_widgets"] = True
    if commit_current(label):
        st.rerun()


def show_effect_summary(target):
    effects = target.get("effects", [])
    if effects:
        capacity = sum(effect["value"] for effect in effects if effect["kind"] == "shield")
        if capacity:
            st.caption(f"🛡 Щит: {capacity}")
        st.caption("Эффекты: " + ", ".join(effect["name"] for effect in effects))


def render_quick_action(data, token):
    if not editing():return
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
    if not editing():return
    target = participant(data, token)
    st.markdown("**Эффекты выбранного участника**")
    st.caption("Урон и лечение срабатывают в конце хода цели. Страх и слабость отсчитываются по личным ходам цели; остальные эффекты — по полным раундам. "
               "Раунд наложения не сокращает длительность. Вне боя эффекты меняются вручную.")
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
        lifetime = effect_label(effect).split(" · ",1)[-1]
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
    from kalista_storage import undo_state
    try:
        restored,revision=undo_state(SAVE_FILE,st.session_state['_save_revision'],migrate)
        st.session_state.data=restored
        st.session_state['_committed_data']=deepcopy(restored)
        st.session_state['_save_revision']=revision
        st.session_state['_undo_history']=[]
        keep={'data','_committed_data','_undo_history','page','battle_section','gm_section','_battle_preferences','_save_revision','_role','_edit_mode'}
        for key in list(st.session_state):
            if key not in keep:del st.session_state[key]
        st.rerun()
    except (ValueError,OSError) as exc:st.error(str(exc))


def render_range_audit(data):
    if not editing():return
    rows=[]
    for owner,abilities in [(data['name'],data['spells'])]+[(a['name'],a.get('actions',[])) for t,a in participants(data) if t!='player']:
        for a in abilities:
            if a.get('kind',a.get('action','damage'))!='damage' or a.get('rule','').startswith('move_'):continue
            if a.get('area_shape')=='cone':continue
            if ability_range(a) is None:rows.append({'Персонаж':owner,'Способность':a['name'],'Дальность':'Не задана — без ограничения'})
    with st.expander(f'Дальность не задана · {len(rows)}'):
        if rows:st.dataframe(rows,hide_index=True,use_container_width=True)
        else:st.caption('У всех атак задана дальность.')
        st.caption('Ближние атаки без отдельного числа ограничены 5 м. У конуса используется его длина. Настрой дальность в карточке способности.')


def remembered_select(label, options, key, default=None, **kwargs):
    """Сохраняем выбор между экранами, даже когда Streamlit удаляет скрытый виджет."""
    prefs = st.session_state.setdefault("_battle_preferences", {})
    candidate = st.session_state.get(key, prefs.get(key, default))
    if candidate not in options:
        candidate = default if default in options else options[0]
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
    value = st.selectbox(label, options, index=options.index(candidate), key=key, **kwargs)
    prefs[key] = value
    return value


def reset_participant_widgets():
    st.session_state["_reset_resource_widgets"] = True


def render_battle_header(data):
    actor=get_current_actor(data) if data['combat_active'] else None
    token=actor_token(actor) if actor else 'player'
    active=participant(data,token);hp,maximum=hp_fields(active)
    used=sum(x['source']==token and x.get('counts',True) for x in data.get('turn_actions',[]))
    turn=f"Раунд {data['round']} · {actor['name']}" if actor else 'Бой не начат'
    resources=f"HP {active[hp]}/{active[maximum]}"+(f" · MP {active['mana_current']}/{active['mana_max']}" if active.get('mana_max') else '')
    budget=f"Действия {max(0,2-used)}/2 · перемещение "+('использовано' if active.get('movement_used') else 'доступно')
    def start():
        create_snapshot(SAVE_FILE,'before-battle')
        for message in start_combat(data):log(message)
        persist_and_rerun('Начало боя')
    with st.container(key='battle_header'):
        with st.container(key='battle_top'):
            left,right=st.columns([4,1])
            left.markdown(f'<div class="battle-strip"><strong>{escape(turn)}</strong><span>{escape(resources)} · {escape(budget)}</span></div>',unsafe_allow_html=True)
            if data['combat_active']:
                if right.button('Конец хода',key='battle_next',disabled=not data['turn_order'],type='primary',use_container_width=True):
                    for message in advance_turn(data):log(message)
                    persist_and_rerun('Следующий ход')
            elif right.button('Начать',key='battle_start',type='primary',use_container_width=True):start()
        prefs=st.session_state.setdefault('_battle_preferences',{})
        if 'battle_section' not in st.session_state:st.session_state['battle_section']=prefs.get('battle_section','Ход')
        if st.session_state['battle_section']=='Калиста':st.session_state['battle_section']='Ход'
        prefs['battle_section']=st.radio('Раздел боя',['Ход','Участники','Эффекты','Очередь','Журнал'],key='battle_section',horizontal=True,label_visibility='collapsed')
    with st.expander('Управление боем · отмена и завершение'):
        columns=st.columns(3)
        if data['combat_active']:
            columns[0].button('Начать',key='battle_start',disabled=True,use_container_width=True)
        else:columns[0].button('Конец хода',key='battle_next',disabled=True,use_container_width=True)
        history=undo_entries(SAVE_FILE)
        if columns[1].button('Отмена',key='battle_undo',disabled=not history,help=f"Отменить: {history[-1]['label']}" if history else 'Нет действий для отмены',use_container_width=True):undo_last_action()
        if columns[2].button('Стоп',key='battle_stop',disabled=not data['combat_active'],use_container_width=True):
            log(end_combat(data));persist_and_rerun('Завершение боя')


def render_selected_spell(data, target, selected_id=None):
    if not data["spells"]:
        st.info("Заклинаний пока нет. Добавь их на странице «Заклинания».")
        return
    spells = {spell["id"]: spell for spell in data["spells"]}
    sid = selected_id if selected_id is not None else remembered_select("Способность", list(spells), "battle_spell", default=data["spells"][0]["id"],
                            format_func=lambda value: f"{spells[value]['name']} · {reach_label(spells[value])} · {spells[value]['mana']} MP" +
                            (f" · КД {spells[value]['cd_left']}" if spells[value]['cd_left'] else ""))
    spell = spells[sid]
    action = spell_action(spell)
    target_token=next((t for t,v in participants(data) if v is target),None)
    if data.get('distance_mode')=='meters' and is_area(spell):
        render_area_spell(data,spell,target);render_spell_extras(data);return
    dual, soul = spell_bonuses(data, spell)
    raw = spell_raw(spell["base"], data.get("spell_power", 0), dual, soul) if action == "damage" else spell.get("effect_value", 0)
    st.caption(f"Мана {spell['mana']} · КД {spell.get('cd_left', 0)}/{spell.get('cd_max', 0)}")
    bonuses = (["Двойное пламя +5%"] if dual else []) + (["Ритуал +40%"] if soul else [])
    if bonuses: st.caption("Прямой урон: " + " · ".join(bonuses))
    if action == "damage": st.caption(f"Шанс крита: {effective_crit_chance(data)*100:.1f}%")
    shield_amount = None
    if action == "shield":
        if spell['name']=='Покров тьмы':
            shield_amount=shadow_shield_amount(data)
            st.caption(f'Щит = Интеллект × (1 + сила заклинаний) = {shield_amount}')
        else:shield_amount = st.number_input("Сила щита", min_value=0, value=spell.get("effect_value", 0), key=f"cast_shield_{sid}")
    override = False
    final_damage = 0
    if action == "damage":
        if editing():
            with st.expander("Крит и ручной урон" if editing() else "Критический удар", expanded=False):
                st.caption("Крит определяется автоматически по формуле при попадании.")
                override = st.checkbox("Назначить итоговый урон вручную", key="battle_override") if editing() else False
                if editing():
                    final_damage = st.number_input("Готовый урон (щит будет учтён)", min_value=0, value=0,
                                                   disabled=not override, key="battle_final_damage")

        target_token=next((t for t,v in participants(data) if v is target),None)
        if target_token:
            if spell.get('reach')=='Ближняя' and distance_between(data,'player',target_token)!='Ближняя':st.warning('Ближнее заклинание: сначала сблизься с целью.')
            if ranged_miss_chance(data,'player',spell,target_token):st.warning('Дальнее заклинание при враге рядом: 50% шанс промаха. При промахе урон и эффекты не накладываются.')
        preview_raw = raw
        if raw > 0:
            preview = spell_damage_preview(data,spell,target,preview_raw,final_damage if override else None)
            st.info(f"{target['name']}: −{preview['hp_loss']} HP · щит поглотит {preview['absorbed']}" + (" · без учёта крита" if not override else ""))
            with st.expander("Расчёт урона"):
                st.caption(damage_message(target["name"],preview))
            if target is data['ally'] or target is data:
                st.warning('Выбрана дружественная цель: заклинание нанесёт ей урон.')
        with st.expander('Правила и эффекты способности'):
            st.caption(spell.get('desc',''))
            st.caption('Ближняя: только рядом. Дальняя: при враге рядом шанс промаха 50%. Любая: без штрафа дистанции.')
            if 'Огонь' in spell['school']:st.caption(f"Горение: шанс 50% · {kalista_dot_damage(data,'burn')} Огнём × 3 хода цели; сила фиксируется при наложении")
            if 'Тьма' in spell['school']:st.caption(f"Проклятие: шанс 50% · {kalista_dot_damage(data,'curse')} Тьмой × 3 хода; слабость: шанс 35% · −35% физического урона на 2 хода")
            if spell['name'] in ('Разряд бездны','Пламя души'):st.caption('Страх: шанс 50% × (1 − сопротивление контролю) · пропуск 2 ходов цели')
            if spell['school']=='Огонь+Тьма':st.caption('Прямой урон: 50% Огнём и 50% Тьмой; эффекты проверяются независимо.')
    elif action == "heal":
        hp_key, maximum_key = hp_fields(target)
        st.info(f"{target['name']}: восстановится {min(raw, max(0, target[maximum_key] - target[hp_key]))} HP")
    elif action == "shield":
        st.info(f"{target['name']}: щит {shield_amount} · " + (f"{spell['effect_duration']} полных раундов" if spell.get("effect_duration") else "бессрочно"))
    else:
        st.info(f"{target['name']}: статус «{spell['name']}»")
    can = data["hp_current"]>0 and data["mana_current"] >= spell["mana"] and spell.get("cd_left", 0) == 0
    if data["combat_active"] and sum(x["source"]=="player" and x.get("counts",True) for x in data.get("turn_actions",[]))>=2:can=False
    if action == "shield": can = can and shield_amount > 0
    if action == "heal": can = can and raw > 0
    if action == "damage": can = can and target[hp_fields(target)[0]] > 0
    blocked=[]
    if target_token and (action=='damage' or spell.get('range_m') is not None):
        try:check_reach(data,'player',dict(kind='damage',damage_type='Тьма',reach=spell.get('reach','Дальняя'),range_m=spell.get('range_m')),target_token)
        except ValueError as exc:blocked.append(str(exc));can=False
    if any(x['kind']=='fear' for x in data.get('effects',[])):blocked.append('Калиста под страхом');can=False
    if data['combat_active'] and sum(x['source']=='player' and x.get('counts',True) for x in data.get('turn_actions',[]))>=2:blocked.append('действия закончились')
    if blocked:st.caption('Недоступно: '+'; '.join(blocked))
    if st.button("Применить способность", key=f"cast_{sid}", disabled=not can, type="primary", use_container_width=True):
        crit = False
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
        if data['hp_current']<=0: reasons.append('у Калисты 0 HP')
        if data["mana_current"] < spell["mana"]: reasons.append("не хватает маны")
        if spell.get("cd_left", 0): reasons.append("способность на перезарядке")
        if action == "damage" and target[hp_fields(target)[0]] == 0: reasons.append("у цели 0 HP")
        if action in ("shield", "heal") and (shield_amount if action == "shield" else raw) == 0: reasons.append("не задана сила эффекта")
        st.caption("Применение недоступно: " + ", ".join(reasons))
    render_spell_extras(data)


def render_spell_extras(data):
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
    if not editing():return
    target = participant(data, token)
    hp_key, maximum_key = hp_fields(target)
    with st.expander("Изменить характеристики участника", expanded=False):
        with st.form(f"edit_participant_{token}"):
            name = st.text_input("Имя", value=target["name"])
            if token.startswith("enemy:"):
                reward_level=st.number_input("Уровень врага для опыта (0 — неизвестен)",min_value=0,value=int(target.get("level") or 0),disabled=token in ("player","ally"))
                reward_boss=st.checkbox("Босс · опыт ×5",value=target.get("is_boss",False),disabled=token in ("player","ally"))
                reward_elite=st.checkbox("Элитный · опыт ×2",value=target.get("is_elite",False),disabled=token in ("player","ally"))
            description = st.text_input("Кто это / заметка", value=target.get("description", ""))
            c1, c2 = st.columns(2)
            hp = c1.number_input("HP", min_value=0, value=target[hp_key])
            maximum = c2.number_input("Максимум HP", min_value=1, value=target[maximum_key], disabled=token == "player")
            armor = st.number_input("Броня без временных эффектов", min_value=0, value=target.get("armor", 0))
            agility=st.number_input("Ловкость (для уклонения)",min_value=0,value=int(total_stat(target,"Ловкость") if token=="player" else target.get("sheet_profile",{}).get("stats",{}).get("Ловкость",target.get("agility",0))),disabled=token in ("player","ally"))
            attack = st.number_input("Урон атаки", min_value=0.0, value=float(target["sheet_profile"]["attack"] if target.get("sheet_profile") else target.get("attack_damage", target.get("phys_attack", 0))))
            heal_amount = st.number_input("Сила лечения", min_value=0, value=target.get("heal_amount", 0), disabled=token == "player")
            use_mana = st.checkbox('Участник использует ману', value='mana_current' in target, disabled=token=='player')
            mana_max = st.number_input('Максимум маны участника',min_value=1,value=target.get('mana_max',1),disabled=token=='player' or not use_mana)
            mana_current = st.number_input('Текущая мана участника',min_value=0,value=target.get('mana_current',0),disabled=token=='player' or not use_mana)
            attack_type = st.selectbox("Тип атаки", DAMAGE_TYPES, index=DAMAGE_TYPES.index(target.get("attack_type", "Физический")))
            resists = {}
            cols = st.columns(2)
            for i, element in enumerate(ELEMENTS):
                resists[element] = cols[i % 2].number_input(element, min_value=-100, max_value=95, value=target.get("resists", {}).get(element, 0))
            if token == "player": st.caption("Максимум HP Калисты рассчитывается из уровня и характеристик.")
            if st.form_submit_button("Сохранить участника"):
                if not name.strip(): st.error("Укажи имя")
                else:
                    target["name"] = name.strip()
                    if token.startswith("enemy:"):target.update(level=reward_level or None,is_boss=reward_boss,is_elite=reward_elite)
                    target[hp_key] = hp
                    target["description"] = description.strip()
                    if token != "player": target[maximum_key] = maximum
                    if token == "player":
                        data["armor_adjustment"] += armor - data["armor"]
                        data["attack_adjustment"] += attack - data["phys_attack"]
                        for element in ELEMENTS:
                            data["resist_adjustments"][element] += resists[element] - data["resists"].get(element, 0)
                    else:
                        target["armor"] = armor; target["attack_damage"] = round(attack)
                        if token not in ("player","ally"):target["agility"]=agility
                        if target.get("sheet_profile"): target["sheet_profile"]["attack"] = float(attack)
                        target["attack_type"] = attack_type; target["resists"] = resists
                        target["heal_amount"] = heal_amount
                        if use_mana:
                            target['mana_max']=mana_max;target['mana_current']=min(mana_current,mana_max)
                        else:
                            target.pop('mana_max',None);target.pop('mana_current',None)
                    if data["combat_active"]: refresh_turn_order(data)
                    log(f"Изменён участник: {name.strip()}")
                    persist_and_rerun()
    if token != "player": render_action_editor(data, token)
    if token.startswith("enemy:"):
        with st.expander("Удалить участника", expanded=False):
            confirm = st.checkbox("Подтверждаю удаление", key=f"confirm_delete_{token}")
            if st.button("Удалить врага", disabled=not confirm, key=f"delete_{token}"):
                data["enemies"] = [enemy for enemy in data["enemies"] if f"enemy:{enemy['id']}" != token]
                for message in exclude_from_queue_after_delete(data, token): log(message)
                log(f"Удалён враг: {target['name']}")
                persist_and_rerun()


def render_combatant_action(data, source_token, victim_token):
    render_action_panel(data, source_token, victim_token)


def render_attack(data, token):
    if token == "player": return
    with st.expander(f"Действия вне очереди · {participant_label(data, token)}", expanded=False):
        tokens = [candidate for candidate, _ in participants(data)]
        default = default_opponent(data, token)
        victim = remembered_select("Цель действия", tokens, f"attack_victim_{token}", default=default,
                                   format_func=lambda value: participant_label(data, value))
        render_combatant_action(data, token, victim)


def render_stat_grid(values, elements=False):
    tiles = ''.join(f'<div class="stat-tile"><span>{escape(str(label))}</span><strong>{escape(str(value))}</strong></div>' for label, value in values)
    st.markdown(f'<div class="stat-grid{ " elements" if elements else ""}">{tiles}</div>', unsafe_allow_html=True)


def render_party(data):
    if not editing():
        render_combatant_card(data,'ally','Персонаж игрока',active=True)
        selected=st.selectbox('Раздел листа',[x for x in PLAYER_SECTIONS if x not in ('Бой','Сцена')],key='party_sheet_section')
        render_player_sheet_section(selected,data,SAVE_FILE.parent)
        return
    st.markdown("<div class='main-title'>Отряд</div>", unsafe_allow_html=True)
    if st.button('Отменить последнее изменение', key='party_undo', disabled=not st.session_state.get('_undo_history')):
        undo_last_action()
    ally = data['ally']
    profile = ally.get('sheet_profile')
    if not profile:
        st.info('Шеогарат · Драконит · Уровень 17 · HP 440/690 · Ледяная скорбь.')
        st.caption('Загрузка заменит текущего союзника. Действие можно отменить в текущей сессии.')
        if st.button('Загрузить персонажа из листа', key='friend_import', type='primary'):
            data['ally'] = imported_friend()
            if data['combat_active']: refresh_turn_order(data)
            log('В отряд добавлен персонаж из листа')
            persist_and_rerun('Загрузка персонажа друга')
        render_combatant_card(data, 'ally', 'Текущий союзник')
        return
    render_combatant_card(data, 'ally', 'Персонаж игрока', active=True)
    view = st.radio('Раздел персонажа', ['Лист', 'Снаряжение', 'Правка','Полный лист'], horizontal=True, key='friend_view', label_visibility='collapsed')
    if view=='Полный лист':
        selected=st.selectbox('Раздел листа',[s for s in PLAYER_SECTIONS if s not in ('Бой','Сцена')],key='party_sheet_section')
        render_player_sheet_section(selected,data,SAVE_FILE.parent)
        return
    if view == 'Лист':
        render_stat_grid(profile['stats'].items())
        st.markdown("<div class='section-h'>Боевые характеристики</div>", unsafe_allow_html=True)
        render_stat_grid([('Атака в листе',profile['attack']),('Критический урон',profile['critical_damage']),('Шанс крита',str(profile['critical_chance'])+'%'),('Свободные очки',profile['free_points'])])
        st.markdown("<div class='section-h'>Сопротивления</div>", unsafe_allow_html=True)
        render_stat_grid([(e,str(ally['resists'][e])+'%') for e in ELEMENTS], elements=True)
        st.caption('Стихийная защита этого персонажа задана в процентах. Свет −50% увеличивает входящий урон в 1,5 раза. В бою урон округляется до целого HP; крит определяется автоматически.')
        if profile['abilities']:
            st.markdown("<div class='section-h'>Способности</div>", unsafe_allow_html=True)
            for ability in profile['abilities'].splitlines():
                if ability.strip(): st.markdown('- '+readable_rules(ability))
        if profile['notes']:
            with st.expander('Связи и заметки'): st.markdown(profile['notes'])
        scene = scene_record(data, data['active_scene_id'])
        if scene:
            with st.expander('Текущая сцена', expanded=True): st.markdown(scene_player_text(data, scene['id']))
        st.caption('Полный лист доступен игроку с его отдельным ключом входа.')
    elif view == 'Снаряжение':
        render_player_sheet_section('Снаряжение',data,SAVE_FILE.parent)
    else:
        with st.form('friend_identity'):
            name = st.text_input('Имя персонажа', ally['name'])
            race = st.text_input('Раса', profile['race'])
            klass = st.text_input('Класс', profile['class'])
            level = st.number_input('Уровень', min_value=1, value=profile['level'])
            points = st.number_input('Свободные очки', min_value=0, value=profile['free_points'])
            stats = {name: st.number_input(name, min_value=0, value=value) for name,value in profile['stats'].items()}
            critical_damage = st.number_input('Критический урон', min_value=0.0, value=float(profile['critical_damage']))
            critical_chance = st.number_input('Шанс крита (%)', min_value=0.0, max_value=100.0, value=float(profile['critical_chance']))
            abilities = st.text_area('Способности и правила', profile['abilities'])
            notes = st.text_area('Заметки персонажа', profile['notes'])
            if st.form_submit_button('Сохранить лист'):
                if not name.strip(): st.error('Укажи имя персонажа')
                else:
                    ally['name'] = name.strip()
                    profile.update(race=race, **{'class':klass}, level=level, free_points=points, stats=stats, critical_damage=critical_damage, critical_chance=critical_chance, abilities=abilities, notes=notes)
                    if data['combat_active']: refresh_turn_order(data)
                    persist_and_rerun('Изменён лист персонажа друга')
        render_participant_editor(data, 'ally')


def render_focus_cards(data,source_token,target_token,player_mode=False):
    cards=[]
    for token,title in ((source_token,'Твой персонаж' if player_mode else 'Действует'),(target_token,'Цель')):
        target=participant(data,token);hp,maximum=hp_fields(target)
        shield=sum(x['value'] for x in target.get('effects',[]) if x['kind']=='shield')
        profile=target.get('sheet_profile',{})
        level=target.get('level',profile.get('level'))
        identity=' · '.join(str(x) for x in (target.get('race',profile.get('race','')),target.get('class',profile.get('class','')),'Ур. '+str(level) if level else '') if x)
        ratio=max(0,min(100,100*target[hp]/max(1,target[maximum])))
        resource=f" · MP {target['mana_current']}/{target['mana_max']}" if 'mana_current' in target else ''
        effects=len(target.get('effects',[]))
        statuses=[effect_label(x) for x in target.get('effects',[])][:2]
        if target.get('eye_damage_boost'):statuses.insert(0,'Десница ×2 · до конца этого хода')
        if target.get('defensive_stance'):statuses.insert(0,'Стойка −30% · до начала следующего хода')
        status=escape(' · '.join(statuses))
        portrait='/component/kalista_interactive_map.kalista_tactical_map/kalista.png' if token=='player' else (profile.get('portrait_url') or '/component/kalista_interactive_map.kalista_tactical_map/sheogarat.webp') if token=='ally' else ''
        avatar=f'<img class="focus-portrait" src="{escape(portrait,quote=True)}" alt=""/>' if portrait else '<span class="focus-initial">'+escape(target['name'][:1])+'</span>'
        cards.append(f'<div class="focus-card"><small>{title}</small>{avatar}<strong>{escape(target["name"])}</strong><span>{escape(identity or combat_side(data,token))}</span><b>HP {target[hp]}/{target[maximum]}</b><div class="combat-health"><div style="width:{ratio:g}%"></div></div><span>Щит {shield}{resource} · эффектов {effects}</span><span>{status}</span></div>')
    st.markdown('<div class="focus-cards">'+''.join(cards)+'</div>',unsafe_allow_html=True)


def render_combatant_card(data, token, title, active=False):
    target = participant(data, token)
    hp_key, maximum_key = hp_fields(target)
    shield = sum(effect["value"] for effect in target.get("effects", []) if effect["kind"] == "shield")
    role = combat_side(data, token) + (f" #{target['id']}" if token.startswith("enemy:") else "")
    identity = [role]
    if target.get("level"): identity.append(f"Уровень {target['level']}")
    if token == "player": identity.extend([target.get("race", ""), target.get("class", "")])
    elif target.get("sheet_profile"):
        profile = target["sheet_profile"]
        identity.extend([profile["race"], profile["class"], f"Уровень {profile['level']}"])
    elif target.get("size"): identity.append(target["size"])
    if target.get("is_elite"): identity.append("Элитный")
    if target.get("description"): identity.append(target["description"][:160])
    ratio = min(100, max(0, 100 * target[hp_key] / max(1, target[maximum_key])))
    details = [f"Броня {effective_defense(target, 'Физический')}", f"Щит {shield}"]
    if "mana_current" in target: details.append(f"MP {target['mana_current']}/{target['mana_max']}")
    elif active: details.append(f"Атака {target.get('attack_damage', 0)} · {target.get('attack_type', 'Физический')}")
    if active and target.get("heal_amount", 0): details.append(f"Лечение {target['heal_amount']}")
    if active: details.append(f"Уклонение {evasion_chance(target)*100:.1f}%")
    if target.get("eye_damage_boost"):details.append("Десница Ока: урон ×2")
    if target.get("defensive_stance"):details.append("Защитная стойка: урон −30%")
    if target.get("fear_immunity_turns",0):details.append("Иммунитет к страху: до конца следующего личного хода")
    if active: details.append(f"Инициатива {data.get('initiative_overrides', {}).get(token, target.get('initiative', 10))}")
    effects = [effect_lifetime(effect) for effect in target.get('effects', [])]
    if target is data and data.get('ten_invis'): effects.append(f"Невидимость: ещё {data['ten_invis_turn_starts_left']} начала хода")
    if target is data and data.get('ten_resist_boost'): effects.append(f"Тень: ещё {data['ten_resist_boost']} начала хода")
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
    if not editing():return
    with st.expander("Добавить врага / подкрепление", expanded=False):
        with st.form("adden"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Имя нового врага", value="Враг")
            level = c2.number_input("Уровень", min_value=1, max_value=MAX_LEVEL, value=min(MAX_LEVEL,max(1,int(data.get("level",1)))))
            size = st.selectbox("Размер", ["Мелкий", "Обычный", "Крупный", "Огромный"])
            from kalista_enemies import RACES, ROLES
            race = st.selectbox('Раса / вид', RACES, key='new_enemy_race')
            magic_element = st.selectbox('Стихия магии',['По классу']+ELEMENTS,key='new_enemy_element')
            enemy_role = st.selectbox('Класс / боевой шаблон', ('По расе и имени',)+ROLES, key='new_enemy_role')
            elite = st.checkbox("Элитный")
            boss = st.checkbox("Босс")
            strength = st.number_input("Сила врага (1 — новая базовая сложность)",min_value=0.5,max_value=3.0,value=1.0,step=0.25)
            st.caption("Элитный: HP ×1,8, урон ×1,25. Босс: HP ×4, урон ×1,6. Коэффициент силы меняет HP и урон; опыт остаётся по уровню и рангу.")
            if st.form_submit_button("Добавить врага"):
                if not name.strip(): st.error("Укажи имя")
                else:
                    eid = data["next_enemy_id"]
                    data["enemies"].append({"id": eid, "name": name.strip(), "level": level, "size": size,
                                            "is_elite": elite, "is_boss":boss, "effects": [], **gen_enemy(level, size, elite, boss, strength)})
                    from kalista_enemies import apply_loadout,suggested_role
                    data['enemies'][-1]['race']=race
                    data['enemies'][-1]['magic_element']=magic_element
                    chosen_role=('Босс' if boss else suggested_role(race+' '+name)) if enemy_role=='По расе и имени' else enemy_role
                    apply_loadout(data['enemies'][-1],chosen_role)
                    validate_action_state(data)
                    data["next_enemy_id"] += 1
                    if data["combat_active"]:register_enemy(data,data["enemies"][-1])
                    if data["combat_active"]: refresh_turn_order(data)
                    st.session_state["_next_battle_target"] = f"enemy:{eid}"
                    log(f"Добавлен враг: {name.strip()}")
                    persist_and_rerun()


def render_queue(data, token):
    if not editing():
        for actor in data['turn_order']:st.write(actor['name'])
        return
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
            set_manual_turn(data,pos)
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


def render_area_selection(data,source,ability,target,prefix):
    limit=ability_range(ability)
    st.caption(area_label(ability)+(' · от атакующего' if ability.get('area_shape')=='cone' else ' · дальность: '+(f'{limit:g} м' if limit is not None else 'не задана')))
    if st.session_state.get(prefix+'_anchor')!=target:
        st.session_state[prefix+'_x'],st.session_state[prefix+'_y']=data['positions'][target]
        st.session_state[prefix+'_anchor']=target
    context=(source,ability['id'],data.get('map_revision',0),data.get('turn_serial',0))
    if st.session_state.get('_board_area_context')==context:
        center=st.session_state['_board_area']
    else:
        from kalista_interactive_map import tactical_map
        center=tactical_map(data,source,prefix+'_canvas',center=[st.session_state[prefix+'_x'],st.session_state[prefix+'_y']],radius=ability.get('area_radius_m',0),mode='area',shape=ability.get('area_shape','circle'),cone_length=ability.get('cone_length_m',0),cone_angle=ability.get('cone_angle_deg',60))
    tokens=[]
    if st.session_state.get('_board_area_context')!=context:st.caption('Коснись центра взрыва или потяни его по полю.')
    problem=''
    try:
        check_area_aim(data,source,ability,center)
        tokens=shape_targets(data,source,ability,center)
    except ValueError as exc:problem=str(exc);st.warning(problem)
    if not tokens and not problem:problem='В области нет живых целей';st.warning(problem)
    friendly=[participant(data,t)['name'] for t in tokens if combat_side(data,t)!='Враг']
    if friendly:st.warning('Заденет героев и союзников: '+', '.join(friendly))
    st.caption('В области: '+(', '.join(participant(data,t)['name'] for t in tokens) or 'никого'))
    return center,tokens,problem


def render_area_spell(data,spell,target):
    from kalista_area import cast_area_spell
    token=next(t for t,a in participants(data) if a is target)
    center,tokens,problem=render_area_selection(data,'player',spell,token,'spell_area_'+str(spell['id']))
    dual,soul=spell_bonuses(data,spell);raw=spell_raw(spell['base'],data['spell_power'],dual,soul)
    st.caption(f"Мана {spell['mana']} · КД {spell.get('cd_left',0)}/{spell.get('cd_max',0)} · одно действие")
    for t in tokens:
        a=participant(data,t);preview=spell_damage_preview(data,spell,a,raw)
        st.caption(f"{a['name']}: −{preview['hp_loss']} HP · щит поглотит {preview['absorbed']} · без учёта крита")
    used=sum(x['source']=='player' and x.get('counts',True) for x in data['turn_actions'])
    reason=problem or ('У Калисты 0 HP' if data['hp_current']<=0 else '') or ('Не хватает маны' if data['mana_current']<spell['mana'] else '') or ('Перезарядка' if spell.get('cd_left') else '') or ('Действия закончились' if data['combat_active'] and used>=2 else '') or ('Калиста под страхом' if any(x['kind']=='fear' for x in data['effects']) else '')
    if reason:st.caption('Недоступно: '+reason)
    if st.button('Применить массовую атаку',key='cast_area_'+str(spell['id']),type='primary',disabled=bool(reason),use_container_width=True):
        try:
            for message in cast_area_spell(data,spell,center):log(message)
            persist_and_rerun('Массовая атака: '+spell['name'])
        except ValueError as exc:st.error(str(exc))
    with st.expander('Правила массовой атаки'):
        st.write(spell.get('desc',''))
        st.caption('Каждая цель получает полный урон. Крит и эффекты проверяются независимо. Мана, Пепел/Тень и перезарядка учитываются один раз за каст.')


def render_movement(data,source_token,target_token,player_mode=False):
    source=participant(data,source_token)
    if data['combat_active']:
        used=sum(x['source']==source_token and x.get('counts',True) for x in data.get('turn_actions',[]))
        st.caption(f'Действия: {max(0,2-used)}/2 · Перемещение: '+('использовано' if source.get('movement_used') else 'доступно'))
    st.caption('Дистанция до цели: '+(f'{separation(data,source_token,target_token):.1f} м · ' if data.get('distance_mode')=='meters' else '')+distance_between(data,source_token,target_token))


def render_ability_palette(data,source,player_mode=False):
    actor=participant(data,source)
    abilities=data['spells'] if source=='player' else [a for a in actor.get('actions',[]) if a.get('rule') not in ('move_close','move_far','move_point')]
    if not abilities:return None
    key='battle_spell' if source=='player' else 'action_choice_'+source
    available={a['id']:a for a in abilities}
    current=st.session_state.get(key,abilities[0]['id'])
    if current not in available:current=abilities[0]['id']
    used=sum(x['source']==source and x.get('counts',True) for x in data.get('turn_actions',[]))
    pending=st.session_state.pop('_pending_ability_'+source,None)
    if pending in available:
        st.session_state[key]=pending;current=pending
        st.session_state['board_mode_'+source]='Атака'
    palette=[]
    for i,a in enumerate(abilities):
        mana=a.get('mana',a.get('mana_cost',0));cd=a.get('cd_left',a.get('cooldown_left',0))
        reasons=[]
        if actor[hp_fields(actor)[0]]<=0:reasons.append('0 HP')
        if any(e['kind'] in ('fear','freeze') for e in actor.get('effects',[])):reasons.append('Страх')
        if mana>actor.get('mana_current',0):reasons.append('Не хватает маны')
        if cd:reasons.append(f'Перезарядка: {cd}')
        if data['combat_active'] and used>=2 and not a.get('reaction'):reasons.append('Действия закончились')
        if a.get('needs_setup'):reasons.append('Нужно настроить правила')
        if player_mode and data['combat_active'] and (not get_current_actor(data) or actor_token(get_current_actor(data))!=source) and not a.get('reaction'):reasons.append('Сейчас ход другого участника')
        if a.get('spent'):reasons.append('Нужна перезарядка')
        if a.get('charges_max') and not a.get('charges_left'):reasons.append('Нет зарядов')
        if a.get('rule')=='eye' and (not data['combat_active'] or actor.get('eye_used')):reasons.append('Десница недоступна')
        palette.append(dict(id=a['id'],name=a['name'],mana=mana,cd=cd,reason='; '.join(reasons)))
    st.session_state['_board_palette_'+source]=palette
    with st.expander('Все способности · просмотр недоступных'):
        selected=remembered_select('Способность' if source=='player' else 'Действие',list(available),key,default=current,format_func=lambda aid:available[aid]['name']+' · '+reach_label(available[aid]))
    return available[selected]


def render_battle_workstation(data,source,target_key,player_mode=False):
    from kalista_interactive_map import tactical_map
    from kalista_map_background import background
    tokens=[t for t,_ in visible_battle_participants(data)]
    default=default_opponent(data,source)
    target=st.session_state.get(target_key,default)
    if target not in tokens:target=default if default in tokens else tokens[0]
    ability=render_ability_palette(data,source,player_mode)
    changed=st.session_state.get('board_ability_'+source)
    if ability and changed is not None and changed!=ability['id']:st.session_state['board_mode_'+source]='Атака'
    if ability:st.session_state['board_ability_'+source]=ability['id']
    mode=st.radio('Режим карты',['Атака','Перемещение'],horizontal=True,key='board_mode_'+source)
    if editing() and not player_mode:
        st.caption('Библиотека и настройки преград: Ведущий → Карты.')
    setup=bool(editing() and not player_mode and st.toggle('Расстановка ведущего',key='map_setup_'+source))
    selected=source
    if setup:selected=remembered_select('Фигурка для расстановки',tokens,'map_edit_actor',default=source,format_func=lambda t:participant_label(data,t))
    area=bool(ability and is_area(ability) and mode=='Атака' and not setup and data.get('distance_mode')=='meters')
    center=list(data['positions'][target]) if area else None
    if area and ability.get('area_shape')=='cone' and math.dist(data['positions'][source],center)<=1e-9:center=[center[0]+1,center[1]]
    st.session_state.pop('_board_area_context',None)
    with st.container(key='battle_workstation'):
        map_column,panel=st.columns([1.65,1],gap='medium')
        with map_column:
            backdrop=background(data)
            if backdrop:st.caption('Локация: '+backdrop['name'])
            if data.get('distance_mode')=='meters':
                destination=tactical_map(data,source,'shared_map_'+source,center=center,radius=ability.get('area_radius_m',0) if area else 0,shape=ability.get('area_shape','circle') if area else 'circle',cone_length=ability.get('cone_length_m',0) if area else 0,cone_angle=ability.get('cone_angle_deg',60) if area else 60,mode='setup' if setup else 'move' if mode=='Перемещение' else 'area' if area else 'target',selected=selected,target=target,target_key=target_key,range_m=ability_range(ability) if ability and mode=='Атака' else None)
                target=st.session_state.get(target_key,target)
                if area:
                    st.session_state['_board_area_context']=(source,ability['id'],data.get('map_revision',0),data.get('turn_serial',0))
                    st.session_state['_board_area']=destination
                st.caption('Укажи направление конуса от атакующего.' if area and ability.get('area_shape')=='cone' else 'Выбери фигурку цели.' if mode=='Атака' and not area and not setup else 'Коснись центра области — оранжевая обводка показывает цели.' if area else 'Потяни фигурку или коснись точки назначения. Затем подтверди справа или под картой.')
            else:destination=data['positions'][source];st.info('Для поля в метрах включи актуальную карту.')
        with panel:
            with st.expander('Выбрать цель из списка'):
                target=remembered_select('Цель действия',tokens,target_key,default=target,format_func=lambda t:participant_label(data,t))
            render_focus_cards(data,source,target,player_mode)
            render_movement(data,source,target,player_mode)
            with st.container(key='board_actionpanel'):
                if setup or mode=='Перемещение':
                    actor=participant(data,source)
                    action=next(a for a in actor['actions'] if a.get('rule')=='move_point')
                    distance=math.dist(data['positions'][source],destination)
                    from kalista_statuses import movement_limit
                    limit=movement_limit(actor)
                    if not setup:st.caption(f'Перемещение: {distance:.1f} / {limit:g} м')
                    reasons=[]
                    if not setup:
                        if player_mode and data['combat_active'] and (not get_current_actor(data) or actor_token(get_current_actor(data))!=source):reasons.append('Сейчас ход другого участника')
                        if distance<=1e-9:reasons.append('Выбери точку назначения')
                        if distance>limit+1e-9:reasons.append(f'Больше {limit:g} м')
                        if data['combat_active'] and actor.get('movement_used'):reasons.append('Перемещение использовано')
                        if actor[hp_fields(actor)[0]]<=0:reasons.append('0 HP')
                        if any(e['kind'] in ('fear','freeze') for e in actor['effects']):reasons.append('Страх')
                    if not setup:
                        from kalista_obstacles import blocking_wall
                        if blocking_wall(data,data['positions'][source],destination,'movement'):reasons.append('Путь перекрывает преграда')
                    if reasons:st.caption('Недоступно: '+'; '.join(reasons))
                    if st.button('Сохранить расстановку' if setup else 'Переместиться',key='map_apply_'+source,type='primary',disabled=bool(reasons),use_container_width=True):
                        try:
                            if setup:
                                data['positions'][selected]=destination;data['map_revision']=data.get('map_revision',0)+1;invalidate_player_requests(data,'Расстановка изменилась; предложи действие заново');persist_and_rerun('Расстановка на карте')
                            elif player_mode:submit_player_action(data,action['id'],[source],False,destination=destination);st.success('Перемещение выполнено')
                            else:
                                for message in perform_action(data,source,action['id'],[source],destination=destination):log(message)
                                persist_and_rerun('Перемещение на карте')
                        except (ValueError,OSError) as exc:st.error(str(exc))
                elif ability:
                    if source=='player':render_selected_spell(data,participant(data,target),selected_id=ability['id'])
                    else:render_action_panel(data,source,target,player_mode,selected_id=ability['id'])
    st.session_state.pop('_board_area_context',None)
    return target


@st.fragment(run_every='3s')
def render_battle(data):
    data=st.session_state.get("data",data)
    latest,revision=read_state(SAVE_FILE)
    if latest is not None and revision!=st.session_state.get('_save_revision'):
        data=migrate(latest);recalc(data)
        st.session_state['data']=data
        st.session_state['_committed_data']=deepcopy(data)
        st.session_state['_save_revision']=revision

    render_range_audit(data)
    render_loot(data)
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
    tokens = [token for token, _ in visible_battle_participants(data)]
    if section == "Ход":
        if not active_token:
            active_token = remembered_select("Кто действует", tokens, "battle_manual_actor", default="player",
                                             format_func=lambda value: participant_label(data, value))
        token=render_battle_workstation(data,active_token,f'turn_target_{active_token}')
        render_recent_results(data)
        render_turn_context(data)
        with st.expander("Подробнее об участнике и цели"):
            render_combatant_card(data,active_token,"Действует",active=True)
            render_combatant_card(data,token,"Цель")
        st.caption('Попадание в область определяется по центру фигурки. Стены учитываются только после разметки ведущим.')
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
                    resists[element] = cols[i%2].number_input(f'Сопротивление: {element} (%)', min_value=0, max_value=95, value=npc['combat']['resists'][element])
            if st.form_submit_button('Сохранить NPC', type='primary'):
                try:
                    update_npc(data, npc_id, dict(name=name, role=role, location=location, side=side, description=description, public_notes=public, gm_notes=private,
                                                combat=dict(**{key:deepcopy(npc['combat'][key]) for key in ('actions','action_limit','mana_current','mana_max') if key in npc['combat']}, hp=hp, hp_max=maximum, armor=armor, attack_damage=attack, heal_amount=healing, initiative=initiative, attack_type=dtype, resists=resists)))
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
    npc['combat'].setdefault('actions',[])
    render_action_editor(data,'npc:'+npc_id)
    with st.expander('Удалить NPC', expanded=False):
        confirm = st.checkbox('Подтверждаю удаление NPC', key=f'gm_npc_delete_confirm_{npc_id}')
        if st.button('Удалить NPC', key=f'gm_npc_delete_{npc_id}', disabled=not confirm):
            delete_npc(data, npc_id); persist_and_rerun(f"Удалён NPC: {npc['name']}")


def render_gm(data):
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Стол ведущего</div>", unsafe_allow_html=True)
    history = undo_entries(SAVE_FILE)
    if st.button('Отменить последнее действие', key='gm_undo', disabled=not history, help=history[-1]['label'] if history else 'Нет действий для отмены'):
        undo_last_action()
    prefs = st.session_state.setdefault('_battle_preferences', {})
    if 'gm_section' not in st.session_state: st.session_state['gm_section'] = prefs.get('gm_section', 'Сцены')
    section = st.radio('Раздел ведущего', ['Сцены','NPC','Карты','Записная книжка'], key='gm_section', horizontal=True, label_visibility='collapsed')
    prefs['gm_section'] = section
    if section == 'Сцены':
        from kalista_map_library_ui import render_scene_map
        render_scene_map(data,'gm_scene_location')
        render_scene_editor(data)
    elif section == 'NPC': render_npc_editor(data)
    elif section == 'Карты':
        from kalista_map_library_ui import render_map_hub
        render_map_hub(data,persist_and_rerun)
    else:
        with st.form('gm_notebook'):
            notes = st.text_area('Общие заметки ведущего', value=data['gm_notes'], height=260)
            if st.form_submit_button('Сохранить заметки', type='primary'):
                data['gm_notes'] = notes
                persist_and_rerun('Заметки ведущего')
        current = scene_record(data, data['active_scene_id'])
        if current: st.caption('Текущая сцена: ' + current['name'])
        st.download_button('Скачать записную книжку', data['gm_notes'], file_name='gm_notes.md', mime='text/markdown')


def render_turn_context(data):
    if data['combat_active'] and data['turn_order']:
        start=data['current_turn'];queue=data['turn_order']
        upcoming=(queue[start:] + queue[:start])[:4]
        st.caption('Очередь: ' + ' → '.join(participant_label(data,actor_token(actor)) for actor in upcoming))
    entries=data.get('turn_actions', [])
    reactions=sum(not entry.get('counts',True) for entry in entries)
    with st.expander(f'Этот ход · действий: {len(entries)-reactions} · реакций и усилений: {reactions}', expanded=False):
        if not entries: st.caption('Действия ещё не применялись. Доступны два действия и одно перемещение.')
        for entry in entries[-5:]: st.write(f"**{entry['name']} → {entry['target']}** · {entry['result']}")
    st.caption('Два действия и одно перемещение за ход.')


def render_action_panel(data, source_token, victim_token, player_mode=False, selected_id=None):
    source=participant(data,source_token)
    if not source.get('actions'):
        source['actions']=[action_template('Атака',amount=source.get('attack_damage',0),shared_attack=True,damage_type=source.get('attack_type','Физический')),
                           action_template('Лечение',kind='heal',amount=source.get('heal_amount',0))]
    actions={a['id']:a for a in source['actions'] if a.get('rule') not in ('move_close','move_far','move_point')}
    if not actions:
        st.caption('Атакующих способностей пока нет. Перемещение доступно в отдельном блоке боя.')
        return
    aid=selected_id if selected_id is not None else remembered_select('Действие', list(actions), f'action_choice_{source_token}', format_func=lambda value: actions[value]['name']+' · '+reach_label(actions[value]))
    action=actions[aid]
    if action['needs_setup']: st.warning('Для этого действия ведущему нужно задать боевые числа и подтвердить правила в редакторе действий.')
    critical=False
    if action['kind']=='damage' and source_token.startswith('enemy:'):
        crit_hint=f" · автоматический крит {source.get('critical_chance',0):g}%"
    elif action['kind']=='damage' and action['shared_attack'] and source.get('sheet_profile'):
        crit_hint=f" · автоматический крит {source['sheet_profile']['critical_chance']:g}%"
    else:crit_hint=''
    amount=action_amount(source,action,critical)
    if critical: st.info(f'Критический урон: {amount} за попадание. Обычный урон сейчас не используется.')
    else: st.caption(f'{amount} × {action["hits"]} · {action["damage_type"]}'+crit_hint)
    target_key=f'action_targets_{source_token}_{aid}'
    anchor_key=f'_action_target_anchor_{source_token}_{aid}'
    if action.get('rule') in ('eye','stance'):victim_token=source_token
    initial=[victim_token] if action['kind']!='damage' or combat_side(data,victim_token)=='Враг' or combat_side(data,source_token)=='Враг' else []
    if st.session_state.get(anchor_key)!=victim_token:
        st.session_state[target_key]=[victim_token]
        st.session_state[anchor_key]=victim_token
    valid_tokens=[t for t,_ in visible_battle_participants(data)]
    if target_key in st.session_state:
        st.session_state[target_key]=[t for t in st.session_state[target_key] if t in valid_tokens]
    area_center=None
    if data.get('distance_mode')=='meters' and is_area(action):
        area_center,victims,area_problem=render_area_selection(data,source_token,action,victim_token,'action_area_'+aid)
    else:
        with st.expander('Несколько целей / изменить цели'):
            victims=st.multiselect('Цели',valid_tokens, default=initial if target_key not in st.session_state else None, format_func=lambda token: participant_label(data,token), key=target_key,placeholder='Выбери цели')
    st.caption('Применится к: '+(', '.join(participant(data,t)['name'] for t in victims) or 'цель не выбрана'))
    if action['kind']=='damage' and any(combat_side(data,t) in ('Героиня','Союзник') for t in victims) and combat_side(data,source_token)!='Враг':
        st.warning('Выбрана дружественная цель: действие нанесёт ей урон.')
    reaction=action.get('reaction',action['name']=='Совершенная контратака')
    if reaction: st.caption('Реакция: ведущий подтверждает, что по персонажу прошла ближняя атака.')
    manual_amount=None
    if editing() and not player_mode and not critical and action['kind']!='note':
        with st.expander('Ручная поправка этого действия'):
            override=st.checkbox('Назначить величину на это применение',key=f'action_override_{source_token}_{aid}')
            if override: manual_amount=st.number_input('Величина за попадание',min_value=0,value=amount,key=f'action_override_value_{source_token}_{aid}')
    for token in victims:
        target=participant(data,token)
        if action['kind']=='damage':
            st.caption('Дистанция: '+(f'{separation(data,source_token,token):.1f} м · ' if data.get('distance_mode')=='meters' else '')+distance_between(data,source_token,token))
            try:result=preview_action(data,source_token,action,token,critical,manual_amount,area_center=area_center)
            except ValueError as exc:st.warning(str(exc));continue
            if result.get('miss'):st.warning(f"Шанс промаха из-за дистанции и эффектов: {result['miss']*100:g}% за попадание.")
            if result.get('dodge'):st.caption(f"Уклонение цели: {result['dodge']*100:.1f}% на каждое попадание")
            loss=str(result['hp_min']) if result['hp_min']==result['hp_max'] else f"{result['hp_min']}–{result['hp_max']}"
            st.caption(f"{target['name']}: потеряет {loss} HP, щит поглотит {result['shield']}")
        elif action['kind']=='heal': st.caption(f"{target['name']}: +{min(amount if manual_amount is None else manual_amount,max(0,target[hp_fields(target)[1]]-target[hp_fields(target)[0]]))} HP")
    unavailable=action['needs_setup'] or action['cooldown_left']>0 or action['spent'] or not victims or (action['kind']!='note' and (amount if manual_amount is None else manual_amount)<=0) or (action['charges_max']>0 and action['charges_left']==0) or action['mana_cost']>source.get('mana_current',0)
    if action['mana_cost']: st.caption(f"Стоимость: {action['mana_cost']} MP")
    if action['charges_max']: st.caption(f"Заряды: {action['charges_left']}/{action['charges_max']}")
    if action['cooldown_left']: st.caption(f'Восстановится через {action["cooldown_left"]} начала хода этого участника')
    if action['spent']: st.caption('Нужна ручная перезарядка у ведущего')
    if action.get('rule')=='eye' and (not data['combat_active'] or source.get('eye_used')):unavailable=True
    if action.get('rule','').startswith('move_') and source.get('movement_used') and data['combat_active']:unavailable=True
    used=sum(a['source']==source_token and a.get('counts',True) for a in data.get('turn_actions',[]))
    if data['combat_active'] and used>=2 and not reaction and not action.get('rule','').startswith('move_'):unavailable=True
    reasons=[]
    if player_mode and data['combat_active'] and (not get_current_actor(data) or actor_token(get_current_actor(data))!=source_token) and not reaction:reasons.append('Сейчас ход другого участника');unavailable=True
    if source[hp_fields(source)[0]]<=0:reasons.append('у персонажа 0 HP');unavailable=True
    if any(x['kind']=='fear' for x in source.get('effects',[])):reasons.append('персонаж под страхом');unavailable=True
    if action['charges_max'] and action['charges_left']<=0:reasons.append('заряды закончились')
    if action.get('rule')=='eye' and source.get('eye_used'):reasons.append('Десница уже использована в этом бою')
    if action.get('rule','').startswith('move_') and source.get('movement_used') and data['combat_active']:reasons.append('перемещение использовано')
    if action['needs_setup']:reasons.append('правила способности ещё не настроены')
    if action['cooldown_left']>0:reasons.append(f"перезарядка: {action['cooldown_left']} хода")
    if action['spent']:reasons.append('нужна ручная перезарядка')
    if source.get('mana_current',0)<action['mana_cost']:reasons.append('не хватает маны')
    if not victims:reasons.append('выбери цель')
    if data['combat_active'] and used>=2 and not reaction and not action.get('rule','').startswith('move_'):reasons.append('действия закончились')
    for token in victims:
        try:
            if area_center is not None:check_area_aim(data,source_token,action,area_center)
            else:check_reach(data,source_token,action,token)
        except ValueError as exc:reasons.append(str(exc));unavailable=True
    if area_center is not None and area_problem:reasons.append(area_problem);unavailable=True
    if reasons:st.caption('Недоступно: '+'; '.join(dict.fromkeys(reasons)))
    if st.button('Применить действие',key=f'perform_{source_token}_{aid}',type='primary',disabled=unavailable,use_container_width=True):
        try:
            if player_mode:
                submit_player_action(data,aid,victims,critical,area_center=area_center)
                st.success('Действие применено')
            else:
                for message in perform_action(data,source_token,aid,victims,critical,reaction,manual_amount,area_center=area_center): log(message)
                persist_and_rerun('Действие: '+action['name'])
        except (ValueError, OSError) as exc: st.error(str(exc))
    with st.expander('Описание способности'):
        st.caption(action['description'])


def render_action_editor(data,token):
    if not editing():return
    target=participant(data,token)
    if token.startswith('enemy:'):
        from kalista_enemy_ui import render_enemy_setup
        render_enemy_setup(data,token,persist_and_rerun)
    with st.expander('Настроить действия и лимит хода'):
        st.caption('У каждого участника 2 действия и 1 перемещение за ход. Контратака не расходует действия.')
        if not target['actions']:
            if st.button('Создать действия атаки и лечения',key=f'init_actions_{token}'):
                target['actions']=[action_template('Атака',amount=target.get('attack_damage',0)),action_template('Лечение',kind='heal',amount=target.get('heal_amount',0))];persist_and_rerun()
            return
        aid=st.selectbox('Редактировать действие',[a['id'] for a in target['actions']],format_func=lambda value:next(a['name'] for a in target['actions'] if a['id']==value),key=f'edit_action_{token}')
        action=next(a for a in target['actions'] if a['id']==aid)
        with st.form(f'action_form_{token}_{aid}'):
            editor_tabs=st.tabs(['Основное', 'Дополнительно', 'Эффекты', 'Правила'])
            with editor_tabs[0]:
                name=st.text_input('Название действия',action['name'])
                kind=st.selectbox('Результат',['damage','heal','shield','note'],index=['damage','heal','shield','note'].index(action['kind']),format_func=lambda v:dict(damage='Урон',heal='Лечение',shield='Щит',note='Статус')[v])
                amount=st.number_input('Базовая величина',min_value=0,value=action['amount'])
                shared=st.checkbox('Брать урон атаки из характеристик участника',action['shared_attack'])
                damage_multiplier=st.number_input('Множитель урона способности',min_value=0.01,value=float(action.get('multiplier',1)),step=0.1)
                hits=st.number_input('Попаданий',min_value=1,max_value=10,value=action['hits'])
                dtype=st.selectbox('Тип урона',DAMAGE_TYPES,index=DAMAGE_TYPES.index(action['damage_type']))
                reach=st.selectbox('Дальность атаки',['Ближняя','Дальняя','Любая'],index=['Ближняя','Дальняя','Любая'].index(action.get('reach','Ближняя')))
                range_m=st.number_input('Дальность в метрах (0 — не задана)',min_value=0.,value=float(action.get('range_m') or 0)) or None
                radius=st.number_input('Радиус массовой атаки (м; 0 — без области)',min_value=0.,value=float(action.get('area_radius_m',0)))
                shape_settings=edit_shape(action,'gm_shape_'+token+'_'+aid)
                cooldown=st.number_input('Перезарядка: начала личного хода',min_value=0,value=action['cooldown'])
                mana_cost=st.number_input('Стоимость маны (0 — без маны)',min_value=0,value=action['mana_cost'])
            with editor_tabs[1]:
                charges=st.number_input('Зарядов (0 — без ограничения)',min_value=0,value=action['charges_max'])
                penetration=st.number_input('Вычесть из брони цели перед физическим уроном',min_value=0,value=action.get('armor_penetration',0))
                dice_count=st.number_input('Дополнительных кубиков урона',min_value=0,max_value=10,value=action.get('extra_dice_count',0))
                dice_sides=st.number_input('Граней дополнительного кубика (0 — нет броска)',min_value=0,max_value=1000,value=action.get('extra_dice_sides',0))
                manual=st.checkbox('После применения нужна ручная перезарядка',action['manual_recharge'])
                reaction=st.checkbox('Реакция вне своего хода (не расходует лимит)',action.get('reaction',False))
            with editor_tabs[2]:
                from kalista_statuses import edit_proc
                hit_effect=edit_proc(action,'proc_'+token+'_'+aid)
                effect_kind=st.selectbox('Дополнительный эффект',list(EFFECT_KINDS),index=list(EFFECT_KINDS).index(action['effect_kind']),format_func=lambda v:EFFECT_KINDS[v])
                effect_value=st.number_input('Величина эффекта (для брони можно отрицательную)',value=action['effect_value'])
                effect_chance=st.number_input('Шанс дополнительного эффекта (%)',min_value=0.,max_value=100.,value=float(action.get('effect_chance',100)))
                duration=st.number_input('Длительность: раунды / тики (0 — бессрочно)',min_value=0,value=action['duration'])
                element=st.selectbox('Стихия эффекта',ELEMENTS,index=ELEMENTS.index(action['effect_element']))
                stacks=st.number_input('Максимум наложений',min_value=1,max_value=20,value=action['max_stacks'])
            with editor_tabs[3]:
                desc=st.text_area('Правила и условия',action['description'])
                ready=st.checkbox('Боевые числа и правила этого действия подтверждены',not action['needs_setup'])
            if st.form_submit_button('Сохранить действие'):
                candidate=deepcopy(data);item=next(a for a in participant(candidate,token)['actions'] if a['id']==aid)
                item.update(name=name,kind=kind,amount=amount,shared_attack=shared,hits=hits,damage_type=dtype,cooldown=cooldown,manual_recharge=manual,effect_kind=effect_kind,effect_value=effect_value,duration=duration,effect_element=element,max_stacks=stacks,description=desc,needs_setup=not ready,mana_cost=mana_cost,charges_max=charges,charges_left=charges if charges!=action['charges_max'] else action['charges_left'],armor_penetration=penetration,extra_dice_count=dice_count,extra_dice_sides=dice_sides,range_m=range_m,area_radius_m=radius,**shape_settings)
                item['hit_effect']=hit_effect
                item['multiplier']=damage_multiplier
                item['effect_chance']=effect_chance
                item['reaction']=reaction
                item['reach']=reach
                try:
                    validate_action_state(candidate);data.clear();data.update(candidate);persist_and_rerun('Настроено действие')
                except ValueError as exc: st.error(str(exc))
        if st.button('Восстановить это действие',key=f'recharge_{token}_{aid}'):
            action['spent']=False;action['cooldown_left']=0;action['charges_left']=action['charges_max'];persist_and_rerun('Ручная перезарядка')
        remove=st.checkbox('Подтвердить удаление способности',key=f'delete_action_confirm_{token}_{aid}')
        if st.button('Удалить способность',key=f'delete_action_{token}_{aid}',disabled=not remove):
            target['actions']=[a for a in target['actions'] if a['id']!=aid];persist_and_rerun('Удалена способность')
        with st.form(f'new_action_{token}'):
            new_name=st.text_input('Новое действие')
            if st.form_submit_button('Добавить действие') and new_name.strip():
                target['actions'].append(action_template(new_name.strip(),needs_setup=True));persist_and_rerun('Новое действие')


def access_config():
    # Credentials stay on the host and are never part of an exported game save.
    try: return dict(st.secrets.get('access', {}))
    except Exception: return {}


def require_access():
    config=access_config()
    if not config.get('gm_password') or not config.get('player_password'):
        st.error('Доступ не настроен. Запусти программу через локальный файл запуска, который создаёт ключи доступа.')
        st.stop()
    if st.session_state.get('_role') in ('gm','player'): return st.session_state['_role']
    st.markdown("<div class='main-title'>Калиста · игровой стол</div>",unsafe_allow_html=True)
    st.caption('Ведущий и игрок входят с разными ключами.')
    if time.time() < st.session_state.get('_login_after',0):
        st.warning('Подожди несколько секунд перед следующей попыткой');st.stop()
    with st.form('login'):
        role=st.selectbox('Кто входит',['Ведущий','Игрок · Шеогарат'])
        password=st.text_input('Ключ доступа',type='password')
        if st.form_submit_button('Войти',type='primary'):
            expected=config['gm_password' if role=='Ведущий' else 'player_password']
            if hmac.compare_digest(password.encode(),str(expected).encode()):
                st.session_state['_role']='gm' if role=='Ведущий' else 'player'
                st.session_state.pop('_login_after',None)
                st.session_state.pop('login',None);st.rerun()
            else:
                st.session_state['_login_after']=time.time()+3
                st.error('Ключ не подходит')
    st.stop()


def submit_player_action(data, aid, victims, critical=False, destination=None, area_center=None):
    from kalista_direct import apply_player_action
    latest,revision,messages=apply_player_action(SAVE_FILE,data,aid,victims,destination,area_center)
    st.session_state['data']=latest
    st.session_state['_committed_data']=deepcopy(latest)
    st.session_state['_save_revision']=revision
    st.rerun()


@st.fragment(run_every='3s')
def render_live_battle():
    latest,_=read_state(SAVE_FILE)
    if latest is None:return
    latest=migrate(latest)
    if latest['combat_active']:
        actor=get_current_actor(latest)
        st.markdown(f"**Сейчас: раунд {latest['round']} · {actor['name'] if actor else 'нет участника'}**")
        if actor:
            token=actor_token(actor);target=participant(latest,token)
            used=sum(x['source']==token and x.get('counts',True) for x in latest['turn_actions'])
            st.caption(f"Действия {max(0,2-used)}/2 · Перемещение: {'использовано' if target.get('movement_used') else 'доступно'}")
    st.caption(f"{latest['name']}: {latest['hp_current']}/{latest['hp_max']} HP · {latest['ally']['name']}: {latest['ally']['hp']}/{latest['ally']['hp_max']} HP")



def render_loot(data):
    batches=data.get('loot_batches',[])
    pending=[r for b in batches for r in b['items'] if not r['recipient'] and not r['discarded']]
    reward=data.get('last_battle_reward') if not data['combat_active'] else None
    if not pending and not reward:return
    title='Итоги последнего боя' if reward else f'Добыча · ожидает выдачи: {len(pending)}'
    with st.expander(title,expanded=False):
        if reward:
            st.markdown('**Опыт уже начислен**')
            for hero in reward['heroes']:
                st.write(f"**{hero['name']}** · +{hero['xp']} XP · уровень {hero['level_after']}")
                if hero['free_points']:st.caption(f"Новый уровень · свободные очки: +{hero['free_points']}")
            with st.expander('Расчёт опыта по врагам'):
                for hero in reward['heroes']:
                    st.markdown('**'+escape(hero['name'])+'**')
                    for detail in hero['details']:st.caption(f"{detail['name']}: {detail['xp']} XP · {detail['reason']}")
            last=next((b for b in batches if b['battle_id']==reward['battle_id']),None)
            if last:
                total=len(last['items']);waiting=sum(not r['recipient'] and not r['discarded'] for r in last['items'])
                st.caption(f'Добыча этого боя: {total} · ожидает выдачи: {waiting}')
                if not total:st.caption('В этом бою предметы не выпали')
        if pending:
            st.markdown(f'**Ожидают выдачи: {len(pending)}**')
            st.caption('Снаряжение попадёт в резерв. Сравнение показывает результат его надевания, а не самой выдачи.')
        for index,record in enumerate(pending):
            original=record['item'];prefix='loot_'+record['id']
            with st.expander(rarity_label(original)+' · '+original['name']+f" ×{original['qty']}",expanded=index==0):
                st.caption('Источник: '+record['enemy'])
                item=deepcopy(original)
                recipients=['player']+(['ally'] if data['ally'].get('sheet_profile') else [])
                recipient=st.selectbox('Получатель',recipients,format_func=lambda t:data['name'] if t=='player' else data['ally']['name'],key=prefix+'_recipient')
                if editing():
                    with st.expander('Изменить свойства перед выдачей'):
                        item['name']=st.text_input('Название предмета',item['name'],key=prefix+'_name')
                        item['rarity']=st.selectbox('Редкость',RARITIES,index=RARITIES.index(item['rarity']),key=prefix+'_rarity')
                        item['qty']=st.number_input('Количество',min_value=1,max_value=100,value=item['qty'],key=prefix+'_qty')
                        item['desc']=st.text_area('Свойства и описание',item['desc'],key=prefix+'_desc')
                        if item.get('gear'):
                            root_keys={'Броня':'armor','Атака':'attack','Интеллект':'int','Сила заклинаний':'spell_power'}
                            for key,value in list(item['gear']['ally_bonuses'].items()):
                                new=st.number_input('Бонус: '+key,min_value=0,value=value,key=prefix+'_bonus_'+key)
                                item['gear']['ally_bonuses'][key]=new;item['gear']['root_bonuses'][root_keys[key]]=new
                        elif item.get('use'):item['use']['value']=st.number_input('Сила расходника',min_value=1,value=item['use']['value'],key=prefix+'_use')
                st.write(item['desc'])
                if item.get('gear'):
                    from kalista_view import show_gear,show_comparison
                    displayed=dict(name=item['name'],rarity=item['rarity'],description='',bonuses=item['gear']['ally_bonuses'])
                    show_gear(displayed)
                    if item['rarity']=='Легендарный':
                        level=data['level'] if recipient=='player' else data['ally']['sheet_profile']['level']
                        st.caption(f'При выдаче привяжется к выбранному владельцу на уровне {level}; рост +2% исходных бонусов за уровень.')
                    show_comparison(data,item,recipient,loot=True)
                elif item.get('use'):
                    st.caption({'heal':'Лечение','mana':'Восстановление маны','shield':'Щит'}[item['use']['kind']]+f" · {item['use']['value']}")
                cols=st.columns(2)
                if cols[0].button('Выдать предмет',key=prefix+'_assign',type='primary'):
                    try:
                        assign_loot(data,record['id'],recipient,item);log('Выдана добыча: '+item['name']);persist_and_rerun('Выдача добычи')
                    except (ValueError,OSError) as exc:st.error(str(exc))
                if cols[1].button('Не выдавать',key=prefix+'_discard'):
                    try:assign_loot(data,record['id'],'discard');persist_and_rerun('Добыча отклонена')
                    except (ValueError,OSError) as exc:st.error(str(exc))
        completed=[r for b in batches for r in b['items'] if r['recipient'] or r['discarded']]
        if completed:
            with st.expander('История выдачи добычи'):
                for record in reversed(completed):
                    name=data['name'] if record['recipient']=='player' else data['ally']['name']
                    status='Не выдано' if record['discarded'] else 'Выдано: '+name
                    st.write(record['item']['name']+' · '+status)
        if not pending:st.caption('Вся добыча распределена')


def render_loot_settings(data):
    if not editing():return
    config=loot_settings(data)
    with st.expander('Настройки случайной добычи'):
        with st.form('loot_configuration'):
            for kind in DEFAULT_CHANCES:
                st.markdown('**'+kind+' враг**')
                config['chances'][kind]=st.number_input('Шанс предмета (%)',min_value=0.,max_value=100.,value=float(config['chances'][kind]),key='loot_chance_'+kind)
                cols=st.columns(5)
                config['weights'][kind]=[cols[i].number_input(rarity,min_value=0.,value=float(config['weights'][kind][i]),key='loot_weight_'+kind+'_'+rarity) for i,rarity in enumerate(RARITIES)]
            st.caption('Веса редкости — относительные частоты. Настройки фиксируются на старте нового боя.')
            if st.form_submit_button('Сохранить добычу'):
                try:
                    candidate=deepcopy(data);candidate['loot_settings']=config;loot_settings(candidate)
                    data['loot_settings']=config;persist_and_rerun('Настройки добычи')
                except ValueError as exc:st.error(str(exc))


def render_backups():
    with st.expander('Снимки сохранений'):
        st.caption('Последние 30 автоматических снимков и до 10 каждого ручного типа. Время в именах — UTC.')
        if st.button('Создать снимок сейчас',key='snapshot_now'):
            create_snapshot(SAVE_FILE);st.success('Снимок создан')
        snapshots=list_snapshots(SAVE_FILE)
        if snapshots:
            name=st.selectbox('Сохранённый снимок',[p.name for p in snapshots],key='snapshot_choice')
            st.download_button('Скачать снимок',(SAVE_FILE.parent/'save_snapshots'/name).read_bytes(),file_name=name,mime='application/json')
            st.caption('Восстановление заменит текущую игру выбранным снимком. Текущая версия останется в автоматических снимках.')
            if st.button('Восстановить выбранный снимок',key='snapshot_restore'):
                try:
                    restore_snapshot(SAVE_FILE,name,st.session_state['_save_revision'],migrate)
                    for key in list(st.session_state):
                        if key!='_role':del st.session_state[key]
                    st.rerun()
                except (ValueError,OSError) as exc:st.error(str(exc))
        else:st.caption('Снимков пока нет')


@st.fragment(run_every='3s')
def render_player():
    latest,revision=read_state(SAVE_FILE)
    data=migrate(latest if latest is not None else deepcopy(DEFAULT))
    public=public_player_state(data)
    profile=public['ally'].get('sheet_profile')
    if st.session_state.get('player_section')!='Бой':
        st.markdown("<div class='main-title'>"+escape(public['ally']['name'])+'</div>',unsafe_allow_html=True)
        st.caption('Игрок · '+(profile['race']+' · '+profile['class'] if profile else 'Союзник'))
    if public['combat_active'] and st.session_state.get('player_section')!='Бой':
        current=public['turn_order'][public['current_turn']] if public['turn_order'] else None
        st.info(f"Раунд {public['round']} · Ход: {current['name'] if current else 'нет участников'}")
    section=st.session_state.get('player_section','Обзор')
    if section=='Обзор':render_combatant_card(data,'ally','Твой персонаж',active=True)
    elif section!='Бой':st.caption(section+' · HP '+str(public['ally']['hp'])+'/'+str(public['ally']['hp_max']))
    if section=='Бой':
        actor=get_current_actor(data) if data['combat_active'] else None
        used=sum(x['source']=='ally' and x.get('counts',True) for x in data.get('turn_actions',[]))
        with st.container(key='player_battle_hud'):
            st.caption(('Раунд '+str(data['round'])+' · ход: '+actor['name'] if actor else 'Бой не начат')+f" · Действия {max(0,2-used)}/2 · Перемещение "+('использовано' if data['ally'].get('movement_used') else 'доступно'))
        if data['combat_active']:
            own=bool(actor and actor_token(actor)=='ally')
            if st.button('Конец моего хода',key='player_end_turn',disabled=not own,use_container_width=True):
                try:
                    from kalista_direct import finish_player_turn
                    latest,newrev=finish_player_turn(SAVE_FILE,data)
                    st.session_state['data']=latest;st.session_state['_committed_data']=deepcopy(latest);st.session_state['_save_revision']=newrev;st.rerun()
                except (ValueError,OSError) as exc:st.error(str(exc))
        if not data['combat_active'] and data.get('last_battle_reward'):
            hero=next((x for x in data['last_battle_reward']['heroes'] if x['token']=='ally'),None)
            if hero:st.caption(f"Награда за бой: +{hero['xp']} XP · уровень {hero['level_after']}"+(f" · +{hero['free_points']} свободных очков" if hero['free_points'] else ''))
        target=render_battle_workstation(data,'ally','player_battle_target',player_mode=True)
        with st.expander('Подробнее об участнике и цели'):
            render_combatant_card(data,'ally','Твой персонаж',active=True)
            render_combatant_card(data,target,'Цель')
        render_recent_results(data)
    elif section=='Сцена':
        from kalista_map_library_ui import render_scene_map
        render_scene_map(data)
        if public['scene']: st.markdown(public['scene'])
        else: st.caption('Ведущий ещё не начал сцену')
    else:render_player_sheet_section(section,data,SAVE_FILE.parent)
    if section=='Бой' and profile and profile['abilities']:
        with st.expander('Правила способностей'):st.write(readable_rules(profile['abilities']))
    if section=='Бой':st.caption('Действия применяются сразу. Попадание в область проверяется по центру фигурки.')
    elif section not in ('Сцена','Кубики'):st.caption('Изменения листа сохраняются кнопками в формах.')


@st.fragment(run_every='3s')
def render_sidebar_status():
    latest,_=read_state(SAVE_FILE)
    data=migrate(latest) if latest is not None else st.session_state.data
    st.caption(f"Ур.{data['level']} · {data['class']}")
    with st.container(key='sidebar_health'):
        st.progress(min(data["hp_current"]/max(data["hp_max"],1),1.0), text=f"HP {data['hp_current']}/{data['hp_max']}")
    with st.container(key='sidebar_mana'):
        st.progress(min(data["mana_current"]/max(data["mana_max"],1),1.0), text=f"MP {data['mana_current']}/{data['mana_max']}")
    if data.get("combat_active"):
        st.markdown(f"**Раунд {data['round']}**")
        actor=get_current_actor(data)
        if actor: st.info(f"Ход: {actor['name']}")


# ===================== INIT =====================
role = require_access()
if role == 'player':
    st.markdown('''<style>
    @media(min-width:641px){
      [data-testid="stSidebar"]{order:2;border-right:0;border-left:1px solid #44364e}
      [data-testid="stMain"]{order:1}
    }
    </style>''',unsafe_allow_html=True)
    if st.session_state.get('player_section')=='Действия':st.session_state['player_section']='Бой'
    with st.sidebar:
        st.markdown("<div class='main-title' style='font-size:1.35rem'>✧ Шеогарат</div>",unsafe_allow_html=True)
        st.radio('Меню персонажа',PLAYER_SECTIONS,key='player_section',label_visibility='collapsed')
        st.toggle('Режим редактирования',key='_edit_mode',help='Показывает поля настройки персонажа. Игровые действия доступны и без него.')
        st.divider()
        if st.button('Выйти', key='player_logout'):
            st.session_state.clear();st.rerun()
    render_player()
    st.stop()
if st.session_state.get('_sync_notice'):
    st.warning(st.session_state.pop('_sync_notice'))
if "data" not in st.session_state:
    st.session_state.data=load()
    recalc(st.session_state.data)
data=st.session_state.data
if data.get("schema_version", 5) < 30:
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
    render_sidebar_status()
    active_scene = scene_record(data, data['active_scene_id'])
    if active_scene: st.caption('Сцена: ' + active_scene['name'])
    st.divider()
    if st.button('Обновить игру', key='sync_game', use_container_width=True):
        st.session_state['data']=load()
        st.session_state['_committed_data']=deepcopy(st.session_state['data'])
        st.rerun()
    if st.button('Выйти', key='gm_logout'):
        st.session_state.clear();st.rerun()
    # Действия игрока применяются напрямую; очередь согласования больше не используется.
    st.toggle('Режим редактирования',key='_edit_mode',help='Показывает настройки персонажей, сцен и правил.')
    page=st.radio("Меню",["Обзор","Бой","Отряд","Экипировка","Характеристики","Инвентарь","Заклинания","Квесты","Ведущий","Кубики","Биография"],label_visibility="collapsed", key="page")
    st.divider()
    if editing():
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
                        if key not in ("data", "_role", "_save_revision"): del st.session_state[key]
                    persist_and_rerun()
            except (ValueError, TypeError, KeyError) as exc:
                st.error(f"Импорт отменён: {exc}")
        reset_confirm = st.checkbox("Подтверждаю сброс к исходной Калисте")
        if st.button("🔄 Сброс",use_container_width=True, disabled=not reset_confirm):
            restored = migrate(deepcopy(DEFAULT)); recalc(restored)
            if save(restored):
                st.session_state.data = restored
                for key in list(st.session_state):
                    if key not in ("data", "_role", "_save_revision"): del st.session_state[key]
                persist_and_rerun()

def apply_view_item(item):
    log(use_item(data,item));persist_and_rerun('Применение предмета')

def apply_view_special(key):
    log(activate_special(data,key));persist_and_rerun('Особое умение')

def apply_view_equip(item_id):
    equip_root_reserve(data,item_id);persist_and_rerun('Смена снаряжения')

if gm_view(page,data,apply_view_item,apply_view_special,apply_view_equip,persist_and_rerun):st.stop()

# ===================== ОБЗОР =====================
if page=="Обзор":
    st.markdown(f"<div class='main-title'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{data['race']} · {data['class']} · Ур.{data['level']}</div>", unsafe_allow_html=True)
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
                st.caption("Портрет пока не добавлен.")
        with info_column:
            with st.container(key='overview_health'):
                st.progress(min(data["hp_current"]/max(data["hp_max"],1),1.0),text=f"HP {data['hp_current']}/{data['hp_max']}")
            with st.container(key='overview_mana'):
                st.progress(min(data["mana_current"]/max(data["mana_max"],1),1.0),text=f"MP {data['mana_current']}/{data['mana_max']}")
            m1,m2=st.columns(2)
            m1.metric("Сила заклинаний",f"+{data['spell_power']*100:.0f}%")
            m2.metric("Броня",data["armor"])
            m3,m4=st.columns(2)
            m3.metric("Инициатива",data["initiative"])
            m4.metric("Свободные очки",data["free_points"])
            st.caption(f"Уклонение: {evasion_chance(data)*100:.1f}% от прямых физических атак")
    st.markdown("<div class='section-h'>Сопротивления</div>", unsafe_allow_html=True)
    render_stat_grid([(e,f"{effective_defense(data,e):g}%") for e in ELEMENTS], elements=True)
    st.caption("Сопротивления в процентах, максимум 95%. Расовая защита от Тьмы дополнительно снижает оставшийся урон на 10%.")
    st.markdown("<div class='section-h'>Характеристики</div>", unsafe_allow_html=True)
    render_stat_grid([(n,total_stat(data,n)) for n in ["Сила","Выносливость","Ловкость","Мудрость","Интеллект","Харизма","Дух"]])
    total_xp=xp_needed(data['level'])
    data['xp_to_next']=max(0,total_xp-data['xp'])
    st.progress(1.0 if data['level']==MAX_LEVEL else min(1,max(0,data['xp']/max(1,total_xp))),text=f"Опыт уровня: {data['xp']} / {total_xp} XP · до следующего уровня: {data['xp_to_next']}")
    st.markdown("<div class='section-h'>Опыт</div>", unsafe_allow_html=True)
    if editing():
        x1,x2,x3=st.columns([2,1,1])
        ax=x1.number_input("XP",0,value=100,step=50)
        if x2.button("➕ XP"): data["xp"]+=ax; data["xp_to_next"]=max(0,data["xp_to_next"]-ax); persist_and_rerun()
        if x3.button("⬆ Ур.+1",disabled=data["level"]>=MAX_LEVEL):
            data["xp"]=max(0,data["xp"]-xp_needed(data["level"])); data["level"]+=1; data["free_points"]+=4; data["xp_to_next"]=xp_needed(data["level"]); recalc(data); persist_and_rerun()
    
        with st.expander("Настройки портрета", expanded=False):
            data["portrait_url"] = st.text_input("URL своего портрета (пусто — портрет Калисты)", value=data.get("portrait_url", ""), key="portrait")

# ===================== БОЙ =====================
elif page=="Бой":
    render_battle(data)
    with st.expander("Состояние стола · автообновление"):
        render_live_battle()

elif page=="Отряд":
    render_party(data)

# ===================== ЭКИПИРОВКА =====================
elif page=="Ведущий":
    render_loot_settings(data)
    render_backups()
    with st.container(key="gm_table"):
        render_gm(data)

elif page=="Экипировка":
    with st.expander("Резерв"):
        for item in data.get("equipment_reserve",[]):
            st.write(item["name"]+" · "+rarity_label(item))
            st.caption(item.get("description",""))
            from kalista_view import show_comparison
            show_comparison(data,item,"player")
            if st.button("Надеть",key="edit_root_equip_"+item["id"]):apply_view_equip(item["id"])
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Экипировка</div>", unsafe_allow_html=True)
    for slot,it in data["equipment"].items():
        with st.expander(f"{rarity_label(it).split()[0] if it.get('name') else '▫️'} {slot.replace(' (посох)','')}: {it.get('name') or '—'}"):
            from kalista_view import gear_summary
            gear_summary(it,root=True)
            with st.expander('Изменить свойства'):
                if it.get("growth"):st.caption(f"Исходные бонусы на уровне {it['growth']['anchor_level']}; текущие значения с ростом — в обычном просмотре.")
                it["rarity"]=st.selectbox("Редкость",RARITIES,index=RARITIES.index(it.get("rarity","Обычный")),key=f"rarity_{slot}")
                it["name"]=st.text_input("Название",it.get("name",""),key=f"n{slot}")
                c=st.columns(4)
                it["armor"]=c[0].number_input("Броня",0,value=int(it.get("armor",0)),key=f"a{slot}")
                it["spell_power"]=st.number_input("Сила заклинаний (%)",value=float(it.get("spell_power",0)),key=f"power_{slot}")
                it["attack"]=c[1].number_input("Атака",0,value=int(it.get("attack",0)),key=f"t{slot}")
                it["int"]=c[2].number_input("Интеллект",0,value=int(it.get("int",0)),key=f"i{slot}")
                it["wis"]=c[3].number_input("Мудрость",0,value=int(it.get("wis",0)),key=f"w{slot}")
                c2=st.columns(4)
                it["spi"]=c2[0].number_input("Дух",0,value=int(it.get("spi",0)),key=f"s{slot}")
                it["fire"]=c2[1].number_input("Огонь (%)",0,value=int(it.get("fire",0)),key=f"f{slot}")
                it["dark"]=c2[2].number_input("Тьма (%)",0,value=int(it.get("dark",0)),key=f"d{slot}")
                it["earth"]=c2[3].number_input("Земля (%)",0,value=int(it.get("earth",0)),key=f"e{slot}")
                c3=st.columns(3)
                it["water"]=c3[0].number_input("Вода (%)",0,value=int(it.get("water",0)),key=f"wa{slot}")
                it["air"]=c3[1].number_input("Воздух (%)",0,value=int(it.get("air",0)),key=f"ai{slot}")
                it["light"]=c3[2].number_input("Свет (%)",0,value=int(it.get("light",0)),key=f"l{slot}")
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
        d1.metric("Сила заклинаний", f"+{data['spell_power']*100:.0f}%")
        d1.metric("Реген маны", data["mana_regen"])
        d2.metric("Сопр. контролю", f"{data.get('control_resist',0)*100:.1f}%")
        d2.metric("Инициатива", data["initiative"])
        d3.metric("Броня", data["armor"])
        d3.metric("Критический удар", f"{effective_crit_chance(data)*100:.1f}%")

    with st.expander("Сопротивления стихиям"):
        rc = st.columns(6)
        for i, e in enumerate(ELEMENTS):
            rc[i].metric(e, str(effective_defense(data,e))+"%")

    with st.expander("Пассивные способности (расовые и классовые)"):
        for k, p in data["passives"].items():
            if p.get("type") in ("racial", "class"):
                st.markdown(f"**{p['name']}** — {p['desc']}")
                if k == "mana_reserve":
                    st.caption("Мана восстанавливается в конце полного раунда. Резерв проверяется до восстановления и усиливает три тика, даже после выхода выше 20%.")
                if k == "shadow_child":
                    st.caption("Тень даёт +20 процентных пунктов сопротивления, максимум 95%, до начала третьего хода Калисты.")

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
    with st.container(key='inventory_money_gm'):
        g,s,c=st.columns(3)
        data["gold"]=g.number_input("Золото",0,value=data["gold"])
        data["silver"]=s.number_input("Серебро",0,value=data["silver"])
        data["copper"]=c.number_input("Медь",0,value=data["copper"])
    for i,it in enumerate(data["inventory"]):
        with st.container(key=f'inventory_row_gm_{i}'):
            cols=st.columns([3,1,1,1])
            cols[0].write(f"**{it['name']}** · {it['type']}")
            cols[0].markdown(rarity_badge(it),unsafe_allow_html=True)
            it["qty"]=cols[1].number_input("Количество",0,value=it["qty"],key=f"q{i}",label_visibility="collapsed")
            use = it.get("use")
            if use:
                cols[0].caption(f"Применение: { {'heal': 'лечение', 'mana': 'мана', 'shield': 'щит'}[use['kind']]} · {use['value']}")
                if cols[2].button("Применить", key=f"use_item_{i}", disabled=it["qty"] <= 0 or use["value"] <= 0):
                    message = use_item(data, it)
                    log(message)
                    persist_and_rerun()
            if it.get("desc"): cols[0].caption(it["desc"])
            if cols[3].button("🗑",key=f"x{i}",help="Удалить предмет"): data["inventory"].pop(i); persist_and_rerun()
        with st.expander(f"Свойства и действие предмета · {it['name']} · #{i + 1}"):
            with st.form(f"item_use_{i}"):
                item_rarity=st.selectbox("Редкость",RARITIES,index=RARITIES.index(it.get("rarity","Обычный")))
                options = ["none", "heal", "mana", "shield"]
                current = use["kind"] if use else "none"
                kind = st.selectbox("Действие", options, index=options.index(current),
                                    format_func=lambda v: {"none": "Справочный предмет", "heal": "Лечение", "mana": "Восстановление маны", "shield": "Щит"}[v])
                amount = st.number_input("Величина", min_value=0, value=use["value"] if use else 0)
                duration = st.number_input("Полных раундов (0 — бессрочно)", min_value=0, value=use.get("duration", 0) if use else 0)
                if st.form_submit_button("Сохранить действие"):
                    it["rarity"]=item_rarity
                    it["use"] = None if kind == "none" else {"kind": kind, "value": amount, "duration": duration}
                    persist_and_rerun()
    with st.form("ai"):
        st.markdown("**Добавить предмет**")
        nn = st.text_input("Название")
        nt = st.selectbox("Тип", ["Расходник", "Реагент", "Свиток", "Оружие", "Броня", "Реликвия", "Инструмент", "Книга", "Валюта", "Прочее"])
        nr = st.selectbox("Редкость",RARITIES)
        nq = st.number_input("Количество", min_value=1, value=1)
        nd = st.text_input("Описание")
        if st.form_submit_button("Добавить") and nn.strip():
            data["inventory"].append({"name": nn.strip(), "type": nt, "qty": int(nq), "desc": nd, "rarity":nr, "use": None})
            persist_and_rerun()


elif page=="Заклинания":
    render_range_audit(data)
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Заклинания</div>", unsafe_allow_html=True)
    st.caption("Перезарядка указана в общих раундах. 0 — без перезарядки. Применение — на странице «Бой».")

    for i, sp in enumerate(list(data["spells"])):
        with st.expander(f"{sp.get('name','?')} · {reach_label(sp)} (КД {sp.get('cd_max',0)})"):
            st.write(sp.get('desc',''))
            st.caption(f"{reach_label(sp)} · Мана {sp['mana']} · Урон {sp['base']} · КД {sp.get('cd_left',0)}/{sp.get('cd_max',0)}")
            with st.expander('Изменить заклинание'):
                sp["name"] = st.text_input("Название", sp.get("name",""), key=f"sn{sp['id']}")
                c1, c2, c3, c4 = st.columns(4)
                sp["base"] = c1.number_input("Базовый урон", min_value=0, value=int(sp.get("base",0) or 0), key=f"sb{sp['id']}")
                sp["mana"] = c2.number_input("Мана", min_value=0, value=int(sp.get("mana",0) or 0), key=f"sm{sp['id']}")
                sp["cd_max"] = c3.number_input("Перезарядка (раунды)", min_value=0, value=int(sp.get("cd_max",0) or 0), key=f"sc{sp['id']}")
                from kalista_statuses import edit_proc
                selected_proc=edit_proc(sp,"spell_proc_"+str(sp["id"]))
                if selected_proc is not None or "hit_effect" in sp:sp["hit_effect"]=selected_proc
                schools = ELEMENTS + ["Огонь+Тьма"]
                cur = sp.get("school", "Огонь")
                sp["school"] = c4.selectbox("Школа", schools, index=schools.index(cur) if cur in schools else 0, key=f"ss{sp['id']}")
                sp["reach"] = st.selectbox("Дальность способности",["Ближняя","Дальняя","Любая"],index=["Ближняя","Дальняя","Любая"].index(sp.get("reach","Дальняя")),format_func=lambda v:reach_label({"reach":v}),key=f"sr{sp['id']}")
                sp["range_m"]=st.number_input("Дальность в метрах (0 — не задана)",min_value=0.,value=float(sp.get("range_m") or 0),key=f"srange{sp['id']}") or None
                sp["area_radius_m"]=st.number_input("Радиус массовой атаки (м; 0 — без области)",min_value=0.,value=float(sp.get("area_radius_m",0)),key=f"sradius{sp['id']}")
                sp.update(edit_shape(sp,"spell_shape_"+str(sp["id"]),standalone=True))
                sp["desc"] = st.text_input("Описание", sp.get("desc",""), key=f"sd{sp['id']}")
                actions = ["damage", "heal", "shield", "note"]
                sp["action"] = st.selectbox("Действие", actions, index=actions.index(spell_action(sp)),
                                            format_func=lambda v: {"damage": "Урон", "heal": "Лечение", "shield": "Щит", "note": "Статус / заметка"}[v], key=f"sa{sp['id']}")
                if sp['name']=='Покров тьмы':st.caption(f'Расчётный щит: {shadow_shield_amount(data)} · Интеллект × (1 + сила заклинаний)')
                elif sp["action"] in ("heal", "shield"):
                    sp["effect_value"] = st.number_input("Лечение / сила щита (без множителей)", min_value=0,value=sp.get("effect_value", 0), key=f"sev{sp['id']}")
                if sp["action"] in ("shield", "note"):
                    sp["effect_duration"] = st.number_input("Полных раундов (0 — бессрочно)", min_value=0,value=sp.get("effect_duration", 0), key=f"sed{sp['id']}")
                if sp['action']=='damage':
                    st.caption(f"Эффекты школы: горение 50% ({kalista_dot_damage(data,'burn')} × 3); проклятие 50% ({kalista_dot_damage(data,'curse')} × 3); слабость 35% (−35%, 2 хода). Повтор сохраняет более сильный ДоТ.")
                    if sp['name'] in ('Разряд бездны','Пламя души'):st.caption('Страх: 50% × (1 − сопротивление контролю), пропуск 2 ходов.')
    
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
        sc = c3.number_input("Перезарядка (раунды)", min_value=0, value=0)
        ss = st.selectbox("Школа", ELEMENTS + ["Огонь+Тьма"])
        sr = st.selectbox("Дальность способности",["Ближняя","Дальняя","Любая"],index=1,format_func=lambda v:reach_label({"reach":v}))
        range_m=st.number_input("Дальность в метрах (0 — не задана)",min_value=0.,value=0.) or None
        radius=st.number_input("Радиус массовой атаки (м; 0 — без области)",min_value=0.,value=0.)
        shape_settings=edit_shape({},"new_spell_shape")
        sd = st.text_input("Описание")
        sg = st.selectbox("Даёт", [None, "pepel", "ten", "both"],
            format_func=lambda x: {None:"Ничего","pepel":"Пепел","ten":"Тень","both":"Оба"}[x])
        if st.form_submit_button("Добавить") and sn.strip():
            nid = max((s.get("id",0) for s in data["spells"]), default=0) + 1
            data["spells"].append({
                "id": nid, "name": sn.strip(), "base": sb, "mana": sm,
                "school": ss, "desc": sd, "gives": sg, "reach": sr,"range_m":range_m,"area_radius_m":radius,**shape_settings,
                "cd_max": sc, "cd_left": 0, "dot": None, "range": "Средняя"
            })
            persist_and_rerun()


# ===================== КВЕСТЫ =====================
elif page=="Квесты":
    st.subheader('Квесты и заметки')
    from kalista_quest_ui import render_root
    render_root(data,persist_and_rerun,editable=True)


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
