use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};
use uuid::Uuid;

#[derive(Serialize, Deserialize, Clone)]
pub struct ConnectionProfile {
    pub id: String,
    pub name: String,
    pub host: String,
    pub port: u16,
    pub database: String,
    pub user: String,
    pub ssl: bool,
    pub encrypted: bool,
}

#[derive(Deserialize)]
pub struct SaveConnectionInput {
    pub id: Option<String>,
    pub name: String,
    pub host: String,
    pub port: Option<u16>,
    pub database: String,
    pub user: String,
    pub ssl: Option<bool>,
    pub password: Option<String>,
}

fn connections_file(app: &AppHandle) -> PathBuf {
    let dir = app
        .path()
        .app_config_dir()
        .expect("nao foi possivel resolver o diretorio de config do app");
    fs::create_dir_all(&dir).expect("nao foi possivel criar o diretorio de config");
    dir.join("connections.json")
}

fn read_all(app: &AppHandle) -> Vec<ConnectionProfile> {
    let path = connections_file(app);
    match fs::read_to_string(&path) {
        Ok(content) => serde_json::from_str(&content).unwrap_or_default(),
        Err(_) => Vec::new(),
    }
}

fn write_all(app: &AppHandle, connections: &[ConnectionProfile]) {
    let path = connections_file(app);
    let content = serde_json::to_string_pretty(connections).expect("falha ao serializar conexoes");
    fs::write(path, content).expect("falha ao gravar connections.json");
}

fn keyring_entry(id: &str) -> Result<keyring::Entry, String> {
    keyring::Entry::new("sparksdb", id).map_err(|e| e.to_string())
}

fn try_store_password_in_keyring(id: &str, password: &str) -> bool {
    match keyring_entry(id) {
        Ok(entry) => entry.set_password(password).is_ok(),
        Err(_) => false,
    }
}

fn read_password_from_keyring(id: &str) -> Option<String> {
    keyring_entry(id).ok()?.get_password().ok()
}

pub fn list_connections(app: &AppHandle) -> Vec<ConnectionProfile> {
    read_all(app)
}

pub fn get_connection_with_password(app: &AppHandle, id: &str) -> Option<(ConnectionProfile, String)> {
    let connections = read_all(app);
    let profile = connections.into_iter().find(|c| c.id == id)?;
    let password = if profile.encrypted {
        read_password_from_keyring(&profile.id).unwrap_or_default()
    } else {
        read_plaintext_fallback(app, &profile.id).unwrap_or_default()
    };
    Some((profile, password))
}

fn fallback_file(app: &AppHandle) -> PathBuf {
    let dir = app.path().app_config_dir().expect("sem config dir");
    dir.join("connections-fallback.json")
}

fn read_plaintext_fallback(app: &AppHandle, id: &str) -> Option<String> {
    let content = fs::read_to_string(fallback_file(app)).ok()?;
    let map: std::collections::HashMap<String, String> = serde_json::from_str(&content).ok()?;
    map.get(id).cloned()
}

fn write_plaintext_fallback(app: &AppHandle, id: &str, password: &str) {
    let path = fallback_file(app);
    let mut map: std::collections::HashMap<String, String> = fs::read_to_string(&path)
        .ok()
        .and_then(|c| serde_json::from_str(&c).ok())
        .unwrap_or_default();
    map.insert(id.to_string(), password.to_string());
    fs::write(path, serde_json::to_string_pretty(&map).unwrap()).ok();
}

fn remove_plaintext_fallback(app: &AppHandle, id: &str) {
    let path = fallback_file(app);
    if let Some(content) = fs::read_to_string(&path).ok() {
        let mut map: std::collections::HashMap<String, String> =
            serde_json::from_str(&content).unwrap_or_default();
        map.remove(id);
        fs::write(path, serde_json::to_string_pretty(&map).unwrap()).ok();
    }
}

pub fn save_connection(app: &AppHandle, input: SaveConnectionInput) -> ConnectionProfile {
    let mut connections = read_all(app);
    let id = input.id.unwrap_or_else(|| Uuid::new_v4().to_string());

    let encrypted = if let Some(password) = &input.password {
        if try_store_password_in_keyring(&id, password) {
            remove_plaintext_fallback(app, &id);
            true
        } else {
            write_plaintext_fallback(app, &id, password);
            false
        }
    } else {
        connections
            .iter()
            .find(|c| c.id == id)
            .map(|c| c.encrypted)
            .unwrap_or(false)
    };

    let record = ConnectionProfile {
        id: id.clone(),
        name: input.name,
        host: input.host,
        port: input.port.unwrap_or(5432),
        database: input.database,
        user: input.user,
        ssl: input.ssl.unwrap_or(false),
        encrypted,
    };

    match connections.iter().position(|c| c.id == id) {
        Some(idx) => connections[idx] = record.clone(),
        None => connections.push(record.clone()),
    }
    write_all(app, &connections);
    record
}

pub fn delete_connection(app: &AppHandle, id: &str) {
    let mut connections = read_all(app);
    connections.retain(|c| c.id != id);
    write_all(app, &connections);
    let _ = keyring_entry(id).and_then(|e| e.delete_credential().map_err(|e| e.to_string()));
    remove_plaintext_fallback(app, id);
}
