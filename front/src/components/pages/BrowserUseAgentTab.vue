<template>
  <div class="browser-use-agent-tab">
    <!-- 信息面板区域 -->
    <el-row :gutter="20" v-if="isRunning">
      <el-col :span="8">
        <el-card class="info-panel browser-panel">
          <div slot="header" class="clearfix">
            <span>Browser Information</span>
          </div>
          <div class="info-content">
            <p v-if="browserInfo.browserType">{{ browserInfo.browserType }}</p>
            <p v-if="browserInfo.browserStatus">{{ browserInfo.browserStatus }}</p>
            <p v-if="browserInfo.connectionType">{{ browserInfo.connectionType }}</p>
            <p v-if="browserInfo.windowSize">{{ browserInfo.windowSize }}</p>
            <p v-if="browserInfo.currentUrl">{{ browserInfo.currentUrl }}</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="info-panel model-panel">
          <div slot="header" class="clearfix">
            <span>Model Information</span>
          </div>
          <div class="info-content">
            <p v-if="modelInfo.llmName">{{ modelInfo.llmName }}</p>
            <p v-if="modelInfo.modelName">{{ modelInfo.modelName }}</p>
            <p v-if="modelInfo.temperature">{{ modelInfo.temperature }}</p>
            <p v-if="modelInfo.tokenUsage">{{ modelInfo.tokenUsage }}</p>
            <p v-if="modelInfo.avgTokensPerStep">{{ modelInfo.avgTokensPerStep }}</p>
            <p v-if="modelInfo.totalDuration">{{ modelInfo.totalDuration }}</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="info-panel tasks-panel">
          <div slot="header" class="clearfix">
            <span>Task Information</span>
          </div>
          <div class="info-content">
            <p v-if="taskInfo.currentTask">{{ taskInfo.currentTask }}</p>
            <p v-if="taskInfo.currentStep">{{ taskInfo.currentStep }}</p>
            <p v-if="taskInfo.stepStatus">{{ taskInfo.stepStatus }}</p>
            <p v-if="taskInfo.goal">{{ taskInfo.goal }}</p>
            <p v-if="taskInfo.lastError" class="error-text">{{ taskInfo.lastError }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 聊天历史记录 -->
    <el-card class="chat-card">
      <div slot="header" class="clearfix">
        <span>Chat History</span>
      </div>
      <div class="chat-history" ref="chatHistory">
        <div
          v-for="(msg, index) in chatHistory"
          :key="index"
          :class="['chat-message', msg.position]"
        >
          <div class="message-content">
            <div class="message-text">{{ msg.content }}</div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          </div>
          <div class="message-avatar">{{ msg.position === 'right' ? 'You' : 'AI' }}</div>
        </div>
        <div v-if="isWaitingForHelp" class="waiting-indicator">
          <i class="el-icon-loading"></i> AI is waiting for your help...
        </div>
        <div v-if="isRunning && !isWaitingForHelp" class="running-indicator">
          <i class="el-icon-loading"></i> AI is thinking...
        </div>
      </div>
    </el-card>

    <!-- 浏览器实时视图 -->
    <el-card v-show="showBrowserView" class="browser-view-card">
      <div slot="header" class="clearfix">
        <span>Browser Live View</span>
      </div>
      <browser-canvas
        ref="browserCanvas"
        :pixelated="true"
        :max-width="1280"
        :max-height="720"
      ></browser-canvas>
    </el-card>

    <!-- 任务输出 -->
    <el-card v-if="taskOutputs" class="task-outputs-card">
      <div slot="header" class="clearfix">
        <span>Task Outputs</span>
      </div>
      <el-row :gutter="20">
        <el-col :span="12">
          <a v-if="historyFile" :href="historyFile" :download="getHistoryFileName()" class="download-link">
            📄 Download Agent History
          </a>
        </el-col>
        <el-col :span="12">
          <img v-if="recordingGif" :src="recordingGif" class="recording-gif">
        </el-col>
      </el-row>
    </el-card>

    <!-- 输入区域 -->
    <el-card class="input-card">
      <el-input
        v-model="userInput"
        placeholder="Enter your task or response..."
        type="textarea"
        :rows="3"
        @keyup.enter.native="handleInputSubmit"
        :disabled="isRunning && !isWaitingForHelp"
      ></el-input>
      <el-row class="button-row">
        <el-button
          :disabled="!isRunning"
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
    </el-card>
  </div>
</template>

<script>
import BrowserCanvas from '@/components/common/BrowserCanvas.vue'

export default {
  name: 'BrowserUseAgentTab',
  components: {
    BrowserCanvas
  },
  created() {
    // 添加 WebSocket 帧消息监听
    this.setupWebSocketListeners()
  },
  beforeDestroy() {
    // 移除监听器
    if (this.$websocket) {
      this.$websocket.removeMessageHandler('frame')
    }
  },
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
      showBrowserView: true,  // 始终显示，使用 v-show 控制可见性
      taskOutputs: false,
      currentTaskId: null,
      // 信息面板数据
      browserInfo: {
        browserType: '',
        browserStatus: '',
        connectionType: '',
        windowSize: '',
        currentUrl: ''
      },
      modelInfo: {
        llmName: '',
        modelName: '',
        temperature: '',
        tokenUsage: '',
        avgTokensPerStep: '',
        totalDuration: ''
      },
      taskInfo: {
        currentTask: '',
        currentStep: '',
        stepStatus: '',
        goal: '',
        lastError: ''
      }
    }
  },
  methods: {
    // 格式化时间
    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString()
    },
    // 设置 WebSocket 监听器
    setupWebSocketListeners() {
      console.log('🔧 Setting up WebSocket listeners')

      // 获取 WebSocket 管理器（使用全局注册的 $websocket）
      const wsManager = this.$websocket
      console.log('🔧 WebSocket manager:', wsManager)

      // 监听 frame 类型消息
      const frameHandler = (data) => {
        console.log('WebSocket frame received:', {
          hasImage: !!data.image,
          imageLength: data.image ? data.image.length : 0,
          frameCount: data.frame_count,
          showBrowserView: this.showBrowserView,
          canvasRefExists: !!this.$refs.browserCanvas
        })

        // 确保浏览器视图已经显示
        if (!this.showBrowserView) {
          this.showBrowserView = true
        }

        // 获取 canvas 组件引用并更新帧
        const canvasComponent = this.$refs.browserCanvas
        console.log('Canvas component details:', {
          component: canvasComponent,
          hasUpdateFrame: canvasComponent && typeof canvasComponent.updateFrame === 'function'
        })

        if (canvasComponent && data.image) {
          canvasComponent.updateFrame(data.image)
        } else {
          if (!canvasComponent) {
            console.warn('Canvas component not found in DOM')
          }
          if (!data.image) {
            console.warn('No image data in frame message')
          }
        }
      }

      wsManager.addMessageHandler('frame', frameHandler)
      console.log('🔧 Frame handler added, current handlers:', Array.from(wsManager.messageHandlers.keys()))

      // 监听 status 消息以响应任务状态
      wsManager.addMessageHandler('status', (data) => {
        if (!data.is_running) {
          this.showBrowserView = false
        }
      })

      console.log('🔧 WebSocket listeners setup complete')
    },
    // 获取历史文件名
    getHistoryFileName() {
      const timestamp = new Date().toISOString().split('T')[0]
      return `agent-history-${timestamp}.json`
    },
    // 处理输入提交
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
    // 处理运行任务
    async handleRunTask(task) {
      this.isRunning = true
      this.isWaitingForHelp = false
      this.currentTaskId = Date.now().toString()
      this.showBrowserView = true // 任务开始时立即显示浏览器视图

      // 初始化信息面板
      this.taskInfo.currentTask = task
      this.taskInfo.currentStep = 'Step 1'
      this.taskInfo.stepStatus = 'Initializing...'

      // 添加用户输入到聊天历史
      this.chatHistory.push({
        type: 'text',
        content: task,
        timestamp: new Date(),
        position: 'right'
      })

      try {
        // 发送任务到后端
        const response = await this.$api.browserUseAgent.run({
          task: task
        })
        if (response.task_id) {
          this.currentTaskId = response.task_id
          this.userInput = ''
          // 开始监控任务状态
          this.startMonitoring()
        }
      } catch (error) {
        console.error('Failed to run task:', error)
        this.isRunning = false
        this.taskInfo.lastError = `Error: ${error.message}`
        this.chatHistory.push({
          type: 'text',
          content: `Error: ${error.message}`,
          timestamp: new Date(),
          position: 'left'
        })
      }
    },
    // 处理停止任务
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
        console.error('Failed to stop task:', error)
      }
    },
    // 处理暂停/恢复
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
        console.error('Failed to pause/resume task:', error)
      }
    },
    // 处理清除
    async handleClear() {
      // 清除 canvas 组件
      const canvasComponent = this.$refs.browserCanvas
      if (canvasComponent) {
        canvasComponent.clear()
      }

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
      // 清除信息面板数据
      this.browserInfo = {
        browserType: '',
        browserStatus: '',
        connectionType: '',
        windowSize: '',
        currentUrl: ''
      }
      this.modelInfo = {
        llmName: '',
        modelName: '',
        temperature: '',
        tokenUsage: '',
        avgTokensPerStep: '',
        totalDuration: ''
      }
      this.taskInfo = {
        currentTask: '',
        currentStep: '',
        stepStatus: '',
        goal: '',
        lastError: ''
      }
    },
    // 处理用户帮助
    async handleUserHelp(response) {
      try {
        await this.$api.browserUseAgent.respond({
          task_id: this.currentTaskId,
          message: response
        })
        this.isWaitingForHelp = false
        this.userInput = ''
      } catch (error) {
        console.error('Failed to send response:', error)
      }
    },
    // 开始监控任务状态
    async startMonitoring() {
      while (this.isRunning) {
        try {
          const status = await this.$api.browserUseAgent.getStatus(this.currentTaskId)
          if (status) {
            // 更新聊天历史
            if (status.chat_history) {
              this.updateChatHistory(status.chat_history)
            }
            // 更新浏览器视图
            if (status.browser_view) {
              this.updateBrowserView(status.browser_view)
            }
            // 检查是否需要帮助
            if (status.is_waiting_for_help) {
              this.isWaitingForHelp = true
            }
            // 检查任务输出
            if (status.task_outputs) {
              this.taskOutputs = true
              if (status.history_file) {
                this.historyFile = status.history_file
              }
              if (status.recording_gif) {
                this.recordingGif = status.recording_gif
              }
            }
            // 更新信息面板
            if (status.browser_info) {
              this.updateBrowserInfo(status.browser_info)
            }
            if (status.model_info) {
              this.updateModelInfo(status.model_info)
            }
            if (status.task_info) {
              this.updateTaskInfo(status.task_info)
            }
            // 检查任务是否完成
            if (!status.is_running) {
              this.isRunning = false
              this.isPaused = false
              this.isWaitingForHelp = false
              break
            }
          }
        } catch (error) {
          console.error('Monitoring error:', error)
          // 处理错误信息
          this.taskInfo.lastError = `Monitoring error: ${error.message}`
        }
        await this.sleep(1000)
      }
    },
    // 更新浏览器信息面板
    updateBrowserInfo(info) {
      this.browserInfo = {
        browserType: info.browserType || '',
        browserStatus: info.browserStatus || '',
        connectionType: info.connectionType || '',
        windowSize: info.windowSize || '',
        currentUrl: info.currentUrl || ''
      }
    },
    // 更新模型信息面板
    updateModelInfo(info) {
      this.modelInfo = {
        llmName: info.llmName || '',
        modelName: info.modelName || '',
        temperature: info.temperature || '',
        tokenUsage: info.tokenUsage || '',
        avgTokensPerStep: info.avgTokensPerStep || '',
        totalDuration: info.totalDuration || ''
      }
    },
    // 更新任务信息面板
    updateTaskInfo(info) {
      this.taskInfo = {
        currentTask: info.currentTask || '',
        currentStep: info.currentStep || '',
        stepStatus: info.stepStatus || '',
        goal: info.goal || '',
        lastError: info.lastError || ''
      }
    },
    // 更新聊天历史
    updateChatHistory(messages) {
      if (messages && messages.length > this.chatHistory.length) {
        this.chatHistory = messages
        // 滚动到底部
        this.$nextTick(() => {
          const chatHistory = this.$refs.chatHistory
          if (chatHistory) {
            chatHistory.scrollTop = chatHistory.scrollHeight
          }
        })
      }
    },
    // 更新浏览器视图
    updateBrowserView(view) {
      if (view) {
        this.browserView = view
        this.showBrowserView = true
      }
    },
    // 睡眠
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

