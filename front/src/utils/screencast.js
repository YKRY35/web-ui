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
 * - FPS 统计：实时计算并报告帧率
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

    // 缓存最后一帧，用于 resize 时重新绘制
    this._lastBitmap = null
    this._lastBitmapData = null // 保存 bitmap 的原始数据，用于重建

    // 帧率统计
    this._frameCount = 0
    this._lastFpsUpdate = 0
    this._currentFps = 0
    this._totalFrames = 0

    // 质量控制
    this._quality = 70

    // 状态回调
    this.onConnected = null
    this.onDisconnected = null
    this.onFPSUpdate = null
    this.onTotalFramesUpdate = null
  }

  setCanvas(canvasEl) {
    this._canvas = canvasEl
    this._ctx = canvasEl.getContext('2d')
  }

  setQuality(quality) {
    this._quality = quality
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'quality',
        quality: quality
      }))
    }
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
      this._startFPSCounter()
      if (this.onConnected) this.onConnected()
    }

    this.socket.onclose = () => {
      this._stopRenderLoop()
      this._stopFPSCounter()
      if (this.onDisconnected) this.onDisconnected()
      if (!this._manualDisconnect) this._scheduleReconnect()
    }

    this.socket.onerror = () => {
      // onclose 会在 onerror 后触发，由 onclose 处理重连
    }

    this.socket.onmessage = (event) => {
      // 如果是二进制数据（PNG/JPEG 帧）
      if (event.data instanceof ArrayBuffer) {
        // event.data 是 ArrayBuffer（原始图片字节）
        // 根据文件头判断格式（PNG: 89 50 4E 47, JPEG: FF D8 FF）
        const view = new Uint8Array(event.data, 0, 4)
        const isPNG = view[0] === 0x89 && view[1] === 0x50 && view[2] === 0x4E && view[3] === 0x47
        const mimeType = isPNG ? 'image/png' : 'image/jpeg'
        const blob = new Blob([event.data], { type: mimeType })
        createImageBitmap(blob)
          .then((bitmap) => {
            // 丢弃上一帧（latest-wins 策略）
            if (this._pendingBitmap) this._pendingBitmap.close()
            this._pendingBitmap = bitmap
            this._frameCount++ // 帧计数
            this._totalFrames++ // 总帧数统计
            if (this.onTotalFramesUpdate) {
              this.onTotalFramesUpdate(this._totalFrames)
            }
          })
          .catch(() => {}) // 忽略损坏帧
      }
      // 如果是文本数据（JSON 消息，如确认消息等）
      else if (typeof event.data === 'string') {
        // 可以处理服务端的响应消息
        try {
          const msg = JSON.parse(event.data)
          // console.log('Screencast message:', msg)
        } catch (e) {
          // 忽略无效 JSON
        }
      }
    }
  }

  _startFPSCounter() {
    this._lastFpsUpdate = performance.now()
    this._frameCount = 0
    this._totalFrames = 0
    this._fpsIntervalId = setInterval(() => {
      const now = performance.now()
      const elapsed = (now - this._lastFpsUpdate) / 1000 // 秒
      this._currentFps = Math.round(this._frameCount / elapsed)
      this._frameCount = 0
      this._lastFpsUpdate = now
      if (this.onFPSUpdate) {
        this.onFPSUpdate(this._currentFps)
      }
    }, 1000) // 每秒更新一次
  }

  _stopFPSCounter() {
    if (this._fpsIntervalId) {
      clearInterval(this._fpsIntervalId)
      this._fpsIntervalId = null
    }
  }

  _startRenderLoop() {
    if (this._rafId !== null) return
    const loop = () => {
      // 如果有新帧，更新缓存并绘制
      if (this._pendingBitmap && this._ctx && this._canvas) {
        const bm = this._pendingBitmap
        this._pendingBitmap = null

        // 释放旧的缓存帧
        if (this._lastBitmap) {
          this._lastBitmap.close()
        }

        // 缓存当前帧（创建副本）
        this._lastBitmap = bm

        // 绘制当前帧
        this._drawBitmap(bm)
      }
      // 如果没有新帧但有缓存的帧，保持显示（不重绘）
      // 这样可以避免白屏

      this._rafId = requestAnimationFrame(loop)
    }
    this._rafId = requestAnimationFrame(loop)
  }

  /**
   * 绘制 bitmap 到 canvas
   * @param {ImageBitmap} bm - 要绘制的 bitmap
   */
  _drawBitmap(bm) {
    if (!bm || !this._ctx || !this._canvas) return

    // 计算保持长宽比的绘制区域
    const canvasWidth = this._canvas.width
    const canvasHeight = this._canvas.height
    const bitmapWidth = bm.width
    const bitmapHeight = bm.height

    // 计算缩放比例（保持长宽比）
    const scale = Math.min(canvasWidth / bitmapWidth, canvasHeight / bitmapHeight)
    const destWidth = bitmapWidth * scale
    const destHeight = bitmapHeight * scale

    // 计算居中偏移
    const destX = (canvasWidth - destWidth) / 2
    const destY = (canvasHeight - destHeight) / 2

    // 先用灰色填充整个 canvas
    this._ctx.fillStyle = '#f5f7fa'
    this._ctx.fillRect(0, 0, canvasWidth, canvasHeight)

    // 绘制图像（保持长宽比，居中显示）
    this._ctx.drawImage(bm, destX, destY, destWidth, destHeight)
  }

  /**
   * 重新绘制缓存的最后一帧（用于 resize）
   */
  redrawLastFrame() {
    if (this._lastBitmap && this._ctx && this._canvas) {
      this._drawBitmap(this._lastBitmap)
    }
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
    // 清理缓存的最后一帧
    if (this._lastBitmap) {
      this._lastBitmap.close()
      this._lastBitmap = null
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
    this._stopFPSCounter()
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
