use crate::pool_manager;
use crate::queries;
use crate::state::AppState;
use crate::store;
use tauri::{AppHandle, State};

#[tauri::command]
pub async fn db_connect(
    app: AppHandle,
    state: State<'_, AppState>,
    id: String,
) -> Result<(), String> {
    {
        let pools = state.pools.lock().unwrap();
        if pools.contains_key(&id) {
            return Ok(());
        }
    }
    let (profile, password) = store::get_connection_with_password(&app, &id)
        .ok_or_else(|| "Conexao nao encontrada".to_string())?;
    let pool = pool_manager::open_pool(&profile, &password).await?;
    state.pools.lock().unwrap().insert(id, pool);
    Ok(())
}

#[tauri::command]
pub fn db_disconnect(state: State<'_, AppState>, id: String) {
    state.pools.lock().unwrap().remove(&id);
}

#[tauri::command]
pub async fn db_query(
    state: State<'_, AppState>,
    id: String,
    sql: String,
) -> Result<pool_manager::QueryResult, String> {
    let pool = pool_manager::get_pool(&state, &id)?;
    Ok(pool_manager::run_query(&pool, &sql).await)
}

#[tauri::command]
pub async fn db_schemas(state: State<'_, AppState>, id: String) -> Result<Vec<String>, String> {
    let pool = pool_manager::get_pool(&state, &id)?;
    queries::list_schemas(&pool).await
}

#[tauri::command]
pub async fn db_tables(
    state: State<'_, AppState>,
    id: String,
    schema: String,
) -> Result<Vec<queries::TableInfo>, String> {
    let pool = pool_manager::get_pool(&state, &id)?;
    queries::list_tables(&pool, &schema).await
}

#[tauri::command]
pub async fn db_columns(
    state: State<'_, AppState>,
    id: String,
    schema: String,
    table: String,
) -> Result<Vec<queries::ColumnInfo>, String> {
    let pool = pool_manager::get_pool(&state, &id)?;
    queries::list_columns(&pool, &schema, &table).await
}

#[tauri::command]
pub async fn db_table_data(
    state: State<'_, AppState>,
    id: String,
    schema: String,
    table: String,
    limit: Option<i64>,
    offset: Option<i64>,
) -> Result<queries::TableDataResult, String> {
    let pool = pool_manager::get_pool(&state, &id)?;
    queries::get_table_data(&pool, &schema, &table, limit.unwrap_or(100), offset.unwrap_or(0)).await
}
