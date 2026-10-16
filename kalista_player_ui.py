"""Full character UI for the ally, shared by the player and GM."""
from pathlib import Path
from kalista_shape_ui import edit_shape
from copy import deepcopy
from uuid import uuid4
from html import escape
import streamlit as st
from kalista_view import editing,player_view,show_comparison,gear_summary
import kalista_engine as e
from kalista_text import readable_rules
from kalista_storage import read_state,write_state,StaleState
from kalista_player_model import EQUIPMENT_SLOTS,ITEM_TYPES,STATS,BONUSES,sheet_snapshot,edit_player_sheet,use_player_item,gear_totals

SECTIONS=['Обзор','Бой','Снаряжение','Инвентарь','Заклинания и способности','Характеристики','Квесты','Заметки','Биография','Кубики','Сцена']

def baseline(data,section):
    key='_ps_baseline_'+section
    if key not in st.session_state: st.session_state[key]=sheet_snapshot(data,section)
    return deepcopy(st.session_state[key])

def persist(root,section,values,expected,item_id=None):
    if st.session_state.get('_role') not in ('gm','player'): raise ValueError('Нужен вход в программу')
    path=Path(root)/'kalista_save.json'
    for attempt in range(2):
        saved,revision=read_state(path);latest=e.migrate(saved if saved is not None else deepcopy(e.DEFAULT))
        candidate=use_player_item(latest,item_id,expected) if item_id else edit_player_sheet(latest,section,values,expected)
        candidate=e.migrate(candidate)
        if candidate['combat_active']: e.refresh_turn_order(candidate)
        label='Предмет Шеогарата' if item_id else 'Лист игрока: '+section
        candidate['combat_log'].insert(0,label);candidate['combat_log']=candidate['combat_log'][:80]
        try:new_revision=write_state(path,candidate,revision,e.migrate)
        except StaleState:
            if attempt==0:continue
            raise ValueError('Игра обновилась; повтори сохранение')
        if st.session_state['_role']=='gm':
            e.add_history(st.session_state.setdefault('_undo_history',[]),latest,candidate,label)
            st.session_state['data']=candidate;st.session_state['_committed_data']=deepcopy(candidate)
            st.session_state['_save_revision']=new_revision
        for key in list(st.session_state):
            if str(key).startswith(('ps_','_ps_baseline_')):del st.session_state[key]
        st.session_state['_ps_notice']='Сохранено'
        st.rerun()

def commit(root,section,values,expected,item_id=None):
    try:persist(root,section,values,expected,item_id)
    except (ValueError,TypeError,KeyError,OSError) as exc:st.error(str(exc))

def refresh_button():
    if st.button('Обновить раздел',key='ps_refresh',help='Загрузить актуальные данные и сбросить незаписанные поля.'):
        for key in list(st.session_state):
            if str(key).startswith(('ps_','_ps_baseline_')):del st.session_state[key]
        st.rerun()
    if st.session_state.get('_ps_notice'):st.success(st.session_state.pop('_ps_notice'))

def tiles(values):
    content=''.join(f'<div class="stat-tile"><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>' for k,v in values)
    st.markdown('<div class="stat-grid">'+content+'</div>',unsafe_allow_html=True)

