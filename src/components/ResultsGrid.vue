<template>
  <div class="flex h-full flex-col bg-neutral-900">
    <div
      v-if="result?.error"
      class="flex items-center gap-1.5 border-b border-red-900/50 bg-red-950/40 px-3 py-2 text-xs text-red-400"
    >
      <AlertCircle :size="13" class="shrink-0" />
      {{ result.error }}
    </div>
    <div class="min-h-0 flex-1 overflow-auto">
      <div v-if="loading && !result" class="flex h-full items-center justify-center text-neutral-500">
        <Loader2 :size="18" class="animate-spin" />
      </div>
      <table v-else-if="result && result.rows.length" class="w-full border-collapse text-xs">
        <thead class="sticky top-0 bg-neutral-800">
          <tr>
            <th
              v-for="field in result.fields"
              :key="field.name"
              class="border-b border-r border-neutral-700 px-2 py-1 text-left font-semibold text-neutral-300"
            >
              {{ field.name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in result.rows" :key="i" class="odd:bg-neutral-900 even:bg-neutral-800/40">
            <td
              v-for="field in result.fields"
              :key="field.name"
              class="border-b border-r border-neutral-800 px-2 py-1 align-top text-neutral-300"
            >
              {{ formatValue(row[field.name]) }}
            </td>
          </tr>
        </tbody>
      </table>
      <div
        v-else-if="result && !result.error"
        class="flex h-full items-center justify-center text-neutral-600"
      >
        Sem linhas retornadas
      </div>
    </div>
    <div
      v-if="result && !result.error"
      class="border-t border-neutral-800 px-3 py-1 text-xs text-neutral-500"
    >
      {{ result.rowCount }} linha(s)
      <span v-if="result.durationMs !== undefined"> · {{ result.durationMs }}ms</span>
    </div>
  </div>
</template>

<script setup>
import { AlertCircle, Loader2 } from '@lucide/vue'

defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

function formatValue(value) {
  if (value === null || value === undefined) return 'NULL'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
</script>
