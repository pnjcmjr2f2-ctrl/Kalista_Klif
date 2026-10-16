from unittest.mock import patch
import kalista_engine as e
with patch('kalista_engine.random.uniform',return_value=1):
    normal=e.gen_enemy(21,'Обычный',False)
    elite=e.gen_enemy(21,'Обычный',True)
    boss=e.gen_enemy(21,'Обычный',True,True)
    assert (normal['hp_max'],normal['attack_damage'],normal['armor'])==(1045,319,262)
    assert elite['hp_max']==1881 and elite['attack_damage']==399
    assert boss['hp_max']==4180 and boss['attack_damage']==510
    assert e.real_dmg(normal['attack_damage'],1800)==98
    assert e.gen_enemy(21,'Обычный',False,strength=2)['hp_max']==2090
    for level in (1,21,100,1650):
        x=e.gen_enemy(level,'Обычный',False)
        assert min(x['resists'].values())<20 and max(x['resists'].values())<=75
for bad in (0,4,float('nan'),True):
    try:e.gen_enemy(21,'Обычный',False,strength=bad)
    except ValueError:pass
    else:raise AssertionError('Invalid strength accepted')
print('Balance: baseline, elite, boss, damage after hero armor, strength and high-level resistance weaknesses OK')
