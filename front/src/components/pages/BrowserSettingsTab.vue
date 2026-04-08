<template>
  <div class="browser-settings-tab">
    <el-form :model="settings" label-width="180px">
      <FormGroup title="Browser Configuration">
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Browser Binary Path">
              <el-input
                v-model="settings.browserBinaryPath"
                placeholder="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Browser User Data Dir">
              <el-input
                v-model="settings.browserUserDataDir"
                placeholder="Leave empty for default"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="6">
            <FormItem label="Use Own Browser">
              <el-switch v-model="settings.useOwnBrowser"></el-switch>
            </FormItem>
          </el-col>
          <el-col :span="6">
            <FormItem label="Keep Browser Open">
              <el-switch v-model="settings.keepBrowserOpen"></el-switch>
            </FormItem>
          </el-col>
          <el-col :span="6">
            <FormItem label="Headless Mode">
              <el-switch v-model="settings.headless"></el-switch>
            </FormItem>
          </el-col>
          <el-col :span="6">
            <FormItem label="Disable Security">
              <el-switch v-model="settings.disableSecurity"></el-switch>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Window Width">
              <el-input-number
                v-model="settings.windowWidth"
                :min="800"
                :max="2560"
                style="width: 100%"
              ></el-input-number>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Window Height">
              <el-input-number
                v-model="settings.windowHeight"
                :min="600"
                :max="1440"
                style="width: 100%"
              ></el-input-number>
            </FormItem>
          </el-col>
        </el-row>
      </FormGroup>

      <FormGroup title="Remote Debugging">
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="CDP URL">
              <el-input
                v-model="settings.cdpUrl"
                placeholder="http://localhost:9222"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="WSS URL">
              <el-input
                v-model="settings.wssUrl"
                placeholder="wss://chrome-devtools..."
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
      </FormGroup>

      <FormGroup title="Save Paths">
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Recording Path">
              <el-input
                v-model="settings.saveRecordingPath"
                placeholder="./tmp/record_videos"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Trace Path">
              <el-input
                v-model="settings.saveTracePath"
                placeholder="./tmp/traces"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Agent History Save Path">
              <el-input
                v-model="settings.saveAgentHistoryPath"
                placeholder="./tmp/agent_history"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Download Path">
              <el-input
                v-model="settings.saveDownloadPath"
                placeholder="./tmp/downloads"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
      </FormGroup>
    </el-form>
  </div>
</template>

<script>
import FormGroup from '@/components/common/FormGroup.vue'
import FormItem from '@/components/common/FormItem.vue'
import { transformGradioConfig, mergeWithDefaults, getConfigValue } from '@/utils/configHelper'

export default {
  name: 'BrowserSettingsTab',
  components: {
    FormGroup,
    FormItem
  },
  props: {
    value: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      settings: {
        browserBinaryPath: '',
        browserUserDataDir: '',
        useOwnBrowser: false,
        keepBrowserOpen: true,
        headless: false,
        disableSecurity: false,
        saveRecordingPath: '',
        saveTracePath: '',
        saveAgentHistoryPath: './tmp/agent_history',
        saveDownloadPath: './tmp/downloads',
        cdpUrl: '',
        wssUrl: '',
        windowHeight: 1100,
        windowWidth: 1280
      }
    }
  },
  watch: {
    value: {
      handler(val) {
        this.settings = { ...this.settings, ...val }
      },
      immediate: true,
      deep: true
    },
    settings: {
      handler(val) {
        this.$emit('input', val)
      },
      deep: true
    },
    'settings.headless'() {
      this.handleBrowserSettingsChange()
    },
    'settings.keepBrowserOpen'() {
      this.handleBrowserSettingsChange()
    },
    'settings.disableSecurity'() {
      this.handleBrowserSettingsChange()
    },
    'settings.useOwnBrowser'() {
      this.handleBrowserSettingsChange()
    }
  },
  methods: {
    handleBrowserSettingsChange() {
      this.$emit('settings-change', this.settings)
    }
  }
}
</script>

<style scoped>
.browser-settings-tab {
  padding: 20px;
}
</style>