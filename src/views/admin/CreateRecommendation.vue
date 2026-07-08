<template>
  <div class="page">
    <div class="container">
      <div class="admin-header">
        <h2>创建推荐</h2>
        <button class="btn btn-ghost" @click="$router.back()">← 返回</button>
      </div>
      <div class="form-card"><p>创建推荐功能开发中，请先使用小程序管理后台。</p></div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.container { max-width: 600px; margin: 0 auto; padding: 24px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.admin-header h2 { font-size: 24px; font-weight: 800; }
.btn { padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; }
.btn-ghost { background: #f1f5f9; color: #475569; border: 1px solid #e8ecf2; }
.form-card { background: #fff; border-radius: 14px; padding: 60px 24px; border: 1px solid #e8ecf2; text-align: center; color: #94a3b8; }
</style>
