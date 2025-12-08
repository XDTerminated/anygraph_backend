from typing import Optional, Dict, List, Any
from datetime import datetime
from .database import get_db_cursor, load_sql


def add_or_login_user(email: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('users', 'insert_user'), (email, full_name))
        user = cursor.fetchone()
        return dict(user) if user else None


def get_user(email: str) -> Optional[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('users', 'get_user'), (email,))
        user = cursor.fetchone()
        return dict(user) if user else None


def get_user_with_chat_sessions(email: str) -> Dict[str, Any]:
    user = get_user(email)
    if not user:
        return None

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('chat_sessions', 'get_user_chat_sessions'), (email,))
        sessions = cursor.fetchall()
        chat_sessions = [dict(session) for session in sessions] if sessions else []

    return {
        "user": user,
        "chat_sessions": chat_sessions
    }


def update_user(email: str, full_name: Optional[str] = None,
                last_log_in: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('users', 'update_user'), (full_name, last_log_in, email))
        user = cursor.fetchone()
        return dict(user) if user else None


def user_exists(email: str) -> bool:
    user = get_user(email)
    return user is not None
