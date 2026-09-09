<template>
  <div class="flex h-full min-h-0 flex-col">
    <div class="flex items-center gap-1 border-b border-neutral-800 bg-neutral-950 px-2 py-1">
      <button
        class="rounded px-2 py-1 text-xs"
        :class="subTab === 'data' ? 'bg-neutral-800 font-medium text-neutral-100' : 'text-neutral-400 hover:bg-neutral-800/60'"
        @click="subTab = 'data'"
      >
        Dados
      </button>
      <button
        class="rounded px-2 py-1 text-xs"
        :class="subTab === 'structure' ? 'bg-neutral-800 font-medium text-neutral-100' : 'text-neutral-400 hover:bg-neutral-800/60'"
        @click="loadColumns"
      >
        Estrutura
      </button>

      <div v-if="subTab === 'data'" class="ml-auto flex items-center gap-2 text-xs text-neutral-500">
        <button
          class="rounded border border-neutral-700 p-0.5 disabled:opacity-30"
          :disabled="tab.page === 0"
          @click="tabs.loadTableData(tab.id, tab.page - 1)"
        >
          <ChevronLeft :size="13" />
        </button>
        <span>página {{ tab.page + 1 }} · {{ tab.result?.totalCount ?? '...' }} linhas</span>
        <button
          class="rounded border border-neutral-700 p-0.5 disabled:opacity-30"
          :disabled="!hasNextPage"
          @click="tabs.loadTableData(tab.id, tab.page + 1)"
        >
          <ChevronRight :size="13" />
        </button>
      </div>
    </div>

    <div class="min-h-0 flex-1">
      <ResultsGrid v-if="subTab === 'data'" :result="dataResult" />
      <div v-else class="h-full overflow-auto bg-neutral-900">
        <table class="w-full border-collapse text-xs">
          <thead class="sticky top-0 bg-neutral-800">
            <tr>
              <th class="border-b border-r border-neutral-700 px-2 py-1 text-left text-neutral-300">coluna</th>
              <th class="border-b border-r border-neutral-700 px-2 py-1 text-left text-neutral-300">tipo</th>
              <th class="border-b border-r border-neutral-700 px-2 py-1 text-left text-neutral-300">nullable</th>
              <th class="border-b border-neutral-700 px-2 py-1 text-left text-neutral-300">default</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="col in columns" :key="col.name" class="odd:bg-neutral-900 even:bg-neutral-800/40">
              <td class="border-b border-r border-neutral-800 px-2 py-1 text-neutral-300">{{ col.name }}</td>
              <td class="border-b border-r border-neutral-800 px-2 py-1 text-neutral-300">{{ col.type }}</td>
              <td class="border-b border-r border-neutral-800 px-2 py-1 text-neutral-300">{{ col.nullable ? 'sim' : 'não' }}</td>
              <td class="border-b border-neutral-800 px-2 py-1 text-neutral-300">{{ col.default ?? '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { useTabsStore } from '../stores/tabs'
import ResultsGrid from './ResultsGrid.vue'

const props = defineProps({ tab: { type: Object, required: true } })
const tabs = useTabsStore()

const subTab = ref('data')
const columns = ref([])

const dataResult = computed(() => {
  const r = props.tab.result
  if (!r) return null
  return { rows: r.rows, fields: r.fields, rowCount: r.rows.length, error: r.error }
})

const hasNextPage = computed(() => {
  const r = props.tab.result
  if (!r) return false
  return (props.tab.page + 1) * props.tab.pageSize < r.totalCount
})

async function loadColumns() {
  subTab.value = 'structure'
  columns.value = await window.sparksdb.db.columns(props.tab.connId, props.tab.schema, props.tab.table)
}
</script>
