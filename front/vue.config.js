const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,
  configureWebpack: {
    devtool: 'source-map'
  },
  chainWebpack: config => {
    config.devtool('source-map')
  }
})
