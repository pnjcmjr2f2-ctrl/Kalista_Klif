"""Item rarity metadata; rarity never changes combat values by itself."""
from html import escape
RARITIES=('Обычный','Необычный','Редкий','Эпический','Легендарный')
COLORS={'Обычный':'#b7b7c4','Необычный':'#73ce95','Редкий':'#78b5ff','Эпический':'#d395f2','Легендарный':'#ffc16e'}
ICONS={'Обычный':'⚪','Необычный':'🟢','Редкий':'🔵','Эпический':'🟣','Легендарный':'🟠'}

def validate_rarity(item):
    if item.get('rarity','Обычный') not in RARITIES:raise ValueError('Неизвестная редкость предмета')

def rarity_label(item):
    rarity=item.get('rarity','Обычный');validate_rarity(item)
    return ICONS[rarity]+' '+rarity

def rarity_badge(item):
    rarity=item.get('rarity','Обычный');validate_rarity(item)
    return f'<span style="color:{COLORS[rarity]};font-weight:600">{escape(rarity_label(item))}</span>'

def ensure_rarities(data):
    initial=not data.get('rarities_initialized')
    armor=('Шлем','Наплечники','Перчатки','Нагрудник','Пояс','Штаны','Сапоги')
    for slot,item in data.get('equipment',{}).items():
        if initial:
            if slot in armor:item['rarity']='Редкий'
            elif slot.startswith('Оружие 1'):item['rarity']='Легендарный'
            elif slot=='Ожерелье':item['rarity']='Эпический'
            elif slot.startswith(('Серьга','Кольцо')):item['rarity']='Необычный'
        item.setdefault('rarity','Обычный');validate_rarity(item)
    profile=data.get('ally',{}).get('sheet_profile')
    if profile:
        friend_initial=not profile.get('rarities_initialized')
        for item in profile['equipment']:
            if friend_initial:
                name=item['name'].lower()
                item['rarity']='Легендарный' if 'ниргхал' in name or 'ледяная скорбь' in name else 'Редкий' if 'грозовой меч' in name else 'Обычный'
            item.setdefault('rarity','Обычный');validate_rarity(item)
        profile['rarities_initialized']=True
        for item in profile.get('inventory',[]):item.setdefault('rarity','Обычный');validate_rarity(item)
    for item in data.get('inventory',[]):item.setdefault('rarity','Обычный');validate_rarity(item)
    for item in data.get('equipment_reserve',[]):validate_rarity(item)
    data['rarities_initialized']=True
