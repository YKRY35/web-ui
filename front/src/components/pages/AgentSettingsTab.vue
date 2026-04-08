<template>
  <div class="agent-settings-tab">
    <el-form :model="settings" label-width="180px">
      <FormGroup title="System Prompt">
        <FormItem label="Override System Prompt">
          <el-input
            v-model="settings.override_system_prompt"
            type="textarea"
            :rows="4"
            placeholder="Override the system prompt"
          ></el-input>
        </FormItem>
        <FormItem label="Extend System Prompt">
          <el-input
            v-model="settings.extend_system_prompt"
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
            v-model="settings.mcp_server_config"
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
              <el-select v-model="settings.llm_provider" @change="handleProviderChange">
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
              <el-select v-model="settings.llm_model_name" filterable allow-create>
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
                v-model="settings.llm_temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
              ></el-slider>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Use Vision">
              <el-switch v-model="settings.use_vision"></el-switch>
            </FormItem>
          </el-col>
        </el-row>
        <FormItem v-if="settings.llm_provider === 'ollama'" label="Ollama Context Length">
          <el-slider
            v-model="settings.ollama_num_ctx"
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
                v-model="settings.llm_base_url"
                placeholder="API endpoint URL (if required)"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="API Key">
              <el-input
                v-model="settings.llm_api_key"
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
              <el-select v-model="settings.planner_llm_provider" @change="handlePlannerProviderChange" clearable>
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
              <el-select v-model="settings.planner_llm_model_name" filterable allow-create clearable>
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
                v-model="settings.planner_llm_temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
              ></el-slider>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Use Vision(Planner LLM)">
              <el-switch v-model="settings.planner_use_vision"></el-switch>
            </FormItem>
          </el-col>
        </el-row>
        <FormItem v-if="settings.planner_llm_provider === 'ollama'" label="Ollama Context Length">
          <el-slider
            v-model="settings.planner_ollama_num_ctx"
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
                v-model="settings.planner_llm_base_url"
                placeholder="API endpoint URL (if required)"
              ></el-input>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="API Key">
              <el-input
                v-model="settings.planner_llm_api_key"
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
                v-model="settings.max_steps"
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
                v-model="settings.max_actions"
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
                v-model="settings.max_input_tokens"
                :min="1"
                :step="1"
                :precision="0"
                style="width: 100%"
              ></el-input-number>
            </FormItem>
          </el-col>
          <el-col :span="12">
            <FormItem label="Tool Calling Method">
              <el-select v-model="settings.tool_calling_method" filterable allow-create>
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
      settings: {
        override_system_prompt: '',
        extend_system_prompt: '',
        llm_provider: 'openai',
        llm_model_name: '',
        llm_temperature: 0.6,
        use_vision: true,
        ollama_num_ctx: 16000,
        llm_base_url: '',
        llm_api_key: '',
        planner_llm_provider: '',
        planner_llm_model_name: '',
        planner_llm_temperature: 0.6,
        planner_use_vision: false,
        planner_ollama_num_ctx: 16000,
        planner_llm_base_url: '',
        planner_llm_api_key: '',
        max_steps: 100,
        max_actions: 10,
        max_input_tokens: 128000,
        tool_calling_method: 'auto',
        mcp_server_config: ''
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
    }
  },
  methods: {
    handleProviderChange(provider) {
      this.llmModels = this.getModelsForProvider(provider)
      this.settings.llm_model_name = this.llmModels[0] || ''
    },
    handlePlannerProviderChange(provider) {
      if (provider) {
        this.plannerModels = this.getModelsForProvider(provider)
        this.settings.planner_llm_model_name = this.plannerModels[0] || ''
      } else {
        this.plannerModels = []
        this.settings.planner_llm_model_name = ''
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
            this.settings.mcp_server_config = JSON.stringify(JSON.parse(e.target.result), null, 2)
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