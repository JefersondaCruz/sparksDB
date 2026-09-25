use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};
use uuid::Uuid;

#[derive(Serialize, Deserialize, Clone)]
pub struct SavedQuery {
    pub id: String,
    #[serde(rename = "connId")]
    pub conn_id: String,
    pub name: String,
    pub sql: String,
}

#[derive(Deserialize)]
pub struct SaveQueryInput {
    pub id: Option<String>,
    #[serde(rename = "connId")]
    pub conn_id: String,
    pub name: String,
    pub sql: String,
}

fn saved_queries_file(app: &AppHandle) -> PathBuf {
    let dir = app
        .path()
        .app_config_dir()
        .expect("nao foi possivel resolver o diretorio de config do app");
    fs::create_dir_all(&dir).expect("nao foi possivel criar o diretorio de config");
    dir.join("saved_queries.json")
}

fn read_all(app: &AppHandle) -> Vec<SavedQuery> {
    let path = saved_queries_file(app);
    match fs::read_to_string(&path) {
        Ok(content) => serde_json::from_str(&content).unwrap_or_default(),
        Err(_) => Vec::new(),
    }
}

fn write_all(app: &AppHandle, queries: &[SavedQuery]) {
    let path = saved_queries_file(app);
    let content = serde_json::to_string_pretty(queries).expect("falha ao serializar queries salvas");
    fs::write(path, content).expect("falha ao gravar saved_queries.json");
}

pub fn list_queries(app: &AppHandle) -> Vec<SavedQuery> {
    read_all(app)
}

pub fn save_query(app: &AppHandle, input: SaveQueryInput) -> SavedQuery {
    let mut queries = read_all(app);
    let id = input.id.unwrap_or_else(|| Uuid::new_v4().to_string());

    let record = SavedQuery {
        id: id.clone(),
        conn_id: input.conn_id,
        name: input.name,
        sql: input.sql,
    };

    match queries.iter().position(|q| q.id == id) {
        Some(idx) => queries[idx] = record.clone(),
        None => queries.push(record.clone()),
    }
    write_all(app, &queries);
    record
}

pub fn delete_query(app: &AppHandle, id: &str) {
    let mut queries = read_all(app);
    queries.retain(|q| q.id != id);
    write_all(app, &queries);
}
