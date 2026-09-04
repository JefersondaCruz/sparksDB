import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import * as store from './db/store'
import * as poolManager from './db/pool-manager'
import * as queries from './db/queries'

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: '#171717',
    title: 'sparksDB',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => mainWindow.show())

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

function registerIpcHandlers() {
  ipcMain.handle('connections:list', () => store.listConnections())
  ipcMain.handle('connections:save', (_e, profile) => store.saveConnection(profile))
  ipcMain.handle('connections:delete', (_e, id) => store.deleteConnection(id))
  ipcMain.handle('connections:test', (_e, profile) => poolManager.testConnection(profile))

  ipcMain.handle('db:connect', (_e, id) => poolManager.connect(id))
  ipcMain.handle('db:disconnect', (_e, id) => poolManager.disconnect(id))
  ipcMain.handle('db:query', (_e, id, sql) => poolManager.runQuery(id, sql))

  ipcMain.handle('db:schemas', (_e, id) => queries.listSchemas(id))
  ipcMain.handle('db:tables', (_e, id, schema) => queries.listTables(id, schema))
  ipcMain.handle('db:columns', (_e, id, schema, table) => queries.listColumns(id, schema, table))
  ipcMain.handle('db:tableData', (_e, id, schema, table, limit, offset) =>
    queries.getTableData(id, schema, table, limit, offset)
  )
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.jefersoncruz.sparksdb')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  registerIpcHandlers()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
