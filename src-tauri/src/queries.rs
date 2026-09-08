use deadpool_postgres::Pool;
use serde::Serialize;

use crate::pool_manager::{describe_error, describe_pool_error};

#[derive(Serialize)]
pub struct TableInfo {
    pub name: String,
    #[serde(rename = "type")]
    pub table_type: String,
}

#[derive(Serialize)]
pub struct ColumnInfo {
    pub name: String,
    #[serde(rename = "type")]
    pub data_type: String,
    pub nullable: bool,
    pub default: Option<String>,
}

#[derive(Serialize)]
pub struct TableDataResult {
    pub rows: Vec<serde_json::Map<String, serde_json::Value>>,
    pub fields: Vec<crate::pool_manager::FieldInfo>,
    #[serde(rename = "totalCount")]
    pub total_count: i64,
}

fn quote_ident(name: &str) -> String {
    format!("\"{}\"", name.replace('"', "\"\""))
}

pub async fn list_schemas(pool: &Pool) -> Result<Vec<String>, String> {
    let client = pool.get().await.map_err(describe_pool_error)?;
    let rows = client
        .query(
            "SELECT schema_name FROM information_schema.schemata \
             WHERE schema_name NOT IN ('pg_catalog', 'information_schema') \
             AND schema_name NOT LIKE 'pg_toast%' \
             AND schema_name NOT LIKE 'pg_temp%' \
             ORDER BY schema_name",
            &[],
        )
        .await
        .map_err(|e| describe_error(&e))?;
    Ok(rows.iter().map(|r| r.get::<_, String>(0)).collect())
}

pub async fn list_tables(pool: &Pool, schema: &str) -> Result<Vec<TableInfo>, String> {
    let client = pool.get().await.map_err(describe_pool_error)?;
    let rows = client
        .query(
            "SELECT table_name, table_type FROM information_schema.tables \
             WHERE table_schema = $1 ORDER BY table_name",
            &[&schema],
        )
        .await
        .map_err(|e| describe_error(&e))?;
    Ok(rows
        .iter()
        .map(|r| TableInfo {
            name: r.get(0),
            table_type: r.get(1),
        })
        .collect())
}

pub async fn list_columns(pool: &Pool, schema: &str, table: &str) -> Result<Vec<ColumnInfo>, String> {
    let client = pool.get().await.map_err(describe_pool_error)?;
    let rows = client
        .query(
            "SELECT column_name, data_type, is_nullable, column_default \
             FROM information_schema.columns \
             WHERE table_schema = $1 AND table_name = $2 \
             ORDER BY ordinal_position",
            &[&schema, &table],
        )
        .await
        .map_err(|e| describe_error(&e))?;
    Ok(rows
        .iter()
        .map(|r| {
            let is_nullable: String = r.get(2);
            ColumnInfo {
                name: r.get(0),
                data_type: r.get(1),
                nullable: is_nullable == "YES",
                default: r.get(3),
            }
        })
        .collect())
}

pub async fn get_table_data(
    pool: &Pool,
    schema: &str,
    table: &str,
    limit: i64,
    offset: i64,
) -> Result<TableDataResult, String> {
    let client = pool.get().await.map_err(describe_pool_error)?;
    let ident = format!("{}.{}", quote_ident(schema), quote_ident(table));

    let select_sql = format!("SELECT * FROM {} LIMIT $1 OFFSET $2", ident);
    let statement = client
        .prepare(&select_sql)
        .await
        .map_err(|e| describe_error(&e))?;
    let fields = statement
        .columns()
        .iter()
        .map(|c| crate::pool_manager::FieldInfo { name: c.name().to_string() })
        .collect();

    let json_sql = format!("SELECT to_jsonb(t)::text AS row_json FROM ({}) t", select_sql);
    let data_rows = client
        .query(&json_sql, &[&limit, &offset])
        .await
        .map_err(|e| describe_error(&e))?;

    let count_sql = format!("SELECT count(*)::bigint AS count FROM {}", ident);
    let count_row = client
        .query_one(&count_sql, &[])
        .await
        .map_err(|e| describe_error(&e))?;
    let total_count: i64 = count_row.get(0);

    let rows = data_rows
        .iter()
        .map(|row| {
            let raw: String = row.get(0);
            match serde_json::from_str::<serde_json::Value>(&raw) {
                Ok(serde_json::Value::Object(map)) => map,
                _ => serde_json::Map::new(),
            }
        })
        .collect();

    Ok(TableDataResult {
        rows,
        fields,
        total_count,
    })
}
