<template>
  <div class="log-panel-inner">
    <div class="log-header">
      <el-radio-group v-model="activeTab" size="mini" class="log-tabs">
        <el-radio-button label="browser-use">Browser-Use</el-radio-button>
        <el-radio-button label="llm">LLM</el-radio-button>
      </el-radio-group>
      <span class="log-count">{{ currentLogs.length }} 条</span>
      <div class="log-controls">
        <el-select v-model="selectedLevel" size="mini" placeholder="日志级别" class="level-select">
          <el-option label="全部" value="all"></el-option>
          <el-option label="INFO" value="info"></el-option>
          <el-option label="WARNING" value="warning"></el-option>
          <el-option label="ERROR" value="error"></el-option>
          <el-option label="DEBUG" value="debug"></el-option>
        </el-select>
        <el-button
          v-if="currentLogs.length > 0"
          type="text"
          size="mini"
          icon="el-icon-delete"
          class="log-clear-btn"
          @click="clearCurrentLogs"
        >清空</el-button>
      </div>
    </div>

    <div class="log-list" ref="logList">
      <div v-if="filteredLogs.length === 0" class="log-empty">
        <i class="el-icon-document"></i>
        <span>暂无日志</span>
      </div>

      <div
        v-for="(log, idx) in filteredLogs"
        :key="log.id"
        class="log-entry"
        :class="['log-level-' + log.level, log.log_type ? 'log-type-' + log.log_type : '']"
      >
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <span class="log-level-badge" :class="'level-' + log.level">{{ log.level.toUpperCase() }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import bus from './bus'

export default {
  name: 'LogPanel',
  data() {
    return {
      activeTab: 'browser-use',
      selectedLevel: 'all',
      browserUseLogs: [],
      llmLogs: []
    }
  },
  computed: {
    currentLogs() {
      return this.activeTab === 'browser-use' ? this.browserUseLogs : this.llmLogs
    },
    filteredLogs() {
      if (this.selectedLevel === 'all') {
        return this.currentLogs
      }
      return this.currentLogs.filter(log => log.level === this.selectedLevel)
    }
  },
  mounted() {
    this._setupWebSocket()
  },
  beforeDestroy() {
    if (this.$websocket) {
      this.$websocket.removeMessageHandler('log')
      this.$websocket.removeMessageHandler('log-history')
      this.$websocket.removeMessageHandler('llm-log')
      this.$websocket.removeMessageHandler('llm-log-history')
    }
  },
  methods: {
    $onInjected() {
      this._setupWebSocket()
    },
    _setupWebSocket() {
      if (!this.$websocket) {
        console.error('LogPanel: $websocket not injected')
        return
      }

      // 接收 browser-use 实时日志
      this.$websocket.addMessageHandler('log', (data) => {
        const log = this._parseLogData(data)
        if (log) {
          this.browserUseLogs.push(log)
          this._scrollToBottom()
        }
      })

      // 接收 browser-use 历史日志
      this.$websocket.addMessageHandler('log-history', (data) => {
        if (data && Array.isArray(data.logs) && data.logs.length > 0) {
          if (this.browserUseLogs.length === 0) {
            this.browserUseLogs = data.logs.map(msg => this._parseLogData(msg.data)).filter(Boolean)
            this.$nextTick(() => this._scrollToBottom())
          }
        }
      })

      // 接收 LLM 实时日志
      this.$websocket.addMessageHandler('llm-log', (data) => {
        const log = this._parseLogData(data)
        if (log) {
          this.llmLogs.push(log)
          if (this.activeTab === 'llm') {
            this._scrollToBottom()
          }
        }
      })

      // 接收 LLM 历史日志
      this.$websocket.addMessageHandler('llm-log-history', (data) => {
        if (data && Array.isArray(data.logs) && data.logs.length > 0) {
          if (this.llmLogs.length === 0) {
            this.llmLogs = data.logs.map(msg => this._parseLogData(msg.data)).filter(Boolean)
            if (this.activeTab === 'llm') {
              this.$nextTick(() => this._scrollToBottom())
            }
          }
        }
      })
    },

    /**
     * 解析后端推送的日志数据
     */
    _parseLogData(data) {
      if (!data) return null

      const { timestamp, level, message } = data

      return {
        id: Date.now() + Math.random(),
        timestamp: timestamp ? new Date(timestamp) : new Date(),
        level: level || 'info',
        message: message || ''
      }
    },

    clearCurrentLogs() {
      if (this.activeTab === 'browser-use') {
        this.browserUseLogs = []
      } else {
        this.llmLogs = []
      }
    },

    _scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.logList
        if (el) el.scrollTop = el.scrollHeight
      })
    },

    formatTime(ts) {
      if (!ts) return ''
      return new Date(ts).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
      })
    }
  }
}
</script>

