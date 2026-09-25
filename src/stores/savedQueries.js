import { defineStore } from 'pinia'

export const useSavedQueriesStore = defineStore('savedQueries', {
  state: () => ({
    list: []
  }),
  getters: {
    forConn: (state) => (connId) =>
      state.list.filter((q) => q.connId === connId).sort((a, b) => a.name.localeCompare(b.name))
  },
  actions: {
    async fetchList() {
      this.list = await window.sparksdb.queries.list()
    },
    async save(input) {
      const saved = await window.sparksdb.queries.save(input)
      const idx = this.list.findIndex((q) => q.id === saved.id)
      if (idx === -1) this.list.push(saved)
      else this.list[idx] = saved
      return saved
    },
    async remove(id) {
      await window.sparksdb.queries.delete(id)
      this.list = this.list.filter((q) => q.id !== id)
    }
  }
})
