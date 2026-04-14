<template>
  <div class="detail-view">
    <div class="top-bar">
      <el-button
        type="primary"
        size="small"
        icon="el-icon-back"
        @click="$router.push('/')"
        title="Back to Home"
      >
        Back
      </el-button>
    </div>
    <div class="layout-container" ref="layoutContainer"></div>
  </div>
</template>

<script>
import { GoldenLayout } from 'golden-layout'
import Vue from 'vue'
import CanvasPanel from '@/components/detail/CanvasPanel.vue'
import ControlPanel from '@/components/detail/ControlPanel.vue'
import StepsPanel from '@/components/detail/StepsPanel.vue'
import { websocketManager } from '@/utils/websocket'

export default {
  name: 'DetailView',
  data() {
    return { layout: null, websocket: websocketManager }
  },
  mounted() {
    this.$nextTick(this.initLayout)
    // 监听窗口大小变化
    this._handleResize = () => {
      if (this.layout) {
        this.layout.updateSize()
      }
    }
    window.addEventListener('resize', this._handleResize)
  },
  beforeDestroy() {
    // 移除 resize 监听器
    if (this._handleResize) {
      window.removeEventListener('resize', this._handleResize)
    }
    if (this.layout) this.layout.destroy()
  },
  methods: {
    mountComponent(Component, glContainer, extraProps) {
      const el = document.createElement('div')
      el.style.width = '100%'
      el.style.height = '100%'
      glContainer.element.appendChild(el)
      const instance = new Vue({
        render: h => h(Component)
      }).$mount(el)
      // inject $api and $websocket into the component instance
      if (extraProps) {
        Object.assign(instance.$children[0], extraProps)
        // 注入完成后，调用组件的后置初始化钩子（如果存在）
        if (typeof instance.$children[0].$onInjected === 'function') {
          instance.$children[0].$onInjected()
        }
      }
      return instance
    },
    initLayout() {
      const container = this.$refs.layoutContainer
      if (!container) return
      const api = this.$api
      const websocket = this.websocket

      this.layout = new GoldenLayout(container)

      this.layout.registerComponentFactoryFunction('canvas-panel', (glContainer) => {
        const vm = this.mountComponent(CanvasPanel, glContainer)
        glContainer.on('resize', () => vm.$children[0].resizeCanvas && vm.$children[0].resizeCanvas())
      })

      this.layout.registerComponentFactoryFunction('control-panel', (glContainer) => {
        this.mountComponent(ControlPanel, glContainer, { $api: api, $websocket: websocket })
      })

      this.layout.registerComponentFactoryFunction('steps-panel', (glContainer) => {
        this.mountComponent(StepsPanel, glContainer, { $websocket: websocket })
      })

      this.layout.loadLayout({
        root: {
          type: 'row',
          content: [
            { type: 'component', componentType: 'canvas-panel', title: 'Canvas', width: 50 },
            {
              type: 'column',
              width: 50,
              content: [
                { type: 'component', componentType: 'control-panel', title: 'Control', height: 15 },
                { type: 'component', componentType: 'steps-panel', title: 'Steps', height: 85 }
              ]
            }
          ]
        }
      })
    }
  }
}
</script>

<style>
@import '~golden-layout/dist/css/goldenlayout-base.css';
@import '~golden-layout/dist/css/themes/goldenlayout-light-theme.css';

.detail-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  padding: 10px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
}

.layout-container {
  flex: 1;
  overflow: hidden;
}

.lm_content {
  background: #ffffff;
  overflow: hidden;
}
.lm_header { background: #f0f2f5; }
.lm_tab {
  background: #e4e7ed;
  color: #606266;
  border-radius: 4px 4px 0 0;
}
.lm_tab.lm_active {
  background: #ffffff;
  color: #303133;
  font-weight: 500;
}
.lm_splitter { background: #dcdfe6; }
.lm_splitter:hover, .lm_splitter.lm_dragging { background: #409EFF; }
</style>
