<template>
  <el-dialog
    :visible.sync="dialogVisible"
    title="设置"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="settings-content">
      <div class="setting-item">
        <div class="setting-label">
          <i class="el-icon-sunny"></i>
          <span>主题模式</span>
        </div>
        <el-radio-group v-model="localSettings.theme" @change="handleThemeChange">
          <el-radio label="light">
            <i class="el-icon-sunny"></i> 浅色模式
          </el-radio>
          <el-radio label="dark">
            <i class="el-icon-moon"></i> 深色模式
          </el-radio>
        </el-radio-group>
      </div>
    </div>

    <span slot="footer" class="dialog-footer">
      <el-button @click="handleClose">关闭</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: 'SettingsDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    settings: {
      type: Object,
      default: () => ({ theme: 'light' })
    }
  },
  data() {
    return {
      dialogVisible: false,
      localSettings: {
        theme: 'light'
      }
    }
  },
  watch: {
    visible(val) {
      this.dialogVisible = val
    },
    settings: {
      handler(val) {
        if (val) {
          this.localSettings = { ...val }
        }
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    handleThemeChange(value) {
      this.$emit('theme-change', value)
    },
    handleClose() {
      this.$emit('update:visible', false)
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.settings-content {
  padding: 10px 0;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid #ebeef5;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.setting-label i {
  font-size: 18px;
  color: #409eff;
}

.dialog-footer {
  text-align: right;
}

/* Dark theme styles for SettingsDialog */
#app.dark .setting-label {
  color: #e0e0e0;
}

#app.dark .setting-label i {
  color: #409eff;
}
</style>
