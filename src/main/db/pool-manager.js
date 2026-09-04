import pg from 'pg'
import { getConnectionWithPassword } from './store'

const { Pool } = pg

/** @type {Map<string, import('pg').Pool>} */
const pools = new Map()

function buildPoolConfig(profile) {
  return {
    host: profile.host,
    port: profile.port,
    database: profile.database,
    user: profile.user,
    password: profile.password,
    ssl: profile.ssl ? { rejectUnauthorized: false } : false,
    max: 5
  }
}

export async function testConnection(profile) {
  const pool = new Pool(buildPoolConfig(profile))
  try {
    await pool.query('SELECT 1')
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  } finally {
    await pool.end()
  }
}

export async function connect(id) {
  if (pools.has(id)) return { ok: true }
  const profile = getConnectionWithPassword(id)
  if (!profile) return { ok: false, error: 'Conexao nao encontrada' }
  const pool = new Pool(buildPoolConfig(profile))
  try {
    await pool.query('SELECT 1')
    pools.set(id, pool)
    return { ok: true }
  } catch (err) {
    await pool.end()
    return { ok: false, error: err.message }
  }
}

export async function disconnect(id) {
  const pool = pools.get(id)
  if (!pool) return
  pools.delete(id)
  await pool.end()
}

export function getPool(id) {
  const pool = pools.get(id)
  if (!pool) throw new Error('Conexao nao esta ativa. Conecte antes de rodar queries.')
  return pool
}

export async function runQuery(id, sql) {
  const pool = getPool(id)
  const start = Date.now()
  try {
    const result = await pool.query(sql)
    const last = Array.isArray(result) ? result[result.length - 1] : result
    return {
      rows: last.rows,
      fields: last.fields?.map((f) => ({ name: f.name })) || [],
      rowCount: last.rowCount,
      durationMs: Date.now() - start,
      error: null
    }
  } catch (err) {
    return {
      rows: [],
      fields: [],
      rowCount: 0,
      durationMs: Date.now() - start,
      error: err.message
    }
  }
}