def overview(data,root):
    a=data['ally'];p=a['sheet_profile']
    portrait=p['portrait_url'] or (str(Path(root)/'assets'/'sheogarat-portrait.webp') if (Path(root)/'assets'/'sheogarat-portrait.webp').is_file() else '')
    if portrait:
        try:st.image(portrait,width=180)
        except Exception:st.caption('Портрет не загрузился')
    if a.get('mana_max'):st.progress(a['mana_current']/a['mana_max'],text=f"MP {a['mana_current']}/{a['mana_max']}")
    xp_goal=e.xp_needed(p['level'])
    if p['level']==e.MAX_LEVEL:
        st.progress(1.0,text='Уровень 1650 · достигнут потолок развития')
    elif p['xp_known'] and xp_goal and xp_goal>0:
        st.progress(min(1,p['xp']/xp_goal),text=f"Опыт уровня: {p['xp']} / {xp_goal} XP · до следующего уровня: {max(0,xp_goal-p['xp'])}")
    else:
        st.progress(0,text=f"Опыт: {p['xp']} XP · порог не задан" if p['xp_known'] else 'Опыт не заполнен · порог не задан')
    tiles([('Уровень',p['level']),('Атака',p['attack']),('Броня',a['armor']),('Сила заклинаний',f"+{a.get('spell_power',0)*100:g}%"),('Уклонение',f"{e.evasion_chance(a)*100:.1f}%"),('Шанс крита',f"{p['critical_chance']:.2f}%"),('Критический урон',p['critical_damage']),('Свободные очки',p['free_points'])])
    with st.expander('Сопротивления и эффекты'):
        tiles([(key,str(value)+'%') for key,value in a['resists'].items()])
        for effect in a['effects']:st.write(e.effect_lifetime(effect))
        if a.get('fear_immunity_turns',0):st.write('Иммунитет к страху и заморозке: до конца следующего личного хода')
    if not editing():return
    with st.expander('HP и мана вручную'):
        expected=baseline(data,'resources')
        with st.form('ps_resources'):
            hp=st.number_input('Текущие HP',min_value=0,max_value=a['hp_max'],value=min(a['hp'],a['hp_max']),key='ps_hp')
            maximum=st.number_input('Максимум маны (0 — нет ресурса)',min_value=0,value=a.get('mana_max',0),key='ps_mmax')
            current=st.number_input('Текущая мана',min_value=0,value=a.get('mana_current',0),key='ps_mp')
            if st.form_submit_button('Сохранить ресурсы'):commit(root,'resources',dict(hp=hp,mana_current=current,mana_max=maximum,effects=expected['effects']),expected)
    with st.expander('Опыт и повышение уровня'):
        expected=baseline(data,'attributes')
        st.caption('Текущий опыт: '+(str(p['xp']) if p['xp_known'] else 'не заполнен в актуальном листе'))
        with st.form('ps_xp_form'):
            xp=st.number_input('Опыт',min_value=0,value=p['xp'],key='ps_xp')
            if st.form_submit_button('Сохранить опыт'):
                values=deepcopy(expected);values.update(xp=xp,xp_known=True);commit(root,'attributes',values,expected)
        if st.button('Повысить уровень · +4 свободных очка',key='ps_level_up',disabled=p['level']>=e.MAX_LEVEL):
            values=deepcopy(expected);values['xp']=max(0,values['xp']-e.xp_needed(values['level']));values['level']+=1;values['free_points']+=4;commit(root,'attributes',values,expected)
    with st.expander('Отдых'):
        expected=baseline(data,'rest')
        st.caption('Восстановит твои HP и ману, снимет эффекты и обычные перезарядки. Заряды и способности с ручной перезарядкой восстанавливаются отдельно.')
        if st.button('Долгий отдых',key='ps_long_rest',disabled=data['combat_active']):commit(root,'rest',None,expected)

def inventory(data,root):
    p=data['ally']['sheet_profile'];expected=baseline(data,'inventory')
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Инвентарь</div>",unsafe_allow_html=True)
    with st.container(key='inventory_money_player'):
        with st.form('ps_money_form'):
            cols=st.columns(3)
            currency={key:cols[i].number_input(label,min_value=0,value=p['currency'][key],key='ps_money_'+key) for i,(key,label) in enumerate((('gold','Золото'),('silver','Серебро'),('copper','Медь')))}
            if st.form_submit_button('Сохранить деньги'):commit(root,'inventory',dict(items=expected['items'],currency=currency),expected)
    for item in p['inventory']:
        with st.container(key='inventory_row_player_'+item['id']):
            cols=st.columns([3,1,1,1])
            cols[0].markdown('**'+escape(item['name'])+'** · '+escape(item['type']))
            cols[0].markdown(e.rarity_badge(item),unsafe_allow_html=True)
            cols[1].write('× '+str(item['qty']))
            if item['desc']:cols[0].caption(item['desc'])
            if item['use']:
                cols[0].caption('Применение: '+{'heal':'лечение','mana':'восстановление маны','shield':'щит'}[item['use']['kind']]+' · '+str(item['use']['value']))
                if cols[2].button('Применить',key='ps_use_'+item['id'],disabled=item['qty']<1 or item['use']['value']<=0):commit(root,'inventory',None,expected,item['id'])
            if cols[3].button('🗑',key='ps_item_'+item['id']+'_delete',help='Удалить предмет'):
                commit(root,'inventory',dict(items=[x for x in expected['items'] if x['id']!=item['id']],currency=expected['currency']),expected)
        with st.expander('Изменить предмет · '+item['name']):item_form(data,root,item,expected)
    with st.expander('Добавить предмет',expanded=not p['inventory']):item_form(data,root,None,expected)


