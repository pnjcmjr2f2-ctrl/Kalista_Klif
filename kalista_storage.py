"""Atomic shared state with revision checking and an inter-process lock."""
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
import fcntl

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
            validator(json.loads(old))
            atomic_text(path.with_suffix('.json.bak'), old)
        atomic_text(path, payload)
    return revision(payload)
