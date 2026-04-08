<template>
  <div class="main-view">
    <div class="header">
      <h1>🌐 Browser Use WebUI</h1>
      <p class="subtitle">Control your browser with AI assistance</p>
    </div>

    <TabContainer :tabs="tabs" @tab-change="handleTabChange">
      <template #agent-settings>
        <AgentSettingsTab v-model="agentSettings" />
      </template>
      <template #browser-settings>
        <BrowserSettingsTab v-model="browserSettings" />
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
      browserSettings: {}
    }
  },
  created() {
    this.loadSettings()
  },
  watch: {
    agentSettings: {
      handler(val) {
        this.$storage.saveAgentSettings(val)
      },
      deep: true
    },
    browserSettings: {
      handler(val) {
        this.$storage.saveBrowserSettings(val)
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

      // 直接使用后端返回的数据，不做复杂转换
      // 避免使用 Object.assign 或扩展运算符，直接替换对象以断开引用
      if (config.agentSettings) {
        this.agentSettings = JSON.parse(JSON.stringify(config.agentSettings))
        console.log('Agent settings applied:', this.agentSettings)
      }

      if (config.browserSettings) {
        this.browserSettings = JSON.parse(JSON.stringify(config.browserSettings))
        console.log('Browser settings applied:', this.browserSettings)
      }

      this.$message.success('Configuration loaded successfully')
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