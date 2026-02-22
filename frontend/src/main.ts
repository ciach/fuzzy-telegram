import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './pages/Dashboard.vue'
import ContractEditor from './pages/ContractEditor.vue'
import ContractHistory from './pages/ContractHistory.vue'
import './styles.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/contracts/:id', component: ContractEditor },
    { path: '/contracts/:id/history', component: ContractHistory }
  ]
})

createApp(App).use(createPinia()).use(router).mount('#app')
