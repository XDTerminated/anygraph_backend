from typing import Dict, List, Any, Optional
import pandas as pd
import requests
from io import BytesIO
from .database import get_db_cursor, load_sql


def get_datatype_string(dtype) -> str:
    dtype_str = str(dtype)

    if 'int' in dtype_str:
        return 'int'
    elif 'float' in dtype_str:
        return 'float'
    elif 'bool' in dtype_str:
        return 'bool'
    elif 'datetime' in dtype_str:
        return 'datetime'
    elif 'object' in dtype_str:
        return 'str'
    else:
        return dtype_str


def analyze_dataset(dataset_url: str, email: str, chat_session_id: str,
                    name: str, file_type: str = None) -> Dict[str, Any]:
    try:
        response = requests.get(dataset_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Failed to download dataset: {str(e)}")

    if not file_type:
        if dataset_url.endswith('.csv'):
            file_type = 'csv'
        elif dataset_url.endswith(('.xlsx', '.xls')):
            file_type = 'excel'
        else:
            file_type = 'csv'

    try:
        file_content = BytesIO(response.content)

        if file_type == 'csv':
            df = pd.read_csv(file_content)
        elif file_type in ['excel', 'xlsx', 'xls']:
            df = pd.read_excel(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        raise Exception(f"Failed to parse dataset: {str(e)}")

    dataset = insert_dataset(dataset_url, name, file_type, chat_session_id)

    columns = []
    for column_name in df.columns:
        dtype = get_datatype_string(df[column_name].dtype)

        example_value = None
        non_null_values = df[column_name].dropna()
        if len(non_null_values) > 0:
            example_value = str(non_null_values.iloc[0])

        column_data = insert_column(
            email=email,
            name=column_name,
            datatype=dtype,
            example_value=example_value,
            dataset_url=dataset_url
        )
        columns.append(column_data)

    return {
        "dataset": dataset,
        "columns": columns,
        "row_count": len(df),
        "column_count": len(df.columns)
    }


def insert_dataset(dataset_url: str, name: str, file_type: str,
                   chat_session_id: str) -> Dict[str, Any]:
    with get_db_cursor() as cursor:
        cursor.execute(
            load_sql('datasets', 'insert_dataset'),
            (dataset_url, name, file_type, chat_session_id)
        )
        dataset = cursor.fetchone()
        return dict(dataset) if dataset else None


def get_dataset(dataset_url: str) -> Optional[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('datasets', 'get_dataset'), (dataset_url,))
        dataset = cursor.fetchone()
        return dict(dataset) if dataset else None


def get_session_datasets(session_id: str) -> List[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('datasets', 'get_session_datasets'), (session_id,))
        datasets = cursor.fetchall()
        return [dict(dataset) for dataset in datasets] if datasets else []


def delete_dataset(dataset_url: str) -> bool:
    with get_db_cursor() as cursor:
        cursor.execute(load_sql('datasets', 'delete_dataset'), (dataset_url,))
        result = cursor.fetchone()
        return result is not None


def insert_column(email: str, name: str, datatype: str,
                  example_value: Optional[str], dataset_url: str) -> Dict[str, Any]:
    with get_db_cursor() as cursor:
        cursor.execute(
            load_sql('columns', 'insert_column'),
            (email, name, datatype, example_value, dataset_url)
        )
        column = cursor.fetchone()
        return dict(column) if column else None


def get_dataset_columns(dataset_url: str) -> List[Dict[str, Any]]:
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(load_sql('columns', 'get_dataset_columns'), (dataset_url,))
        columns = cursor.fetchall()
        return [dict(column) for column in columns] if columns else []
