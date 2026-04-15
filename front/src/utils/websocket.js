import Vue from 'vue'
import { getCurrentSessionId } from './sessionId'

export class WebSocketManager {
  constructor(url) {
    this.url = url
    this.socket = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = Infinity  // 无限重连
    this.reconnectDelay = 1000
    this.reconnectDelayMax = 30000  // 最大重连间隔 30s
    // 使用 Vue.observable 创建响应式对象（Vue 2.6+）
    this.state = Vue.observable({
      isConnected: false,
      isRegistered: false
    })
    this.messageHandlers = new Map()
    this.reconnectTimer = null
    this.heartbeatTimer = null
    this.heartbeatInterval = 30000  // 30秒心跳间隔

    // 默认消息处理器
    this.messageHandlers.set('step', (data) => {
      console.log('Step received:', data)
    })

    this.messageHandlers.set('history', (data) => {
      console.log('History received:', data)
    })

    this.messageHandlers.set('status', (data) => {
      console.log('Status update:', data)
    })

    this.messageHandlers.set('error', (data) => {
      console.error('Error from server:', data)
    })

    // 注册消息处理器
    this.messageHandlers.set('registered', (data, message) => {
      console.log('WebSocket registered:', message.sessionId)
      this.state.isRegistered = true
      this.startHeartbeat()
    })

    // 心跳响应处理器
    this.messageHandlers.set('pong', () => {
      // console.log('Heartbeat pong received')
    })
  }

  // 兼容性 getter
  get isConnected() {
    return this.state.isConnected
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(this.url)

      this.socket.onopen = () => {
        console.log('WebSocket connected')
        this.state.isConnected = true
        this.reconnectAttempts = 0
        // 连接后立即注册会话
        this.registerSession()
        resolve()
      }

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event)
        this.state.isConnected = false
        this.state.isRegistered = false
        this.stopHeartbeat()
        if (!this._manualDisconnect) {
          this.handleReconnect()
        }
      }

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.state.isConnected = false
        // 不 reject，让 onclose 触发重连
      }

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    })
  }

  registerSession() {
    const sessionId = getCurrentSessionId()
    if (sessionId) {
      console.log('Registering session:', sessionId)
      this.send({ type: 'register', sessionId })
    } else {
      console.warn('No sessionId found, cannot register')
    }
  }

  startHeartbeat() {
    this.stopHeartbeat()  // 确保没有重复的定时器
    this.heartbeatTimer = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' })
        // console.log('Heartbeat ping sent')
      }
    }, this.heartbeatInterval)
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  handleMessage(message) {
    const { type, data } = message
    const handler = this.messageHandlers.get(type)

    if (handler) {
      // 传递 data 和完整消息对象
      handler(data, message)
    } else {
      console.warn('No handler for message type:', type)
    }
  }

  addMessageHandler(type, handler) {
    this.messageHandlers.set(type, handler)
  }

  removeMessageHandler(type) {
    this.messageHandlers.delete(type)
  }

  send(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected, cannot send message')
    }
  }

  handleReconnect() {
    if (this.reconnectTimer) return
    // 指数退避，最大 30s
    const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts), this.reconnectDelayMax)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectAttempts++
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
      this.connect()
    }, delay)
  }

  disconnect() {
    this._manualDisconnect = true
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.state.isConnected = false
    this.state.isRegistered = false
    this._manualDisconnect = false
  }

  // Vue 组合式函数
  useWebSocket() {
    // Vue 2 不支持 onMounted/onBeforeUnmount 的导入，这里简化处理
    this.connect()

    return {
      isConnected: this.state.isConnected,
      isRegistered: this.state.isRegistered,
      sendMessage: (message) => this.send(message),
      addMessageHandler: (type, handler) => this.addMessageHandler(type, handler),
      removeMessageHandler: (type, handler) => this.removeMessageHandler(type, handler)
    }
  }
}

// 创建一个全局 WebSocket 管理器实例
// 用于传输代理执行事件（步骤、状态、日志等）
export const websocketManager = new WebSocketManager(
  process.env.VUE_APP_API_BASE_URL.replace('http', 'ws') + '/ws/agent-events'
)
