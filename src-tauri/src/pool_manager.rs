use deadpool_postgres::{Config as PoolConfig, Pool, PoolError, Runtime};
use serde::Serialize;
use std::time::Instant;
use tokio_postgres::NoTls;

use crate::store::ConnectionProfile;

#[derive(Serialize)]
pub struct FieldInfo {
    pub name: String,
}

#[derive(Serialize)]
pub struct QueryResult {
    pub rows: Vec<serde_json::Map<String, serde_json::Value>>,
    pub fields: Vec<FieldInfo>,
    #[serde(rename = "rowCount")]
    pub row_count: i64,
    #[serde(rename = "durationMs")]
    pub duration_ms: u128,
    pub error: Option<String>,
}

fn build_pool(profile: &ConnectionProfile, password: &str) -> Result<Pool, String> {
    if profile.ssl {
        return Err("Conexao com SSL ainda nao e suportada nesta versao do sparksDB.".to_string());
    }

    let mut cfg = PoolConfig::new();
    cfg.host = Some(profile.host.clone());
    cfg.port = Some(profile.port);
    cfg.dbname = Some(profile.database.clone());
    cfg.user = Some(profile.user.clone());
    cfg.password = Some(password.to_string());
    cfg.create_pool(Some(Runtime::Tokio1), NoTls)
        .map_err(|e| e.to_string())
}

pub async fn test_connection(profile: &ConnectionProfile, password: &str) -> Result<(), String> {
    open_pool(profile, password).await.map(|_| ())
}

pub async fn open_pool(profile: &ConnectionProfile, password: &str) -> Result<Pool, String> {
    let pool = build_pool(profile, password)?;
    let client = pool.get().await.map_err(describe_pool_error)?;
    client
        .query("SELECT 1", &[])
        .await
        .map_err(|e| describe_error(&e))?;
    Ok(pool)
}

pub fn describe_error(e: &tokio_postgres::Error) -> String {
    e.as_db_error()
        .map(|db_err| db_err.message().to_string())
        .unwrap_or_else(|| e.to_string())
}

pub fn describe_pool_error(e: PoolError) -> String {
    match &e {
        PoolError::Backend(db_err) => describe_error(db_err),
        other => other.to_string(),
    }
}

pub async fn run_query(pool: &Pool, sql: &str) -> QueryResult {
    let start = Instant::now();
    let client = match pool.get().await {
        Ok(c) => c,
        Err(e) => {
            return QueryResult {
                rows: vec![],
                fields: vec![],
                row_count: 0,
                duration_ms: start.elapsed().as_millis(),
                error: Some(describe_pool_error(e)),
            }
        }
    };
    match client.simple_query(sql).await {
        Ok(messages) => {
            let mut rows_json = Vec::new();
            let mut fields = Vec::new();
            let mut row_count: i64 = 0;
            for message in &messages {
                match message {
                    tokio_postgres::SimpleQueryMessage::RowDescription(columns) => {
                        fields = columns
                            .iter()
                            .map(|c| FieldInfo { name: c.name().to_string() })
                            .collect();
                        rows_json.clear();
                        row_count = 0;
                    }
                    tokio_postgres::SimpleQueryMessage::Row(row) => {
                        if fields.is_empty() {
                            fields = row
                                .columns()
                                .iter()
                                .map(|c| FieldInfo { name: c.name().to_string() })
                                .collect();
                        }
                        let mut map = serde_json::Map::new();
                        for (i, column) in row.columns().iter().enumerate() {
                            let value = row
                                .try_get(i)
                                .ok()
                                .flatten()
                                .map(|v| serde_json::json!(v))
                                .unwrap_or(serde_json::Value::Null);
                            map.insert(column.name().to_string(), value);
                        }
                        rows_json.push(map);
                        row_count += 1;
                    }
                    tokio_postgres::SimpleQueryMessage::CommandComplete(n) => {
                        row_count = *n as i64;
                    }
                    _ => {}
                }
            }
            QueryResult {
                rows: rows_json,
                fields,
                row_count,
                duration_ms: start.elapsed().as_millis(),
                error: None,
            }
        }
        Err(e) => QueryResult {
            rows: vec![],
            fields: vec![],
            row_count: 0,
            duration_ms: start.elapsed().as_millis(),
            error: Some(describe_error(&e)),
        },
    }
}

pub fn get_pool(state: &crate::state::AppState, id: &str) -> Result<Pool, String> {
    state
        .pools
        .lock()
        .unwrap()
        .get(id)
        .cloned()
        .ok_or_else(|| "Conexao nao esta ativa. Conecte antes de rodar queries.".to_string())
}
