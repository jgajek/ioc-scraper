<template>
  <div class="iocs">
    <div class="row mb-4">
      <div class="col">
        <h1><i class="fas fa-search me-2"></i>IOCs Database</h1>
        <p class="text-muted">Browse and search extracted Indicators of Compromise</p>
      </div>
    </div>

    <!-- Filters and Search -->
    <div class="card mb-4">
      <div class="card-header">
        <h5><i class="fas fa-filter me-2"></i>Filters & Search</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-4 mb-3">
            <label class="form-label">Search IOCs</label>
            <input 
              type="text" 
              class="form-control" 
              v-model="searchQuery" 
              placeholder="Search by value..."
              @input="debouncedSearch"
            >
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label">IOC Type</label>
            <select class="form-control" v-model="selectedType" @change="loadIOCs">
              <option value="">All Types</option>
              <option value="ip_address">IP Addresses</option>
              <option value="url">URLs</option>
              <option value="domain">Domains</option>
              <option value="hash">Hashes</option>
              <option value="filename">Filenames</option>
              <option value="asn">ASNs</option>
            </select>
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label">Items per page</label>
            <select class="form-control" v-model="perPage" @change="loadIOCs">
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
          <div class="col-md-2 mb-3">
            <label class="form-label">&nbsp;</label>
            <div>
              <button class="btn btn-outline-secondary w-100" @click="resetFilters">
                <i class="fas fa-undo me-1"></i>Reset
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- IOCs Table -->
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5>
          IOCs 
          <span v-if="pagination.total" class="badge bg-secondary ms-2">
            {{ pagination.total }} total
          </span>
        </h5>
        <button class="btn btn-sm btn-outline-primary" @click="loadIOCs">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
        
        <div v-else-if="iocs.length === 0" class="text-center py-4 text-muted">
          <i class="fas fa-search fa-3x mb-3"></i>
          <p v-if="searchQuery || selectedType">No IOCs found matching your criteria.</p>
          <p v-else>No IOCs in the database yet. Start scraping to populate it!</p>
        </div>
        
        <div v-else>
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Value</th>
                  <th>Confidence</th>
                  <th>First Seen</th>
                  <th>Last Seen</th>
                  <th>Context</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="ioc in iocs" :key="ioc.id" class="fade-in">
                  <td>
                    <span class="badge" :class="getIOCTypeBadgeClass(ioc.ioc_type)">
                      {{ formatIOCType(ioc.ioc_type) }}
                    </span>
                  </td>
                  <td>
                    <code class="small">{{ ioc.value }}</code>
                  </td>
                  <td>
                    <span :class="getConfidenceClass(ioc.confidence)">
                      {{ Math.round(ioc.confidence * 100) }}%
                    </span>
                  </td>
                  <td>
                    <small>{{ formatDateTime(ioc.first_seen) }}</small>
                  </td>
                  <td>
                    <small>{{ formatDateTime(ioc.last_seen) }}</small>
                  </td>
                  <td>
                    <small class="text-muted text-truncate d-inline-block" style="max-width: 250px;">
                      {{ ioc.context || '-' }}
                    </small>
                  </td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-info" @click="viewIOCDetails(ioc)" title="View Details">
                        <i class="fas fa-eye"></i>
                      </button>
                      <button class="btn btn-outline-primary" @click="copyToClipboard(ioc.value)" title="Copy Value">
                        <i class="fas fa-copy"></i>
                      </button>
                    </div>
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

    <!-- IOC Details Modal -->
    <div class="modal fade" :class="{ show: showDetailsModal }" style="display: block;" v-if="showDetailsModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">IOC Details</h5>
            <button type="button" class="btn-close" @click="showDetailsModal = false"></button>
          </div>
          <div class="modal-body" v-if="selectedIOC">
            <div class="row">
              <div class="col-md-6">
                <h6>Basic Information</h6>
                <table class="table table-sm">
                  <tr>
                    <td><strong>Type:</strong></td>
                    <td>
                      <span class="badge" :class="getIOCTypeBadgeClass(selectedIOC.ioc_type)">
                        {{ formatIOCType(selectedIOC.ioc_type) }}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Value:</strong></td>
                    <td><code>{{ selectedIOC.value }}</code></td>
                  </tr>
                  <tr>
                    <td><strong>Confidence:</strong></td>
                    <td>
                      <span :class="getConfidenceClass(selectedIOC.confidence)">
                        {{ Math.round(selectedIOC.confidence * 100) }}%
                      </span>
                    </td>
                  </tr>
                </table>
              </div>
              <div class="col-md-6">
                <h6>Timeline</h6>
                <table class="table table-sm">
                  <tr>
                    <td><strong>First Seen:</strong></td>
                    <td>{{ formatDateTime(selectedIOC.first_seen) }}</td>
                  </tr>
                  <tr>
                    <td><strong>Last Seen:</strong></td>
                    <td>{{ formatDateTime(selectedIOC.last_seen) }}</td>
                  </tr>
                  <tr>
                    <td><strong>Session ID:</strong></td>
                    <td>{{ selectedIOC.scrape_session_id }}</td>
                  </tr>
                </table>
              </div>
            </div>
            
            <div v-if="selectedIOC.context" class="mt-3">
              <h6>Context</h6>
              <div class="border p-3 bg-light">
                <small class="font-monospace">{{ selectedIOC.context }}</small>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showDetailsModal = false">Close</button>
            <button type="button" class="btn btn-primary" @click="copyToClipboard(selectedIOC.value)">
              <i class="fas fa-copy me-1"></i>Copy Value
            </button>
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
  name: 'IOCs',
  data() {
    return {
      iocs: [],
      loading: true,
      searchQuery: '',
      selectedType: '',
      perPage: 50,
      pagination: {
        current_page: 1,
        total: 0,
        pages: 0
      },
      showDetailsModal: false,
      selectedIOC: null,
      searchTimeout: null
    }
  },
  computed: {
    visiblePages() {
      const current = this.pagination.current_page
      const total = this.pagination.pages
      const delta = 2
      
      let start = Math.max(1, current - delta)
      let end = Math.min(total, current + delta)
      
      if (end - start < 4) {
        start = Math.max(1, end - 4)
        end = Math.min(total, start + 4)
      }
      
      const pages = []
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    }
  },
  async mounted() {
    await this.loadIOCs()
  },
  methods: {
    async loadIOCs() {
      this.loading = true
      try {
        const params = {
          page: this.pagination.current_page,
          per_page: this.perPage
        }
        
        if (this.searchQuery.trim()) {
          params.search = this.searchQuery.trim()
        }
        
        if (this.selectedType) {
          params.type = this.selectedType
        }
        
        const response = await api.getIOCs(params)
        this.iocs = response.data.iocs
        this.pagination = {
          current_page: response.data.current_page,
          total: response.data.total,
          pages: response.data.pages
        }
      } catch (error) {
        console.error('Error loading IOCs:', error)
        alert('Error loading IOCs')
      } finally {
        this.loading = false
      }
    },
    
    debouncedSearch() {
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.pagination.current_page = 1
        this.loadIOCs()
      }, 500)
    },
    
    changePage(page) {
      if (page >= 1 && page <= this.pagination.pages) {
        this.pagination.current_page = page
        this.loadIOCs()
      }
    },
    
    resetFilters() {
      this.searchQuery = ''
      this.selectedType = ''
      this.perPage = 50
      this.pagination.current_page = 1
      this.loadIOCs()
    },
    
    viewIOCDetails(ioc) {
      this.selectedIOC = ioc
      this.showDetailsModal = true
    },
    
    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text)
        alert('Copied to clipboard!')
      } catch (error) {
        console.error('Error copying to clipboard:', error)
        alert('Error copying to clipboard')
      }
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
    }
  }
}
</script> 