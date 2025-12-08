from typing import Dict, Any
from datetime import datetime
from .database import get_db_cursor, load_sql


def get_user_stats(email: str) -> Dict[str, Any]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('stats', 'get_total_datasets'), (email,))
        datasets_result = cursor.fetchone()
        total_datasets = datasets_result['total_datasets'] if datasets_result else 0

        cursor.execute(load_sql('stats', 'get_total_queries'), (email,))
        queries_result = cursor.fetchone()
        total_queries = queries_result['total_queries'] if queries_result else 0

        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cursor.execute(load_sql('stats', 'get_sessions_this_month'), (email, current_month_start))
        month_result = cursor.fetchone()
        sessions_this_month = month_result['sessions_this_month'] if month_result else 0

        return {
            "total_datasets": total_datasets,
            "total_queries": total_queries,
            "sessions_this_month": sessions_this_month
        }
