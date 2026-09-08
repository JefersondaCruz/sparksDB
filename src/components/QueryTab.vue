<template>
  <div class="flex h-full min-h-0 flex-col">
    <div class="flex items-center gap-2 border-b border-neutral-800 bg-neutral-950 px-2 py-1.5">
      <button
        class="flex items-center gap-1.5 rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-40"
        :disabled="tab.loading || !tab.sql.trim()"
        @click="run"
      >
        <Loader2 v-if="tab.loading" :size="13" class="animate-spin" />
        <Play v-else :size="13" />
        {{ tab.loading ? 'Executando...' : 'Run' }}
      </button>
      <span class="text-xs text-neutral-600">Ctrl+Enter</span>
    </div>

    <div class="min-h-0 flex-[2] border-b border-neutral-800">
      <VueMonacoEditor
        :value="tab.sql"
        language="pgsql"
        theme="vs-dark"
        height="100%"
        :options="{ minimap: { enabled: false }, fontSize: 13, automaticLayout: true }"
        @change="(v) => tabs.setSql(tab.id, v)"
        @mount="onMount"
      />
    </div>

    <div class="min-h-0 flex-[1]">
      <ResultsGrid :result="tab.result" />
    </div>
  </div>
</template>

<script setup>
import * as monaco from 'monaco-editor'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { Loader2, Play } from '@lucide/vue'
import { useTabsStore } from '../stores/tabs'
import ResultsGrid from './ResultsGrid.vue'

const props = defineProps({ tab: { type: Object, required: true } })
const tabs = useTabsStore()

function run() {
  tabs.runQuery(props.tab.id)
}

function onMount(editor) {
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run)
}
</script>
