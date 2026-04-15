// 存储相关工具函数
const storage = {
  // 存储配置
  saveConfig: (config) => {
    try {
      localStorage.setItem('browser-use-config', JSON.stringify(config))
    } catch (error) {
      console.error('Failed to save config:', error)
    }
  },

  // 加载配置
  loadConfig: () => {
    try {
      const config = localStorage.getItem('browser-use-config')
      return config ? JSON.parse(config) : null
    } catch (error) {
      console.error('Failed to load config:', error)
      return null
    }
  },

  // 保存代理设置
  saveAgentSettings: (settings) => {
    try {
      localStorage.setItem('agent-settings', JSON.stringify(settings))
    } catch (error) {
      console.error('Failed to save agent settings:', error)
    }
  },

  // 加载代理设置
  loadAgentSettings: () => {
    try {
      const settings = localStorage.getItem('agent-settings')
      return settings ? JSON.parse(settings) : null
    } catch (error) {
      console.error('Failed to load agent settings:', error)
      return null
    }
  },

  // 保存浏览器设置
  saveBrowserSettings: (settings) => {
    try {
      localStorage.setItem('browser-settings', JSON.stringify(settings))
    } catch (error) {
      console.error('Failed to save browser settings:', error)
    }
  },

  // 加载浏览器设置
  loadBrowserSettings: () => {
    try {
      const settings = localStorage.getItem('browser-settings')
      return settings ? JSON.parse(settings) : null
    } catch (error) {
      console.error('Failed to load browser settings:', error)
      return null
    }
  },

  // 保存主题设置
  saveThemeSettings: (settings) => {
    try {
      localStorage.setItem('theme-settings', JSON.stringify(settings))
    } catch (error) {
      console.error('Failed to save theme settings:', error)
    }
  },

  // 加载主题设置
  loadThemeSettings: () => {
    try {
      const settings = localStorage.getItem('theme-settings')
      return settings ? JSON.parse(settings) : { theme: 'light' }
    } catch (error) {
      console.error('Failed to load theme settings:', error)
      return { theme: 'light' }
    }
  }
}

export default storage