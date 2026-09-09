<template>
  <div class="border-b border-neutral-800 p-2">
    <div class="mb-1 flex items-center justify-between px-1">
      <span class="text-xs font-semibold uppercase tracking-wide text-neutral-500">Conexões</span>
      <button
        class="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-blue-400 hover:bg-blue-500/10"
        @click="showForm = !showForm"
      >
        <X v-if="showForm" :size="12" />
        <Plus v-else :size="12" />
        {{ showForm ? 'cancelar' : 'nova' }}
      </button>
    </div>

    <ul class="mb-2 space-y-0.5">
      <li
        v-for="c in connections.list"
        :key="c.id"
        class="group flex items-center justify-between rounded px-1.5 py-1"
        :class="connections.activeConnectionId === c.id ? 'bg-blue-500/10' : 'hover:bg-neutral-800'"
      >
        <button class="flex flex-1 items-center gap-2 truncate text-left" @click="toggleConnect(c)">
          <Loader2
            v-if="connections.status[c.id] === 'connecting'"
            :size="12"
            class="shrink-0 animate-spin text-yellow-500"
          />
          <span
            v-else
            class="h-2 w-2 shrink-0 rounded-full"
            :class="connections.status[c.id] === 'connected' ? 'bg-green-500' : 'bg-neutral-600'"
          />
          <span class="truncate text-neutral-200">{{ c.name }}</span>
        </button>
        <button
          class="px-1 text-neutral-600 opacity-0 hover:text-red-400 group-hover:opacity-100"
          title="remover"
          @click="connections.remove(c.id)"
        >
          <Trash2 :size="13" />
        </button>
      </li>
      <li v-if="!connections.list.length" class="px-1.5 py-1 text-xs text-neutral-600">
        Nenhuma conexão salva
      </li>
    </ul>

    <p v-if="connections.connectError" class="mb-2 flex items-start gap-1 px-1.5 text-xs text-red-400">
      <AlertCircle :size="13" class="mt-0.5 shrink-0" />
      <span>{{ connections.connectError }}</span>
    </p>

    <form v-if="showForm" class="space-y-1.5 rounded border border-neutral-800 bg-neutral-900 p-2" @submit.prevent="save">
      <input v-model="form.name" placeholder="Nome" class="input" required />
      <div class="flex gap-1.5">
        <input v-model="form.host" placeholder="Host" class="input flex-1" required />
        <input v-model.number="form.port" placeholder="Porta" class="input w-20" required />
      </div>
      <input v-model="form.database" placeholder="Database" class="input" required />
      <input v-model="form.user" placeholder="Usuário" class="input" required />
      <input v-model="form.password" type="password" placeholder="Senha" class="input" />
      <label class="flex items-center gap-1.5 text-xs text-neutral-400">
        <input v-model="form.ssl" type="checkbox" /> SSL
      </label>

      <p v-if="testMessage" class="flex items-center gap-1 text-xs" :class="testOk ? 'text-green-500' : 'text-red-400'">
        <CheckCircle2 v-if="testOk" :size="13" />
        <AlertCircle v-else :size="13" />
        {{ testMessage }}
      </p>

      <div class="flex gap-1.5 pt-1">
        <button type="button" class="btn-secondary" @click="test">Testar</button>
        <button type="submit" class="btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { AlertCircle, CheckCircle2, Loader2, Plus, Trash2, X } from '@lucide/vue'
import { errorText, useConnectionsStore } from '../stores/connections'

const connections = useConnectionsStore()
const showForm = ref(false)
const testMessage = ref('')
const testOk = ref(false)

const form = reactive({
  name: '',
  host: 'localhost',
  port: 5432,
  database: '',
  user: '',
  password: '',
  ssl: false
})

async function test() {
  testMessage.value = 'Testando...'
  try {
    await connections.test({ ...form })
    testOk.value = true
    testMessage.value = 'Conexão OK'
  } catch (error) {
    testOk.value = false
    testMessage.value = `Falhou: ${errorText(error)}`
  }
}

async function save() {
  await connections.save({ ...form })
  showForm.value = false
  testMessage.value = ''
  Object.assign(form, {
    name: '',
    host: 'localhost',
    port: 5432,
    database: '',
    user: '',
    password: '',
    ssl: false
  })
}

async function toggleConnect(c) {
  if (connections.status[c.id] === 'connected') {
    await connections.disconnect(c.id)
  } else {
    await connections.connect(c.id)
  }
}
</script>

<style scoped>
.input {
  @apply w-full rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-neutral-100 placeholder-neutral-500 focus:border-blue-500 focus:outline-none;
}
.btn-primary {
  @apply rounded bg-blue-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-blue-500;
}
.btn-secondary {
  @apply rounded border border-neutral-700 px-2.5 py-1 text-xs text-neutral-200 hover:bg-neutral-800;
}
</style>
