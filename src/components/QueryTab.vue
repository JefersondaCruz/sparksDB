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
      <button
        class="ml-auto flex items-center gap-1.5 rounded border px-2.5 py-1 text-xs disabled:opacity-40"
        :class="
          isDirty
            ? 'border-amber-600/60 text-amber-400 hover:bg-amber-500/10'
            : 'border-neutral-700 text-neutral-200 hover:bg-neutral-800'
        "
        :disabled="!tab.sql.trim()"
        @click="openSaveForm"
      >
        <Save :size="13" />
        {{ tab.savedQueryId ? (isDirty ? 'Atualizar query' : 'Query salva') : 'Salvar query' }}
      </button>
      <span v-if="tab.savedQueryId" class="text-xs text-neutral-600">Ctrl+S</span>
    </div>

    <form
      v-if="showSaveForm"
      class="flex items-center gap-1.5 border-b border-neutral-800 bg-neutral-900 px-2 py-1.5"
      @submit.prevent="submitSave"
    >
      <input
        v-model="saveName"
        placeholder="Nome da query"
        class="flex-1 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-neutral-100 placeholder-neutral-500 focus:border-blue-500 focus:outline-none"
        required
      />
      <button
        type="submit"
        class="rounded bg-blue-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-40"
        :disabled="saving"
      >
        {{ saving ? 'Salvando...' : tab.savedQueryId ? 'Atualizar' : 'Salvar' }}
      </button>
      <button
        v-if="tab.savedQueryId"
        type="button"
        class="rounded border border-neutral-700 px-2.5 py-1 text-xs text-neutral-200 hover:bg-neutral-800 disabled:opacity-40"
        :disabled="saving"
        @click="saveAsNew"
      >
        Salvar como nova
      </button>
      <button
        type="button"
        class="rounded border border-neutral-700 px-2.5 py-1 text-xs text-neutral-200 hover:bg-neutral-800"
        @click="closeSaveForm"
      >
        Cancelar
      </button>
    </form>
    <p v-if="saveError" class="border-b border-neutral-800 bg-neutral-900 px-2 py-1 text-xs text-red-400">
      {{ saveError }}
    </p>

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
      <ResultsGrid :result="tab.result" :loading="tab.loading" />
    </div>
  </div>
</template>

<script>
import * as monaco from 'monaco-editor'

const schemaCacheByConn = new Map()

async function buildSchemaCache(connId) {
  const schemas = await window.sparksdb.db.schemas(connId)
  const tables = {}
  const columns = {}
  await Promise.all(
    schemas.map(async (schema) => {
      const schemaTables = await window.sparksdb.db.tables(connId, schema)
      tables[schema] = schemaTables
      await Promise.all(
        schemaTables.map(async (t) => {
          columns[`${schema}.${t.name}`] = await window.sparksdb.db.columns(connId, schema, t.name)
        })
      )
    })
  )
  return { schemas, tables, columns }
}

function loadSchemaCache(connId) {
  if (!schemaCacheByConn.has(connId)) {
    schemaCacheByConn.set(connId, buildSchemaCache(connId))
  }
  return schemaCacheByConn.get(connId)
}

function invalidateSchemaCache(connId) {
  schemaCacheByConn.delete(connId)
}

const SQL_KEYWORDS = [
  'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'LIKE', 'ILIKE',
  'BETWEEN', 'EXISTS', 'DISTINCT', 'AS', 'ON', 'JOIN', 'INNER JOIN', 'LEFT JOIN',
  'RIGHT JOIN', 'FULL JOIN', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET',
  'UNION', 'UNION ALL', 'INSERT INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE FROM',
  'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE', 'PRIMARY KEY', 'FOREIGN KEY',
  'REFERENCES', 'DEFAULT', 'RETURNING', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
  'WITH', 'ASC', 'DESC'
]

const CLAUSE_START_REGEX = /\b(FROM|JOIN|UPDATE|INTO)\b/gi
const CLAUSE_END_REGEX = /\b(WHERE|GROUP|ORDER|HAVING|LIMIT|OFFSET|UNION|JOIN|ON|SET|VALUES|RETURNING)\b/i
const TABLE_REF_ITEM_REGEX =
  /^"?([a-zA-Z_][\w$]*)"?(?:\s*\.\s*"?([a-zA-Z_][\w$]*)"?)?(?:\s+(?:AS\s+)?"?([a-zA-Z_][\w$]*)"?)?/i
