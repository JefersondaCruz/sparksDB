<template>
  <div class="max-h-56 shrink-0 overflow-y-auto border-t border-neutral-800 p-2">
    <div class="mb-1 flex items-center justify-between px-1">
      <span class="text-xs font-semibold uppercase tracking-wide text-neutral-500">Queries salvas</span>
    </div>
    <ul class="space-y-0.5">
      <li
        v-for="q in savedQueries.forConn(connId)"
        :key="q.id"
        class="group flex items-center justify-between rounded px-1.5 py-1 hover:bg-neutral-800"
      >
        <button
          class="flex flex-1 items-center gap-1.5 truncate text-left text-neutral-300"
          :title="q.sql"
          @click="open(q)"
        >
          <FileCode :size="13" class="shrink-0 text-neutral-500" />
          <span class="truncate">{{ q.name }}</span>
        </button>
        <button
          class="px-1 text-neutral-600 opacity-0 hover:text-red-400 group-hover:opacity-100"
          title="remover"
          @click="remove(q.id)"
        >
          <Trash2 :size="13" />
        </button>
      </li>
      <li v-if="!savedQueries.forConn(connId).length" class="px-1.5 py-1 text-xs text-neutral-600">
        Nenhuma query salva
      </li>
    </ul>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { FileCode, Trash2 } from '@lucide/vue'
import { useSavedQueriesStore } from '../stores/savedQueries'
import { useTabsStore } from '../stores/tabs'

const props = defineProps({ connId: { type: String, required: true } })
const savedQueries = useSavedQueriesStore()
const tabs = useTabsStore()

function open(q) {
  tabs.openQueryTab(q.connId, q.sql, q.id, q.name)
}

async function remove(id) {
  try {
    await savedQueries.remove(id)
    tabs.unlinkSavedQuery(id)
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => savedQueries.fetchList())
</script>
