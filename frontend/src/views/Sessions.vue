<template>
  <div class="sessions">
    <div class="row mb-4">
      <div class="col">
        <h1><i class="fas fa-history me-2"></i>Scrape Sessions</h1>
        <p class="text-muted">View history of scraping activities</p>
      </div>
    </div>

    <!-- Sessions Table -->
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5>Recent Sessions</h5>
        <button class="btn btn-sm btn-outline-primary" @click="loadSessions">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
        
        <div v-else-if="sessions.length === 0" class="text-center py-4 text-muted">
          <i class="fas fa-clock fa-3x mb-3"></i>
          <p>No scraping sessions yet. Start scraping to see activity here!</p>
        </div>
        
        <div v-else>
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Source</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th>Duration</th>
                  <th>IOCs Found</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="session in sessions" :key="session.id" class="fade-in">
                  <td><strong>#{{ session.id }}</strong></td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClass(session.status)">
                      {{ session.status }}
                    </span>
                  </td>
                  <td>
                    <span v-if="session.source_url_id">
                      Source #{{ session.source_url_id }}
                    </span>
                    <span v-else class="text-muted">Ad-hoc</span>
                  </td>
                  <td>{{ formatDateTime(session.started_at) }}</td>
                  <td>
                    {{ session.completed_at ? formatDateTime(session.completed_at) : '-' }}
                  </td>
                  <td>
                    {{ session.completed_at ? formatDuration(session.started_at, session.completed_at) : '-' }}
                  </td>
                  <td>
                    <span class="badge bg-primary">{{ session.iocs_found }}</span>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-outline-info" @click="viewSessionDetails(session)">
                      <i class="fas fa-eye me-1"></i>View IOCs
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <nav v-if="pagination.pages > 1" class="mt-3">
            <ul class="pagination justify-content-center">
              <li class="page-item" :class="{ disabled: pagination.current_page === 1 }">
                <button class="page-link" @click="changePage(pagination.current_page - 1)">Previous</button>
              </li>
              
              <li 
                v-for="page in visiblePages" 
                :key="page" 
                class="page-item" 
                :class="{ active: page === pagination.current_page }"
              >
                <button class="page-link" @click="changePage(page)">{{ page }}</button>
              </li>
              
              <li class="page-item" :class="{ disabled: pagination.current_page === pagination.pages }">
                <button class="page-link" @click="changePage(pagination.current_page + 1)">Next</button>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>

    <!-- Session Details Modal -->
    <div class="modal fade" :class="{ show: showDetailsModal }" style="display: block;" v-if="showDetailsModal">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Session #{{ selectedSession?.id }} Details</h5>
            <button type="button" class="btn-close" @click="closeDetailsModal"></button>
          </div>
          <div class="modal-body" v-if="selectedSession">
            <!-- Session Info -->
            <div class="row mb-4">
              <div class="col-md-6">
                <h6>Session Information</h6>
                <table class="table table-sm">
                  <tr>
                    <td><strong>Status:</strong></td>
                    <td>
                      <span class="badge" :class="getStatusBadgeClass(selectedSession.status)">
                        {{ selectedSession.status }}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Started:</strong></td>
                    <td>{{ formatDateTime(selectedSession.started_at) }}</td>
                  </tr>
                  <tr>
                    <td><strong>Completed:</strong></td>
                    <td>
                      {{ selectedSession.completed_at ? formatDateTime(selectedSession.completed_at) : 'Not completed' }}
                    </td>
                  </tr>
                  <tr v-if="selectedSession.error_message">
                    <td><strong>Error:</strong></td>
                    <td class="text-danger">{{ selectedSession.error_message }}</td>
                  </tr>
                </table>
              </div>
              <div class="col-md-6">
                <h6>Statistics</h6>
                <table class="table table-sm">
                  <tr>
                    <td><strong>IOCs Found:</strong></td>
                    <td><span class="badge bg-primary">{{ selectedSession.iocs_found }}</span></td>
                  </tr>
                  <tr v-if="selectedSession.completed_at">
                    <td><strong>Duration:</strong></td>
                    <td>{{ formatDuration(selectedSession.started_at, selectedSession.completed_at) }}</td>
                  </tr>
                </table>
              </div>
            </div>

            <!-- IOCs Table -->
            <div v-if="sessionIOCs.length > 0">
              <h6>Extracted IOCs</h6>
              <div class="table-responsive">
                <table class="table table-sm table-hover">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Value</th>
                      <th>Confidence</th>
                      <th>Context</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="ioc in sessionIOCs" :key="ioc.id">
                      <td>
                        <span class="badge" :class="getIOCTypeBadgeClass(ioc.ioc_type)">
                          {{ formatIOCType(ioc.ioc_type) }}
                        </span>
                      </td>
                      <td><code class="small">{{ ioc.value }}</code></td>
                      <td>
                        <span :class="getConfidenceClass(ioc.confidence)">
                          {{ Math.round(ioc.confidence * 100) }}%
                        </span>
                      </td>
                      <td>
                        <small class="text-muted">{{ ioc.context || '-' }}</small>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div v-else-if="selectedSession.status === 'completed'" class="text-center py-4 text-muted">
              <p>No IOCs found in this session.</p>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeDetailsModal">Close</button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showDetailsModal"></div>
  </div>