def item_form(data,root,item,expected):
    x=item or dict(id='new',name='',type='Предмет',qty=1,desc='',use=None);prefix='ps_item_'+x['id']
    with st.form(prefix):
        name=st.text_input('Название предмета',x['name'],key=prefix+'_name')
        types=list(ITEM_TYPES)+( [x['type']] if x['type'] not in ITEM_TYPES else [])
        kind=st.selectbox('Тип',types,index=types.index(x['type']),key=prefix+'_type')
        rarity=st.selectbox('Редкость',e.RARITIES,index=e.RARITIES.index(x.get('rarity','Обычный')),key=prefix+'_rarity')
        qty=st.number_input('Количество',min_value=0,value=x['qty'],key=prefix+'_qty')
        desc=st.text_area('Описание предмета',x['desc'],key=prefix+'_desc')
        use=st.selectbox('При использовании',['Нет','Лечение','Мана','Щит'],index=['Нет','heal','mana','shield'].index(x['use']['kind'] if x['use'] else 'Нет'),key=prefix+'_use')
        value=st.number_input('Сила применения',min_value=0,value=x['use']['value'] if x['use'] else 0,key=prefix+'_value')
        if st.form_submit_button('Сохранить предмет' if item else 'Добавить предмет'):
            new=dict(id=x['id'] if item else uuid4().hex,name=name,type=kind,qty=qty,desc=desc,rarity=rarity,use=None if use=='Нет' else dict(kind={'Лечение':'heal','Мана':'mana','Щит':'shield'}[use],value=value))
            items=[new if old['id']==x['id'] else old for old in expected['items']] if item else expected['items']+[new]
            commit(root,'inventory',dict(items=items,currency=expected['currency']),expected)

def equipment(data,root):
    p=data['ally']['sheet_profile'];expected=baseline(data,'equipment')
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Экипировка</div>",unsafe_allow_html=True)
    st.caption('Бонусы надетых вещей участвуют в характеристиках. Снятые вещи остаются в резерве. Сопротивления указаны в процентах; итог не выше 95%.')
    for slot in EQUIPMENT_SLOTS:
        items=[x for x in p['equipment'] if x['equipped'] and x['slot']==slot]
        if not items:
            with st.expander('▫️ '+slot+': —'):gear_form(root,None,expected,slot)
        for item in items:
            with st.container(border=True):
                st.caption(slot);gear_summary(item)
                with st.expander('Изменить · '+item['name']):gear_form(root,item,expected)
    reserve=[x for x in p['equipment'] if not x['equipped'] or x['slot'] not in EQUIPMENT_SLOTS]
    if reserve:st.markdown('**Резерв и другие ячейки**')
    for item in reserve:
        with st.expander(('🔹 ' if item['equipped'] else '▫️ ')+item['name']):
            if not item['equipped']:show_comparison(data,item,'ally')
            gear_form(root,item,expected)
    with st.expander('Добавить снаряжение в резерв'):gear_form(root,None,expected,'Резерв')


