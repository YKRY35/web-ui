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

export default {
  name: 'DetailView',
  data() {
    return { layout: null }
  },
  mounted() {
    this.$nextTick(this.initLayout)
  },
  beforeDestroy() {
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
      // inject $api into the component instance
      if (extraProps) {
        Object.assign(instance.$children[0], extraProps)
      }
      return instance
    },
    initLayout() {
      const container = this.$refs.layoutContainer
      if (!container) return
      const api = this.$api

      this.layout = new GoldenLayout(container)

      this.layout.registerComponentFactoryFunction('canvas-panel', (glContainer) => {
        const vm = this.mountComponent(CanvasPanel, glContainer)
        glContainer.on('resize', () => vm.$children[0].resizeCanvas && vm.$children[0].resizeCanvas())
      })

      this.layout.registerComponentFactoryFunction('control-panel', (glContainer) => {
        this.mountComponent(ControlPanel, glContainer, { $api: api })
      })

      this.layout.registerComponentFactoryFunction('steps-panel', (glContainer) => {
        this.mountComponent(StepsPanel, glContainer)
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
                { type: 'component', componentType: 'control-panel', title: 'Control', height: 45 },
                { type: 'component', componentType: 'steps-panel', title: 'Steps', height: 55 }
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
