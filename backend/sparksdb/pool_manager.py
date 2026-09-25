import threading
import time

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.postgres import types as pg_types
from psycopg.types.string import TextLoader
from psycopg_pool import ConnectionPool

NOT_ACTIVE = "Conexao nao esta ativa. Conecte antes de rodar queries."
SSL_UNSUPPORTED = "Conexao com SSL ainda nao e suportada nesta versao do sparksDB."


class BackendError(Exception):
    """Erro cuja mensagem vai direto pra UI."""


_pools: dict[str, ConnectionPool] = {}
_lock = threading.Lock()


def describe_error(e: Exception) -> str:
    diag = getattr(e, "diag", None)
    if diag is not None and diag.message_primary:
        return diag.message_primary
    message = str(e)
    if "FATAL:" in message:
        return message.rsplit("FATAL:", 1)[1].strip()
    return message


def build_conninfo(profile: dict, password: str) -> str:
    if profile.get("ssl"):
        raise BackendError(SSL_UNSUPPORTED)
    return make_conninfo(
        host=profile["host"],
        port=profile.get("port") or 5432,
        dbname=profile["database"],
        user=profile["user"],
        password=password,
        sslmode="disable",
        connect_timeout=10,
    )


def check_connection(conninfo: str) -> None:
    try:
        with psycopg.connect(conninfo, autocommit=True) as conn:
            conn.execute("SELECT 1")
    except psycopg.Error as e:
        raise BackendError(describe_error(e)) from None


def open_pool(conninfo: str) -> ConnectionPool:
    check_connection(conninfo)
    return ConnectionPool(
        conninfo,
        min_size=1,
        max_size=4,
        kwargs={"autocommit": True, "prepare_threshold": None},
        check=ConnectionPool.check_connection,
        timeout=10,
        open=True,
    )


def register(conn_id: str, pool: ConnectionPool) -> None:
    with _lock:
        existing = _pools.get(conn_id)
        if existing is None:
            _pools[conn_id] = pool
    if existing is not None:
        pool.close()


def is_active(conn_id: str) -> bool:
    with _lock:
        return conn_id in _pools


def get_pool(conn_id: str) -> ConnectionPool:
    with _lock:
        pool = _pools.get(conn_id)
    if pool is None:
        raise BackendError(NOT_ACTIVE)
    return pool


def close(conn_id: str) -> None:
    with _lock:
        pool = _pools.pop(conn_id, None)
    if pool is not None:
        pool.close()


def close_all() -> None:
    with _lock:
        pools = list(_pools.values())
        _pools.clear()
    for pool in pools:
        pool.close()


def _use_text_loaders(cursor) -> None:
    for pg_type in pg_types:
        cursor.adapters.register_loader(pg_type.oid, TextLoader)
        if pg_type.array_oid:
            cursor.adapters.register_loader(pg_type.array_oid, TextLoader)


def run_query(pool: ConnectionPool, sql: str) -> dict:
    start = time.perf_counter()
    fields, rows, row_count, error = [], [], 0, None
    try:
        with pool.connection() as conn:
            cursor = conn.cursor()
            _use_text_loaders(cursor)
            cursor.execute(sql)
            while True:
                if cursor.description is not None:
                    names = [column.name for column in cursor.description]
                    fields = [{"name": name} for name in names]
                    rows = [dict(zip(names, row)) for row in cursor.fetchall()]
                row_count = max(cursor.rowcount, 0)
                if not cursor.nextset():
                    break
    except psycopg.Error as e:
        fields, rows, row_count, error = [], [], 0, describe_error(e)
    return {
        "rows": rows,
        "fields": fields,
        "rowCount": row_count,
        "durationMs": int((time.perf_counter() - start) * 1000),
        "error": error,
    }