def gear_form(root,item,expected,default_slot="Резерв"):
    x=item or dict(id='new_'+default_slot,slot=default_slot,name='',description='',bonuses={},equipped=default_slot!='Резерв');prefix='ps_gear_'+x['id']
    with st.form(prefix):
        name=st.text_input('Название',x['name'],key=prefix+'_name')
        slots=list(EQUIPMENT_SLOTS)+['Резерв']+([x['slot']] if x['slot'] not in EQUIPMENT_SLOTS and x['slot']!='Резерв' else [])
        slot=st.selectbox('Ячейка',slots,index=slots.index(x['slot']),key=prefix+'_slot')
        rarity=st.selectbox('Редкость',e.RARITIES,index=e.RARITIES.index(x.get('rarity','Обычный')),key=prefix+'_rarity')
        equipped=st.checkbox('Надето',x['equipped'],key=prefix+'_equipped')
        desc=st.text_area('Описание / свойства',x['description'],key=prefix+'_desc')
        st.caption('Введите только известные числовые бонусы. Особые свойства остаются в описании.')
        if x.get('growth'):st.caption(f"Это исходные бонусы на уровне {x['growth']['anchor_level']}. Текущие бонусы с ростом показаны в обычном просмотре.")
        bonuses={}
        columns=st.columns(4)
        for index,key in enumerate(BONUSES):
            value=x['bonuses'].get(key,0)
            numeric=float(value) if key in ('Атака','Сила заклинаний','Критический урон','Шанс крита') else int(value)
            label=key+' (%)' if key in e.ELEMENTS or key in ('Шанс крита','Сила заклинаний') else key
            bonuses[key]=columns[index%4].number_input(label,value=numeric,key=prefix+'_'+key)
        if st.form_submit_button('Сохранить снаряжение'):
            if equipped and slot in EQUIPMENT_SLOTS and any(old['equipped'] and old['slot']==slot and old['id']!=x['id'] for old in expected):
                st.error('Ячейка занята. Сначала сними текущий предмет или выбери другую ячейку.');return
            new=dict(id=x['id'] if item else uuid4().hex,slot=slot,name=name,description=desc,rarity=rarity,bonuses=bonuses,equipped=equipped)
            if x.get('growth'):new['growth']=deepcopy(x['growth'])
            values=[new if old['id']==x['id'] else old for old in expected] if item else expected+[new]
            commit(root,'equipment',values,expected)
    if item and st.button('Удалить снаряжение',key=prefix+'_delete'):commit(root,'equipment',[old for old in expected if old['id']!=x['id']],expected)