</template>

<script>
import api from '../services/api'
import moment from 'moment'

export default {
  name: 'Sessions',
  data() {
    return {
      sessions: [],
      loading: true,
      pagination: {
        current_page: 1,
        total: 0,
        pages: 0
      },
      showDetailsModal: false,
      selectedSession: null,
      sessionIOCs: []
    }
  },
  computed: {
    visiblePages() {
      const current = this.pagination.current_page
      const total = this.pagination.pages
      const delta = 2
      
      let start = Math.max(1, current - delta)
      let end = Math.min(total, current + delta)
      
      const pages = []
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    }
  },
  async mounted() {
    await this.loadSessions()
  },
  methods: {
    async loadSessions() {
      this.loading = true
      try {
        const response = await api.getSessions({
          page: this.pagination.current_page,
          per_page: 20
        })
        
        this.sessions = response.data.sessions
        this.pagination = {
          current_page: response.data.current_page,
          total: response.data.total,
          pages: response.data.pages
        }
      } catch (error) {
        console.error('Error loading sessions:', error)
        alert('Error loading sessions')
      } finally {
        this.loading = false
      }
    },
    
    async viewSessionDetails(session) {
      this.selectedSession = session
      this.sessionIOCs = []
      this.showDetailsModal = true
      
      try {
        const response = await api.getSessionIOCs(session.id)
        this.sessionIOCs = response.data.iocs || []
      } catch (error) {
        console.error('Error loading session IOCs:', error)
      }
    },
    
    closeDetailsModal() {
      this.showDetailsModal = false
      this.selectedSession = null
      this.sessionIOCs = []
    },
    
    changePage(page) {
      if (page >= 1 && page <= this.pagination.pages) {
        this.pagination.current_page = page
        this.loadSessions()
      }
    },
    
    getStatusBadgeClass(status) {
      const classMap = {
        'pending': 'status-pending',
        'running': 'status-running',
        'completed': 'status-completed',
        'failed': 'status-failed'
      }
      return classMap[status] || 'bg-secondary'
    },
    
    formatIOCType(type) {
      return type.replace('_', ' ').toUpperCase()
    },
    
    getIOCTypeBadgeClass(type) {
      const classMap = {
        'ip_address': 'ioc-type-ip',
        'url': 'ioc-type-url',
        'domain': 'ioc-type-domain',
        'hash': 'ioc-type-hash',
        'filename': 'ioc-type-filename',
        'asn': 'ioc-type-asn'
      }
      return classMap[type] || 'bg-secondary'
    },
    
    getConfidenceClass(confidence) {
      if (confidence >= 0.8) return 'confidence-high'
      if (confidence >= 0.5) return 'confidence-medium'
      return 'confidence-low'
    },
    
    formatDateTime(dateString) {
      return moment(dateString).format('MMM DD, YYYY HH:mm')
    },
    
    formatDuration(start, end) {
      const duration = moment(end).diff(moment(start))
      return moment.duration(duration).humanize()
    }
  }
}
</script> 