use crate::saved_queries;
use crate::saved_queries::{SaveQueryInput, SavedQuery};
use tauri::AppHandle;

#[tauri::command]
pub fn queries_list(app: AppHandle) -> Vec<SavedQuery> {
    saved_queries::list_queries(&app)
}

#[tauri::command]
pub fn queries_save(app: AppHandle, input: SaveQueryInput) -> SavedQuery {
    saved_queries::save_query(&app, input)
}

#[tauri::command]
pub fn queries_delete(app: AppHandle, id: String) {
    saved_queries::delete_query(&app, &id)
}
