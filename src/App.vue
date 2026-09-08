<template>
  <div class="flex h-full w-full bg-neutral-900 text-sm text-neutral-200">
    <aside class="flex w-72 shrink-0 flex-col border-r border-neutral-800 bg-neutral-950">
      <div class="flex items-center gap-2 border-b border-neutral-800 px-3 py-2.5">
        <DatabaseZap :size="16" class="text-blue-500" />
        <span class="font-semibold text-neutral-100">sparksDB</span>
      </div>
      <ConnectionManager />
      <SchemaTree
        v-if="connections.activeConnectionId"
        :conn-id="connections.activeConnectionId"
      />
    </aside>

    <main class="flex min-w-0 flex-1 flex-col">
      <div class="flex items-center gap-1 border-b border-neutral-800 bg-neutral-950 px-2 py-1">
        <button
          v-for="tab in tabs.tabs"
          :key="tab.id"
          class="flex items-center gap-2 rounded px-3 py-1.5 text-xs"
          :class="
            tab.id === tabs.activeTabId
              ? 'bg-neutral-800 font-medium text-neutral-100'
              : 'text-neutral-400 hover:bg-neutral-800/60'
          "
          @click="tabs.activeTabId = tab.id"
        >
          <TerminalSquare v-if="tab.type === 'query'" :size="13" />
          <Table2 v-else :size="13" />
          {{ tab.title }}
          <X :size="13" class="text-neutral-500 hover:text-neutral-200" @click.stop="tabs.closeTab(tab.id)" />
        </button>
        <button
          v-if="connections.activeConnectionId"
          class="ml-1 flex items-center gap-1 rounded px-2 py-1 text-xs text-blue-400 hover:bg-blue-500/10"
          @click="tabs.openQueryTab(connections.activeConnectionId)"
        >
          <Plus :size="13" /> Query
        </button>
      </div>

      <div class="min-h-0 flex-1 bg-neutral-900">
        <template v-if="tabs.activeTab">
          <QueryTab v-if="tabs.activeTab.type === 'query'" :tab="tabs.activeTab" />
          <TableDataView v-else :tab="tabs.activeTab" />
        </template>
        <div v-else class="flex h-full items-center justify-center text-neutral-600">
          Conecte a um banco e abra uma query ou tabela
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { DatabaseZap, Plus, Table2, TerminalSquare, X } from '@lucide/vue'
import ConnectionManager from './components/ConnectionManager.vue'
import SchemaTree from './components/SchemaTree.vue'
import QueryTab from './components/QueryTab.vue'
import TableDataView from './components/TableDataView.vue'
import { useConnectionsStore } from './stores/connections'
import { useTabsStore } from './stores/tabs'

const connections = useConnectionsStore()
const tabs = useTabsStore()

onMounted(() => connections.fetchList())
</script>
