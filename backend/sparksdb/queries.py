import json

import psycopg
from psycopg import sql

from .pool_manager import BackendError, describe_error

SCHEMAS_SQL = (
    "SELECT schema_name FROM information_schema.schemata "
    "WHERE schema_name NOT IN ('pg_catalog', 'information_schema') "
    "AND schema_name NOT LIKE 'pg_toast%' "
    "AND schema_name NOT LIKE 'pg_temp%' "
    "ORDER BY schema_name"
)
TABLES_SQL = (
    "SELECT table_name, table_type FROM information_schema.tables "
    "WHERE table_schema = %s ORDER BY table_name"
)
COLUMNS_SQL = (
    "SELECT column_name, data_type, is_nullable, column_default "
    "FROM information_schema.columns "
    "WHERE table_schema = %s AND table_name = %s "
    "ORDER BY ordinal_position"
)


def _fetch_all(pool, query, params=None):
    try:
        with pool.connection() as conn:
            return conn.execute(query, params).fetchall()
    except psycopg.Error as e:
        raise BackendError(describe_error(e)) from None


def list_schemas(pool) -> list[str]:
    return [row[0] for row in _fetch_all(pool, SCHEMAS_SQL)]


def list_tables(pool, schema: str) -> list[dict]:
    return [
        {"name": name, "type": table_type}
        for name, table_type in _fetch_all(pool, TABLES_SQL, (schema,))
    ]


def list_columns(pool, schema: str, table: str) -> list[dict]:
    return [
        {"name": name, "type": data_type, "nullable": is_nullable == "YES", "default": default}
        for name, data_type, is_nullable, default in _fetch_all(pool, COLUMNS_SQL, (schema, table))
    ]


def get_table_data(pool, schema: str, table: str, limit: int, offset: int) -> dict:
    ident = sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table))
    page = sql.SQL("SELECT * FROM {} LIMIT %s OFFSET %s").format(ident)
    try:
        with pool.connection() as conn:
            described = conn.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(ident))
            fields = [{"name": column.name} for column in described.description]
            json_rows = conn.execute(
                sql.SQL("SELECT to_jsonb(t)::text FROM ({}) t").format(page), (limit, offset)
            ).fetchall()
            total = conn.execute(sql.SQL("SELECT count(*) FROM {}").format(ident)).fetchone()[0]
    except psycopg.Error as e:
        raise BackendError(describe_error(e)) from None

    rows = []
    for (raw,) in json_rows:
        value = json.loads(raw)
        rows.append(value if isinstance(value, dict) else {})
    return {"rows": rows, "fields": fields, "totalCount": int(total)}
