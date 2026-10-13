"""Atomic shared state with revision checking and an inter-process lock."""
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
import fcntl
from datetime import datetime, timezone
from uuid import uuid4

class StaleState(ValueError):
    pass

def revision(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

@contextmanager
def locked(path):
    path = Path(path)
    with path.with_suffix(path.suffix + '.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(handle, fcntl.LOCK_UN)

def read_state(path):
    path = Path(path)
    with locked(path):
        text = path.read_text(encoding='utf-8') if path.exists() else ''
    return (json.loads(text) if text else None), revision(text)

def atomic_text(path, text):
    path = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(text); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None: temp.unlink(missing_ok=True)

def write_state(path, state, expected_revision, validator):
    path = Path(path)
    payload = json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False)
    validator(state)
    with locked(path):
        old = path.read_text(encoding='utf-8') if path.exists() else ''
        if revision(old) != expected_revision: raise StaleState('Другой экран уже изменил игру')
        if old == payload: return revision(old)
        if old:
            snapshot_text(path,old,"auto")
            validator(json.loads(old))
            atomic_text(path.with_suffix('.json.bak'), old)
        atomic_text(path, payload)
    return revision(payload)


def snapshot_text(path,text,label='manual'):
    path=Path(path);folder=path.parent/'save_snapshots';folder.mkdir(exist_ok=True)
    label=label if label in ('auto','manual','before-battle','before-restore') else 'manual'
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S-%f')
    destination=folder/(stamp+'_'+label+'_'+uuid4().hex[:6]+'.json')
    atomic_text(destination,text);destination.chmod(0o600)
    files=sorted(folder.glob('*_'+label+'_*.json'))
    for old in files[:-30 if label=='auto' else -10]:old.unlink()
    return destination.name


def create_snapshot(path,label='manual'):
    path=Path(path)
    with locked(path):
        return snapshot_text(path,path.read_text(encoding='utf-8'),label)


def list_snapshots(path):
    return sorted((Path(path).parent/'save_snapshots').glob('*.json'),reverse=True)


def restore_snapshot(path,name,expected_revision,validator):
    path=Path(path);folder=(path.parent/'save_snapshots').resolve();source=(folder/name).resolve()
    if source.parent!=folder or source.suffix!='.json':raise ValueError('Неверный снимок')
    candidate=validator(json.loads(source.read_text(encoding='utf-8')))
    write_state(path,candidate,expected_revision,validator)
    return candidate
