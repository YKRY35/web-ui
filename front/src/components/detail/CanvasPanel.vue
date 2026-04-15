<template>
  <div class="canvas-wrapper">
    <div class="control-bar">
      <div class="control-item">
        <span class="control-label">Quality:</span>
        <el-slider
          v-model="quality"
          :min="10"
          :max="100"
          :step="5"
          :disabled="!isConnected"
          @change="handleQualityChange"
          style="width: 120px; margin-left: 8px;"
        />
        <span class="control-value">{{ quality }}%</span>
      </div>
      <div class="control-item">
        <span class="control-label">FPS:</span>
        <span class="fps-value" :class="{ 'fps-good': fps > 20, 'fps-medium': fps > 10 && fps <= 20, 'fps-low': fps > 0 && fps <= 10, 'fps-idle': fps === 0 }">
          {{ fps }}
          <el-tooltip v-if="fps === 0" content="Page is idle (no changes)" placement="top">
            <i class="el-icon-info" style="font-size: 12px; color: #909399;"></i>
          </el-tooltip>
        </span>
      </div>
      <div class="control-item">
        <span class="control-label">Total:</span>
        <span class="control-value">{{ totalFrames }} frames</span>
      </div>
      <div class="connection-status">
        <el-tag :type="isConnected ? 'success' : 'info'" size="mini">
          {{ isConnecting ? 'Connecting...' : isConnected ? 'Connected' : 'Disconnected' }}
        </el-tag>
      </div>
    </div>
    <div class="canvas-container">
      <canvas ref="canvas" class="main-canvas"></canvas>
      <div v-if="!isConnected" class="canvas-placeholder">
        {{ isConnecting ? 'Connecting...' : 'Waiting for stream...' }}
      </div>
    </div>
  </div>
</template>

<script>
import { screencastClient } from '@/utils/screencast'

export default {
  name: 'CanvasPanel',
  data() {
    return {
      isConnected: false,
      isConnecting: false,
      quality: 100, // 默认质量 100%（最佳画质）
      fps: 0, // 当前帧率
      totalFrames: 0, // 总帧数统计
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.resizeCanvas()
      screencastClient.setCanvas(this.$refs.canvas)
      screencastClient.onConnected = () => {
        this.isConnected = true
        this.isConnecting = false
        // 连接成功后应用当前质量设置
        this.applyQuality()
      }
      screencastClient.onDisconnected = () => {
        this.isConnected = false
      }
      screencastClient.onFPSUpdate = (fps) => {
        this.fps = fps
      }
      screencastClient.onTotalFramesUpdate = (total) => {
        this.totalFrames = total
      }
      this.isConnecting = true
      screencastClient.connect()
    })
    this._obs = new ResizeObserver(this.resizeCanvas)
    this._obs.observe(this.$el)
  },
  beforeDestroy() {
    if (this._obs) this._obs.disconnect()
    screencastClient.disconnect()
  },
  methods: {
    resizeCanvas() {
      const c = this.$refs.canvas
      if (!c) return
      const container = this.$el.querySelector('.canvas-container')
      if (!container) return
      c.width = container.clientWidth
      c.height = container.clientHeight

      // resize 后重新绘制缓存的最后一帧，避免白屏
      if (this.isConnected) {
        screencastClient.redrawLastFrame()
      }
    },
    handleQualityChange(value) {
      this.quality = value
      if (this.isConnected) {
        this.applyQuality()
      }
    },
    applyQuality() {
      screencastClient.setQuality(this.quality)
    },
  },
}
</script>

<style scoped>
.canvas-wrapper {
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  position: relative;
  display: flex;
  flex-direction: column;
}

.control-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  gap: 24px;
  flex-shrink: 0;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.control-value {
  font-size: 13px;
  color: #909399;
  min-width: 35px;
}

.fps-value {
  font-size: 16px;
  font-weight: bold;
  font-family: 'Courier New', monospace;
  min-width: 30px;
  text-align: center;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.fps-good {
  color: #67c23a;
}

.fps-medium {
  color: #e6a23c;
}

.fps-low {
  color: #f56c6c;
}

.fps-idle {
  color: #909399;
}

.connection-status {
  margin-left: auto;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.main-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #c0c4cc;
  font-size: 14px;
  pointer-events: none;
}

/* Dark theme styles for CanvasPanel */
#app.dark .canvas-wrapper {
  background: #1a1a1a;
}

#app.dark .control-bar {
  background: #2d2d2d;
  border-bottom-color: #3d3d3d;
}

#app.dark .control-label {
  color: #b0b0b0;
}

#app.dark .control-value {
  color: #909399;
}

#app.dark .canvas-placeholder {
  color: #606266;
}
</style>
