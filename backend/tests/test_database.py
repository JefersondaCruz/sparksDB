import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from sparksdb import pool_manager, queries, store
from sparksdb.api import Api
from sparksdb.pool_manager import BackendError, run_query


def test_run_query_returns_postgres_text_values(pg_pool):
    result = run_query(
        pg_pool,
        "SELECT 1.50::numeric AS n, '2024-01-02 03:04:05'::timestamp AS ts, "
        "'{\"b\": 2, \"a\": 1}'::jsonb AS j, NULL::int AS x, 'a%' LIKE 'a%' AS b",
    )

    assert result["error"] is None
    assert result["fields"] == [{"name": n} for n in ["n", "ts", "j", "x", "b"]]
    assert result["rows"] == [
        {"n": "1.50", "ts": "2024-01-02 03:04:05", "j": '{"a": 1, "b": 2}', "x": None, "b": "t"}
    ]
    assert result["rowCount"] == 1
    assert isinstance(result["durationMs"], int)


def test_run_query_multiple_statements_keeps_last_result_set(pg_pool, pg_schema):
    result = run_query(
        pg_pool,
        "CREATE TABLE sparksdb_test.t (a int); INSERT INTO sparksdb_test.t VALUES (1), (2); "
        "SELECT a FROM sparksdb_test.t ORDER BY a; UPDATE sparksdb_test.t SET a = a + 10",
    )
    assert result["error"] is None
    assert result["fields"] == [{"name": "a"}]
    assert result["rows"] == [{"a": "1"}, {"a": "2"}]
    assert result["rowCount"] == 2

    ddl = run_query(pg_pool, "DROP TABLE sparksdb_test.t")
    assert (ddl["error"], ddl["rowCount"]) == (None, 0)

    blank = run_query(pg_pool, "   ")
    assert (blank["error"], blank["rows"], blank["fields"], blank["rowCount"]) == (None, [], [], 0)


def test_errors_return_primary_postgres_message(pg_pool, pg_dsn):
    result = run_query(pg_pool, "SELEC 1")
    assert result["error"] == 'syntax error at or near "SELEC"'
    assert (result["rows"], result["fields"], result["rowCount"]) == ([], [], 0)

    wrong = make_conninfo(**{**conninfo_to_dict(pg_dsn), "password": "senha-errada"})
    with pytest.raises(BackendError) as excinfo:
        pool_manager.check_connection(wrong)
    assert str(excinfo.value).startswith("password authentication failed for user")


def test_table_data_paginates_and_counts(pg_pool, pg_schema):
    run_query(
        pg_pool,
        'CREATE TABLE sparksdb_test."we""ird" (id int, name text); '
        "INSERT INTO sparksdb_test.\"we\"\"ird\" SELECT i, 'n' || i FROM generate_series(1, 5) i",
    )

    data = queries.get_table_data(pg_pool, "sparksdb_test", 'we"ird', 2, 2)

    assert data == {
        "fields": [{"name": "id"}, {"name": "name"}],
        "rows": [{"id": 3, "name": "n3"}, {"id": 4, "name": "n4"}],
        "totalCount": 5,
    }


def test_schema_tables_and_columns(pg_pool, pg_schema):
    run_query(
        pg_pool,
        "CREATE TABLE sparksdb_test.items (id serial PRIMARY KEY, label text NOT NULL, note text); "
        "CREATE VIEW sparksdb_test.v AS SELECT 1 AS one",
    )

    schemas = queries.list_schemas(pg_pool)
    assert "sparksdb_test" in schemas
    assert "pg_catalog" not in schemas and "information_schema" not in schemas

    assert queries.list_tables(pg_pool, "sparksdb_test") == [
        {"name": "items", "type": "BASE TABLE"},
        {"name": "v", "type": "VIEW"},
    ]
    assert queries.list_columns(pg_pool, "sparksdb_test", "items") == [
        {"name": "id", "type": "integer", "nullable": False,
         "default": "nextval('sparksdb_test.items_id_seq'::regclass)"},
        {"name": "label", "type": "text", "nullable": False, "default": None},
        {"name": "note", "type": "text", "nullable": True, "default": None},
    ]


def test_api_connection_lifecycle(config_home, memory_keyring, pg_dsn, pg_schema):
    params = conninfo_to_dict(pg_dsn)
    profile = store.save_connection({
        "name": "teste",
        "host": params.get("host", "localhost"),
        "port": int(params.get("port", 5432)),
        "database": params["dbname"],
        "user": params["user"],
        "password": params.get("password", ""),
    })
    api = Api()

    api.db_connect(profile["id"])
    first_pool = pool_manager.get_pool(profile["id"])
    api.db_connect(profile["id"])
    assert pool_manager.get_pool(profile["id"]) is first_pool

    api.db_query(
        profile["id"],
        "CREATE TABLE sparksdb_test.many AS SELECT i FROM generate_series(1, 150) i",
    )
    data = api.db_table_data(profile["id"], "sparksdb_test", "many", None, None)
    assert (len(data["rows"]), data["rows"][0], data["totalCount"]) == (100, {"i": 1}, 150)

    api.db_disconnect(profile["id"])
    with pytest.raises(BackendError, match="Conexao nao esta ativa"):
        api.db_query(profile["id"], "SELECT 1")
    with pytest.raises(BackendError, match="Conexao nao encontrada"):
        api.db_connect("id-inexistente")


def test_queries_keep_working_after_schema_change_elsewhere(pg_pool, pg_schema, pg_dsn):
    run_query(pg_pool, "CREATE TABLE sparksdb_test.t AS SELECT 1 AS a")
    for _ in range(10):
        run_query(pg_pool, "SELECT * FROM sparksdb_test.t")
        queries.get_table_data(pg_pool, "sparksdb_test", "t", 100, 0)

    with psycopg.connect(pg_dsn, autocommit=True) as other:
        other.execute("ALTER TABLE sparksdb_test.t ADD COLUMN b text")

    result = run_query(pg_pool, "SELECT * FROM sparksdb_test.t")
    assert (result["error"], result["fields"]) == (None, [{"name": "a"}, {"name": "b"}])
    assert queries.get_table_data(pg_pool, "sparksdb_test", "t", 100, 0)["fields"] == result["fields"]


def test_pool_recovers_after_server_drops_connections(pg_pool, pg_dsn):
    assert run_query(pg_pool, "SELECT 1")["error"] is None

    with psycopg.connect(pg_dsn, autocommit=True) as admin:
        admin.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = current_database() AND pid <> pg_backend_pid() AND backend_type = 'client backend'"
        )

    assert run_query(pg_pool, "SELECT 1")["error"] is None
