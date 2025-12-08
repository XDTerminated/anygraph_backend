from typing import Optional, Dict, List, Any
from .database import get_db_cursor, load_sql


def create_chat_session(email: str, title: str = "New Chat") -> Dict[str, Any]:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('chat_sessions', 'insert_chat_session'), (email, title))
        session = cursor.fetchone()
        return dict(session) if session else None


def get_chat_session(session_id: str) -> Optional[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('chat_sessions', 'get_chat_session'), (session_id,))
        session = cursor.fetchone()
        return dict(session) if session else None


def verify_session_owner(session_id: str, email: str) -> bool:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('chat_sessions', 'verify_session_owner'), (session_id, email))
        result = cursor.fetchone()
        return result is not None


def get_chat_session_with_messages(session_id: str) -> Optional[Dict[str, Any]]:
    session = get_chat_session(session_id)
    if not session:
        return None

    messages = get_messages(session_id)

    return {
        "session": session,
        "messages": messages
    }


def get_user_chat_sessions(email: str) -> List[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('chat_sessions', 'get_user_chat_sessions'), (email,))
        sessions = cursor.fetchall()
        return [dict(session) for session in sessions] if sessions else []


def update_chat_session_title(session_id: str, title: str) -> Optional[Dict[str, Any]]:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('chat_sessions', 'update_chat_session'), (title, session_id))
        session = cursor.fetchone()
        return dict(session) if session else None


def delete_chat_session(session_id: str) -> bool:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('chat_sessions', 'delete_chat_session'), (session_id,))
        result = cursor.fetchone()
        return result is not None


def add_message(session_id: str, sender: str, message_text: str, generated_code: Optional[str] = None) -> Dict[str, Any]:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('messages', 'insert_message'), (sender, message_text, session_id, generated_code))
        message = cursor.fetchone()
        return dict(message) if message else None


def get_messages(session_id: str) -> List[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('messages', 'get_messages'), (session_id,))
        messages = cursor.fetchall()
        return [dict(message) for message in messages] if messages else []
