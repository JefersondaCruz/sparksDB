import { invoke } from '@tauri-apps/api/core'

window.sparksdb = {
  connections: {
    list: () => invoke('connections_list'),
    save: (profile) => invoke('connections_save', { profile }),
    delete: (id) => invoke('connections_delete', { id }),
    test: (profile) => invoke('connections_test', { profile })
  },
  db: {
    connect: (id) => invoke('db_connect', { id }),
    disconnect: (id) => invoke('db_disconnect', { id }),
    query: (id, sql) => invoke('db_query', { id, sql }),
    schemas: (id) => invoke('db_schemas', { id }),
    tables: (id, schema) => invoke('db_tables', { id, schema }),
    columns: (id, schema, table) => invoke('db_columns', { id, schema, table }),
    tableData: (id, schema, table, limit, offset) =>
      invoke('db_table_data', { id, schema, table, limit, offset })
  }
}
