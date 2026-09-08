use std::collections::HashMap;
use std::sync::Mutex;

pub struct AppState {
    pub pools: Mutex<HashMap<String, deadpool_postgres::Pool>>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            pools: Mutex::new(HashMap::new()),
        }
    }
}
