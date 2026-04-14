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

      <!-- 大步骤容器：浅绿色背景 -->
      <div
        v-for="(step, idx) in steps"
        :key="step.id"
        class="step-container"
        :class="'step-type-' + step.type"
      >
        <!-- 步骤描述（顶部字段） -->
        <div class="step-description">
          <div class="step-header-row">
            <span class="step-label">步骤 {{ idx + 1 }}</span>
            <span class="step-time">{{ formatTime(step.timestamp) }}</span>
          </div>
          <div v-if="step.intent" class="step-intent">
            <i class="el-icon-aim"></i> {{ step.intent }}
          </div>
        </div>

        <!-- 原子操作区域：白色背景块 -->
        <div class="atomic-operations">
          <!-- 循环显示多个 actions -->
          <div v-if="step.actions && step.actions.length > 0" class="actions-container">
            <div
              v-for="(action, actionIdx) in step.actions"
              :key="actionIdx"
              class="atomic-block action-block"
            >
              <div class="atomic-header">
                <span class="atomic-label">操作 {{ actionIdx + 1 }}</span>
                <span class="action-type-tag" :class="getActionTypeClass(action.name)">
                  {{ action.name }}
                </span>
              </div>
              <div class="atomic-content">
                <!-- 操作值 -->
                <div v-if="Object.keys(action.params).length > 0" class="atomic-detail">
                  <span class="detail-label">参数:</span>
                  <div class="params-container">
                    <div
                      v-for="(value, key) in action.params"
                      :key="key"
                      class="param-item"
                    >
                      <span class="param-key">{{ key }}:</span>
                      <span class="param-value">{{ formatParamValue(value) }}</span>
                    </div>
                  </div>
                </div>
                <!-- XPath 定位信息 -->
                <div v-if="action.xpath" class="atomic-detail xpath-detail">
                  <span class="detail-label">XPath:</span>
                  <div class="xpath-container">
                    <code class="detail-value monospace xpath-code">{{ action.xpath }}</code>
                    <button
                      class="pick-button-mini"
                      @click="handlePickXPath(action.xpath, idx, actionIdx)"
                      title="定位拾取"
                    >
                      <i class="el-icon-aim"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 执行结果 -->
          <div v-if="step.resultText" class="atomic-block">
            <div class="atomic-header">
              <span class="atomic-label">结果</span>
              <span class="test-status" :class="getTestStatusClass(step)">
                {{ getTestStatusText(step) }}
              </span>
            </div>
            <div class="atomic-content">
              <div class="atomic-detail">
                <span class="detail-value success">{{ step.resultText }}</span>
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="step.errors && step.errors.length > 0" class="atomic-block error-block">
            <div class="atomic-header">
              <span class="atomic-label">错误</span>
              <span class="test-status failed">失败</span>
            </div>
            <div class="atomic-content">
              <div
                v-for="(e, i) in step.errors"
                :key="i"
                class="atomic-detail"
              >
                <span class="detail-value error">{{ e }}</span>
              </div>
            </div>
          </div>

          <!-- 思考过程（可折叠） -->
          <div v-if="step.thought" class="atomic-block thought-block">
            <div class="atomic-header">
              <span class="atomic-label">思考</span>
            </div>
            <div class="atomic-content">
              <el-collapse>
                <el-collapse-item title="Agent 思考过程">
                  <div class="thought-text monospace">{{ step.thought }}</div>
                </el-collapse-item>
              </el-collapse>
            </div>
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

      const { step_number, timestamp, model_output, result, state, actions, next_goal } = data

      // 用户意图：优先用顶层 next_goal，再从 model_output 提取
      const intent = next_goal
        || (model_output && model_output.next_goal)
        || (model_output && model_output.current_state && model_output.current_state.next_goal)
        || ''

      // 解析所有 actions（新格式）
      let parsedActions = []
      if (actions && Array.isArray(actions)) {
        parsedActions = actions.map(action => ({
          name: action.name,
          params: action.params || {},
          xpath: action.xpath || null
        }))
      } else if (model_output && model_output.action && model_output.action.length > 0) {
        // 兼容旧格式：从 model_output 提取
        parsedActions = model_output.action.map(act => {
          const actName = Object.keys(act).find(k => k !== 'index' && k !== 'xpath')
          if (actName) {
            const params = act[actName]
            return {
              name: actName,
              params: typeof params === 'object' ? params : {},
              xpath: null
            }
          }
          return null
        }).filter(Boolean)
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
        actions: parsedActions,  // 新增：所有 actions 数组
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
    },

    /**
     * 处理定位拾取按钮点击
     * @param {string} xpath - XPath 表达式
     * @param {number} stepIndex - 步骤索引
     * @param {number} actionIndex - action 索引
     */
    handlePickXPath(xpath, stepIndex, actionIndex) {
      // 触发自定义事件，可由父组件或其他监听者处理
      this.$emit('pick-xpath', { xpath, stepIndex, actionIndex })
      // 同时触发 bus 事件，便于跨组件通信
      bus.$emit('xpath-pick', { xpath, stepIndex, actionIndex })
    },

    /**
     * 格式化参数值
     * @param {*} value - 参数值
     * @returns {string} 格式化后的值
     */
    formatParamValue(value) {
      if (typeof value === 'string') {
        return value.length > 100 ? value.substring(0, 100) + '...' : value
      }
      if (typeof value === 'object') {
        const str = JSON.stringify(value)
        return str.length > 100 ? str.substring(0, 100) + '...' : str
      }
      return String(value)
    },

    /**
     * 获取操作类型的样式类
     * @param {string} actionName - 操作名称
     * @returns {string} 样式类名
     */
    getActionTypeClass(actionName) {
      const typeMap = {
        'click': 'action-click',
        'input': 'action-input',
        'navigate': 'action-navigate',
        'scroll': 'action-scroll',
        'wait': 'action-wait',
        'done': 'action-done',
        'search': 'action-search'
      }
      return typeMap[actionName] || 'action-other'
    },

    /**
     * 获取测试状态样式类
     * @param {Object} step - 步骤对象
     * @returns {string} 状态类名
     */
    getTestStatusClass(step) {
      if (step.errors && step.errors.length > 0) {
        return 'failed'
      }
      if (step.resultText) {
        return 'success'
      }
      return 'pending'
    },

    /**
     * 获取测试状态文本
     * @param {Object} step - 步骤对象
     * @returns {string} 状态文本
     */
    getTestStatusText(step) {
      if (step.errors && step.errors.length > 0) {
        return '失败'
      }
      if (step.resultText) {
        return '成功'
      }
      return '执行中'
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
  padding: 8px;
  background: #f5f7fa;
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

/* 大步骤容器：浅绿色背景 */
.step-container {
  background: #d9eada;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  transition: box-shadow 0.2s;
}

.step-container:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.step-container:last-child {
  margin-bottom: 0;
}

/* 步骤描述区域 */
.step-description {
  margin-bottom: 10px;
}

.step-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.step-label {
  display: inline-block;
  background: #67c23a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.step-time {
  font-size: 11px;
  color: #606266;
}

.step-intent {
  font-size: 13px;
  color: #303133;
  font-weight: 600;
  line-height: 1.5;
  word-break: break-word;
}
.step-intent i {
  color: #67c23a;
  margin-right: 4px;
}

/* 原子操作区域 */
.atomic-operations {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Actions 容器 */
.actions-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 操作块样式 */
.action-block {
  border-left: 3px solid #409eff;
}

/* 操作类型标签 */
.action-type-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
}

.action-type-tag.action-click {
  background: #ecf5ff;
  color: #409eff;
}

.action-type-tag.action-input {
  background: #fef0f0;
  color: #f56c6c;
}

.action-type-tag.action-navigate {
  background: #f0f9eb;
  color: #67c23a;
}

.action-type-tag.action-scroll {
  background: #fdf6ec;
  color: #e6a23c;
}

.action-type-tag.action-wait {
  background: #f4f4f5;
  color: #909399;
}

.action-type-tag.action-done {
  background: #f0f9eb;
  color: #67c23a;
}

.action-type-tag.action-search {
  background: #ecf5ff;
  color: #409eff;
}

.action-type-tag.action-other {
  background: #f4f4f5;
  color: #606266;
}

/* 参数容器 */
.params-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.param-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  line-height: 1.5;
}

