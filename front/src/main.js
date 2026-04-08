import Vue from 'vue'
import App from './App.vue'
import router from './router'
import './plugins/element.js'
import VueClipboard from 'vue-clipboard2'

// 引入API和工具函数
import api from './api'
import storage from './utils/storage'

// 注册全局属性
Vue.prototype.$api = api
Vue.prototype.$storage = storage

Vue.use(VueClipboard)
Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
