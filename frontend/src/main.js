import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import Home from './views/Home.vue'
import Translate from './views/Translate.vue'
import Glossary from './views/Glossary.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/translate', name: 'Translate', component: Translate },
  { path: '/glossary', name: 'Glossary', component: Glossary }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
