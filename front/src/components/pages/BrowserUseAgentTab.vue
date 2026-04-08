<template>
  <div class="browser-use-agent-tab">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="chat-card">
          <el-chat :messages="chatHistory" :show-timestamp="true" height="600">
            <template slot="footer">
              <el-input
                v-model="userInput"
                placeholder="Enter your task or response..."
                type="textarea"
                :rows="3"
                @keyup.enter.native="handleInputSubmit"
              ></el-input>
              <el-row class="button-row">
                <el-button
                  :disabled="isRunning && !isWaitingForHelp"
                  type="danger"
                  @click="handleStop"
                >⏹️ Stop</el-button>
                <el-button
                  :disabled="!isRunning"
                  :type="isPaused ? 'primary' : 'warning'"
                  @click="handlePauseResume"
                >{{ isPaused ? '▶️ Resume' : '⏸️ Pause' }}</el-button>
                <el-button
                  :disabled="isRunning"
                  type="info"
                  @click="handleClear"
                >🗑️ Clear</el-button>
                <el-button
                  :disabled="!userInput.trim() || (isRunning && !isWaitingForHelp)"
                  type="primary"
                  @click="handleInputSubmit"
                >{{ isWaitingForHelp ? '✔️ Submit Response' : '▶️ Submit Task' }}</el-button>
              </el-row>
            </template>
          </el-chat>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="showBrowserView">
      <el-col :span="24">
        <el-card class="browser-view-card">
          <div slot="header" class="clearfix">
            <span>Browser Live View</span>
          </div>
          <div v-html="browserView" class="browser-view"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="taskOutputs">
      <el-col :span="24">
        <el-card class="task-outputs-card">
          <div slot="header" class="clearfix">
            <span>Task Outputs</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-link v-if="historyFile" type="primary" download :href="historyFile">📄 Download Agent History</el-link>
            </el-col>
            <el-col :span="12">
              <img v-if="recordingGif" :src="recordingGif" class="recording-gif">
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'BrowserUseAgentTab',
  data() {
    return {
      userInput: '',
      chatHistory: [],
      browserView: '',
      historyFile: '',
      recordingGif: '',
      isRunning: false,
      isPaused: false,
      isWaitingForHelp: false,
      showBrowserView: false,
      taskOutputs: false,
      currentTaskId: null
    }
  },
  methods: {
    async handleInputSubmit() {
      if (!this.userInput.trim()) {
        return
      }

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

      // 发送任务到后端
      try {
        const response = await this.$api.browserUseAgent.run({
          task: task
        })
        if (response.task_id) {
          this.currentTaskId = response.task_id
          this.chatHistory.push({
            type: 'text',
            content: task,
            timestamp: new Date(),
            position: 'right'
          })
          this.userInput = ''
          this.startMonitoring()
        }
      } catch (error) {
        this.$message.error('Failed to start agent: ' + error.message)
        this.isRunning = false
      }
    },

    async handleStop() {
      if (!this.currentTaskId) {
        return
      }
      try {
        await this.$api.browserUseAgent.stop(this.currentTaskId)
        this.isRunning = false
        this.isPaused = false
        this.isWaitingForHelp = false
      } catch (error) {
        this.$message.error('Failed to stop agent: ' + error.message)
      }
    },

    async handlePauseResume() {
      if (!this.currentTaskId) {
        return
      }

      try {
        if (this.isPaused) {
          await this.$api.browserUseAgent.resume(this.currentTaskId)
          this.isPaused = false
        } else {
          await this.$api.browserUseAgent.pause(this.currentTaskId)
          this.isPaused = true
        }
      } catch (error) {
        this.$message.error('Failed to pause/resume agent: ' + error.message)
      }
    },

    async handleClear() {
      this.userInput = ''
      this.chatHistory = []
      this.browserView = ''
      this.historyFile = ''
      this.recordingGif = ''
      this.isRunning = false
      this.isPaused = false
      this.isWaitingForHelp = false
      this.showBrowserView = false
      this.taskOutputs = false
      this.currentTaskId = null
    },

    async handleUserHelp(response) {
      try {
        await this.$api.browserUseAgent.respond({
          task_id: this.currentTaskId,
          message: response
        })
        this.isWaitingForHelp = false
        this.userInput = ''
      } catch (error) {
        this.$message.error('Failed to send response: ' + error.message)
      }
    },

    async startMonitoring() {
      while (this.isRunning) {
        try {
          const status = await this.$api.browserUseAgent.getStatus(this.currentTaskId)
          if (status) {
            this.updateChatHistory(status.chat_history)
            this.updateBrowserView(status.browser_view)

            if (status.is_waiting_for_help) {
              this.isWaitingForHelp = true
            }

            if (status.task_outputs) {
              this.taskOutputs = true
              this.historyFile = status.history_file
              this.recordingGif = status.recording_gif
            }

            if (!status.is_running) {
              this.isRunning = false
              this.isPaused = false
              this.isWaitingForHelp = false
              break
            }
          }
        } catch (error) {
          console.error('Monitoring error:', error)
        }
        await this.sleep(1000)
      }
    },

    updateChatHistory(messages) {
      if (messages && messages.length > this.chatHistory.length) {
        this.chatHistory = messages
      }
    },

    updateBrowserView(view) {
      if (view) {
        this.browserView = view
        this.showBrowserView = true
      }
    },

    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }
  }
}
</script>

<style scoped>
.browser-use-agent-tab {
  padding: 20px;
}

.chat-card {
  margin-bottom: 20px;
}

.browser-view-card {
  margin-bottom: 20px;
}

.browser-view {
  width: 100%;
  height: 500px;
  border: 1px solid #ebeef5;
  overflow: auto;
  background: #fff;
}

.task-outputs-card {
  margin-bottom: 20px;
}

.button-row {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.recording-gif {
  max-width: 100%;
  height: auto;
}
</style>