<template>
  <div class="steps-panel-inner">
    <div v-if="steps.length === 0" class="steps-empty">No steps yet. Submit a task to begin.</div>
    <div v-for="(step, idx) in steps" :key="step.id" class="step-item">
      <div class="step-num">{{ idx + 1 }}</div>
      <div class="step-body">
        <div class="step-meta">
          <el-tag size="mini" :type="tagType(step.type)">{{ step.type === 'user' ? 'You' : step.type === 'error' ? 'Error' : 'Agent' }}</el-tag>
          <span class="step-time">{{ formatTime(step.timestamp) }}</span>
        </div>
        <div class="step-content">{{ step.content }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import bus from './bus'

export default {
  name: 'StepsPanel',
  data() {
    return { steps: [] }
  },
  created() {
    this._onAdd = step => this.steps.push(step)
    this._onUpdate = msgs => {
      this.steps = msgs.map((m, i) => ({
        id: i,
        type: m.position === 'right' ? 'user' : 'agent',
        content: m.content,
        timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
        status: 'done'
      }))
    }
    this._onClear = () => { this.steps = [] }
    bus.$on('step-added', this._onAdd)
    bus.$on('steps-updated', this._onUpdate)
    bus.$on('steps-cleared', this._onClear)
  },
  beforeDestroy() {
    bus.$off('step-added', this._onAdd)
    bus.$off('steps-updated', this._onUpdate)
    bus.$off('steps-cleared', this._onClear)
  },
  methods: {
    formatTime(ts) {
      return ts ? new Date(ts).toLocaleTimeString() : ''
    },
    tagType(type) {
      return { user: 'primary', agent: 'success', error: 'danger' }[type] || 'info'
    }
  }
}
</script>

<style scoped>
.steps-panel-inner {
  height: 100%;
  overflow-y: auto;
  padding: 8px 12px;
  box-sizing: border-box;
  background: #fff;
}
.steps-empty {
  color: #c0c4cc;
  text-align: center;
  padding: 40px 20px;
  font-size: 13px;
}
.step-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f2f6fc;
}
.step-num {
  min-width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f0f2f5;
  color: #909399;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.step-body { flex: 1; min-width: 0; }
.step-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}
.step-time { font-size: 11px; color: #c0c4cc; }
.step-content {
  font-size: 13px;
  color: #303133;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
