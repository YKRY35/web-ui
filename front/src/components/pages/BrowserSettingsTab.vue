<template>
  <div class="browser-settings-tab">
    <el-form :model="settings" label-width="180px">
      <FormGroup title="Browser Configuration">
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Browser Binary Path">
              <el-input
                v-model="settings.browser_binary_path"
                placeholder="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Browser User Data Dir">
              <el-input
                v-model="settings.browser_user_data_dir"
                placeholder="Leave empty for default"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="6">
            <FormItem label="Use Own Browser">
              <el-switch v-model="settings.use_own_browser"></el-switch>
            </FormItem>
          </el-col>
          <el-col :span="6">
            <FormItem label="Keep Browser Open">
              <el-switch v-model="settings.keep_browser_open"></el-switch>
            </FormItem>
          </el-col>
          <el-col :span="6">
            <FormItem label="Headless Mode">
              <el-switch v-model="settings.headless"></el-switch>
            </FormItem>
          </el-col>
          <el-col :span="6">
            <FormItem label="Disable Security">
              <el-switch v-model="settings.disable_security"></el-switch>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Window Width">
              <el-input-number
                v-model="settings.window_w"
                :min="800"
                :max="2560"
                style="width: 100%"
              ></el-input-number>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Window Height">
              <el-input-number
                v-model="settings.window_h"
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
                v-model="settings.cdp_url"
                placeholder="http://localhost:9222"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="WSS URL">
              <el-input
                v-model="settings.wss_url"
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
                v-model="settings.save_recording_path"
                placeholder="./tmp/record_videos"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Trace Path">
              <el-input
                v-model="settings.save_trace_path"
                placeholder="./tmp/traces"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Agent History Save Path">
              <el-input
                v-model="settings.save_agent_history_path"
                placeholder="./tmp/agent_history"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Download Path">
              <el-input
                v-model="settings.save_download_path"
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
        browser_binary_path: '',
        browser_user_data_dir: '',
        use_own_browser: false,
        keep_browser_open: true,
        headless: false,
        disable_security: false,
        save_recording_path: '',
        save_trace_path: '',
        save_agent_history_path: './tmp/agent_history',
        save_download_path: './tmp/downloads',
        cdp_url: '',
        wss_url: '',
        window_h: 1100,
        window_w: 1280
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
    'settings.keep_browser_open'() {
      this.handleBrowserSettingsChange()
    },
    'settings.disable_security'() {
      this.handleBrowserSettingsChange()
    },
    'settings.use_own_browser'() {
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