"""Direct player actions, simulated on fresh state and committed with CAS."""
from copy import deepcopy
from datetime import datetime
from kalista_storage import read_state,write_state
import kalista_engine as e

def apply_player_action(path,seen,aid,victims,destination=None,area_center=None):
    latest,revision=read_state(path)
    if latest is None:raise ValueError('Игра не найдена')
    latest=e.migrate(latest)
    if latest.get('map_revision',0)!=seen.get('map_revision',0):raise ValueError('Карта изменилась; обнови экран')
    if latest['turn_serial']!=seen['turn_serial']:raise ValueError('Ход изменился; обнови экран')
    if latest.get('turn_actions',[])!=seen.get('turn_actions',[]):raise ValueError('Действия этого хода изменились; обнови экран')
    action=next((a for a in latest['ally']['actions'] if a['id']==aid),None)
    if action is None:raise ValueError('Способность изменилась; обнови экран')
    seen_action=next((a for a in seen['ally']['actions'] if a['id']==aid),None)
    if action!=seen_action:raise ValueError('Настройки способности изменились; обнови экран')
    if latest['combat_active'] and (not e.get_current_actor(latest) or e.actor_token(e.get_current_actor(latest))!='ally') and not action.get('reaction'):raise ValueError('Сейчас ход другого участника')
    candidate=deepcopy(latest)
    messages=e.perform_action(candidate,'ally',aid,victims,False,destination=destination,area_center=area_center)
    candidate['combat_log']=[f"[{datetime.now().strftime('%H:%M:%S')}] {m}" for m in reversed(messages)]+candidate['combat_log']
    candidate['combat_log']=candidate['combat_log'][:80]
    e.recalc(candidate)
    revision=write_state(path,candidate,revision,e.migrate)
    return candidate,revision,messages


def finish_player_turn(path,seen):
    latest,revision=read_state(path)
    if latest is None:raise ValueError('Игра не найдена')
    latest=e.migrate(latest)
    if latest['turn_serial']!=seen['turn_serial']:raise ValueError('Ход уже изменился')
    if not latest['combat_active'] or not e.get_current_actor(latest) or e.actor_token(e.get_current_actor(latest))!='ally':raise ValueError('Сейчас ход другого участника')
    messages=e.advance_turn(latest)
    latest['combat_log']=[f"[{datetime.now().strftime('%H:%M:%S')}] {m}" for m in reversed(messages)]+latest['combat_log']
    latest['combat_log']=latest['combat_log'][:80]
    return latest,write_state(path,latest,revision,e.migrate)
