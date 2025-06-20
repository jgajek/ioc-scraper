<template>
  <div class="adhoc-scrape">
    <div class="row mb-4">
      <div class="col">
        <h1><i class="fas fa-play me-2"></i>Ad-hoc Scrape</h1>
        <p class="text-muted">Scrape any URL on-demand for IOCs</p>
      </div>
    </div>

    <!-- Scrape Form -->
    <div class="row mb-4">
      <div class="col-md-8 mx-auto">
        <div class="card">
          <div class="card-header">
            <h5><i class="fas fa-link me-2"></i>Enter URL to Scrape</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="performScrape">
              <div class="mb-3">
                <label class="form-label">URL *</label>
                <input 
                  type="url" 
                  class="form-control form-control-lg" 
                  v-model="scrapeUrl" 
                  required 
                  placeholder="https://example.com/threat-intelligence"
                  :disabled="loading"
                >
                <div class="form-text">Enter the full URL including protocol (http:// or https://)</div>
              </div>
              
              <div class="form-check mb-3">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  v-model="includePrivateIps" 
                  id="privateIpCheck"
                  :disabled="loading"
                >
                <label class="form-check-label" for="privateIpCheck">
                  Include private IP addresses (RFC 1918)
                </label>
              </div>
              
              <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg" :disabled="!scrapeUrl || loading">
                  <span v-if="loading">
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    Scraping...
                  </span>
                  <span v-else>
                    <i class="fas fa-search me-2"></i>
                    Start Scrape
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="lastResult" class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">
            <h5>
              <i class="fas fa-chart-bar me-2"></i>
              Scrape Results
              <span class="badge ms-2" :class="lastResult.status === 'completed' ? 'bg-success' : 'bg-danger'">
                {{ lastResult.status }}
              </span>
            </h5>
          </div>
          <div class="card-body">
            <!-- Error Message -->
            <div v-if="lastResult.error_message" class="alert alert-danger">
              <i class="fas fa-exclamation-triangle me-2"></i>
              {{ lastResult.error_message }}
            </div>

            <!-- Success Summary -->
            <div v-else-if="lastResult.status === 'completed'" class="row mb-4">
              <div class="col-md-3">
                <div class="text-center">
                  <h3 class="text-primary">{{ lastResult.iocs_found }}</h3>
                  <p class="text-muted">IOCs Found</p>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <h3 class="text-info">{{ formatDuration(lastResult.started_at, lastResult.completed_at) }}</h3>
                  <p class="text-muted">Duration</p>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <h3 class="text-success">{{ formatDateTime(lastResult.completed_at) }}</h3>
                  <p class="text-muted">Completed</p>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <h3 class="text-warning">
                    <i class="fas fa-eye me-1"></i>
                    {{ lastResult.content_type === 'html_visible' ? 'Visible' : 'Raw' }}
                  </h3>
                  <p class="text-muted">Content Type</p>
                </div>
              </div>
            </div>

            <!-- Content Analysis Info -->
            <div v-if="lastResult.status === 'completed' && lastResult.content_type === 'html_visible'" class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              <strong>Smart Analysis:</strong> Extracted IOCs from visible content only ({{ formatBytes(lastResult.visible_content_length) }} analyzed from {{ formatBytes(lastResult.content_length) }} total).
              This reduces false positives from JavaScript, CSS, and hidden elements.
            </div>

            <!-- IOCs Table -->
            <div v-if="iocs && iocs.length > 0">
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
                        <small class="text-muted text-truncate d-inline-block" style="max-width: 300px;">
                          {{ ioc.context || '-' }}
                        </small>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div v-else-if="lastResult.status === 'completed'" class="text-center py-4 text-muted">
              <i class="fas fa-search fa-2x mb-3"></i>
              <p>No IOCs found in the scraped content.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import moment from 'moment'

export default {
  name: 'AdHocScrape',
  data() {
    return {
      scrapeUrl: '',
      includePrivateIps: false,
      loading: false,
      lastResult: null,
      iocs: []
    }
  },
  methods: {
    async performScrape() {
      this.loading = true
      this.lastResult = null
      this.iocs = []
      
      try {
        const response = await api.scrapeAdhoc(this.scrapeUrl, this.includePrivateIps)
        this.lastResult = response.data
        this.iocs = response.data.iocs || []
      } catch (error) {
        console.error('Error performing scrape:', error)
        this.lastResult = {
          status: 'failed',
          error_message: error.response?.data?.error || 'An unexpected error occurred'
        }
      } finally {
        this.loading = false
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
      return moment(dateString).format('MMM DD, YYYY HH:mm:ss')
    },
    
    formatDuration(start, end) {
      const duration = moment(end).diff(moment(start))
      return moment.duration(duration).humanize()
    },
    
    formatBytes(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
  }
}
</script> 