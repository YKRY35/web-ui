<template>
  <div class="deep-research-agent-tab">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <div slot="header" class="clearfix">
            <span>Deep Research Configuration</span>
          </div>
          <el-form :model="settings" label-width="180px">
            <FormItem label="Research Task">
              <el-input
                v-model="settings.research_task"
                placeholder="Enter your research topic..."
                type="textarea"
                :rows="5"
              ></el-input>
            </FormItem>
            <el-row :gutter="20">
              <el-col :span="8">
                <FormItem label="Resume Task ID">
                  <el-input
                    v-model="settings.resume_task_id"
                    placeholder="Leave empty for new task"
                  ></el-input>
                </FormItem>
              </el-col>
              <el-col :span="8">
                <FormItem label="Parallel Agent Num">
                  <el-input-number
                    v-model="settings.parallel_num"
                    :min="1"
                    :max="5"
                    style="width: 100%"
                  ></el-input-number>
                </FormItem>
              </el-col>
              <el-col :span="8">
                <FormItem label="Research Save Dir">
                  <el-input
                    v-model="settings.save_dir"
                    placeholder="./tmp/deep_research"
                  ></el-input>
                </FormItem>
              </el-col>
            </el-row>
            <FormItem label="MCP Server">
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
          </el-form>
          <el-row class="button-row">
            <el-button
              :disabled="isRunning"
              type="primary"
              @click="handleStart"
            >▶️ Run</el-button>
            <el-button
              :disabled="!isRunning"
              type="danger"
              @click="handleStop"
            >⏹️ Stop</el-button>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="reportContent">
      <el-col :span="24">
        <el-card>
          <div slot="header" class="clearfix">
            <span>Research Report</span>
            <div class="toolbar">
              <el-button
                v-if="reportFile"
                type="success"
                size="small"
                @click="handleDownload"
              >📥 Download Report</el-button>
            </div>
          </div>
          <div v-html="formattedReport" class="report-content"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import FormItem from '@/components/common/FormItem.vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

export default {
  name: 'DeepResearchAgentTab',
  components: {
    FormItem
  },
  data() {
    return {
      settings: {
        research_task: '',
        resume_task_id: '',
        parallel_num: 1,
        save_dir: './tmp/deep_research',
        mcp_server_config: ''
      },
      isRunning: false,
      reportContent: '',
      reportFile: '',
      showMcpConfig: false,
      currentTaskId: null
    }
  },
  computed: {
    formattedReport() {
      return marked(this.reportContent, {
        highlight: function(code, lang) {
          if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(lang, code).value
          }
          return hljs.highlightAuto(code).value
        },
        breaks: true
      })
    }
  },
  methods: {
    async handleStart() {
      if (!this.settings.research_task.trim()) {
        this.$message.warning('Please enter a research task')
        return
      }

      this.isRunning = true
      this.reportContent = 'Starting research...'
      this.reportFile = ''

      try {
        const response = await this.$api.deepResearch.run({
          topic: this.settings.research_task,
          resume_task_id: this.settings.resume_task_id || null,
          parallel_num: this.settings.parallel_num,
          save_dir: this.settings.save_dir
        })

        if (response.task_id) {
          this.currentTaskId = response.task_id
          await this.startMonitoring()
        }
      } catch (error) {
        this.$message.error('Failed to start research: ' + error.message)
        this.isRunning = false
      }
    },

    async handleStop() {
      if (!this.currentTaskId) {
        return
      }

      try {
        await this.$api.deepResearch.stop(this.currentTaskId)
        this.isRunning = false
      } catch (error) {
        this.$message.error('Failed to stop research: ' + error.message)
      }
    },

    async handleDownload() {
      if (!this.reportFile) {
        return
      }
      window.open(this.reportFile)
    },

    async handleMcpFileChange(file) {
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
    },

    async startMonitoring() {
      while (this.isRunning) {
        try {
          const report = await this.$api.deepResearch.getReport(this.currentTaskId)
          if (report && report.content) {
            this.reportContent = report.content
            if (report.file_path) {
              this.reportFile = report.file_path
            }
          }
        } catch (error) {
          console.error('Report monitoring error:', error)
        }
        await this.sleep(2000)
      }
    },

    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }
  }
}
</script>

<style scoped>
.deep-research-agent-tab {
  padding: 20px;
}

.button-row {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.toolbar {
  float: right;
}

.report-content {
  padding: 20px 0;
  font-size: 14px;
  line-height: 1.6;
}

.report-content h1,
.report-content h2,
.report-content h3,
.report-content h4,
.report-content h5,
.report-content h6 {
  margin: 20px 0 10px;
  font-weight: bold;
  line-height: 1.2;
}

.report-content p {
  margin-bottom: 10px;
}

.report-content code {
  background-color: #f4f4f4;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

.report-content pre {
  background-color: #f4f4f4;
  padding: 15px;
  border-radius: 5px;
  overflow-x: auto;
}

.report-content blockquote {
  border-left: 4px solid #ddd;
  padding-left: 15px;
  margin: 0;
  color: #666;
}
</style>