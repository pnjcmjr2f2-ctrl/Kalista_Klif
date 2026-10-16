"""Quest journal content and non-destructive legacy field handling."""
from copy import deepcopy
import json
STATUSES=('Активен','В процессе','Ожидание','Выполнен','Провален')
DRAFTS={
'Пепел старого дома':dict(desc='Выяснить, что произошло во время ритуала, уничтожившего Дом Клиф, и найти уцелевшие записи матери о Чёрном Пламени.\n\nЗадачи:\n• Найти свидетеля или следы последнего ритуала.\n• Добраться до сохранившегося тайника Дома Клиф и извлечь записи.\n• Установить, была ли катастрофа случайностью или результатом чужого вмешательства.\n\nЗавершение: Калиста получает записи и подтверждённую зацепку о причине гибели дома.',reward='4 000 XP Калисте; 150 золотых; уцелевшие рукописи матери — сюжетный предмет без автоматических боевых бонусов.'),
'Кристалл пустоты':dict(desc='Исследовать связь кристалла пустоты с Чёрным Пламенем и понять, можно ли безопасно использовать его в работе над Пламенем души.\n\nЗадачи:\n• Найти специалиста или достоверные записи о кристаллах пустоты.\n• Проверить один образец в защищённых условиях и записать результат.\n• Определить безопасный способ хранения и применения образца.\n\nЗавершение: исследование подтверждено ведущим, свойства и ограничения кристалла записаны. Существующие образцы в инвентаре не расходуются автоматически.',reward='2 000 XP Калисте; 60 золотых; один стабилизированный осколок пустоты — реагент для дальнейших исследований, без заданного усиления урона.'),
'Долг Серому':dict(desc='Встретиться с Серым, который знает о прошлом Калисты, и закрыть старый долг, не поставив под угрозу её поиски.\n\nЗадачи:\n• Уточнить у Серого условия долга и получателя поручения.\n• Доставить запечатанное послание и забрать ответ, не раскрыв отправителя.\n• Вернуться к Серому и получить подтверждение, что долг погашен.\n\nЗавершение: поручение принято Серым; он передаёт Калисте новую зацепку о связях Дома Клиф.',reward='1 500 XP Калисте; 40 золотых; долг погашен; доступ к сведениям и безопасному ночлегу через контакты Серого.')}

def as_text(value):
    labels={'xp':'Опыт','gold':'Золото','silver':'Серебро','copper':'Медь','items':'Предметы','name':'Название','qty':'Количество','desc':'Описание','description':'Описание'}
    if isinstance(value,dict):return '\n'.join((labels.get(k,k)+': '+as_text(v)) for k,v in value.items() if k not in ('id','source','source_id') and v not in (None,''))
    if isinstance(value,(list,tuple)):return '\n'.join(as_text(x) for x in value)
    return '' if value is None else str(value)

def description(q):return next((as_text(q[k]) for k in ('desc','description','text') if q.get(k)), '')
def reward(q):return next((as_text(q[k]) for k in ('reward','rewards') if q.get(k)), '')

def initialize(data,seed=False):
    collections=[data.get('quests',[])]
    profile=data.get('ally',{}).get('sheet_profile')
    if profile:collections.append(profile.get('quests',[]))
    for index,quests in enumerate(collections):
        if not isinstance(quests,list):raise ValueError('Квесты должны быть списком')
        for q in quests:
            if not isinstance(q,dict) or not isinstance(q.get('name'),str):raise ValueError('Неверная карточка квеста')
            if not q.get('desc'):q['desc']=description(q)
            if not q.get('reward'):q['reward']=deepcopy(q.get('rewards',''))
            if seed and index==0 and q['name'] in DRAFTS:
                for field,value in DRAFTS[q['name']].items():
                    if not q.get(field):q[field]=value
            if not isinstance(q.get('desc',''),str):raise ValueError('Описание квеста должно быть текстом')
            try:json.dumps(q.get('reward',''),allow_nan=False)
            except (ValueError,TypeError):raise ValueError('Неверная награда квеста')