def attributes(data,root):
    a=data['ally'];p=a['sheet_profile'];expected=baseline(data,'attributes')
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Характеристики</div>",unsafe_allow_html=True)
    st.info(f"Свободные очки: **{p['free_points']}** · Уровень **{p['level']}**")
    gear=gear_totals(p)
    with st.expander('Характеристики',expanded=True):
        for stat in STATS:
            cols=st.columns([2,1,1,1,1])
            cols[0].write(f"**{stat}**")
            cols[1].write(f"База {p['base_stats'][stat]}")
            bonus=gear[stat]+p['stat_adjustments'][stat]
            cols[2].write(f"{bonus:+g}")
            cols[3].write(f"**{p['stats'][stat]}**")
            if cols[4].button('＋',key='ps_plus_'+stat,disabled=p['free_points']<=0):
                values=deepcopy(expected);values['base_stats'][stat]+=1;values['free_points']-=1
                commit(root,'attributes',values,expected)
        st.markdown('**Производные**')
        c1,c2,c3=st.columns(3)
        c1.metric('Атака',p['attack']);c1.metric('Критический урон',p['critical_damage'])
        c2.metric('Уклонение',f"{e.evasion_chance(a)*100:.1f}%");c2.metric('Инициатива',a.get('initiative',0))
        c3.metric('Броня',a['armor']);c3.metric('Критический удар',f"{p['critical_chance']:.2f}%");c3.metric('Сила заклинаний',f"+{a.get('spell_power',0)*100:g}%")
    with st.expander('Сопротивления стихиям'):
        cols=st.columns(6)
        for index,element in enumerate(e.ELEMENTS):cols[index].metric(element,str(e.effective_defense(a,element))+'%')
    with st.expander('Пассивные способности (расовые и классовые)'):
        st.write(readable_rules(p['abilities']))
    with st.expander('Особые умения'):
        for action in a['actions']:
            if action.get('rule') not in ('eye','stance'):continue
            reason=a.get('eye_used',False) if action.get('rule')=='eye' else action.get('cooldown_left',0)>0
            status='⏳ сейчас недоступно' if reason else '🟢 доступно'
            st.markdown(f"**{action['name']}** — {status}")
            st.write(action['description'])
        st.caption('Применение — на странице «Бой», с учётом действий и текущего хода.')
    with st.expander('Вложить несколько очков'):
        with st.form('ps_allocate'):
            stat=st.selectbox('Вложить в',STATS,key='ps_allocate_stat');count=st.number_input('Очков',min_value=1,value=1,key='ps_allocate_count')
            if st.form_submit_button('Вложить очки'):
                if count>expected['free_points']:st.error('Не хватает свободных очков')
                else:
                    values=deepcopy(expected);values['base_stats'][stat]+=count;values['free_points']-=count;commit(root,'attributes',values,expected)
    with st.expander('Ручная правка характеристик'):
        with st.form('ps_attributes'):
            base={key:st.number_input('Базовая: '+key,min_value=0,value=p['base_stats'][key],key='ps_base_'+key) for key in STATS}
            level=st.number_input('Уровень',min_value=1,max_value=e.MAX_LEVEL,value=p['level'],key='ps_level');points=st.number_input('Свободные очки',min_value=0,value=p['free_points'],key='ps_points')
            adjust={key:st.number_input('Ручная поправка: '+label,value=float(p['formula_adjustments'][key]),key='ps_adjust_'+key) for key,label in (('hp','максимум HP'),('armor','броня'),('attack','атака'),('critical_damage','критический урон'),('critical_chance','шанс крита'))}
            resist={key:st.number_input('Базовое сопротивление: '+key,value=int(p['resist_adjustments'][key]),key='ps_resist_'+key) for key in a['resists']}
            if st.form_submit_button('Сохранить характеристики'):
                values=deepcopy(expected);values.update(base_stats=base,level=level,free_points=points,formula_adjustments=adjust,resist_adjustments=resist);commit(root,'attributes',values,expected)
    st.caption('HP = уровень×20 + выносливость×10; броня = 10 + выносливость×5 + бонусы надетых вещей; атака = бонус атаки оружия×(1 + сила/500). Крит = атака×2 + бонус; шанс = 5 + ловкость×0,05 + бонус, максимум 95%. Ручные поправки сохраняются.')

def quests(data,root):
    expected=baseline(data,'quests')
    for quest in data['ally']['sheet_profile']['quests']:
        with st.expander(quest['name']+' · '+quest['status']):
            from kalista_quest_ui import show_quest
            show_quest(quest)
            quest_form(root,quest,expected)
    with st.expander('Добавить квест',expanded=not expected):quest_form(root,None,expected)

def quest_form(root,item,expected):
    x=item or dict(id='new',name='',desc='',reward='',status='Активен');prefix='ps_quest_'+x['id']
    with st.form(prefix):
        name=st.text_input('Название квеста',x['name'],key=prefix+'_name');desc=st.text_area('Задачи и заметки',x['desc'],key=prefix+'_desc')
        from kalista_quests import STATUSES,reward
        rewards=st.text_area('Награда за квест',reward(x),key=prefix+'_reward')
        status=st.selectbox('Статус квеста',STATUSES,index=STATUSES.index(x['status']),key=prefix+'_status')
        if st.form_submit_button('Сохранить квест'):
            new=deepcopy(x);new.update(id=x['id'] if item else uuid4().hex,name=name,desc=desc,status=status)
            if rewards!=reward(x):new['reward']=rewards
            commit(root,'quests',[new if old['id']==x['id'] else old for old in expected] if item else expected+[new],expected)
    if item and st.button('Удалить квест',key=prefix+'_delete'):commit(root,'quests',[q for q in expected if q['id']!=x['id']],expected)

