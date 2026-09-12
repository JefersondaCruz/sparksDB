<template>
  <div class="min-h-0 flex-1 overflow-y-auto p-2">
    <div class="mb-1 flex items-center justify-between px-1">
      <span class="text-xs font-semibold uppercase tracking-wide text-neutral-500">Schemas</span>
      <button
        class="rounded p-0.5 text-neutral-500 hover:bg-neutral-800 hover:text-neutral-300 disabled:opacity-40"
        title="Atualizar schemas"
        :disabled="refreshing"
        @click="refresh"
      >
        <RefreshCw :size="13" :class="{ 'animate-spin': refreshing }" />
      </button>
    </div>
    <div v-if="loadingSchemas" class="flex items-center justify-center py-4 text-neutral-500">
      <Loader2 :size="16" class="animate-spin" />
    </div>
    <ul v-else>
      <li v-for="schema in schemas" :key="schema">
        <button
          class="flex w-full items-center gap-1.5 rounded px-1 py-0.5 text-left text-neutral-300 hover:bg-neutral-800"
          @click="toggleSchema(schema)"
        >
          <Loader2 v-if="loadingTables[schema]" :size="13" class="shrink-0 animate-spin text-neutral-500" />
          <ChevronDown v-else-if="expanded[schema]" :size="13" class="shrink-0 text-neutral-500" />
          <ChevronRight v-else :size="13" class="shrink-0 text-neutral-500" />
          <FolderTree :size="13" class="shrink-0 text-neutral-500" />
          {{ schema }}
        </button>
        <ul v-if="expanded[schema]" class="ml-4">
          <li v-for="table in tables[schema] || []" :key="table.name">
            <button
              class="flex w-full items-center gap-1.5 truncate rounded px-1 py-0.5 text-left text-neutral-300 hover:bg-blue-500/10 hover:text-blue-300"
              @click="tabs.openTableTab(connId, schema, table.name)"
            >
              <Eye v-if="table.type === 'VIEW'" :size="13" class="shrink-0 text-neutral-500" />
              <Table2 v-else :size="13" class="shrink-0 text-neutral-500" />
              <span class="truncate">{{ table.name }}</span>
            </button>
          </li>
          <li v-if="tables[schema] && !tables[schema].length" class="px-1 py-0.5 text-xs text-neutral-600">
            (vazio)
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { ChevronDown, ChevronRight, Eye, FolderTree, Loader2, RefreshCw, Table2 } from '@lucide/vue'
import { useTabsStore } from '../stores/tabs'

const props = defineProps({ connId: { type: String, required: true } })
const tabs = useTabsStore()

const schemas = ref([])
const expanded = reactive({})
const tables = reactive({})
const refreshing = ref(false)
const loadingTables = reactive({})
const loadingSchemas = ref(false)

async function load() {
  loadingSchemas.value = true
  try {
    schemas.value = await window.sparksdb.db.schemas(props.connId)
  } finally {
    loadingSchemas.value = false
  }
}

async function toggleSchema(schema) {
  expanded[schema] = !expanded[schema]
  if (expanded[schema] && !tables[schema]) {
    loadingTables[schema] = true
    try {
      tables[schema] = await window.sparksdb.db.tables(props.connId, schema)
    } finally {
      loadingTables[schema] = false
    }
  }
}

async function refresh() {
  refreshing.value = true
  try {
    await load()
    const expandedSchemas = Object.keys(expanded).filter((schema) => expanded[schema])
    await Promise.all(
      expandedSchemas.map(async (schema) => {
        tables[schema] = await window.sparksdb.db.tables(props.connId, schema)
      })
    )
  } finally {
    refreshing.value = false
  }
}

watch(() => props.connId, load, { immediate: true })
</script>
