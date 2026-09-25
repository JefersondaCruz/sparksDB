import uuid

from .paths import config_dir, read_json, storage_lock, write_json


def _file():
    return config_dir() / "saved_queries.json"


def list_queries() -> list[dict]:
    data = read_json(_file(), [])
    return data if isinstance(data, list) else []


def save_query(data: dict) -> dict:
    with storage_lock:
        return _save_query(data)


def _save_query(data: dict) -> dict:
    queries = list_queries()
    record = {
        "id": data.get("id") or str(uuid.uuid4()),
        "connId": data["connId"],
        "name": data["name"],
        "sql": data["sql"],
    }
    for index, query in enumerate(queries):
        if query.get("id") == record["id"]:
            queries[index] = record
            break
    else:
        queries.append(record)
    write_json(_file(), queries)
    return record


def delete_query(query_id: str) -> None:
    with storage_lock:
        write_json(_file(), [q for q in list_queries() if q.get("id") != query_id])
