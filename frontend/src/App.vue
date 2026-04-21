<template>
  <div id="app">
    <el-container style="min-height: 100vh">
      <el-header style="background-color: #409EFF; color: white; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 15px;">
          <h2 style="margin: 0; color: white;">📚 小说翻译系统</h2>
          <el-tag v-if="llmBackendInfo" size="small" :type="llmBackendInfo.backend === 'ollama' ? 'success' : 'warning'">
            {{ llmBackendInfo.backend.toUpperCase() }}: {{ llmBackendInfo.model_name }}
          </el-tag>
        </div>
        <el-menu
          mode="horizontal"
          :ellipsis="false"
          background-color="#409EFF"
          text-color="#fff"
          active-text-color="#ffd044"
          :default-active="$route.path"
          router
          style="border: none; background: transparent;"
        >
          <el-menu-item index="/">🏠 首页</el-menu-item>
          <el-menu-item index="/translate">📝 翻译控制台</el-menu-item>
          <el-menu-item index="/glossary">📖 人名词典</el-menu-item>
        </el-menu>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { llmApi } from './api/request'

const llmBackendInfo = ref(null)

onMounted(async () => {
  try {
    const info = await llmApi.getBackendInfo()
    llmBackendInfo.value = info
  } catch (e) {
    console.error('获取LLM后端信息失败:', e)
  }
})
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
#app {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
