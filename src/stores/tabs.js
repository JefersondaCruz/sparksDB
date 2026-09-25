import { defineStore } from 'pinia'

let nextId = 1

export const useTabsStore = defineStore('tabs', {
  state: () => ({
    tabs: [],
    activeTabId: null
  }),
  getters: {
    activeTab: (state) => state.tabs.find((t) => t.id === state.activeTabId) || null
  },
  actions: {
    openQueryTab(connId, sql = '', savedQueryId = null, title = null) {
      if (savedQueryId) {
        const existing = this.tabs.find((t) => t.type === 'query' && t.savedQueryId === savedQueryId)
        if (existing) {
          this.activeTabId = existing.id
          return existing.id
        }
      }
      const tab = {
        id: nextId++,
        type: 'query',
        connId,
        title: title || `Query ${nextId - 1}`,
        sql,
        savedQueryId,
        savedQuerySql: savedQueryId ? sql : null,
        result: null,
        loading: false
      }
      this.tabs.push(tab)
      this.activeTabId = tab.id
      return tab.id
    },
    openTableTab(connId, schema, table) {
      const existing = this.tabs.find(
        (t) => t.type === 'table' && t.connId === connId && t.schema === schema && t.table === table
      )
      if (existing) {
        this.activeTabId = existing.id
        return existing.id
      }
      const tab = {
        id: nextId++,
        type: 'table',
        connId,
        schema,
        table,
        title: `${schema}.${table}`,
        page: 0,
        pageSize: 100,
        columns: [],
        result: null,
        loading: false
      }
      this.tabs.push(tab)
      this.activeTabId = tab.id
      this.loadTableData(tab.id)
      return tab.id
    },
    closeTab(id) {
      const idx = this.tabs.findIndex((t) => t.id === id)
      if (idx === -1) return
      this.tabs.splice(idx, 1)
      if (this.activeTabId === id) {
        this.activeTabId = this.tabs.length ? this.tabs[Math.max(0, idx - 1)].id : null
      }
    },
    closeAllTabs() {
      this.tabs = []
      this.activeTabId = null
    },
    setSql(id, sql) {
      const tab = this.tabs.find((t) => t.id === id)
      if (tab) tab.sql = sql
    },
    markSaved(id, savedQueryId, sql, title) {
      const tab = this.tabs.find((t) => t.id === id)
      if (!tab) return
      tab.savedQueryId = savedQueryId
      tab.savedQuerySql = sql
      if (title) tab.title = title
    },
    unlinkSavedQuery(savedQueryId) {
      for (const tab of this.tabs) {
        if (tab.type === 'query' && tab.savedQueryId === savedQueryId) {
          tab.savedQueryId = null
          tab.savedQuerySql = null
          tab.title = `Query ${tab.id}`
        }
      }
    },
    async runQuery(id, sql) {
      const tab = this.tabs.find((t) => t.id === id)
      if (!tab || tab.type !== 'query') return
      tab.loading = true
      try {
        tab.result = await window.sparksdb.db.query(tab.connId, sql ?? tab.sql)
      } finally {
        tab.loading = false
      }
    },
    async loadTableData(id, page = 0) {
      const tab = this.tabs.find((t) => t.id === id)
      if (!tab || tab.type !== 'table') return
      tab.loading = true
      tab.page = page
      try {
        const data = await window.sparksdb.db.tableData(
          tab.connId,
          tab.schema,
          tab.table,
          tab.pageSize,
          page * tab.pageSize
        )
        tab.result = data
      } finally {
        tab.loading = false
      }
    }
  }
})
