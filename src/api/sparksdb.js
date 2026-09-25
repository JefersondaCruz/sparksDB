// O pywebview injeta window.pywebview.api e so depois dispara 'pywebviewready'.
// Erros do Python chegam como Error(message), que o errorText() ja trata.
const ready = new Promise((resolve) => {
  if (window.pywebview?.api?.connections_list) resolve()
  else window.addEventListener('pywebviewready', () => resolve(), { once: true })
})

async function call(name, ...args) {
  await ready
  return window.pywebview.api[name](...args)
}

window.sparksdb = {
  connections: {
    list: () => call('connections_list'),
    save: (profile) => call('connections_save', profile),
    delete: (id) => call('connections_delete', id),
    test: (profile) => call('connections_test', profile)
  },
  db: {
    connect: (id) => call('db_connect', id),
    disconnect: (id) => call('db_disconnect', id),
    query: (id, sql) => call('db_query', id, sql),
    schemas: (id) => call('db_schemas', id),
    tables: (id, schema) => call('db_tables', id, schema),
    columns: (id, schema, table) => call('db_columns', id, schema, table),
    tableData: (id, schema, table, limit, offset) =>
      call('db_table_data', id, schema, table, limit, offset)
  },
  queries: {
    list: () => call('queries_list'),
    save: (input) => call('queries_save', input),
    delete: (id) => call('queries_delete', id)
  }
}
