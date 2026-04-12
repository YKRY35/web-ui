<template>
  <div class="steps-panel-inner">
    <div class="steps-header">
      <span class="steps-title">执行步骤</span>
      <span class="steps-count">{{ steps.length }} 步</span>
      <el-button
        v-if="steps.length > 0"
        type="text"
        size="mini"
        icon="el-icon-delete"
        class="steps-clear-btn"
        @click="clearSteps"
      >清空</el-button>
    </div>

    <div class="steps-list" ref="stepsList">
      <div v-if="steps.length === 0" class="steps-empty">
        <i class="el-icon-time"></i>
        <span>暂无步骤，提交任务后将实时显示执行过程</span>
      </div>

      <div
        v-for="(step, idx) in steps"
        :key="step.id"
        class="step-item"
        :class="'step-type-' + step.type"
      >
        <div class="step-num">{{ idx + 1 }}</div>
        <div class="step-body">
          <div class="step-meta">
            <span v-if="step.stepNumber" class="step-seq">Step {{ step.stepNumber }}</span>
            <span class="step-time">{{ formatTime(step.timestamp) }}</span>
          </div>

          <!-- 用户意图（next_goal） -->
          <div v-if="step.intent" class="step-intent">
            <i class="el-icon-aim"></i> {{ step.intent }}
          </div>

          <!-- 操作元素 XPath -->
          <div v-if="step.xpath" class="step-xpath">
            <span class="xpath-label">XPath:</span>
            <code class="xpath-value">{{ step.xpath }}</code>
          </div>

          <!-- 操作摘要（最醒目） -->
          <div v-if="step.actionSummary" class="step-action">
            <i class="el-icon-right"></i> {{ step.actionSummary }}
          </div>

          <!-- 页面信息 -->
          <div v-if="step.url || step.title" class="step-page">
            <span v-if="step.title" class="page-title">{{ step.title }}</span>
            <span v-if="step.url" class="page-url">{{ step.url }}</span>
          </div>

          <!-- 结果 -->
          <div v-if="step.resultText" class="step-result">{{ step.resultText }}</div>

          <!-- 错误 -->
          <div v-if="step.errors && step.errors.length > 0" class="step-errors">
            <span v-for="(e, i) in step.errors" :key="i" class="step-error-item">{{ e }}</span>
          </div>

          <!-- 思考/推理（可折叠） -->
          <div v-if="step.thought" class="step-thought">
            <el-collapse>
              <el-collapse-item title="Agent 思考过程">
                <div class="thought-text">{{ step.thought }}</div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import bus from './bus'

export default {
  name: 'StepsPanel',
  data() {
    return {
      steps: []
    }
  },
  created() {
    // bus 事件：用户消息 / 清空
    this._onAdd = step => {
      if (step && step.content) {
        this.steps.push({
          id: Date.now(),
          type: step.type || 'user',
          actionSummary: step.content,
          timestamp: step.timestamp || new Date()
        })
        this._scrollToBottom()
      }
    }
    this._onClear = () => { this.steps = [] }
    bus.$on('step-added', this._onAdd)
    bus.$on('steps-cleared', this._onClear)
  },
  mounted() {
    // $websocket 由 DetailView 通过 Object.assign 注入（在 $mount 之后）
    // _setupWebSocket 会在 $onInjected 中被调用（注入完成后）
  },
  beforeDestroy() {
    bus.$off('step-added', this._onAdd)
    bus.$off('steps-cleared', this._onClear)

    if (this.$websocket) {
      this.$websocket.removeMessageHandler('step')
      this.$websocket.removeMessageHandler('history')
    }
  },
  methods: {
    // DetailView 注入 props 完成后调用此钩子
    $onInjected() {
      this._setupWebSocket()
    },
    _setupWebSocket() {
      if (!this.$websocket) {
        console.error('StepsPanel: $websocket not injected')
        return
      }

      // 实时步骤
      this.$websocket.addMessageHandler('step', (data) => {
        // handleMessage 已将 message.data 解包后传入，data 即 step data 对象
        const step = this._parseStepData(data)
        if (step) {
          this.steps.push(step)
          this._scrollToBottom()
        }
      })

      // 历史步骤批量推送（新连接时服务端发送）
      this.$websocket.addMessageHandler('history', (data) => {
        if (data && Array.isArray(data.steps) && data.steps.length > 0) {
          // 仅在当前无步骤时加载历史，避免重复
          if (this.steps.length === 0) {
            this.steps = data.steps.map(msg => this._parseStepData(msg.data)).filter(Boolean)
            this.$nextTick(() => this._scrollToBottom())
          }
        }
      })
    },

    /**
     * 将后端推送的 step data 对象转换为 UI 显示格式。
     * 入参 data 是 message.data 字段（即 _on_agent_step 构建的 step_data["data"]）
     */
    _parseStepData(data) {
      if (!data) return null

      const { step_number, timestamp, model_output, result, state, action_summary, next_goal, xpath } = data

      // 用户意图：优先用顶层 next_goal，再从 model_output 提取
      const intent = next_goal
        || (model_output && model_output.next_goal)
        || (model_output && model_output.current_state && model_output.current_state.next_goal)
        || ''

      // 操作摘要：优先用 action_summary，其次从 model_output 提取
      let actionSummary = ''
      if (action_summary) {
        const actionName = Object.keys(action_summary).find(k => k !== 'index' && k !== 'xpath')
        if (actionName) {
          const val = action_summary[actionName]
          actionSummary = `${actionName}: ${typeof val === 'string' ? val : JSON.stringify(val)}`
        } else {
          actionSummary = JSON.stringify(action_summary)
        }
      } else if (model_output && model_output.action && model_output.action.length > 0) {
        const act = model_output.action[0]
        const actName = Object.keys(act).find(k => k !== 'index' && k !== 'xpath')
        if (actName) {
          const val = act[actName]
          actionSummary = `${actName}: ${typeof val === 'string' ? val : JSON.stringify(val)}`
        }
      }

      // 思考过程
      const thought = model_output && model_output.current_state && model_output.current_state.thought
        ? model_output.current_state.thought
        : ''

      // 结果文本
      let resultText = ''
      if (result && result.length > 0) {
        resultText = result
          .map(r => r.extracted_content || r.error || '')
          .filter(Boolean)
          .join(' | ')
      }

      // 浏览器错误
      const errors = (state && state.browser_errors) ? state.browser_errors : []

      return {
        id: Date.now() + Math.random(),
        type: 'agent',
        stepNumber: step_number,
        timestamp: timestamp ? new Date(timestamp) : new Date(),
        intent,
        xpath: xpath || '',
        actionSummary,
        thought,
        resultText,
        url: state && state.url ? state.url : '',
        title: state && state.title ? state.title : '',
        errors
      }
    },

    clearSteps() {
      this.steps = []
      bus.$emit('steps-cleared')
    },

    _scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.stepsList
        if (el) el.scrollTop = el.scrollHeight
      })
    },

    formatTime(ts) {
      if (!ts) return ''
      return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    },

    tagType(type) {
      return { user: 'primary', agent: 'success', error: 'danger' }[type] || 'info'
    },

    labelOf(type) {
      return { user: '用户', agent: 'Agent', error: '错误' }[type] || type
    }
  }
}
</script>

