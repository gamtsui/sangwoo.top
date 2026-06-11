"""AI Chatbot - Product knowledge base + conversation context."""
import os
import json
import time
import uuid
from typing import Optional
from datetime import datetime
from collections import OrderedDict

import httpx

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .database import SessionLocal
from .models import Products, SystemLog

# ============ Config ============
AI_API_BASE = os.getenv('AI_API_BASE', 'https://sangwoozen.com/v1')
AI_API_KEY = os.getenv('AI_API_KEY', '')
AI_MODEL = os.getenv('AI_MODEL', 'qwen3-32b')
CHAT_HISTORY_LIMIT = 5  # Keep last 5 rounds per session

# In-memory session store: session_id -> list of messages
# In production, replace with Redis. For now, it survives restarts via SQLite.
_chat_sessions: dict[str, list[dict]] = {}

router = APIRouter(prefix='/api/chat', tags=['chat'])

# System prompt - loaded once
SYSTEM_PROMPT_ZH = """你是Sangwoo的AI客服助手。Sangwoo是一家韩国食品进口商。
请用中文回答客户问题。如果问题与产品相关，请基于以下产品信息回答。
如果不知道答案，请礼貌地建议客户联系我们获取更多信息。
保持回答简洁、专业、友好。"""

SYSTEM_PROMPT_EN = """You are the AI customer service assistant for Sangwoo, a Korean food importer.
Please answer customer questions in English. If the question is product-related, base your answer on the product information below.
If you don't know the answer, politely suggest the customer contact us for more information.
Keep responses concise, professional, and friendly."""


def _get_product_context() -> str:
    """Load active products from SQLite as knowledge context."""
    db = SessionLocal()
    try:
        products = db.query(Products).filter(Products.is_active == True).all()
        if not products:
            return ""
        lines = []
        for p in products:
            desc = p.description_zh or p.description_en or ''
            specs = ''
            if p.specifications:
                specs = ' 规格: ' + json.dumps(p.specifications, ensure_ascii=False)
            lines.append(f"- {p.name_zh or p.name_en}: {desc[:200]}{specs}")
        return '\n'.join(lines)
    finally:
        db.close()


def _ensure_chat_table():
    """Lazily create the chat sessions table."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                messages TEXT,
                created_at TEXT,
                UNIQUE(session_id)
            )
        """))
        db.commit()
    finally:
        db.close()


def _load_session(session_id: str) -> list[dict]:
    """Load conversation history from SQLite for a session."""
    _ensure_chat_table()
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text(
            "SELECT messages FROM ai_chat_sessions WHERE session_id = :sid ORDER BY created_at DESC LIMIT 1"
        ), {"sid": session_id})
        row = result.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    finally:
        db.close()


def _save_session(session_id: str, messages: list[dict]):
    """Upsert conversation history to SQLite."""
    _ensure_chat_table()
    db = SessionLocal()
    try:
        from sqlalchemy import text
        now = datetime.now().isoformat()
        # Delete old records for this session
        db.execute(text(
            "DELETE FROM ai_chat_sessions WHERE session_id = :sid"
        ), {"sid": session_id})
        # Insert new
        db.execute(text(
            "INSERT INTO ai_chat_sessions (session_id, messages, created_at) VALUES (:sid, :msgs, :ts)"
        ), {"sid": session_id, "msgs": json.dumps(messages, ensure_ascii=False), "ts": now})
        db.commit()
    except Exception as e:
        # Non-critical - chat still works without persistence
        _log_error(f"Failed to save chat session: {e}")
    finally:
        db.close()


def _log_error(message: str):
    db = SessionLocal()
    try:
        db.add(SystemLog(level='error', message=message))
        db.commit()
    finally:
        db.close()




class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    lang: str = 'zh'


class ChatResponse(BaseModel):
    reply: str
    session_id: str




@router.post('')
async def chat(data: ChatRequest):
    """Handle chat message. Returns AI reply with product context."""
    session_id = data.session_id or str(uuid.uuid4())
    lang = data.lang

    # Load history (last CHAT_HISTORY_LIMIT rounds = 10 messages)
    history = _load_session(session_id)

    # Build messages
    system_prompt = SYSTEM_PROMPT_ZH if lang == 'zh' else SYSTEM_PROMPT_EN
    product_context = _get_product_context()
    if product_context:
        system_prompt += f"\n\n当前产品信息：\n{product_context}"

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-CHAT_HISTORY_LIMIT * 2:])  # Last N rounds
    messages.append({"role": "user", "content": data.message})

    # Call AI API
    api_key = AI_API_KEY or os.getenv('SANGWOOPEN_API_KEY', '')
    if not api_key:
        reply_text = '抱歉，AI客服功能暂未配置。请直接通过联系我们页面咨询。' if lang == 'zh' else 'Sorry, AI chat is not configured. Please use our contact form instead.'
        return ChatResponse(reply=reply_text, session_id=session_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{AI_API_BASE}/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': AI_MODEL,
                    'messages': messages,
                    'max_tokens': 1024,
                    'temperature': 0.7,
                }
            )
            resp.raise_for_status()
            result = resp.json()
            reply = result['choices'][0]['message']['content']
    except Exception as e:
        error_msg = str(e)
        _log_error(f"AI chat API error: {error_msg}")
        reply = '抱歉，服务暂时不可用，请稍后再试。您也可以联系我们获取帮助。' if lang == 'zh' else 'Sorry, the service is temporarily unavailable. Please try again later or contact us.'

    # Update history
    new_history = history + [
        {"role": "user", "content": data.message},
        {"role": "assistant", "content": reply},
    ]
    # Trim to last CHAT_HISTORY_LIMIT rounds
    new_history = new_history[-CHAT_HISTORY_LIMIT * 2:]
    _save_session(session_id, new_history)

    return ChatResponse(reply=reply, session_id=session_id)
