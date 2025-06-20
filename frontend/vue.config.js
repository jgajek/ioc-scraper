const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // Development server configuration
  devServer: {
    port: 8080,
    host: '0.0.0.0',
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // Build configuration
  publicPath: '/',
  outputDir: 'dist',
  assetsDir: 'static',
  
  // Performance optimizations
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    }
  }
}) 