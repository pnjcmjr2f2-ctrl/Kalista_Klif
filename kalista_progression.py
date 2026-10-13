"""Shared level curve; XP inside current level, manual level-up, capped at 1650."""
MAX_LEVEL=1650

def xp_needed(level):
    if isinstance(level,bool) or not isinstance(level,int) or not 1<=level<=MAX_LEVEL:
        raise ValueError('Уровень должен быть от 1 до 1650')
    return 0 if level==MAX_LEVEL else round(1000*level**1.2)

def initialize_progress(character):
    xp_needed(character['level'])
    if character.get('xp_curve_version')!=1:
        character['legacy_xp']=character.get('xp',0)
        character['legacy_xp_known']=character.get('xp_known',True)
        character['xp']=0;character['xp_known']=True;character['xp_curve_version']=1
    character['xp_goal']=xp_needed(character['level'])
    character['xp_to_next']=max(0,character['xp_goal']-character['xp'])

def advance_levels(character):
    before=character['level']
    while character['level']<MAX_LEVEL and character['xp']>=xp_needed(character['level']):
        character['xp']-=xp_needed(character['level']);character['level']+=1
        character['free_points']=character.get('free_points',0)+4
    if character['level']==MAX_LEVEL:character['xp']=0
    character['xp_goal']=xp_needed(character['level']);character['xp_to_next']=max(0,character['xp_goal']-character['xp'])
    return character['level']-before
