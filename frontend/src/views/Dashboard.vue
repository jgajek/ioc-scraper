<template>
  <div class="dashboard">
    <div class="row mb-4">
      <div class="col">
        <h1><i class="fas fa-tachometer-alt me-2"></i>Dashboard</h1>
        <p class="text-muted">Overview of your IOC scraping activities</p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="row mb-4" v-if="stats">
      <div class="col-md-3 mb-3">
        <div class="card text-white bg-primary">
          <div class="card-body">
            <div class="d-flex justify-content-between">
              <div>
                <h5 class="card-title">Total IOCs</h5>
                <h2>{{ stats.total || 0 }}</h2>
              </div>
              <div class="align-self-center">
                <i class="fas fa-shield-alt fa-2x"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-3 mb-3">
        <div class="card text-white bg-success">
          <div class="card-body">
            <div class="d-flex justify-content-between">
              <div>
                <h5 class="card-title">Recent (24h)</h5>
                <h2>{{ stats.recent || 0 }}</h2>
              </div>
              <div class="align-self-center">
                <i class="fas fa-clock fa-2x"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-3 mb-3">
        <div class="card text-white bg-info">
          <div class="card-body">
            <div class="d-flex justify-content-between">
              <div>
                <h5 class="card-title">Active Sources</h5>
                <h2>{{ activeSources }}</h2>
              </div>
              <div class="align-self-center">
                <i class="fas fa-link fa-2x"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-3 mb-3">
        <div class="card text-white bg-warning">
          <div class="card-body">
            <div class="d-flex justify-content-between">
              <div>
                <h5 class="card-title">Sessions Today</h5>
                <h2>{{ todaySessions }}</h2>
              </div>
              <div class="align-self-center">
                <i class="fas fa-history fa-2x"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- IOC Type Distribution -->
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5><i class="fas fa-chart-pie me-2"></i>IOC Type Distribution</h5>
          </div>
          <div class="card-body" v-if="stats">
            <div class="row">
              <div class="col-6 mb-2" v-for="(count, type) in iocTypes" :key="type">
                <div class="d-flex justify-content-between align-items-center">
                  <span class="badge me-2" :class="getIOCTypeBadgeClass(type)">
                    {{ formatIOCType(type) }}
                  </span>
                  <span class="fw-bold">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5><i class="fas fa-clock me-2"></i>Recent Sessions</h5>
          </div>
          <div class="card-body">
            <div v-if="recentSessions.length === 0" class="text-muted text-center py-3">
              No recent sessions
            </div>
            <div v-else>
              <div v-for="session in recentSessions" :key="session.id" class="d-flex justify-content-between align-items-center mb-2">
                <div>
                  <small class="text-muted">{{ formatDateTime(session.started_at) }}</small>
                  <div>
                    <span class="badge me-2" :class="getStatusBadgeClass(session.status)">
                      {{ session.status }}
                    </span>
                    <span>{{ session.iocs_found }} IOCs</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">
            <h5><i class="fas fa-rocket me-2"></i>Quick Actions</h5>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-3 mb-2">
                <router-link to="/scrape" class="btn btn-primary w-100">
                  <i class="fas fa-play me-2"></i>Start Ad-hoc Scrape
                </router-link>
              </div>
              <div class="col-md-3 mb-2">
                <router-link to="/sources" class="btn btn-success w-100">
                  <i class="fas fa-plus me-2"></i>Add Source URL
                </router-link>
              </div>
              <div class="col-md-3 mb-2">
                <router-link to="/iocs" class="btn btn-info w-100">
                  <i class="fas fa-search me-2"></i>Browse IOCs
                </router-link>
              </div>
              <div class="col-md-3 mb-2">
                <router-link to="/sessions" class="btn btn-secondary w-100">
                  <i class="fas fa-history me-2"></i>View Sessions
                </router-link>
              </div>
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
  name: 'Dashboard',
  data() {
    return {
      stats: null,
      sources: [],
      recentSessions: [],
      loading: true
    }
  },
  computed: {
    iocTypes() {
      if (!this.stats) return {}
      const { total, recent, ...types } = this.stats
      return types
    },
    activeSources() {
      return this.sources.filter(source => source.active).length
    },
    todaySessions() {
      const today = moment().startOf('day')
      return this.recentSessions.filter(session => 
        moment(session.started_at).isAfter(today)
      ).length
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const [statsResponse, sourcesResponse, sessionsResponse] = await Promise.all([
          api.getIOCStats(),
          api.getSources(),
          api.getSessions({ per_page: 10 })
        ])
        
        this.stats = statsResponse.data
        this.sources = sourcesResponse.data
        this.recentSessions = sessionsResponse.data.sessions || []
      } catch (error) {
        console.error('Error loading dashboard data:', error)
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
    
    getStatusBadgeClass(status) {
      const classMap = {
        'pending': 'status-pending',
        'running': 'status-running',
        'completed': 'status-completed',
        'failed': 'status-failed'
      }
      return classMap[status] || 'bg-secondary'
    },
    
    formatDateTime(dateString) {
      return moment(dateString).format('MMM DD, HH:mm')
    }
  }
}
</script> 