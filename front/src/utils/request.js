import axios from 'axios'
import { getCurrentSessionId } from './sessionId'

// 创建axios实例
const request = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 添加 sessionId 到请求头
    const sessionId = getCurrentSessionId()
    if (sessionId) {
      config.headers['X-Session-ID'] = sessionId
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('Response error:', error)
    return Promise.reject(error)
  }
)

export default request