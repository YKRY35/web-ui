import request from '@/utils/request'

// 配置相关API
export const configApi = {
  // 加载配置
  load: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/load-config', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 保存配置
  save: () => {
    return request.get('/save-config')
  }
}

// 代理设置相关API
export const agentSettingsApi = {
  // 获取代理设置
  get: () => {
    return request.get('/agent-settings')
  },

  // 更新代理设置
  update: (settings) => {
    return request.post('/agent-settings', settings)
  }
}

// 浏览器设置相关API
export const browserSettingsApi = {
  // 获取浏览器设置
  get: () => {
    return request.get('/browser-settings')
  },

  // 更新浏览器设置
  update: (settings) => {
    return request.post('/browser-settings', settings)
  }
}

// 浏览器使用代理API
export const browserUseAgentApi = {
  // 运行代理
  run: (data) => {
    return request.post('/agent/run', data)
  },

  // 停止代理
  stop: (taskId) => {
    return request.post('/agent/stop', { task_id: taskId })
  },

  // 暂停/恢复代理
  pause: (taskId) => {
    return request.post('/agent/pause', { task_id: taskId })
  },

  resume: (taskId) => {
    return request.post('/agent/resume', { task_id: taskId })
  },

  // 获取状态
  getStatus: (taskId) => {
    return request.get(`/agent/status?task_id=${taskId}`)
  },

  // 发送响应
  respond: (data) => {
    return request.post('/agent/respond', data)
  }
}

// 深度研究代理API
export const deepResearchApi = {
  // 运行研究
  run: (data) => {
    return request.post('/deep-research/run', data)
  },

  // 停止研究
  stop: (taskId) => {
    return request.post('/deep-research/stop', { task_id: taskId })
  },

  // 获取报告
  getReport: (taskId) => {
    return request.get(`/deep-research/report?task_id=${taskId}`)
  }
}