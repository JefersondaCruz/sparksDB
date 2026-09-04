import { getPool } from './pool-manager'

function quoteIdent(name) {
  return `"${String(name).replace(/"/g, '""')}"`
}

export async function listSchemas(connId) {
  const pool = getPool(connId)
  const { rows } = await pool.query(`
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
      AND schema_name NOT LIKE 'pg_toast%'
      AND schema_name NOT LIKE 'pg_temp%'
    ORDER BY schema_name
  `)
  return rows.map((r) => r.schema_name)
}

export async function listTables(connId, schema) {
  const pool = getPool(connId)
  const { rows } = await pool.query(
    `
    SELECT table_name, table_type
    FROM information_schema.tables
    WHERE table_schema = $1
    ORDER BY table_name
  `,
    [schema]
  )
  return rows.map((r) => ({ name: r.table_name, type: r.table_type }))
}

export async function listColumns(connId, schema, table) {
  const pool = getPool(connId)
  const { rows } = await pool.query(
    `
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position
  `,
    [schema, table]
  )
  return rows.map((r) => ({
    name: r.column_name,
    type: r.data_type,
    nullable: r.is_nullable === 'YES',
    default: r.column_default
  }))
}

export async function getTableData(connId, schema, table, limit = 100, offset = 0) {
  const pool = getPool(connId)
  const ident = `${quoteIdent(schema)}.${quoteIdent(table)}`
  const [dataResult, countResult] = await Promise.all([
    pool.query(`SELECT * FROM ${ident} LIMIT $1 OFFSET $2`, [limit, offset]),
    pool.query(`SELECT count(*)::bigint AS count FROM ${ident}`)
  ])
  return {
    rows: dataResult.rows,
    fields: dataResult.fields.map((f) => ({ name: f.name })),
    totalCount: Number(countResult.rows[0].count)
  }
}
