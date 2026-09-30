from . import pool_manager, queries, saved_queries, store
from .pool_manager import BackendError


class Api:
    """Metodos expostos ao frontend via window.pywebview.api (mesmos nomes dos commands Tauri)."""

    def connections_list(self):
        return store.list_connections()

    def connections_save(self, profile):
        return store.save_connection(profile)

    def connections_delete(self, conn_id):
        store.delete_connection(conn_id)

    def connections_test(self, profile):
        conninfo = pool_manager.build_conninfo(profile, profile.get("password") or "")
        pool_manager.check_connection(conninfo)

    def db_connect(self, conn_id):
        if pool_manager.is_active(conn_id):
            return
        found = store.get_connection_with_password(conn_id)
        if found is None:
            raise BackendError("Conexao nao encontrada")
        profile, password = found
        pool = pool_manager.open_pool(pool_manager.build_conninfo(profile, password))
        pool_manager.register(conn_id, pool)

    def db_disconnect(self, conn_id):
        pool_manager.close(conn_id)

    def db_query(self, conn_id, sql):
        return pool_manager.run_query(pool_manager.get_pool(conn_id), sql)

    def db_schemas(self, conn_id):
        return queries.list_schemas(pool_manager.get_pool(conn_id))

    def db_tables(self, conn_id, schema):
        return queries.list_tables(pool_manager.get_pool(conn_id), schema)

    def db_columns(self, conn_id, schema, table):
        return queries.list_columns(pool_manager.get_pool(conn_id), schema, table)

    def db_table_data(self, conn_id, schema, table, limit=None, offset=None):
        return queries.get_table_data(
            pool_manager.get_pool(conn_id),
            schema,
            table,
            100 if limit is None else limit,
            0 if offset is None else offset,
        )

    def queries_list(self):
        return saved_queries.list_queries()

    def queries_save(self, data):
        return saved_queries.save_query(data)

    def queries_delete(self, query_id):
        saved_queries.delete_query(query_id)