.param-key {
  color: #909399;
  font-weight: 600;
  white-space: nowrap;
  min-width: 60px;
}

.param-value {
  color: #303133;
  word-break: break-word;
  flex: 1;
}

/* XPath 详情 */
.xpath-detail {
  margin-top: 6px;
}

.xpath-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.xpath-code {
  flex: 1;
  word-break: break-all;
}

/* 迷你拾取按钮 */
.pick-button-mini {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(155, 89, 182, 0.3);
  flex-shrink: 0;
}

.pick-button-mini:hover {
  background: linear-gradient(135deg, #8e44ad, #7d3c98);
  transform: scale(1.1);
  box-shadow: 0 2px 5px rgba(155, 89, 182, 0.4);
}

.pick-button-mini:active {
  transform: scale(0.95);
}

.pick-button-mini i {
  font-size: 12px;
}

/* 原子操作块：白色背景 */
.atomic-block {
  background: #fff;
  border-radius: 6px;
  padding: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.atomic-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.atomic-label {
  font-size: 11px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.atomic-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.atomic-detail {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  flex-wrap: wrap;
}

.detail-label {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  flex-shrink: 0;
}

.detail-value {
  font-size: 12px;
  color: #303133;
  word-break: break-word;
  line-height: 1.5;
}

.detail-value.success {
  color: #67c23a;
}

.detail-value.error {
  color: #f56c6c;
}

/* 等宽字体 */
.monospace {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

/* 紫色圆形定位拾取按钮 */
.pick-button {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(155, 89, 182, 0.3);
}

.pick-button:hover {
  background: linear-gradient(135deg, #8e44ad, #7d3c98);
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(155, 89, 182, 0.4);
}

.pick-button:active {
  transform: scale(0.95);
}

.pick-button i {
  font-size: 14px;
}

/* 测试执行状态标识 */
.test-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
}

.test-status.success {
  background: #f0f9eb;
  color: #67c23a;
}

.test-status.failed {
  background: #fef0f0;
  color: #f56c6c;
}

.test-status.pending {
  background: #fdf6ec;
  color: #e6a23c;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* 错误块特殊样式 */
.error-block {
  border-left: 3px solid #f56c6c;
}

/* 思考块特殊样式 */
.thought-block {
  background: #fafafa;
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
.thought-block >>> .el-collapse {
  border: none;
}
.thought-block >>> .el-collapse-item__header {
  font-size: 11px;
  color: #909399;
  height: 28px;
  line-height: 28px;
  border: none;
  background: transparent;
  padding: 0;
}
.thought-block >>> .el-collapse-item__wrap {
  border: none;
  background: transparent;
}
.thought-block >>> .el-collapse-item__content {
  padding: 0;
}

/* 步骤类型样式（保留用于特殊标记） */
.step-type-user .step-label { background: #409eff; }
.step-type-agent .step-label { background: #67c23a; }
.step-type-error .step-label { background: #f56c6c; }
</style>
