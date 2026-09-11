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
import { Loader2, Play } from '@lucide/vue'
import { shallowRef, watch } from 'vue'
import { useTabsStore } from '../stores/tabs'
import { useConnectionsStore } from '../stores/connections'
import ResultsGrid from './ResultsGrid.vue'

const props = defineProps({ tab: { type: Object, required: true } })
const tabs = useTabsStore()
const editorRef = shallowRef(null)
const connections = useConnectionsStore()

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

watch(
  () => connections.status[props.tab.connId],
  (status) => {
    if (status === 'connecting') invalidateSchemaCache(props.tab.connId)
  }
)
</script>