def biography(data,root):
    p=data['ally']['sheet_profile'];expected=baseline(data,'identity')
    if p['biography']:st.markdown(p['biography'])
    with st.form('ps_identity'):
        values=dict(name=st.text_input('Имя',data['ally']['name'],key='ps_name'),race=st.text_input('Раса',p['race'],key='ps_race'),klass=st.text_input('Класс',p['class'],key='ps_class'),portrait_url=st.text_input('URL портрета',p['portrait_url'],key='ps_portrait'),biography=st.text_area('Биография',p['biography'],height=220,key='ps_biography'))
        if st.form_submit_button('Сохранить персонажа'):commit(root,'identity',values,expected)

def abilities(data,root):
    expected=baseline(data,'actions');actions=[a for a in data['ally']['actions'] if a.get('rule') not in ('move_close','move_far','move_point')]
    st.markdown("<div class='main-title' style='font-size:1.6rem'>Заклинания и способности</div>",unsafe_allow_html=True)
    st.caption('Перезарядка указана в личных ходах. 0 — без перезарядки. Применение — на странице «Бой».')
    for action in actions:
        with st.expander(f"{action['name']} · {e.reach_label(action)} (КД {action['cooldown']})"):
            st.write(action['description'])
            st.caption(f"Мана {action['mana_cost']} · КД {action['cooldown_left']}/{action['cooldown']} · Заряды {action['charges_left']}/{action['charges_max']}")
            with st.expander('Изменить способность'):
                action_form(root,action,expected)
            if st.button('Ручная перезарядка способности',key='ps_recharge_'+action['id']):
                values=deepcopy(expected);new=next(a for a in values if a['id']==action['id'])
                new.update(cooldown_left=0,spent=False,charges_left=new['charges_max']);commit(root,'actions',values,expected)
    with st.expander('Расовые и классовые свойства'):
        st.write(readable_rules(data['ally']['sheet_profile']['abilities']))
    with st.expander('Добавить способность'):
        action_form(root,None,expected)


