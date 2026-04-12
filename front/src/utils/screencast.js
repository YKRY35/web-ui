/**
 * ScreencastClient - 高性能浏览器画面流客户端
 *
 * 使用二进制 WebSocket 接收原始 JPEG 帧，通过 createImageBitmap + requestAnimationFrame
 * 渲染到 canvas，实现最低延迟的画面流传输。
 *
 * 性能设计：
 * - binaryType='arraybuffer'：避免 Blob 分配
 * - createImageBitmap：在浏览器内部 worker 异步解码 JPEG，不阻塞主线程
 * - 单槽位帧队列（latest-wins）：高帧率时自动丢弃中间帧，无内存积压
 * - bm.close()：drawImage 后立即释放 GPU 纹理内存
 */
export class ScreencastClient {
  constructor(url) {
    this.url = url
    this.socket = null
    this._manualDisconnect = false
    this.reconnectTimer = null
    this.reconnectAttempts = 0

    // 单槽位帧队列
    this._pendingBitmap = null
    this._rafId = null
    this._canvas = null
    this._ctx = null

    // 状态回调
    this.onConnected = null
    this.onDisconnected = null
  }

  setCanvas(canvasEl) {
    this._canvas = canvasEl
    this._ctx = canvasEl.getContext('2d')
  }

  connect() {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    this.socket = new WebSocket(this.url)
    this.socket.binaryType = 'arraybuffer' // 关键：直接获取 ArrayBuffer，避免 Blob 开销

    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this._startRenderLoop()
      if (this.onConnected) this.onConnected()
    }

    this.socket.onclose = () => {
      this._stopRenderLoop()
      if (this.onDisconnected) this.onDisconnected()
      if (!this._manualDisconnect) this._scheduleReconnect()
    }

    this.socket.onerror = () => {
      // onclose 会在 onerror 后触发，由 onclose 处理重连
    }

    this.socket.onmessage = (event) => {
      // event.data 是 ArrayBuffer（原始 JPEG 字节）
      const blob = new Blob([event.data], { type: 'image/jpeg' })
      createImageBitmap(blob)
        .then((bitmap) => {
          // 丢弃上一帧（latest-wins 策略）
          if (this._pendingBitmap) this._pendingBitmap.close()
          this._pendingBitmap = bitmap
        })
        .catch(() => {}) // 忽略损坏帧
    }
  }

  _startRenderLoop() {
    if (this._rafId !== null) return
    const loop = () => {
      if (this._pendingBitmap && this._ctx && this._canvas) {
        const bm = this._pendingBitmap
        this._pendingBitmap = null
        this._ctx.drawImage(bm, 0, 0, this._canvas.width, this._canvas.height)
        bm.close() // 立即释放 GPU 纹理内存
      }
      this._rafId = requestAnimationFrame(loop)
    }
    this._rafId = requestAnimationFrame(loop)
  }

  _stopRenderLoop() {
    if (this._rafId !== null) {
      cancelAnimationFrame(this._rafId)
      this._rafId = null
    }
    if (this._pendingBitmap) {
      this._pendingBitmap.close()
      this._pendingBitmap = null
    }
  }

  _scheduleReconnect() {
    if (this.reconnectTimer) return
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 10000)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }

  disconnect() {
    this._manualDisconnect = true
    this._stopRenderLoop()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this._manualDisconnect = false
  }
}

export const screencastClient = new ScreencastClient(
  process.env.VUE_APP_API_BASE_URL.replace('http', 'ws') + '/ws/screen'
)
