"""Simple JSON-based persistence layer (replaces SQLite).

Data model (all optional – created lazily):
  data/users.json                 { user_id: {"username": str, "first_seen": iso } }
  data/warnings.json              { user_id: [ {"moderator": id, "reason": str, "ts": iso} ] }
  data/challenge_submissions.json { challenge_id: [ {"user_id": id, "link": str, "ts": iso} ] }
  data/qotd_submissions.json      { question_id: [ {"user_id": id, "answer": str, "ts": iso} ] }

All functions are async for API parity with previous aiosqlite calls, but they
perform small synchronous file I/O guarded by an asyncio.Lock per path.
"""
from __future__ import annotations

import json
import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

_LOCKS: Dict[str, asyncio.Lock] = {}
_BASE = os.path.join('data')

def _path(name: str) -> str:
    os.makedirs(_BASE, exist_ok=True)
    return os.path.join(_BASE, name)

def _lock(path: str) -> asyncio.Lock:
    if path not in _LOCKS:
        _LOCKS[path] = asyncio.Lock()
    return _LOCKS[path]

async def _load(path: str) -> Any:
    lock = _lock(path)
    async with lock:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            backup = path + '.corrupt.' + datetime.utcnow().strftime('%Y%m%d%H%M%S')
            try:
                os.replace(path, backup)
            except OSError:
                pass
            return {}

async def _save(path: str, data: Any) -> None:
    lock = _lock(path)
    async with lock:
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

# Users ----------------------------------------------------------------------
async def add_or_update_user(user_id: int, username: str) -> None:
    path = _path('users.json')
    data = await _load(path)
    key = str(user_id)
    if key not in data:
        data[key] = {
            'username': username,
            'first_seen': datetime.now(timezone.utc).isoformat()
        }
    else:
        data[key]['username'] = username
    await _save(path, data)

# Warnings ------------------------------------------------------------------
async def add_warning(user_id: int, moderator_id: int, reason: str) -> None:
    path = _path('warnings.json')
    data = await _load(path)
    key = str(user_id)
    data.setdefault(key, []).append({
        'moderator': moderator_id,
        'reason': reason,
        'ts': datetime.now(timezone.utc).isoformat()
    })
    await _save(path, data)

async def get_warnings(user_id: int) -> List[dict]:
    path = _path('warnings.json')
    data = await _load(path)
    return data.get(str(user_id), [])

# Challenge submissions ------------------------------------------------------
async def add_challenge_submission(user_id: int, challenge_id: str, link: str) -> None:
    path = _path('challenge_submissions.json')
    data = await _load(path)
    bucket = data.setdefault(challenge_id, [])
    bucket.append({
        'user_id': user_id,
        'link': link,
        'ts': datetime.now(timezone.utc).isoformat()
    })
    await _save(path, data)

async def get_challenge_submissions(challenge_id: str) -> List[dict]:
    path = _path('challenge_submissions.json')
    data = await _load(path)
    return data.get(challenge_id, [])

# QOTD submissions -----------------------------------------------------------
async def add_qotd_submission(user_id: int, question_id: str, answer: str) -> None:
    path = _path('qotd_submissions.json')
    data = await _load(path)
    bucket = data.setdefault(question_id, [])
    bucket.append({
        'user_id': user_id,
        'answer': answer,
        'ts': datetime.now(timezone.utc).isoformat()
    })
    await _save(path, data)

async def get_qotd_submissions(question_id: str) -> List[dict]:
    path = _path('qotd_submissions.json')
    data = await _load(path)
    return data.get(question_id, [])

# Generic helpers ------------------------------------------------------------
async def health_snapshot() -> Dict[str, int]:
    users = await _load(_path('users.json'))
    return { 'users': len(users) }

__all__ = [
    'add_or_update_user', 'add_warning', 'get_warnings',
    'add_challenge_submission', 'get_challenge_submissions',
    'add_qotd_submission', 'get_qotd_submissions', 'health_snapshot'
]