def action_form(root,action,expected):
    x=action or e.action_template('');prefix='ps_action_'+(x['id'] if action else 'new')
    with st.form(prefix):
        editor_tabs=st.tabs(['Основное', 'Эффекты', 'Дополнительно', 'Правила'])
        with editor_tabs[0]:
            name=st.text_input('Название способности',x['name'],key=prefix+'_name')
            types=['damage','heal','shield','note'];kind=st.selectbox('Действие',types,index=types.index(x['kind']),format_func=lambda v:dict(damage='Урон',heal='Лечение',shield='Щит',note='Статус')[v],key=prefix+'_kind')
            amount=st.number_input('Базовая величина',min_value=0,value=x['amount'],key=prefix+'_amount');shared=st.checkbox('Использовать атаку из характеристик',x['shared_attack'],key=prefix+'_shared')
            dtype=st.selectbox('Тип урона',e.DAMAGE_TYPES,index=e.DAMAGE_TYPES.index(x['damage_type']),key=prefix+'_dtype')
            reach=st.selectbox('Дальность атаки',['Ближняя','Дальняя','Любая'],index=['Ближняя','Дальняя','Любая'].index(x.get('reach','Ближняя')),format_func=lambda v:e.reach_label({'reach':v}),key=prefix+'_reach')
            range_m=st.number_input('Дальность в метрах (0 — не задана)',min_value=0.,value=float(x.get('range_m') or 0),key=prefix+'_range_m') or None
            radius=st.number_input('Радиус массовой атаки (м; 0 — без области)',min_value=0.,value=float(x.get('area_radius_m',0)),key=prefix+'_radius')
            shape_settings=edit_shape(x,prefix+'_area')
            mana=st.number_input('Стоимость маны',min_value=0,value=x['mana_cost'],key=prefix+'_mana');cooldown=st.number_input('Перезарядка (личные ходы)',min_value=0,value=x['cooldown'],key=prefix+'_cd')
            hits=st.number_input('Попаданий',min_value=1,max_value=10,value=x['hits'],key=prefix+'_hits')
        with editor_tabs[1]:
            effect=st.selectbox('Дополнительный эффект',list(e.EFFECT_KINDS),index=list(e.EFFECT_KINDS).index(x['effect_kind']),format_func=lambda v:e.EFFECT_KINDS[v],key=prefix+'_effect')
            effect_value=st.number_input('Величина эффекта',value=x['effect_value'],key=prefix+'_ev');duration=st.number_input('Длительность: раунды или срабатывания (0 — бессрочно)',min_value=0,value=x['duration'],key=prefix+'_dur')
            element=st.selectbox('Стихия эффекта',e.ELEMENTS,index=e.ELEMENTS.index(x['effect_element']),key=prefix+'_element')
            stacks=st.number_input('Максимум наложений',min_value=1,max_value=20,value=x['max_stacks'],key=prefix+'_stacks')
        with editor_tabs[2]:
            charges=st.number_input('Максимум зарядов (0 — без ограничения)',min_value=0,value=x['charges_max'],key=prefix+'_charges')
            left=st.number_input('Осталось зарядов',min_value=0,value=x['charges_left'],key=prefix+'_left')
            penetration=st.number_input('Вычесть из брони',min_value=0,value=x.get('armor_penetration',0),key=prefix+'_penetration')
            dice=st.number_input('Дополнительных кубиков',min_value=0,max_value=10,value=x.get('extra_dice_count',0),key=prefix+'_dice');sides=st.number_input('Граней кубика',min_value=0,max_value=1000,value=x.get('extra_dice_sides',0),key=prefix+'_sides')
            reaction=st.checkbox('Реакция вне своего хода',x.get('reaction',False),key=prefix+'_reaction');manual=st.checkbox('Ручная перезарядка после применения',x['manual_recharge'],key=prefix+'_manual')
        with editor_tabs[3]:
            desc=st.text_area('Правила и описание',x['description'],key=prefix+'_desc');ready=st.checkbox('Правила и числа согласованы с ведущим',not x['needs_setup'],key=prefix+'_ready')
        if st.form_submit_button('Сохранить способность'):
            new=deepcopy(x);new.update(name=name,kind=kind,amount=amount,shared_attack=shared,damage_type=dtype,reach=reach,mana_cost=mana,cooldown=cooldown,hits=hits,effect_kind=effect,effect_value=effect_value,duration=duration,effect_element=element,max_stacks=stacks,charges_max=charges,charges_left=left,armor_penetration=penetration,extra_dice_count=dice,extra_dice_sides=sides,reaction=reaction,manual_recharge=manual,description=desc,needs_setup=not ready,range_m=range_m,area_radius_m=radius,**shape_settings)
            values=[new if old['id']==x['id'] else old for old in expected] if action else expected+[new]
            commit(root,'actions',values,expected)
    if action and st.button('Удалить способность',key=prefix+'_delete'):commit(root,'actions',[old for old in expected if old['id']!=x['id']],expected)

def render_section(section,data,root):
    if not data['ally'].get('sheet_profile'):st.info('Ведущему нужно загрузить лист персонажа в «Отряде».');return
    refresh_button()
    if player_view(section,data,root,commit):return
    if section=='Обзор':overview(data,root)
    elif section=='Снаряжение':equipment(data,root)
    elif section=='Инвентарь':inventory(data,root)
    elif section=='Характеристики':attributes(data,root)
    elif section=='Заклинания и способности':abilities(data,root)
    elif section=='Квесты':quests(data,root)
    elif section=='Биография':biography(data,root)
    elif section=='Заметки':
        expected=baseline(data,'notes')
        with st.form('ps_notes_form'):
            notes=st.text_area('Мои заметки',data['ally']['sheet_profile']['notes'],height=300,key='ps_notes')
            if st.form_submit_button('Сохранить заметки'):commit(root,'notes',notes,expected)
    elif section=='Кубики':
        count=st.number_input('Количество кубиков',min_value=1,max_value=100,value=1,key='ps_roll_count');sides=st.selectbox('Кубик',[4,6,8,10,12,20,100],index=5,key='ps_roll_sides');mod=st.number_input('Модификатор',value=0,key='ps_roll_mod')
        if st.button('Бросить',key='ps_roll'):
            rolls=[e.random.randint(1,sides) for _ in range(count)];st.session_state['_ps_roll_result']=f"{rolls} + {mod} = {sum(rolls)+mod}"
        if st.session_state.get('_ps_roll_result'):st.info(st.session_state['_ps_roll_result'])
