import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

export class WebSocketManager {
  constructor(url) {
    this.url = url
    this.socket = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = Infinity  // 无限重连
    this.reconnectDelay = 1000
    this.reconnectDelayMax = 30000  // 最大重连间隔 30s
    this.isConnected = ref(false)
    this.messageHandlers = new Map()
    this.reconnectTimer = null

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
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(this.url)

      this.socket.onopen = () => {
        console.log('WebSocket connected')
        this.isConnected.value = true
        this.reconnectAttempts = 0
        resolve()
      }

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event)
        this.isConnected.value = false
        if (!this._manualDisconnect) {
          this.handleReconnect()
        }
      }

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnected.value = false
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

  handleMessage(message) {
    const { type, data } = message
    const handler = this.messageHandlers.get(type)

    if (handler) {
      handler(data)
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
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.isConnected.value = false
    this._manualDisconnect = false
  }

  // Vue 组合式函数
  useWebSocket() {
    onMounted(() => {
      this.connect()
    })

    onBeforeUnmount(() => {
      this.disconnect()
    })

    return {
      isConnected: this.isConnected,
      sendMessage: (message) => this.send(message),
      addMessageHandler: (type, handler) => this.addMessageHandler(type, handler),
      removeMessageHandler: (type) => this.removeMessageHandler(type)
    }
  }
}

// 创建一个全局 WebSocket 管理器实例
export const websocketManager = new WebSocketManager(
  process.env.VUE_APP_API_BASE_URL.replace('http', 'ws') + '/ws'
)
