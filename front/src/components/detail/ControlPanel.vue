<template>
  <div class="control-panel-inner">
    <div v-if="isRunning" class="status-bar">
      <i class="el-icon-loading"></i>
      <span>{{ isWaitingForHelp ? 'Waiting for your response...' : isPaused ? 'Paused' : 'Running...' }}</span>
    </div>
    <el-input
      v-model="userInput"
      placeholder="打开百度，搜索金价"
      type="textarea"
      :autosize="{ minRows: 4, maxRows: 10 }"
      @keyup.ctrl.enter.native="handleInputSubmit"
      :disabled="isRunning && !isWaitingForHelp"
      class="task-input"
    ></el-input>
    <div class="btn-row">
      <el-button size="small" :disabled="!isRunning" type="danger" @click="handleStop">⏹ Stop</el-button>
      <el-button size="small" :disabled="!isRunning" :type="isPaused ? 'primary' : 'warning'" @click="handlePauseResume">
        {{ isPaused ? '▶ Resume' : '⏸ Pause' }}
      </el-button>
      <el-button size="small" :disabled="isRunning" type="info" @click="handleClear">🗑 Clear</el-button>
      <el-button
        size="small"
        :disabled="!userInput.trim() || (isRunning && !isWaitingForHelp)"
        type="primary"
        @click="handleInputSubmit"
      >{{ isWaitingForHelp ? '✔ Submit Response' : '▶ Submit Task' }}</el-button>
    </div>
  </div>
</template>

<script>
import bus from './bus'

export default {
  name: 'ControlPanel',
  data() {
    return {
      userInput: '',
      isRunning: false,
      isPaused: false,
      isWaitingForHelp: false,
      currentTaskId: null
    }
  },
  methods: {
    async handleInputSubmit() {
      if (!this.userInput.trim()) return
      if (this.isWaitingForHelp) {
        await this.handleUserHelp(this.userInput)
      } else {
        await this.handleRunTask(this.userInput)
      }
    },
    async handleRunTask(task) {
      this.isRunning = true
      this.isWaitingForHelp = false
      this.currentTaskId = Date.now().toString()
      bus.$emit('step-added', { id: Date.now(), type: 'user', content: task, timestamp: new Date(), status: 'running' })
      console.log('Emitted step-added event:', { id: Date.now(), type: 'user', content: task, timestamp: new Date(), status: 'running' })
      try {
        const response = await this.$api.browserUseAgent.run({ task })
        if (response && response.task_id) this.currentTaskId = response.task_id
        this.userInput = ''
        this.startMonitoring()
      } catch (error) {
        this.isRunning = false
        bus.$emit('step-added', { id: Date.now(), type: 'error', content: `Error: ${error.message}`, timestamp: new Date(), status: 'error' })
        console.log('Emitted step-added error event:', { id: Date.now(), type: 'error', content: `Error: ${error.message}`, timestamp: new Date(), status: 'error' })
      }
    },
    async handleStop() {
      if (!this.currentTaskId) return
      try { await this.$api.browserUseAgent.stop(this.currentTaskId) } catch (e) { /* ignore */ }
      this.isRunning = false
      this.isPaused = false
      this.isWaitingForHelp = false
    },
    async handlePauseResume() {
      if (!this.currentTaskId) return
      try {
        if (this.isPaused) {
          await this.$api.browserUseAgent.resume(this.currentTaskId)
          this.isPaused = false
        } else {
          await this.$api.browserUseAgent.pause(this.currentTaskId)
          this.isPaused = true
        }
      } catch (e) { console.error(e) }
    },
    handleClear() {
      this.userInput = ''
      this.isRunning = false
      this.isPaused = false
      this.isWaitingForHelp = false
      this.currentTaskId = null
      bus.$emit('steps-cleared')
    },
    async handleUserHelp(msg) {
      try {
        await this.$api.browserUseAgent.respond({ task_id: this.currentTaskId, message: msg })
        this.isWaitingForHelp = false
        this.userInput = ''
      } catch (e) { console.error(e) }
    },
    async startMonitoring() {
      while (this.isRunning) {
        try {
          const status = await this.$api.browserUseAgent.getStatus(this.currentTaskId)
          if (status) {
            if (status.chat_history) {
              bus.$emit('steps-updated', status.chat_history)
              console.log('Emitted steps-updated event:', status.chat_history)
            }
            if (status.is_waiting_for_help) this.isWaitingForHelp = true
            if (!status.is_running) {
              this.isRunning = false
              this.isPaused = false
              this.isWaitingForHelp = false
              break
            }
          }
        } catch (e) { console.error('monitor error', e) }
        await new Promise(r => setTimeout(r, 1000))
      }
    }
  }
}
</script>

<style scoped>
.control-panel-inner {
  padding: 12px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fff;
}
.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  color: #409EFF;
  font-size: 13px;
}
.task-input {
  flex: 1;
}
.task-input >>> .el-textarea__inner {
  resize: none;
  font-size: 14px;
  line-height: 1.6;
}
.btn-row {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
  padding-bottom: 4px;
}
</style>
