<template>
  <el-tabs v-model="activeTab" @tab-click="handleTabClick">
    <el-tab-pane
      v-for="tab in tabs"
      :key="tab.name"
      :label="tab.label"
      :name="tab.name"
    >
      <slot :name="tab.name"></slot>
    </el-tab-pane>
  </el-tabs>
</template>

<script>
export default {
  name: 'TabContainer',
  props: {
    tabs: {
      type: Array,
      required: true
    },
    defaultTab: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      activeTab: this.defaultTab || this.tabs[0]?.name || ''
    }
  },
  watch: {
    defaultTab(val) {
      this.activeTab = val
    }
  },
  methods: {
    handleTabClick(tab) {
      this.$emit('tab-change', tab.name)
    }
  }
}
</script>

<style>
/* Dark theme styles for TabContainer */
#app.dark .el-tabs__item {
  color: #909399;
}

#app.dark .el-tabs__item:hover {
  color: #409eff;
}

#app.dark .el-tabs__item.is-active {
  color: #409eff;
}

#app.dark .el-tabs__nav-wrap::after {
  background-color: #3d3d3d;
}

#app.dark .el-tabs__content {
  color: #e0e0e0;
}
</style>