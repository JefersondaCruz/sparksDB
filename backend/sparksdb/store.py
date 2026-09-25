import uuid

import keyring

from .paths import config_dir, read_json, storage_lock, write_json

KEYRING_SERVICE = "sparksdb"


def _connections_file():
    return config_dir() / "connections.json"


def _fallback_file():
    return config_dir() / "connections-fallback.json"

def _keyring_get(conn_id: str) -> str | None:
    try:
        return keyring.get_password(KEYRING_SERVICE, conn_id)
    except Exception:
        return None


def _keyring_set(conn_id: str, password: str) -> bool:
    try:
        keyring.set_password(KEYRING_SERVICE, conn_id, password)
        return True
    except Exception:
        return False


def _keyring_delete(conn_id: str) -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, conn_id)
    except Exception:
        pass


def _read_fallback() -> dict:
    data = read_json(_fallback_file(), {})
    return data if isinstance(data, dict) else {}


def _write_fallback(conn_id: str, password: str) -> None:
    passwords = _read_fallback()
    passwords[conn_id] = password
    write_json(_fallback_file(), passwords)


def _remove_fallback(conn_id: str) -> None:
    if not _fallback_file().exists():
        return
    passwords = _read_fallback()
    passwords.pop(conn_id, None)
    write_json(_fallback_file(), passwords)


def list_connections() -> list[dict]:
    data = read_json(_connections_file(), [])
    return data if isinstance(data, list) else []


def get_connection_with_password(conn_id: str) -> tuple[dict, str] | None:
    profile = next((c for c in list_connections() if c.get("id") == conn_id), None)
    if profile is None:
        return None
    if profile.get("encrypted"):
        password = _keyring_get(conn_id)
    else:
        password = _read_fallback().get(conn_id)
    return profile, password or ""


def save_connection(data: dict) -> dict:
    with storage_lock:
        return _save_connection(data)


def _save_connection(data: dict) -> dict:
    connections = list_connections()
    conn_id = data.get("id") or str(uuid.uuid4())
    password = data.get("password")

    if password is not None:
        encrypted = _keyring_set(conn_id, password)
        if encrypted:
            _remove_fallback(conn_id)
        else:
            _write_fallback(conn_id, password)
    else:
        previous = next((c for c in connections if c.get("id") == conn_id), {})
        encrypted = bool(previous.get("encrypted", False))

    record = {
        "id": conn_id,
        "name": data["name"],
        "host": data["host"],
        "port": data.get("port") or 5432,
        "database": data["database"],
        "user": data["user"],
        "ssl": bool(data.get("ssl")),
        "encrypted": encrypted,
    }
    for index, connection in enumerate(connections):
        if connection.get("id") == conn_id:
            connections[index] = record
            break
    else:
        connections.append(record)
    write_json(_connections_file(), connections)
    return record


def delete_connection(conn_id: str) -> None:
    with storage_lock:
        write_json(_connections_file(), [c for c in list_connections() if c.get("id") != conn_id])
        _keyring_delete(conn_id)
        _remove_fallback(conn_id)
