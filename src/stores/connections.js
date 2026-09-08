import { defineStore } from 'pinia'

export function errorText(error) {
  if (typeof error === 'string') return error
  if (error instanceof Error) return error.message
  if (error == null) return 'Erro desconhecido'
  return String(error)
}

export const useConnectionsStore = defineStore('connections', {
  state: () => ({
    list: [],
    status: {},
    activeConnectionId: null,
    connectError: null
  }),
  actions: {
    async fetchList() {
      this.list = await window.sparksdb.connections.list()
    },
    async save(profile) {
      const saved = await window.sparksdb.connections.save(profile)
      await this.fetchList()
      return saved
    },
    async remove(id) {
      await window.sparksdb.connections.delete(id)
      if (this.activeConnectionId === id) this.activeConnectionId = null
      await this.fetchList()
    },
    async test(profile) {
      return window.sparksdb.connections.test(profile)
    },
    async connect(id) {
      this.status = { ...this.status, [id]: 'connecting' }
      this.connectError = null
      try {
        await window.sparksdb.db.connect(id)
        this.status = { ...this.status, [id]: 'connected' }
        this.activeConnectionId = id
        return true
      } catch (error) {
        this.status = { ...this.status, [id]: 'disconnected' }
        this.connectError = errorText(error)
        if (this.activeConnectionId === id) this.activeConnectionId = null
        return false
      }
    },
    async disconnect(id) {
      await window.sparksdb.db.disconnect(id)
      this.status = { ...this.status, [id]: 'disconnected' }
      this.connectError = null
      if (this.activeConnectionId === id) this.activeConnectionId = null
    }
  }
})
