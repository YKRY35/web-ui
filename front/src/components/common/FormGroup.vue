<template>
  <div class="form-group">
    <el-card class="box-card" v-if="title">
      <div slot="header" class="clearfix">
        <span>{{ title }}</span>
      </div>
      <slot></slot>
    </el-card>
    <div v-else class="form-group-content">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FormGroup',
  props: {
    title: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
.form-group {
  margin-bottom: 20px;
}
.form-group-content {
  padding: 10px 0;
}
</style>