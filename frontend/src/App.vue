<template>
  <div id="app">
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <router-link class="navbar-brand" to="/">
          <i class="fas fa-shield-alt me-2"></i>
          IOC Scraper
        </router-link>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/">
                <i class="fas fa-home me-1"></i>
                Dashboard
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/sources">
                <i class="fas fa-list me-1"></i>
                Sources
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/iocs">
                <i class="fas fa-search me-1"></i>
                IOCs
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/scrape">
                <i class="fas fa-play me-1"></i>
                Ad-hoc Scrape
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/sessions">
                <i class="fas fa-history me-1"></i>
                Sessions
              </router-link>
            </li>
          </ul>
          
          <div class="navbar-text">
            <i class="fas fa-clock me-1"></i>
            {{ currentTime }}
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="container mt-4">
      <router-view />
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-light mt-5 py-4">
      <div class="container text-center">
        <p>&copy; 2024 IOC Scraper - Indicators of Compromise Detection Platform</p>
      </div>
    </footer>
  </div>
</template>

<script>
import moment from 'moment'

export default {
  name: 'App',
  data() {
    return {
      currentTime: ''
    }
  },
  mounted() {
    this.updateTime()
    setInterval(this.updateTime, 1000)
  },
  methods: {
    updateTime() {
      this.currentTime = moment().format('YYYY-MM-DD HH:mm:ss')
    }
  }
}
</script> 