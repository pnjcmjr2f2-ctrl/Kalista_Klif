"""Quest recovery, readable rewards and explicit saves in both character sheets."""
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import json
from streamlit.testing.v1 import AppTest
import kalista_engine as e
from kalista_quests import DRAFTS,description,reward
legacy=deepcopy(e.DEFAULT);legacy['schema_version']=28
legacy['quests']=[dict(id=i,name=name,status=status,desc='') for i,(name,status) in enumerate(zip(DRAFTS,['В процессе','Активен','Ожидание']),1)]
d=e.migrate(legacy)
assert all(description(q) and reward(q) for q in d['quests'])
assert [q['status'] for q in d['quests']]==['В процессе','Активен','Ожидание']
d['quests'][0]['desc']='';d['quests'][0]['reward']='';assert not description(e.migrate(d)['quests'][0]),'User-cleared text was restored again'
d=e.migrate(legacy);d['ally']=e.imported_friend();e.recalc(d);d=e.migrate(d)
d['quests'][0].update(desc='Авторское описание',reward={'xp':777,'items':[{'name':'Ключ','qty':1}]},tasks=['Сохранить задачу'],notes='Важная заметка')
assert reward(e.migrate(d)['quests'][0])=='Опыт: 777\nПредметы: Название: Ключ\nКоличество: 1'
with TemporaryDirectory() as folder:
    root=Path(folder);source=root/'kalista_app.py';source.write_text(Path(__file__).with_name('kalista_app.py').read_text());save=root/'kalista_save.json';save.write_text(json.dumps(d,ensure_ascii=False))
    app=AppTest.from_file(str(source),default_timeout=30);app.secrets['access']={'gm_password':'g','player_password':'p'};app.session_state['_role']='gm';app.run();app.radio(key='page').set_value('Квесты').run();assert not app.exception
    assert any('Авторское описание' in x.value for x in app.markdown)
    assert any('Опыт: 777' in x.value for x in app.markdown)
    assert json.loads(save.read_text())==d
    app.toggle(key='_edit_mode').set_value(True).run();assert not app.exception
    assert any(x.key=='new_quest_reward' for x in app.text_area)
    app.text_area(key='quest_1_desc').set_value('Обновлённое описание\nС переносом строки')
    next(x for x in app.button if x.key=='FormSubmitter:quest_1-Сохранить квест').click().run();assert not app.exception
    actual=json.loads(save.read_text());q=actual['quests'][0]
    assert q['desc'].endswith('С переносом строки') and q['reward']==d['quests'][0]['reward'] and q['tasks']==d['quests'][0]['tasks'] and q['notes']==d['quests'][0]['notes']
    app.text_input(key='new_quest_name').set_value('Новый заказ');app.text_area(key='new_quest_desc').set_value('Доставить письмо');app.text_area(key='new_quest_reward').set_value('100 XP и 3 золотых')
    next(x for x in app.button if x.key=='FormSubmitter:aq-Добавить квест').click().run();assert not app.exception
    actual=json.loads(save.read_text());assert actual['quests'][-1]['reward']=='100 XP и 3 золотых'
    assert actual['gold']==d['gold'] and actual.get('xp')==d.get('xp'),'Editing quest granted rewards'
    player=AppTest.from_file(str(source),default_timeout=30);player.secrets['access']={'gm_password':'g','player_password':'p'};player.session_state['_role']='player';player.session_state['_edit_mode']=True;player.run();player.radio(key='player_section').set_value('Квесты').run();assert not player.exception
    player.text_input(key='ps_quest_new_name').set_value('Поручение Шеогарату');player.text_area(key='ps_quest_new_desc').set_value('Доставить ответ');player.text_area(key='ps_quest_new_reward').set_value('50 XP')
    next(x for x in player.button if x.label=='Сохранить квест').click().run();assert not player.exception
    actual=json.loads(save.read_text());assert actual['ally']['sheet_profile']['quests'][0]['reward']=='50 XP'
    player.toggle(key='_edit_mode').set_value(False).run();assert not player.exception
    assert any('50 XP' in x.value for x in player.markdown)
print('Passed: legacy quest drafts, editable rewards, read-only descriptions, empty-text preservation, structured reward/extra-field preservation, no automatic payout, both character sheets.')
