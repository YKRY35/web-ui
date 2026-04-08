<template>
  <div class="load-save-config-tab">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <div slot="header" class="clearfix">
            <span>Load & Save Configuration</span>
          </div>
          <el-form label-width="180px">
            <FormItem label="Load UI Settings">
              <el-upload
                :auto-upload="false"
                :on-change="handleLoadFileChange"
                :show-file-list="false"
                accept=".json"
              >
                <el-button slot="trigger" size="small" type="primary">Select Config File</el-button>
                <el-button v-if="selectedFile" slot="tip" size="small" type="info">{{ selectedFile.name }}</el-button>
              </el-upload>
            </FormItem>
            <FormItem>
              <el-button
                :disabled="!selectedFile"
                type="primary"
                @click="handleLoadConfig"
              >Load Config</el-button>
              <el-button
                type="success"
                @click="handleSaveConfig"
              >Save Config</el-button>
            </FormItem>
            <FormItem label="Status">
              <el-input
                v-model="status"
                type="textarea"
                :rows="2"
                readonly
              ></el-input>
            </FormItem>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import FormItem from '@/components/common/FormItem.vue'

export default {
  name: 'LoadSaveConfigTab',
  components: {
    FormItem
  },
  data() {
    return {
      selectedFile: null,
      status: ''
    }
  },
  methods: {
    handleLoadFileChange(file) {
      this.selectedFile = file.raw
      this.status = ''
    },

    async handleLoadConfig() {
      debugger
      if (!this.selectedFile) {
        this.$message.warning('Please select a config file first')
        return
      }

      try {
        const result = await this.$api.config.load(this.selectedFile)
        this.status = `Successfully loaded config: ${this.selectedFile.name}`
        this.$message.success('Configuration loaded successfully')

        // 传递解析后的配置数据到父组件
        this.$emit('config-loaded', {
          agentSettings: result.agentSettings,
          browserSettings: result.browserSettings
        })
      } catch (error) {
        this.status = `Failed to load config: ${error.message}`
        this.$message.error('Failed to load config')
      }
    },

    async handleSaveConfig() {
      try {
        await this.$api.config.save()
        this.status = 'Configuration saved successfully'
        this.$message.success('Configuration saved successfully')
      } catch (error) {
        this.status = `Failed to save config: ${error.message}`
        this.$message.error('Failed to save config')
      }
    }
  }
}
</script>

<style scoped>
.load-save-config-tab {
  padding: 20px;
}
</style>