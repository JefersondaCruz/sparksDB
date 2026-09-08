pub mod commands;
pub mod pool_manager;
pub mod queries;
pub mod state;
pub mod store;

use state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .manage(AppState::new())
    .invoke_handler(tauri::generate_handler![
      commands::connections::connections_list,
      commands::connections::connections_save,
      commands::connections::connections_delete,
      commands::connections::connections_test,
      commands::db::db_connect,
      commands::db::db_disconnect,
      commands::db::db_query,
      commands::db::db_schemas,
      commands::db::db_tables,
      commands::db::db_columns,
      commands::db::db_table_data,
    ])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
