<template>
  <div class="min-h-0 flex-1 overflow-y-auto p-2">
    <div class="mb-1 px-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">Schemas</div>
    <ul>
      <li v-for="schema in schemas" :key="schema">
        <button
          class="flex w-full items-center gap-1.5 rounded px-1 py-0.5 text-left text-neutral-300 hover:bg-neutral-800"
          @click="toggleSchema(schema)"
        >
          <ChevronDown v-if="expanded[schema]" :size="13" class="shrink-0 text-neutral-500" />
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
import { ChevronDown, ChevronRight, Eye, FolderTree, Table2 } from '@lucide/vue'
import { useTabsStore } from '../stores/tabs'

const props = defineProps({ connId: { type: String, required: true } })
const tabs = useTabsStore()

const schemas = ref([])
const expanded = reactive({})
const tables = reactive({})

async function load() {
  schemas.value = await window.sparksdb.db.schemas(props.connId)
}

async function toggleSchema(schema) {
  expanded[schema] = !expanded[schema]
  if (expanded[schema] && !tables[schema]) {
    tables[schema] = await window.sparksdb.db.tables(props.connId, schema)
  }
}

watch(() => props.connId, load, { immediate: true })
</script>
