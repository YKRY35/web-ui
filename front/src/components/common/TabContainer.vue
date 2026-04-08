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