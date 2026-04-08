<template>
  <div class="agent-settings-tab">
    <el-form :model="settings" label-width="180px">
      <FormGroup title="System Prompt">
        <FormItem label="Override System Prompt">
          <el-input
            v-model="settings.overrideSystemPrompt"
            type="textarea"
            :rows="4"
            placeholder="Override the system prompt"
          ></el-input>
        </FormItem>
        <FormItem label="Extend System Prompt">
          <el-input
            v-model="settings.extendSystemPrompt"
            type="textarea"
            :rows="4"
            placeholder="Extend the system prompt"
          ></el-input>
        </FormItem>
      </FormGroup>

      <FormGroup title="MCP Server">
        <FormItem label="MCP Server JSON">
          <el-upload
            :auto-upload="false"
            :on-change="handleMcpFileChange"
            :show-file-list="false"
            accept=".json"
          >
            <el-button slot="trigger" size="small" type="primary">Select MCP JSON</el-button>
          </el-upload>
        </FormItem>
        <FormItem v-if="showMcpConfig" label="MCP Server Config">
          <el-input
            v-model="settings.mcpServerConfig"
            type="textarea"
            :rows="6"
            readonly
          ></el-input>
        </FormItem>
      </FormGroup>

      <FormGroup title="LLM Configuration">
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="LLM Provider">
              <el-select v-model="settings.llmProvider" @change="handleProviderChange">
                <el-option
                  v-for="provider in llmProviders"
                  :key="provider"
                  :label="provider"
                  :value="provider"
                ></el-option>
              </el-select>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="LLM Model Name">
              <el-select v-model="settings.llmModelName" filterable allow-create>
                <el-option
                  v-for="model in llmModels"
                  :key="model"
                  :label="model"
                  :value="model"
                ></el-option>
              </el-select>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="LLM Temperature">
              <el-slider
                v-model="settings.llmTemperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
              ></el-slider>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Use Vision">
              <el-switch v-model="settings.useVision"></el-switch>
            </FormItem>
          </el-col>
        </el-row>
        <FormItem v-if="settings.llmProvider === 'ollama'" label="Ollama Context Length">
          <el-slider
            v-model="settings.ollamaNumCtx"
            :min="256"
            :max="65536"
            :step="1"
            show-input
          ></el-slider>
        </FormItem>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Base URL">
              <el-input
                v-model="settings.llmBaseUrl"
                placeholder="API endpoint URL (if required)"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="API Key">
              <el-input
                v-model="settings.llmApiKey"
                type="password"
                placeholder="Your API key (leave blank to use .env)"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
      </FormGroup>

      <FormGroup title="Planner LLM Configuration">
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Planner LLM Provider">
              <el-select v-model="settings.plannerLlmProvider" @change="handlePlannerProviderChange" clearable>
                <el-option
                  v-for="provider in llmProviders"
                  :key="provider"
                  :label="provider"
                  :value="provider"
                ></el-option>
              </el-select>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Planner LLM Model Name">
              <el-select v-model="settings.plannerLlmModelName" filterable allow-create clearable>
                <el-option
                  v-for="model in plannerModels"
                  :key="model"
                  :label="model"
                  :value="model"
                ></el-option>
              </el-select>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Planner LLM Temperature">
              <el-slider
                v-model="settings.plannerLlmTemperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
              ></el-slider>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Use Vision(Planner LLM)">
              <el-switch v-model="settings.plannerUseVision"></el-switch>
            </FormItem>
          </el-col>
        </el-row>
        <FormItem v-if="settings.plannerLlmProvider === 'ollama'" label="Ollama Context Length">
          <el-slider
            v-model="settings.plannerOllamaNumCtx"
            :min="256"
            :max="65536"
            :step="1"
            show-input
          ></el-slider>
        </FormItem>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Base URL">
              <el-input
                v-model="settings.plannerLlmBaseUrl"
                placeholder="API endpoint URL (if required)"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="API Key">
              <el-input
                v-model="settings.plannerLlmApiKey"
                type="password"
                placeholder="Your API key (leave blank to use .env)"
              ></el-input>
            </FormItem>
          </el-col>
        </el-row>
      </FormGroup>

      <FormGroup>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Max Run Steps">
              <el-slider
                v-model="settings.maxSteps"
                :min="1"
                :max="1000"
                :step="1"
                show-input
              ></el-slider>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Max Number of Actions">
              <el-slider
                v-model="settings.maxActions"
                :min="1"
                :max="100"
                :step="1"
                show-input
              ></el-slider>
            </FormItem>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <FormItem label="Max Input Tokens">
              <el-input-number
                v-model="settings.maxInputTokens"
                :min="1"
                :step="1"
                :precision="0"
                style="width: 100%"
              ></el-input-number>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Tool Calling Method">
              <el-select v-model="settings.toolCallingMethod" filterable allow-create>
                <el-option label="function_calling" value="function_calling"></el-option>
                <el-option label="json_mode" value="json_mode"></el-option>
                <el-option label="raw" value="raw"></el-option>
                <el-option label="auto" value="auto"></el-option>
                <el-option label="tools" value="tools"></el-option>
                <el-option label="None" value="None"></el-option>
              </el-select>
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
  name: 'AgentSettingsTab',
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
      isInitialized: false,
      isUpdatingFromParent: false, // 防止循环更新的标志位
      settings: {
        overrideSystemPrompt: '',
        extendSystemPrompt: '',
        llmProvider: 'openai',
        llmModelName: '',
        llmTemperature: 0.6,
        useVision: true,
        ollamaNumCtx: 16000,
        llmBaseUrl: '',
        llmApiKey: '',
        plannerLlmProvider: '',
        plannerLlmModelName: '',
        plannerLlmTemperature: 0.6,
        plannerUseVision: false,
        plannerOllamaNumCtx: 16000,
        plannerLlmBaseUrl: '',
        plannerLlmApiKey: '',
        maxSteps: 100,
        maxActions: 10,
        maxInputTokens: 128000,
        toolCallingMethod: 'auto',
        mcpServerConfig: ''
      },
      showMcpConfig: false,
      llmProviders: ['openai', 'ollama', 'mistral'],
      llmModels: ['gpt-4', 'gpt-3.5-turbo'],
      plannerModels: []
    }
  },
  watch: {
    value: {
      handler(val) {
        // 使用标志位防止循环更新
        this.isUpdatingFromParent = true
        try {
          this.settings = { ...this.settings, ...val }
        } finally {
          // 使用 $nextTick 确保本次更新完成后再重置标志位
          this.$nextTick(() => {
            this.isUpdatingFromParent = false
          })
        }
      },
      immediate: true,
      deep: true
    },
    settings: {
      handler(val) {
        // 如果正在从父组件更新，则不触发 emit，避免循环
        if (this.isInitialized && !this.isUpdatingFromParent) {
          this.$emit('input', val)
        }
      },
      deep: true
    }
  },
  created() {
    this.isInitialized = false
  },
  mounted() {
    this.$nextTick(() => {
      this.isInitialized = true
    })
  },
  methods: {
    handleProviderChange(provider) {
      this.llmModels = this.getModelsForProvider(provider)
      this.settings.llmModelName = this.llmModels[0] || ''
    },
    handlePlannerProviderChange(provider) {
      if (provider) {
        this.plannerModels = this.getModelsForProvider(provider)
        this.settings.plannerLlmModelName = this.plannerModels[0] || ''
      } else {
        this.plannerModels = []
        this.settings.plannerLlmModelName = ''
      }
    },
    getModelsForProvider(provider) {
      const modelMap = {
        openai: ['gpt-4', 'gpt-3.5-turbo'],
        ollama: ['llama2', 'mistral', 'codellama'],
        mistral: ['mistral-large-latest', 'mistral-small-latest']
      }
      return modelMap[provider] || []
    },
    handleMcpFileChange(file) {
      if (file.raw) {
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            this.settings.mcpServerConfig = JSON.stringify(JSON.parse(e.target.result), null, 2)
            this.showMcpConfig = true
          } catch (error) {
            this.$message.error('Invalid JSON file')
          }
        }
        reader.readAsText(file.raw)
      }
    }
  }
}
</script>

<style scoped>
.agent-settings-tab {
  padding: 20px;
}
</style>