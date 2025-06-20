import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Sources from '../views/Sources.vue'
import IOCs from '../views/IOCs.vue'
import AdHocScrape from '../views/AdHocScrape.vue'
import Sessions from '../views/Sessions.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/sources',
    name: 'Sources',
    component: Sources
  },
  {
    path: '/iocs',
    name: 'IOCs',
    component: IOCs
  },
  {
    path: '/scrape',
    name: 'AdHocScrape',
    component: AdHocScrape
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: Sessions
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 