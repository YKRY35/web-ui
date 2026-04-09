<template>
  <div class="main-view">
    <div class="header">
      <h1>🌐 Browser Use WebUI</h1>
      <p class="subtitle">Control your browser with AI assistance</p>
    </div>

    <TabContainer :tabs="tabs" @tab-change="handleTabChange">
      <template #agent-settings>
        <AgentSettingsTab v-model="agentSettings" :sync-enabled="!isConfigLoading" />
      </template>
      <template #browser-settings>
        <BrowserSettingsTab v-model="browserSettings" :sync-enabled="!isConfigLoading" />
      </template>
      <template #browser-use-agent>
        <BrowserUseAgentTab />
      </template>
      <template #deep-research>
        <DeepResearchAgentTab />
      </template>
      <template #load-save-config>
        <LoadSaveConfigTab @config-loaded="handleConfigLoaded" />
      </template>
    </TabContainer>
  </div>
</template>

<script>
import TabContainer from '@/components/common/TabContainer.vue'
import AgentSettingsTab from '@/components/pages/AgentSettingsTab.vue'
import BrowserSettingsTab from '@/components/pages/BrowserSettingsTab.vue'
import BrowserUseAgentTab from '@/components/pages/BrowserUseAgentTab.vue'
import DeepResearchAgentTab from '@/components/pages/DeepResearchAgentTab.vue'
import LoadSaveConfigTab from '@/components/pages/LoadSaveConfigTab.vue'

export default {
  name: 'MainView',
  components: {
    TabContainer,
    AgentSettingsTab,
    BrowserSettingsTab,
    BrowserUseAgentTab,
    DeepResearchAgentTab,
    LoadSaveConfigTab
  },
  data() {
    return {
      tabs: [
        { name: 'agent-settings', label: '⚙️ Agent Settings' },
        { name: 'browser-settings', label: '🌐 Browser Settings' },
        { name: 'browser-use-agent', label: '🤖 Run Agent' },
        { name: 'deep-research', label: '🎁 Deep Research' },
        { name: 'load-save-config', label: '📁 Load & Save Config' }
      ],
      agentSettings: {},
      browserSettings: {},
      // 添加标志位来控制watch触发
      isConfigLoading: false
    }
  },
  created() {
    this.loadSettings()
  },
  watch: {
    agentSettings: {
      handler(val) {
        // 只有在非配置加载状态下才触发更新
        if (!this.isConfigLoading) {
          this.$storage.saveAgentSettings(val)
        }
      },
      deep: true
    },
    browserSettings: {
      handler(val) {
        // 只有在非配置加载状态下才触发更新
        if (!this.isConfigLoading) {
          this.$storage.saveBrowserSettings(val)
        }
      },
      deep: true
    }
  },
  methods: {
    loadSettings() {
      const savedAgentSettings = this.$storage.loadAgentSettings()
      const savedBrowserSettings = this.$storage.loadBrowserSettings()

      if (savedAgentSettings) {
        this.agentSettings = savedAgentSettings
      }

      if (savedBrowserSettings) {
        this.browserSettings = savedBrowserSettings
      }
    },

    handleTabChange(tabName) {
      console.log('Tab changed to:', tabName)
    },

    handleConfigLoaded(config) {
      console.log('Config loaded:', config)

      // 设置加载标志位，防止watch触发
      this.isConfigLoading = true

      // 直接使用后端返回的数据，不做复杂转换
      if (config.agentSettings) {
        this.agentSettings = JSON.parse(JSON.stringify(config.agentSettings))
        console.log('Agent settings applied:', this.agentSettings)
      }

      if (config.browserSettings) {
        this.browserSettings = JSON.parse(JSON.stringify(config.browserSettings))
        console.log('Browser settings applied:', this.browserSettings)
      }

      // 加载配置后同步到后端
      this.$nextTick(async () => {
        try {
          if (config.agentSettings) {
            await this.$api.agentSettings.update(config.agentSettings)
            console.log('Agent settings synced to backend after load')
          }

          if (config.browserSettings) {
            await this.$api.browserSettings.update(config.browserSettings)
            console.log('Browser settings synced to backend after load')
          }

          this.$message.success('Configuration loaded and synced to backend successfully')
        } catch (error) {
          console.error('Failed to sync settings after load:', error)
          this.$message.error('Configuration loaded but failed to sync to backend')
        } finally {
          // 重置加载标志位
          this.isConfigLoading = false
        }
      })
    }
  }
}
</script>

<style scoped>
.main-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 16px;
  color: #909399;
  margin: 0;
}
</style>