.info-panel {
  margin-bottom: 20px;
  border-radius: 4px;
}

.browser-panel {
  border-top: 3px solid #409EFF;
}

.model-panel {
  border-top: 3px solid #67C23A;
}

.tasks-panel {
  border-top: 3px solid #E6A23C;
}

.info-content {
  min-height: 120px;
  font-size: 14px;
  line-height: 1.6;
}

.info-content p {
  margin: 8px 0;
  word-wrap: break-word;
}

.error-text {
  color: #F56C6C;
  font-weight: 500;
}

.chat-card {
  margin-bottom: 20px;
}

.chat-history {
  height: 400px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f9f9f9;
}

.chat-message {
  display: flex;
  margin-bottom: 15px;
  animation: fadeIn 0.3s ease;
}

.chat-message.left {
  flex-direction: row;
}

.chat-message.right {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 18px;
  word-wrap: break-word;
}

.chat-message.left .message-content {
  background-color: #e0e0e0;
  border-bottom-left-radius: 5px;
}

.chat-message.right .message-content {
  background-color: #409EFF;
  color: white;
  border-bottom-right-radius: 5px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 10px;
  font-size: 12px;
}

.chat-message.left .message-avatar {
  background-color: #ccc;
}

.chat-message.right .message-avatar {
  background-color: #409EFF;
  color: white;
}

.message-text {
  font-size: 14px;
  line-height: 1.4;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.waiting-indicator, .running-indicator {
  text-align: center;
  padding: 20px;
  color: #409EFF;
  font-size: 14px;
}

.waiting-indicator i, .running-indicator i {
  margin-right: 5px;
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

.download-link {
  color: #409EFF;
  text-decoration: none;
}

.download-link:hover {
  text-decoration: underline;
}

.recording-gif {
  max-width: 100%;
  height: auto;
}

.input-card {
  margin-bottom: 20px;
}

.button-row {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
