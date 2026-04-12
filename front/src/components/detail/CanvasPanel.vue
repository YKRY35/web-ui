<template>
  <div class="canvas-wrapper">
    <canvas ref="canvas" class="main-canvas"></canvas>
    <div v-if="!isConnected" class="canvas-placeholder">
      {{ isConnecting ? 'Connecting...' : 'Waiting for stream...' }}
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
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.resizeCanvas()
      screencastClient.setCanvas(this.$refs.canvas)
      screencastClient.onConnected = () => {
        this.isConnected = true
        this.isConnecting = false
      }
      screencastClient.onDisconnected = () => {
        this.isConnected = false
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
      c.width = this.$el.clientWidth
      c.height = this.$el.clientHeight
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
</style>
