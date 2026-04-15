<template>
  <div id="app" :class="currentTheme">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      currentTheme: 'light'
    }
  },
  created() {
    // 监听主题变化事件
    this.$root.$on('theme-change', this.handleThemeChange)

    // 加载保存的主题设置
    this.loadTheme()
  },
  beforeDestroy() {
    this.$root.$off('theme-change', this.handleThemeChange)
  },
  methods: {
    handleThemeChange(theme) {
      this.currentTheme = theme
      document.documentElement.setAttribute('data-theme', theme)
    },
    loadTheme() {
      const savedThemeSettings = this.$storage.loadThemeSettings()
      if (savedThemeSettings && savedThemeSettings.theme) {
        this.handleThemeChange(savedThemeSettings.theme)
      }
    }
  }
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  margin: 0;
  padding: 0;
  transition: background-color 0.3s, color 0.3s;
}

/* Light theme (default) */
#app.light {
  background-color: #f5f7fa;
  color: #303133;
}

/* Dark theme */
#app.dark {
  background-color: #1a1a1a;
  color: #e0e0e0;
}

/* Dark theme global styles */
#app.dark .el-card {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
  color: #e0e0e0;
}

#app.dark .el-input__inner {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
  color: #e0e0e0;
}

#app.dark .el-select .el-input__inner {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
  color: #e0e0e0;
}

#app.dark .el-textarea__inner {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
  color: #e0e0e0;
}

#app.dark .el-button {
  border-color: #3d3d3d;
}

#app.dark .el-button--default {
  background-color: #2d2d2d;
  color: #e0e0e0;
}

#app.dark .el-tabs__item {
  color: #909399;
}

#app.dark .el-tabs__item.is-active {
  color: #409eff;
}

#app.dark .el-tabs__nav-wrap::after {
  background-color: #3d3d3d;
}

#app.dark .el-form-item__label {
  color: #e0e0e0;
}

#app.dark .el-dialog {
  background-color: #2d2d2d;
}

#app.dark .el-dialog__header {
  background-color: #2d2d2d;
}

#app.dark .el-dialog__title {
  color: #e0e0e0;
}

#app.dark .el-dialog__body {
  background-color: #2d2d2d;
  color: #e0e0e0;
}

#app.dark .el-dialog__footer {
  background-color: #2d2d2d;
}

#app.dark .el-radio__label {
  color: #e0e0e0;
}

#app.dark .el-collapse {
  border-color: #3d3d3d;
}

#app.dark .el-collapse-item__header {
  background-color: #2d2d2d;
  color: #e0e0e0;
  border-color: #3d3d3d;
}

#app.dark .el-collapse-item__wrap {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
}

#app.dark .el-collapse-item__content {
  color: #e0e0e0;
}

#app.dark h1,
#app.dark h2,
#app.dark h3,
#app.dark h4,
#app.dark h5,
#app.dark h6 {
  color: #e0e0e0;
}

#app.dark p {
  color: #b0b0b0;
}

#app.dark .el-message-box {
  background-color: #2d2d2d;
}

#app.dark .el-message-box__title {
  color: #e0e0e0;
}

#app.dark .el-message-box__content {
  color: #e0e0e0;
}

#app.dark .el-dropdown-menu {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
}

#app.dark .el-dropdown-menu__item {
  color: #e0e0e0;
}

#app.dark .el-select-dropdown {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
}

#app.dark .el-select-dropdown__item {
  color: #e0e0e0;
}

#app.dark .el-select-dropdown__item.hover {
  background-color: #3d3d3d;
}

#app.dark .el-popper {
  background-color: #2d2d2d;
  border-color: #3d3d3d;
}

#app.dark .el-tooltip__popper {
  background-color: #2d2d2d;
  color: #e0e0e0;
}
</style>
