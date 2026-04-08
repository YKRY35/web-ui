<template>
  <el-form-item :label="label" :prop="prop" class="form-item">
    <slot></slot>
    <div v-if="description" class="description">{{ description }}</div>
  </el-form-item>
</template>

<script>
export default {
  name: 'FormItem',
  props: {
    label: {
      type: String,
      default: ''
    },
    prop: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
.form-item .description {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}
</style>