<style scoped>
.steps-panel-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

.steps-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
  background: #fafafa;
}

.steps-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.steps-count {
  margin-left: 8px;
  font-size: 11px;
  color: #909399;
  background: #f0f2f5;
  padding: 1px 6px;
  border-radius: 8px;
}

.steps-clear-btn {
  margin-left: auto;
  color: #c0c4cc;
  font-size: 11px;
}
.steps-clear-btn:hover { color: #f56c6c; }

.steps-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.steps-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: #c0c4cc;
  font-size: 13px;
  gap: 8px;
}
.steps-empty i { font-size: 28px; }

.step-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #f5f7fa;
  transition: background 0.15s;
}
.step-item:hover { background: #f9fafc; }
.step-item:last-child { border-bottom: none; }

.step-num {
  min-width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e8f4ff;
  color: #409eff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.step-type-user .step-num { background: #ecf5ff; color: #409eff; }
.step-type-agent .step-num { background: #f0f9eb; color: #67c23a; }
.step-type-error .step-num { background: #fef0f0; color: #f56c6c; }

.step-body { flex: 1; min-width: 0; }

.step-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.step-seq {
  font-size: 11px;
  color: #909399;
  background: #f5f7fa;
  padding: 1px 5px;
  border-radius: 3px;
}

.step-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-left: auto;
}

.step-action {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.5;
  word-break: break-word;
}
.step-action i { color: #409eff; margin-right: 3px; }

.step-intent {
  font-size: 13px;
  color: #303133;
  font-weight: 600;
  margin-bottom: 4px;
  line-height: 1.5;
  word-break: break-word;
}
.step-intent i { color: #409eff; margin-right: 3px; }

.step-xpath {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 4px;
}

.xpath-label {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  margin-top: 1px;
}

.xpath-value {
  font-size: 11px;
  color: #606266;
  background: #f5f7fa;
  padding: 1px 5px;
  border-radius: 3px;
  word-break: break-all;
  font-family: monospace;
}

.step-page {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 4px;
}

.page-title {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.page-url {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-result {
  font-size: 12px;
  color: #67c23a;
  background: #f0f9eb;
  padding: 3px 7px;
  border-radius: 3px;
  margin-top: 4px;
  word-break: break-word;
}

.step-errors {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-error-item {
  font-size: 11px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 2px 6px;
  border-radius: 3px;
  word-break: break-word;
}

.step-thought {
  margin-top: 6px;
}

.thought-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 4px 0;
}

/* 覆盖 el-collapse 样式使其更紧凑 */
.step-thought >>> .el-collapse {
  border: none;
}
.step-thought >>> .el-collapse-item__header {
  font-size: 11px;
  color: #909399;
  height: 28px;
  line-height: 28px;
  border: none;
  background: transparent;
  padding: 0;
}
.step-thought >>> .el-collapse-item__wrap {
  border: none;
  background: transparent;
}
.step-thought >>> .el-collapse-item__content {
  padding: 0;
}
</style>
