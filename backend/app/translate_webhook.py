"""Auto-translation webhook + retry queue."""
import os
import json
import asyncio
from typing import Optional
from datetime import datetime, timedelta

import httpx

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from .database import SessionLocal
from .models import News, Products, SystemLog

AI_API_BASE = os.getenv('AI_API_BASE', 'https://sangwoozen.com/v1')
AI_API_KEY = os.getenv('AI_API_KEY', os.getenv('SANGWOOPEN_API_KEY', ''))
AI_MODEL = os.getenv('AI_MODEL', 'qwen3-32b')

router = APIRouter(prefix='/webhook', tags=['webhook'])

# Retry delays in seconds: 1min, 5min, 15min
RETRY_DELAYS = [60, 300, 900]
MAX_RETRIES = 3

# Simple in-memory queue (for production, use Redis/RQ)
_pending_translations: dict[str, dict] = {}


def _log(level: str, message: str):
    db = SessionLocal()
    try:
        db.add(SystemLog(level=level, message=message))
        db.commit()
    finally:
        db.close()


async def _translate_text(text: str, target_lang: str, context: str = '') -> str:
    """Call AI API to translate text."""
    system_prompt = f"""You are a professional translator. Translate the following text to {target_lang}.
Maintain the meaning, tone, and technical accuracy. 
If the source is Chinese, translate to English. If English, translate to Chinese.
Return ONLY the translated text, no explanations."""
    if context:
        system_prompt += f"\nContext: {context}"

    prompt = text

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f'{AI_API_BASE}/chat/completions',
                headers={
                    'Authorization': f'Bearer {AI_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': AI_MODEL,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt},
                    ],
                    'max_tokens': 4096,
                    'temperature': 0.3,
                }
            )
            resp.raise_for_status()
            result = resp.json()
            return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise Exception(f"Translation API error: {e}")


async def _do_translate(task_id: str, item_type: str, item_id: int, field_zh: str, field_en_key: str):
    """Execute a single translation task with retries."""
    task = _pending_translations.get(task_id)
    if not task:
        return

    attempt = task.get('attempt', 0)
    for i in range(max(attempt, 0), MAX_RETRIES):
        task['attempt'] = i
        try:
            translated = await _translate_text(
                field_zh,
                target_lang='English',
                context=f"{item_type} ({item_id})"
            )
            # Write back to database
            db = SessionLocal()
            try:
                if item_type == 'news':
                    item = db.query(News).filter(News.id == item_id).first()
                    if item:
                        setattr(item, field_en_key, translated)
                elif item_type == 'product':
                    item = db.query(Products).filter(Products.id == item_id).first()
                    if item:
                        setattr(item, field_en_key, translated)
                db.commit()
                _log('info', f"Translation success: {item_type}/{item_id}/{field_en_key} (attempt {i+1})")
            finally:
                db.close()
            # Remove from pending
            _pending_translations.pop(task_id, None)
            return
        except Exception as e:
            _log('warning', f"Translation attempt {i+1}/{MAX_RETRIES} failed for {item_type}/{item_id}: {e}")
            if i < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[i]
                await asyncio.sleep(delay)

    # All retries exhausted
    _log('error', f"Translation FAILED after {MAX_RETRIES} attempts: {item_type}/{item_id}")
    _pending_translations.pop(task_id, None)


def _trigger_translation(item_type: str, item_id: int, text_zh: str, field_zh: str, field_en_key: str) -> str:
    """Queue a translation task. Returns task_id."""
    task_id = f"{item_type}_{item_id}_{field_zh}"
    _pending_translations[task_id] = {
        'type': item_type,
        'item_id': item_id,
        'field_zh': field_zh,
        'field_en_key': field_en_key,
        'text_zh': text_zh,
        'attempt': 0,
        'queued_at': datetime.now().isoformat(),
    }
    _log('info', f"Translation queued: {task_id}")
    return task_id


class TranslateRequest(BaseModel):
    """Manual translation trigger."""
    item_type: str  # 'news' or 'product'
    item_id: int
    field_zh: str   # 'title_zh' or 'content_zh'
    text: str       # The Chinese text to translate


class TranslateResponse(BaseModel):
    task_id: str
    status: str


@router.post('/translate')
async def translate_webhook(data: TranslateRequest, background_tasks: BackgroundTasks):
    """
    Webhook endpoint to trigger auto-translation.
    Called when Chinese content is published without English translation.
    """
    if not AI_API_KEY:
        raise HTTPException(status_code=503, detail='Translation API not configured')

    if data.item_type not in ('news', 'product'):
        raise HTTPException(status_code=400, detail='item_type must be news or product')

    # Determine the English field name
    field_en_key = data.field_zh.replace('_zh', '_en')

    # Verify the item exists
    db = SessionLocal()
    try:
        if data.item_type == 'news':
            item = db.query(News).filter(News.id == data.item_id).first()
        else:
            item = db.query(Products).filter(Products.id == data.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f'{data.item_type} not found')
    finally:
        db.close()

    task_id = _trigger_translation(
        data.item_type, data.item_id, data.text, data.field_zh, field_en_key
    )
    background_tasks.add_task(
        _do_translate, task_id, data.item_type, data.item_id, data.text, field_en_key
    )

    return TranslateResponse(task_id=task_id, status='queued')


@router.get('/translate/status/{task_id}')
async def translation_status(task_id: str):
    """Check translation task status."""
    task = _pending_translations.get(task_id)
    if task:
        return {"task_id": task_id, "status": "pending", "attempt": task.get('attempt', 0)}
    # If not in pending, check logs
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text(
            "SELECT message FROM system_log WHERE message LIKE :pattern ORDER BY id DESC LIMIT 1"
        ), {"pattern": f"%{task_id}%"})
        row = result.fetchone()
        if row and 'success' in row[0]:
            return {"task_id": task_id, "status": "completed"}
    finally:
        db.close()
    return {"task_id": task_id, "status": "unknown"}
