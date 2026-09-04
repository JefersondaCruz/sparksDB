import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as monaco from 'monaco-editor'
import { loader } from '@guolao/vue-monaco-editor'
import EditorWorker from 'monaco-editor/editor/editor.worker?worker'
import './assets/main.css'
import App from './App.vue'

self.MonacoEnvironment = {
  getWorker: () => new EditorWorker()
}
loader.config({ monaco })

createApp(App).use(createPinia()).mount('#app')
