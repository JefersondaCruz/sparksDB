import Store from 'electron-store'
import { safeStorage } from 'electron'
import { randomUUID } from 'crypto'

const store = new Store({ name: 'connections' })

function encryptPassword(password) {
  if (!password) return { encrypted: false, password: '' }
  if (safeStorage.isEncryptionAvailable()) {
    return { encrypted: true, password: safeStorage.encryptString(password).toString('base64') }
  }
  // Sem keyring do SO disponivel (ex: libsecret ausente) - guarda em texto puro como fallback.
  return { encrypted: false, password }
}

function decryptPassword(entry) {
  if (!entry.password) return ''
  if (entry.encrypted) {
    return safeStorage.decryptString(Buffer.from(entry.password, 'base64'))
  }
  return entry.password
}

export function listConnections() {
  const connections = store.get('connections', [])
  return connections.map(({ password, encrypted, ...rest }) => rest)
}

export function getConnectionWithPassword(id) {
  const connections = store.get('connections', [])
  const entry = connections.find((c) => c.id === id)
  if (!entry) return null
  return { ...entry, password: decryptPassword(entry) }
}

export function saveConnection(profile) {
  const connections = store.get('connections', [])
  const { encrypted, password } = encryptPassword(profile.password)
  const id = profile.id || randomUUID()
  const record = {
    id,
    name: profile.name,
    host: profile.host,
    port: profile.port || 5432,
    database: profile.database,
    user: profile.user,
    ssl: !!profile.ssl,
    encrypted,
    password
  }
  const idx = connections.findIndex((c) => c.id === id)
  if (idx >= 0) connections[idx] = record
  else connections.push(record)
  store.set('connections', connections)
  const { password: _pw, encrypted: _enc, ...safe } = record
  return safe
}

export function deleteConnection(id) {
  const connections = store.get('connections', [])
  store.set(
    'connections',
    connections.filter((c) => c.id !== id)
  )
}
