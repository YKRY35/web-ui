<template>
  <div class="browser-canvas-container">
    <div class="canvas-header">
      <span class="status-dot" :class="{ active: hasFrame }"></span>
      <span class="status-text">{{ hasFrame ? 'Live' : 'Waiting for stream...' }}</span>
      <span v-if="frameInfo" class="frame-info">
        {{ frameInfo.fps }} FPS
      </span>
    </div>
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas
        ref="browserCanvas"
        class="browser-canvas"
        :class="{ 'pixelated': pixelated }"
      ></canvas>
      <div v-if="!hasFrame" class="placeholder">
        <i class="el-icon-video-camera"></i>
        <p>Browser stream will appear here</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BrowserCanvas',
  props: {
    /**
     * 像素化渲染（提高性能，降低质量）
     * Pixelated rendering (faster, lower quality)
     */
    pixelated: {
      type: Boolean,
      default: false
    },
    /**
     * 最大画布宽度（像素）
     * Max canvas width in pixels
     */
    maxWidth: {
      type: Number,
      default: 1280
    },
    /**
     * 最大画布高度（像素）
     * Max canvas height in pixels
     */
    maxHeight: {
      type: Number,
      default: 720
    }
  },
  data() {
    return {
      hasFrame: false,
      frameInfo: null,
      currentImage: null,
      canvasContext: null,
      animationFrameId: null,
      imageLoader: null,
      lastFrameTime: 0,
      frameCount: 0,
      fpsWindowStart: 0,
      fpsWindowFrames: 0
    }
  },
  mounted() {
    this.initCanvas()
    this.startFpsCounter()
  },
  beforeDestroy() {
    this.cleanup()
  },
  methods: {
    /**
     * 初始化 Canvas
     * Initialize Canvas
     */
    initCanvas() {
      const canvas = this.$refs.browserCanvas
      const wrapper = this.$refs.canvasWrapper

      // 设置初始尺寸
      canvas.width = this.maxWidth
      canvas.height = this.maxHeight

      // 获取 2D 上下文
      this.canvasContext = canvas.getContext('2d', {
        alpha: false,  // 禁用 alpha 通道提高性能
        desynchronized: true  // 启用不同步渲染
      })

      // 填充初始黑色背景
      this.canvasContext.fillStyle = '#1a1a1a'
      this.canvasContext.fillRect(0, 0, canvas.width, canvas.height)

      // 监听容器尺寸变化
      this.resizeObserver = new ResizeObserver(() => {
        this.adjustCanvasSize()
      })
      this.resizeObserver.observe(wrapper)
    },

    /**
     * 调整画布尺寸以适应容器
     * Adjust canvas size to fit container
     */
    adjustCanvasSize() {
      const canvas = this.$refs.browserCanvas
      const wrapper = this.$refs.canvasWrapper

      if (!canvas || !wrapper) return

      const rect = wrapper.getBoundingClientRect()

      // 计算保持宽高比的缩放
      const aspectRatio = 16 / 9  // 默认宽高比
      let width = Math.min(rect.width, this.maxWidth)
      let height = width / aspectRatio

      if (height > this.maxHeight) {
        height = this.maxHeight
        width = height * aspectRatio
      }

      // 设置 CSS 尺寸（显示尺寸）
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
    },

    /**
     * 更新画布帧（从 base64 图像数据）
     * Update canvas frame from base64 image data
     * @param {string} base64Image - base64 编码的图像数据
     */
    updateFrame(base64Image) {
      console.log('BrowserCanvas.updateFrame called:', {
        hasImage: !!base64Image,
        imageLength: base64Image ? base64Image.length : 0,
        hasCanvasContext: !!this.canvasContext,
        canvasElement: this.$refs.browserCanvas || 'undefined',
        canvasContext: this.canvasContext || 'undefined'
      })

      if (!base64Image) {
        console.warn('BrowserCanvas: No image data provided')
        return
      }

      if (!this.canvasContext) {
        console.warn('BrowserCanvas: Canvas context not initialized')
        // 尝试重新初始化
        this.initCanvas()
        if (!this.canvasContext) {
          console.error('BrowserCanvas: Failed to initialize canvas context')
          return
        }
      }

      // 创建图像加载器
      if (!this.imageLoader) {
        this.imageLoader = new Image()
        this.imageLoader.onload = () => {
          console.log('BrowserCanvas: Image loaded, natural dimensions:', this.imageLoader.naturalWidth, 'x', this.imageLoader.naturalHeight)
          this.scheduleRender(this.imageLoader)
        }
        this.imageLoader.onerror = (err) => {
          console.warn('BrowserCanvas: Failed to load frame:', err)
        }
      }

      // 更新图像源（使用数据 URL）
      const dataUrl = `data:image/jpeg;base64,${base64Image}`
      console.log('BrowserCanvas: Setting image src, dataUrl length:', dataUrl.length)
      this.imageLoader.src = dataUrl
    },

    /**
     * 调度渲染到下一帧
     * Schedule render to next animation frame
     * @param {HTMLImageElement} image - 要渲染的图像
     */
    scheduleRender(image) {
      // 取消上一个调度的帧
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId)
      }

      // 调度新帧
      this.animationFrameId = requestAnimationFrame(() => {
        this.renderFrame(image)
      })
    },

    /**
     * 渲染图像到画布
     * Render image to canvas
     * @param {HTMLImageElement} image - 要渲染的图像
     */
    renderFrame(image) {
      const canvas = this.$refs.browserCanvas
      const ctx = this.canvasContext

      if (!canvas || !ctx) {
        console.warn('BrowserCanvas: No canvas or context available')
        return
      }

      console.log('BrowserCanvas.renderFrame called, image:', image)

      try {
        // 设置画布实际像素尺寸（如果与图像尺寸匹配）
        if (canvas.width !== image.naturalWidth || canvas.height !== image.naturalHeight) {
          canvas.width = Math.min(image.naturalWidth, this.maxWidth)
          canvas.height = Math.min(image.naturalHeight, this.maxHeight)
          console.log('BrowserCanvas: Canvas dimensions updated:', canvas.width, 'x', canvas.height)
        }

        // 计算缩放比例以保持宽高比
        const scaleX = canvas.width / image.naturalWidth
        const scaleY = canvas.height / image.naturalHeight
        const scale = Math.min(scaleX, scaleY)

        const drawWidth = image.naturalWidth * scale
        const drawHeight = image.naturalHeight * scale
        const drawX = (canvas.width - drawWidth) / 2
        const drawY = (canvas.height - drawHeight) / 2

        console.log('BrowserCanvas: Drawing frame at:', drawX, drawY, 'size:', drawWidth, 'x', drawHeight)

        // 清除画布
        ctx.fillStyle = '#000'
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        // 绘制图像（禁用平滑以提高性能）
        ctx.imageSmoothingEnabled = !this.pixelated
        ctx.drawImage(image, drawX, drawY, drawWidth, drawHeight)

        // 更新状态
        this.hasFrame = true
        this.updateFpsCounter()

        console.log('BrowserCanvas: Frame rendered successfully')
      } catch (e) {
        console.warn('BrowserCanvas: Render error:', e)
      }
    },

    /**
     * 启动 FPS 计数器
     * Start FPS counter
     */
    startFpsCounter() {
      this.fpsWindowStart = performance.now()
      this.fpsWindowFrames = 0
      this.frameInfo = { fps: 0 }
    },

    /**
     * 更新 FPS 计数
     * Update FPS counter
     */
    updateFpsCounter() {
      const now = performance.now()
      this.fpsWindowFrames++

      // 每秒更新一次 FPS 显示
      if (now - this.fpsWindowStart >= 1000) {
        const fps = Math.round(this.fpsWindowFrames * 1000 / (now - this.fpsWindowStart))
        this.frameInfo = { fps }
        this.fpsWindowStart = now
        this.fpsWindowFrames = 0
      }
    },

    /**
     * 清理资源
     * Cleanup resources
     */
    cleanup() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId)
        this.animationFrameId = null
      }

      if (this.resizeObserver) {
        this.resizeObserver.disconnect()
        this.resizeObserver = null
      }

      this.canvasContext = null
      this.imageLoader = null
    },

    /**
     * 清除画布显示
     * Clear canvas display
     */
    clear() {
      this.hasFrame = false
      this.frameInfo = null

      if (this.canvasContext) {
        const canvas = this.$refs.browserCanvas
        this.canvasContext.fillStyle = '#1a1a1a'
        this.canvasContext.fillRect(0, 0, canvas.width, canvas.height)
      }
    }
  }
}
</script>

<style scoped>
.browser-canvas-container {
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  border-radius: 4px;
  overflow: hidden;
}

.canvas-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #2d2d2d;
  border-bottom: 1px solid #404040;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
  transition: background-color 0.3s;
}

.status-dot.active {
  background: #67c23a;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 12px;
  color: #999;
  flex: 1;
}

.frame-info {
  font-size: 12px;
  color: #67c23a;
  font-family: 'Courier New', monospace;
}

.canvas-wrapper {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: #000;
}

.browser-canvas {
  display: block;
  max-width: 100%;
  max-height: 100%;
}

.browser-canvas.pixelated {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

.placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  pointer-events: none;
}

.placeholder i {
  font-size: 48px;
  margin-bottom: 16px;
}

.placeholder p {
  font-size: 14px;
  margin: 0;
}
</style>
