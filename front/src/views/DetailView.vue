<template>
  <div class="detail-view">
    <div class="top-bar">
      <div class="top-bar-left">
        <el-button
          type="text"
          size="mini"
          icon="el-icon-back"
          @click="$router.push('/')"
          class="back-button"
        >
          Back
        </el-button>
        <el-button
          type="text"
          size="mini"
          icon="el-icon-plus"
          @click="openNewDetailPage"
          class="new-page-button"
        >
          新执行页
        </el-button>
      </div>
      <div class="top-bar-right">
        <el-button
          type="text"
          size="mini"
          icon="el-icon-setting"
          @click="showSettingsDialog = true"
          class="settings-button"
        >
          设置
        </el-button>
        <div class="session-info">
          <span class="session-label">Session:</span>
          <span class="session-id">{{ detailId || '...' }}</span>
        </div>
      </div>
    </div>
    <div class="layout-container" ref="layoutContainer"></div>

    <SettingsDialog
      :visible.sync="showSettingsDialog"
      :settings="themeSettings"
      @theme-change="handleThemeChange"
    />
  </div>
</template>

<script>
import { GoldenLayout } from 'golden-layout'
import Vue from 'vue'
import CanvasPanel from '@/components/detail/CanvasPanel.vue'
import ControlPanel from '@/components/detail/ControlPanel.vue'
import StepsPanel from '@/components/detail/StepsPanel.vue'
import LogPanel from '@/components/detail/LogPanel.vue'
import SettingsDialog from '@/components/common/SettingsDialog.vue'
import { websocketManager } from '@/utils/websocket'
import { getOrCreateDetailID } from '@/utils/detailId'

const DETAIL_ID_KEY = 'browser_use_detail_id'

export default {
  name: 'DetailView',
  components: {
    SettingsDialog
  },
  data() {
    return {
      layout: null,
      websocket: websocketManager,
      detailId: null,
      showSettingsDialog: false,
      themeSettings: { theme: 'light' }
    }
  },
  created() {
    // 加载主题设置
    this.loadThemeSettings()
  },
  async mounted() {
    // 获取或创建 Detail ID
    this.detailId = await getOrCreateDetailID()
    console.log('[DetailView] Detail ID:', this.detailId)
    console.log('[DetailView] Session Storage Key:', DETAIL_ID_KEY)
    console.log('[DetailView] Session Storage Value:', sessionStorage.getItem('browser_use_detail_id'))

    // 设置页面标题显示 ID
    document.title = `Browser Use - ${this.detailId}`

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
    loadThemeSettings() {
      const savedThemeSettings = this.$storage.loadThemeSettings()
      if (savedThemeSettings) {
        this.themeSettings = savedThemeSettings
        this.applyTheme(savedThemeSettings.theme)
      }
    },

    applyTheme(theme) {
      this.$root.$emit('theme-change', theme)
    },

    handleThemeChange(theme) {
      this.themeSettings.theme = theme
      this.$storage.saveThemeSettings(this.themeSettings)
      this.applyTheme(theme)
    },

    openNewDetailPage() {
      // 打开新标签页，访问 /detail 路由
      // 添加时间戳参数，强制新标签页生成新 ID
      const timestamp = Date.now()

      // 使用 Vue Router 生成带查询参数的 URL
      const route = this.$router.resolve({
        path: '/detail',
        query: { _new_tab: timestamp }
      })

      const url = route.href
      console.log('[DetailView] Opening new detail page:', url)
      console.log('[DetailView] Full URL:', window.location.origin + url)

      window.open(url, '_blank')
    },
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

      this.layout.registerComponentFactoryFunction('log-panel', (glContainer) => {
        this.mountComponent(LogPanel, glContainer, { $websocket: websocket })
      })

      this.layout.loadLayout({
        root: {
          type: 'row',
          content: [
            {
              type: 'column',
              width: 64.3,  // 左侧面板占 1.8/(1.8+1) ≈ 64.3%
              content: [
                { type: 'component', componentType: 'canvas-panel', title: '浏览器', height: 70 },
                { type: 'component', componentType: 'log-panel', title: '日志', height: 30 }
              ]
            },
            {
              type: 'column',
              width: 35.7,  // 右侧面板占 1/(1.8+1) ≈ 35.7%
              content: [
                { type: 'component', componentType: 'control-panel', title: '案例', height: 15 },
                { type: 'component', componentType: 'steps-panel', title: 'UI脚本', height: 85 }
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
  margin: 0;
  padding: 0;
}

.top-bar {
  height: 36px;
  padding: 0 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-button,
.new-page-button,
.settings-button {
  padding: 4px 8px;
  font-size: 12px;
  color: #606266;
}

.back-button:hover,
.new-page-button:hover,
.settings-button:hover {
  color: #409eff;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.session-label {
  color: #909399;
  font-weight: 500;
}

.session-id {
  color: #409eff;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  background: #ecf5ff;
  padding: 2px 8px;
  border-radius: 3px;
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

/* Dark theme styles for DetailView */
#app.dark .top-bar {
  background: #2d2d2d;
  border-bottom-color: #3d3d3d;
}

#app.dark .back-button,
#app.dark .new-page-button,
#app.dark .settings-button {
  color: #b0b0b0;
}

#app.dark .back-button:hover,
#app.dark .new-page-button:hover,
#app.dark .settings-button:hover {
  color: #409eff;
}

#app.dark .session-label {
  color: #909399;
}

#app.dark .session-id {
  background: #1a3a4d;
  color: #409eff;
}

#app.dark .lm_content {
  background: #2d2d2d;
}

#app.dark .lm_header {
  background: #252525;
}

#app.dark .lm_tab {
  background: #3d3d3d;
  color: #b0b0b0;
}

#app.dark .lm_tab.lm_active {
  background: #2d2d2d;
  color: #e0e0e0;
}

#app.dark .lm_splitter {
  background: #3d3d3d;
}

#app.dark .lm_splitter:hover,
#app.dark .lm_splitter.lm_dragging {
  background: #409EFF;
}
</style>
