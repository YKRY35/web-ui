import request from '@/utils/request'

// 配置相关API
const configApi = {
  // 加载配置
  load: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/api/load-config', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 保存配置
  save: () => {
    return request.get('/api/save-config')
  }
}

// 代理设置相关API
const agentSettingsApi = {
  // 获取代理设置
  get: () => {
    return request.get('/api/agent-settings')
  },

  // 更新代理设置
  update: (settings) => {
    return request.post('/api/agent-settings', settings)
  }
}

// 浏览器设置相关API
const browserSettingsApi = {
  // 获取浏览器设置
  get: () => {
    return request.get('/api/browser-settings')
  },

  // 更新浏览器设置
  update: (settings) => {
    return request.post('/api/browser-settings', settings)
  }
}

// 浏览器使用代理API
const browserUseAgentApi = {
  // 运行代理
  run: (data) => {
    return request.post('/api/agent/run', data)
  },

  // 停止代理
  stop: (taskId) => {
    const formData = new FormData()
    formData.append('task_id', taskId)
    return request.post('/api/agent/stop', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 暂停/恢复代理
  pause: (taskId) => {
    const formData = new FormData()
    formData.append('task_id', taskId)
    return request.post('/api/agent/pause', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  resume: (taskId) => {
    const formData = new FormData()
    formData.append('task_id', taskId)
    return request.post('/api/agent/resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取状态
  getStatus: (taskId) => {
    return request.get(`/api/agent/status?task_id=${taskId}`)
  },

  // 发送响应
  respond: (data) => {
    const formData = new FormData()
    formData.append('task_id', data.task_id)
    formData.append('message', data.message)
    return request.post('/api/agent/respond', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

// 深度研究代理API
const deepResearchApi = {
  // 运行研究
  run: (data) => {
    return request.post('/api/deep-research/run', data)
  },

  // 停止研究
  stop: (taskId) => {
    const formData = new FormData()
    formData.append('task_id', taskId)
    return request.post('/api/deep-research/stop', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取报告
  getReport: (taskId) => {
    return request.get(`/api/deep-research/report?task_id=${taskId}`)
  }
}

// 统一导出
export default {
  config: configApi,
  agentSettings: agentSettingsApi,
  browserSettings: browserSettingsApi,
  browserUseAgent: browserUseAgentApi,
  deepResearch: deepResearchApi
}