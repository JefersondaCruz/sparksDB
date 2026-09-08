use crate::pool_manager;
use crate::store;
use crate::store::{ConnectionProfile, SaveConnectionInput};
use tauri::AppHandle;

#[tauri::command]
pub fn connections_list(app: AppHandle) -> Vec<ConnectionProfile> {
    store::list_connections(&app)
}

#[tauri::command]
pub fn connections_save(app: AppHandle, profile: SaveConnectionInput) -> ConnectionProfile {
    store::save_connection(&app, profile)
}

#[tauri::command]
pub fn connections_delete(app: AppHandle, id: String) {
    store::delete_connection(&app, &id)
}

#[tauri::command]
pub async fn connections_test(profile: store::SaveConnectionInput) -> Result<(), String> {
    let temp_profile = ConnectionProfile {
        id: "temp".into(),
        name: profile.name,
        host: profile.host,
        port: profile.port.unwrap_or(5432),
        database: profile.database,
        user: profile.user,
        ssl: profile.ssl.unwrap_or(false),
        encrypted: false,
    };
    let password = profile.password.unwrap_or_default();
    pool_manager::test_connection(&temp_profile, &password).await
}
