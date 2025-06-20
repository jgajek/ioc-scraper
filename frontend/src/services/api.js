import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for logging
api.interceptors.request.use(request => {
  console.log('API Request:', request)
  return request
})

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // Health check
  healthCheck() {
    return api.get('/health')
  },

  // Source URLs
  getSources() {
    return api.get('/sources')
  },
  
  createSource(sourceData) {
    return api.post('/sources', sourceData)
  },
  
  updateSource(sourceId, sourceData) {
    return api.put(`/sources/${sourceId}`, sourceData)
  },
  
  deleteSource(sourceId) {
    return api.delete(`/sources/${sourceId}`)
  },

  // Scraping
  scrapeAdhoc(url, includePrivateIps = false) {
    return api.post('/scrape/adhoc', {
      url,
      include_private_ips: includePrivateIps
    })
  },
  
  scrapeSource(sourceId) {
    return api.post(`/scrape/source/${sourceId}`)
  },

  // IOCs
  getIOCs(params = {}) {
    return api.get('/iocs', { params })
  },
  
  getIOCStats() {
    return api.get('/iocs/stats')
  },

  // Sessions
  getSessions(params = {}) {
    return api.get('/sessions', { params })
  },
  
  getSessionIOCs(sessionId) {
    return api.get(`/sessions/${sessionId}/iocs`)
  }
} 