<style scoped>
.log-panel-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

.log-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
  background: #fafafa;
}

.log-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.log-count {
  margin-left: 8px;
  font-size: 11px;
  color: #909399;
  background: #f0f2f5;
  padding: 1px 6px;
  border-radius: 8px;
}

.log-controls {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-tabs {
  margin-right: 4px;
}

.log-tabs >>> .el-radio-button__inner {
  padding: 5px 12px;
  font-size: 11px;
}

.level-select {
  width: 100px;
}

.log-clear-btn {
  color: #c0c4cc;
  font-size: 11px;
}
.log-clear-btn:hover {
  color: #f56c6c;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background: #f8f9fa;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.log-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #c0c4cc;
  font-size: 13px;
  gap: 8px;
}
.log-empty i {
  font-size: 28px;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 8px;
  margin-bottom: 4px;
  border-radius: 3px;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.log-entry:hover {
  background: #fff;
}

.log-time {
  color: #909399;
  font-size: 11px;
  white-space: nowrap;
  flex-shrink: 0;
}

.log-level-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  text-transform: uppercase;
  flex-shrink: 0;
}

.log-level-badge.level-info {
  background: #e1f3fb;
  color: #409eff;
}

.log-level-badge.level-warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.log-level-badge.level-error {
  background: #fef0f0;
  color: #f56c6c;
}

.log-level-badge.level-debug {
  background: #f4f4f5;
  color: #909399;
}

.log-message {
  color: #303133;
  flex: 1;
}

/* 不同级别日志的特殊样式 */
.log-level-error {
  border-left: 3px solid #f56c6c;
  background: #fef0f0;
}

.log-level-warning {
  border-left: 3px solid #e6a23c;
  background: #fdf6ec;
}

.log-level-info {
  border-left: 3px solid #409eff;
}

.log-level-debug {
  opacity: 0.7;
}

/* Dark theme styles for LogPanel */
#app.dark .log-panel-inner {
  background: #2d2d2d;
}

#app.dark .log-header {
  background: #252525;
  border-bottom-color: #3d3d3d;
}

#app.dark .log-count {
  background: #3d3d3d;
  color: #909399;
}

#app.dark .log-list {
  background: #1a1a1a;
}

#app.dark .log-empty {
  color: #606266;
}

#app.dark .log-entry:hover {
  background: #2d2d2d;
}

#app.dark .log-time {
  color: #909399;
}

#app.dark .log-message {
  color: #e0e0e0;
}

#app.dark .log-level-badge.level-info {
  background: #1a3a4d;
  color: #409eff;
}

#app.dark .log-level-badge.level-warning {
  background: #3d3219;
  color: #e6a23c;
}

#app.dark .log-level-badge.level-error {
  background: #3d1919;
  color: #f56c6c;
}

#app.dark .log-level-badge.level-debug {
  background: #2d2d2d;
  color: #909399;
}

#app.dark .log-level-error {
  border-left-color: #f56c6c;
  background: #3d1919;
}

#app.dark .log-level-warning {
  border-left-color: #e6a23c;
  background: #3d3219;
}

#app.dark .log-level-info {
  border-left-color: #409eff;
}
</style>
