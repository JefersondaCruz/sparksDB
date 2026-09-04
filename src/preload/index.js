import { contextBridge, ipcRenderer } from 'electron'

const api = {
  connections: {
    list: () => ipcRenderer.invoke('connections:list'),
    save: (profile) => ipcRenderer.invoke('connections:save', profile),
    delete: (id) => ipcRenderer.invoke('connections:delete', id),
    test: (profile) => ipcRenderer.invoke('connections:test', profile)
  },
  db: {
    connect: (id) => ipcRenderer.invoke('db:connect', id),
    disconnect: (id) => ipcRenderer.invoke('db:disconnect', id),
    query: (id, sql) => ipcRenderer.invoke('db:query', id, sql),
    schemas: (id) => ipcRenderer.invoke('db:schemas', id),
    tables: (id, schema) => ipcRenderer.invoke('db:tables', id, schema),
    columns: (id, schema, table) => ipcRenderer.invoke('db:columns', id, schema, table),
    tableData: (id, schema, table, limit, offset) =>
      ipcRenderer.invoke('db:tableData', id, schema, table, limit, offset)
  }
}

contextBridge.exposeInMainWorld('sparksdb', api)
