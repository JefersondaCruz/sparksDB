import { defineStore } from 'pinia'

export const useConnectionsStore = defineStore('connections', {
  state: () => ({
    list: [],
    status: {}, // id -> 'connected' | 'connecting' | 'disconnected'
    activeConnectionId: null
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
      const result = await window.sparksdb.db.connect(id)
      this.status = { ...this.status, [id]: result.ok ? 'connected' : 'disconnected' }
      if (result.ok) this.activeConnectionId = id
      return result
    },
    async disconnect(id) {
      await window.sparksdb.db.disconnect(id)
      this.status = { ...this.status, [id]: 'disconnected' }
      if (this.activeConnectionId === id) this.activeConnectionId = null
    }
  }
})