const ALIAS_BLACKLIST = new Set([
  'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'ON', 'SET', 'VALUES',
  'RETURNING', 'UNION', 'AND', 'OR', 'NOT', 'JOIN', 'INNER', 'LEFT', 'RIGHT',
  'FULL', 'CROSS', 'NATURAL', 'USING', 'AS', 'BY', 'ALL', 'WITH', 'SELECT',
  'FROM', 'INTO', 'UPDATE', 'DELETE', 'INSERT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
])

function parseStatementRefs(statementText) {
  const tables = new Set()
  const aliasMap = new Map()

  let match
  CLAUSE_START_REGEX.lastIndex = 0
  while ((match = CLAUSE_START_REGEX.exec(statementText))) {
    const keyword = match[1].toUpperCase()
    const afterKeyword = statementText.slice(match.index + match[0].length)
    const endMatch = CLAUSE_END_REGEX.exec(afterKeyword)
    const clauseText = endMatch ? afterKeyword.slice(0, endMatch.index) : afterKeyword
    const items = keyword === 'FROM' ? clauseText.split(',') : [clauseText]

    for (const item of items) {
      const itemMatch = item.trim().match(TABLE_REF_ITEM_REGEX)
      if (!itemMatch) continue
      const [, first, second, aliasCandidate] = itemMatch
      const table = (second || first).toLowerCase()
      tables.add(table)
      aliasMap.set(table, table)
      if (aliasCandidate && !ALIAS_BLACKLIST.has(aliasCandidate.toUpperCase())) {
        aliasMap.set(aliasCandidate.toLowerCase(), table)
      }
    }
  }

  return { tables, aliasMap }
}

let providerRegistered = false
const modelConnId = new WeakMap()

function ensureCompletionProvider() {
  if (providerRegistered) return
  providerRegistered = true

  monaco.languages.registerCompletionItemProvider('pgsql', {
    triggerCharacters: ['.', ' '],
    async provideCompletionItems(model, position) {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn
      }

      const lineUntilWord = model.getValueInRange({
        startLineNumber: position.lineNumber,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: word.startColumn
      })
      const qualifierMatch = lineUntilWord.match(/([a-zA-Z_][\w$]*)\.\s*$/)
      const qualifier = qualifierMatch ? qualifierMatch[1].toLowerCase() : null

      const connId = modelConnId.get(model)
      let cache = null
      if (connId) {
        try {
          cache = await loadSchemaCache(connId)
        } catch {}
      }

      if (cache) {
        const textUntilCursor = model.getValueInRange({
          startLineNumber: 1,
          startColumn: 1,
          endLineNumber: position.lineNumber,
          endColumn: position.column
        })
        const currentStatement = textUntilCursor.split(';').pop()
        const { tables: referencedTables, aliasMap } = parseStatementRefs(currentStatement)

        if (qualifier) {
          const resolvedTable = aliasMap.get(qualifier) ?? (referencedTables.has(qualifier) ? qualifier : null)
          const columnEntries = Object.entries(cache.columns)
          const matchingColumnEntries = resolvedTable
            ? columnEntries.filter(([key]) => key.split('.').pop().toLowerCase() === resolvedTable)
            : []
          const relevantColumnEntries = matchingColumnEntries.length ? matchingColumnEntries : columnEntries

          const suggestions = []
          for (const [key, tableColumns] of relevantColumnEntries) {
            for (const column of tableColumns) {
              suggestions.push({
                label: column.name,
                kind: monaco.languages.CompletionItemKind.Field,
                insertText: column.name,
                detail: `coluna · ${key}`,
                range
              })
            }
          }
          return { suggestions }
        }

        const suggestions = SQL_KEYWORDS.map((keyword) => ({
          label: keyword,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: keyword,
          range
        }))

        for (const [schema, schemaTables] of Object.entries(cache.tables)) {
          for (const table of schemaTables) {
            suggestions.push({
              label: table.name,
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: table.name,
              detail: `tabela · ${schema}`,
              range
            })
          }
        }

        const columnEntries = Object.entries(cache.columns)
        const matchingColumnEntries = columnEntries.filter(([key]) =>
          referencedTables.has(key.split('.').pop().toLowerCase())
        )
        const relevantColumnEntries = matchingColumnEntries.length ? matchingColumnEntries : columnEntries
        for (const [key, tableColumns] of relevantColumnEntries) {
          for (const column of tableColumns) {
            suggestions.push({
              label: column.name,
              kind: monaco.languages.CompletionItemKind.Field,
              insertText: column.name,
              detail: `coluna · ${key}`,
              range
            })
          }
        }

        return { suggestions }
      }

      if (qualifier) return { suggestions: [] }

      const suggestions = SQL_KEYWORDS.map((keyword) => ({
        label: keyword,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: keyword,
        range
      }))
      return { suggestions }
    }
  })
}
</script>

