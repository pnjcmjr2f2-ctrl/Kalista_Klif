"""Enemy archetypes exercise the same action engine as heroes."""
from copy import deepcopy
from unittest.mock import patch
import kalista_engine as e
from kalista_enemies import ROLES, apply_loadout

for role in ROLES:
    data=e.migrate(deepcopy(e.DEFAULT))
    enemy=dict(id=999,name='Проверочный враг',level=10,size='Обычный',is_elite=False,is_boss=False,effects=[],**e.gen_enemy(10,'Обычный',False))
    enemy['race']='Лич' if role=='Некромант' else 'Человек'
    before=(enemy['hp'],enemy['armor'],deepcopy(enemy['resists']))
    apply_loadout(enemy,role)
    assert before==(enemy['hp'],enemy['armor'],enemy['resists'])
    data['enemies'].append(enemy);data=e.migrate(data)
    source='enemy:999'
    assert len([a for a in e.participant(data,source)['actions'] if not a.get('rule','').startswith('move_')])>=3
    for action in list(e.participant(data,source)['actions']):
        if action.get('rule','').startswith('move_'):continue
        d=deepcopy(data);d['distance_mode']='simple'
        d['distances']['|'.join(sorted((source,'player')))]='Ближняя'
        victim=source if action['kind']!='damage' else 'player'
        actor=e.participant(d,source)
        if action['kind']=='heal':actor['hp']=max(1,actor['hp']-20)
        mana=actor.get('mana_current',0)
        with patch('kalista_engine.random.random',return_value=.99):
            messages=e.perform_action(d,source,action['id'],[victim])
        actor=e.participant(d,source)
        assert actor.get('mana_current',0)==mana-action['mana_cost']
        assert next(a for a in actor['actions'] if a['id']==action['id'])['cooldown_left']==action['cooldown']
        assert messages
# Invalid effect chances must be rejected without spending resources.
d=e.migrate(deepcopy(e.DEFAULT));d['ally']['actions'][0]['effect_chance']=101
try:e.validate_action_state(d)
except ValueError:pass
else:raise AssertionError('Invalid chance accepted')
print('Enemy archetypes, action costs, cooldowns and validation: OK')
