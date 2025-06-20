<template>
  <div class="sources">
    <div class="row mb-4">
      <div class="col">
        <h1><i class="fas fa-list me-2"></i>Source URLs</h1>
        <p class="text-muted">Manage URLs for periodic scraping</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="showAddModal = true">
          <i class="fas fa-plus me-2"></i>Add Source
        </button>
      </div>
    </div>

    <!-- Sources Table -->
    <div class="card">
      <div class="card-header">
        <h5>Configured Sources</h5>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
        
        <div v-else-if="sources.length === 0" class="text-center py-4 text-muted">
          <i class="fas fa-inbox fa-3x mb-3"></i>
          <p>No sources configured yet. Add your first source to get started!</p>
        </div>
        
        <div v-else class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>Name</th>
                <th>URL</th>
                <th>Description</th>
                <th>Status</th>
                <th>Interval</th>
                <th>Last Scraped</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="source in sources" :key="source.id" class="fade-in">
                <td>
                  <strong>{{ source.name || 'Unnamed' }}</strong>
                </td>
                <td>
                  <a :href="source.url" target="_blank" class="text-truncate d-inline-block" style="max-width: 200px;">
                    {{ source.url }}
                  </a>
                </td>
                <td class="text-muted">{{ source.description || '-' }}</td>
                <td>
                  <span class="badge" :class="source.active ? 'bg-success' : 'bg-secondary'">
                    {{ source.active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>{{ formatInterval(source.scrape_interval) }}</td>
                <td>
                  {{ source.last_scraped ? formatDateTime(source.last_scraped) : 'Never' }}
                </td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" @click="scrapeSource(source)" :disabled="scraping === source.id">
                      <i class="fas fa-play me-1"></i>
                      <span v-if="scraping === source.id">Scraping...</span>
                      <span v-else>Scrape</span>
                    </button>
                    <button class="btn btn-outline-secondary" @click="editSource(source)">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger" @click="deleteSource(source)">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add/Edit Source Modal -->
    <div class="modal fade" :class="{ show: showAddModal }" style="display: block;" v-if="showAddModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingSource ? 'Edit Source' : 'Add New Source' }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveSource">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input type="text" class="form-control" v-model="sourceForm.name" placeholder="Enter a name for this source">
              </div>
              
              <div class="mb-3">
                <label class="form-label">URL *</label>
                <input type="url" class="form-control" v-model="sourceForm.url" required placeholder="https://example.com/threats">
              </div>
              
              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea class="form-control" v-model="sourceForm.description" rows="3" placeholder="Describe this source..."></textarea>
              </div>
              
              <div class="mb-3">
                <label class="form-label">Scrape Interval (seconds)</label>
                <select class="form-control" v-model="sourceForm.scrape_interval">
                  <option value="300">5 minutes</option>
                  <option value="900">15 minutes</option>
                  <option value="1800">30 minutes</option>
                  <option value="3600">1 hour</option>
                  <option value="7200">2 hours</option>
                  <option value="21600">6 hours</option>
                  <option value="43200">12 hours</option>
                  <option value="86400">24 hours</option>
                </select>
              </div>
              
              <div class="form-check">
                <input class="form-check-input" type="checkbox" v-model="sourceForm.active" id="activeCheck">
                <label class="form-check-label" for="activeCheck">
                  Active (enable periodic scraping)
                </label>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Cancel</button>
            <button type="button" class="btn btn-primary" @click="saveSource" :disabled="!sourceForm.url">
              {{ editingSource ? 'Update' : 'Add' }} Source
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showAddModal"></div>
  </div>
</template>

<script>
import api from '../services/api'
import moment from 'moment'

export default {
  name: 'Sources',
  data() {
    return {
      sources: [],
      loading: true,
      showAddModal: false,
      editingSource: null,
      scraping: null,
      sourceForm: {
        name: '',
        url: '',
        description: '',
        scrape_interval: 3600,
        active: true
      }
    }
  },
  async mounted() {
    await this.loadSources()
  },
  methods: {
    async loadSources() {
      this.loading = true
      try {
        const response = await api.getSources()
        this.sources = response.data
      } catch (error) {
        console.error('Error loading sources:', error)
        alert('Error loading sources')
      } finally {
        this.loading = false
      }
    },
    
    editSource(source) {
      this.editingSource = source
      this.sourceForm = { ...source }
      this.showAddModal = true
    },
    
    async saveSource() {
      try {
        if (this.editingSource) {
          await api.updateSource(this.editingSource.id, this.sourceForm)
        } else {
          await api.createSource(this.sourceForm)
        }
        
        await this.loadSources()
        this.closeModal()
      } catch (error) {
        console.error('Error saving source:', error)
        alert('Error saving source')
      }
    },
    
    async deleteSource(source) {
      if (confirm(`Are you sure you want to delete "${source.name || source.url}"?`)) {
        try {
          await api.deleteSource(source.id)
          await this.loadSources()
        } catch (error) {
          console.error('Error deleting source:', error)
          alert('Error deleting source')
        }
      }
    },
    
    async scrapeSource(source) {
      this.scraping = source.id
      try {
        await api.scrapeSource(source.id)
        await this.loadSources()
        alert('Scrape completed successfully!')
      } catch (error) {
        console.error('Error scraping source:', error)
        alert('Error during scraping')
      } finally {
        this.scraping = null
      }
    },
    
    closeModal() {
      this.showAddModal = false
      this.editingSource = null
      this.sourceForm = {
        name: '',
        url: '',
        description: '',
        scrape_interval: 3600,
        active: true
      }
    },
    
    formatInterval(seconds) {
      if (seconds < 60) return `${seconds}s`
      if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
      if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
      return `${Math.floor(seconds / 86400)}d`
    },
    
    formatDateTime(dateString) {
      return moment(dateString).format('MMM DD, YYYY HH:mm')
    }
  }
}
</script> 