<script setup>
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { Loader2, Play, Save } from '@lucide/vue'
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { errorText, useConnectionsStore } from '../stores/connections'
import { useTabsStore } from '../stores/tabs'
import { useSavedQueriesStore } from '../stores/savedQueries'
import ResultsGrid from './ResultsGrid.vue'

const props = defineProps({ tab: { type: Object, required: true } })
const tabs = useTabsStore()
const editorRef = shallowRef(null)
const connections = useConnectionsStore()
const savedQueries = useSavedQueriesStore()
const showSaveForm = ref(false)
const saveName = ref('')
const saveError = ref('')
const saving = ref(false)
const isDirty = computed(() => Boolean(props.tab.savedQueryId) && props.tab.sql !== props.tab.savedQuerySql)

function openSaveForm() {
  if (showSaveForm.value) return
  const existing = props.tab.savedQueryId
    ? savedQueries.list.find((q) => q.id === props.tab.savedQueryId)
    : null
  saveName.value = existing?.name || ''
  showSaveForm.value = true
}

function closeSaveForm() {
  saveName.value = ''
  saveError.value = ''
  showSaveForm.value = false
}

async function persist(id) {
  if (saving.value) return
  if (!saveName.value.trim()) {
    saveError.value = 'Informe um nome para a query'
    return
  }
  saving.value = true
  saveError.value = ''
  try {
    const saved = await savedQueries.save({ id, connId: props.tab.connId, name: saveName.value, sql: props.tab.sql })
    tabs.markSaved(props.tab.id, saved.id, saved.sql, saved.name)
    closeSaveForm()
  } catch (error) {
    saveError.value = errorText(error)
  } finally {
    saving.value = false
  }
}

function saveAsNew() {
  persist(undefined)
}

function updateExisting() {
  persist(props.tab.savedQueryId)
}

function submitSave() {
  if (props.tab.savedQueryId) {
    updateExisting()
  } else {
    saveAsNew()
  }
}

function quickSave() {
  if (showSaveForm.value) {
    submitSave()
    return
  }
  if (!props.tab.sql.trim()) return
  if (!props.tab.savedQueryId) {
    openSaveForm()
    return
  }
  const existing = savedQueries.list.find((q) => q.id === props.tab.savedQueryId)
  saveName.value = existing?.name || props.tab.title
  updateExisting()
}

function run() {
  const editor = editorRef.value
  const selection = editor?.getSelection()
  const selectedSql = selection && !selection.isEmpty()
    ? editor.getModel().getValueInRange(selection)
    : null
  tabs.runQuery(props.tab.id, selectedSql?.trim() || undefined)
}

function onMount(editor) {
  editorRef.value = editor
  ensureCompletionProvider()
  modelConnId.set(editor.getModel(), props.tab.connId)
  loadSchemaCache(props.tab.connId)
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run)
}

function handleKeydown(event) {
  if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 's') return
  event.preventDefault()
  quickSave()
}

onMounted(() => window.addEventListener('keydown', handleKeydown, { capture: true }))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown, { capture: true }))

watch(
  () => connections.status[props.tab.connId],
  (status) => {
    if (status === 'connecting') invalidateSchemaCache(props.tab.connId)
  }
)
</script>
