<template>
  <div class="translate-container">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>📝 翻译控制台</span>
          <el-tag v-if="taskStatus" :type="getStatusType(taskStatus.status)">
            {{ getStatusText(taskStatus.status) }}
          </el-tag>
        </div>
      </template>
      
      <div v-if="!currentTaskId" class="no-task">
        <el-empty description="请先上传小说文件">
          <el-button type="primary" @click="$router.push('/')">返回首页上传</el-button>
        </el-empty>
      </div>
      
      <div v-else>
        <el-alert
          :title="`任务ID: ${currentTaskId}`"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px;"
        />
        
        <div class="language-display">
          <el-tag type="primary" size="large">{{ sourceLang }}</el-tag>
          <el-icon :size="24" style="margin: 0 15px;"><Right /></el-icon>
          <el-tag type="success" size="large">{{ targetLang }}</el-tag>
        </div>
        
        <div v-if="taskStatus" class="progress-section">
          <h3>翻译进度</h3>
          <el-progress 
            :percentage="taskStatus.progress || 0" 
            :status="getProgressStatus(taskStatus.status)"
            :stroke-width="20"
            style="margin: 20px 0;"
          />
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="当前章节">
              第 {{ taskStatus.current_chapter }} / {{ taskStatus.total_chapters }} 章
            </el-descriptions-item>
            <el-descriptions-item label="完成度">
              {{ taskStatus.progress }}%
            </el-descriptions-item>
          </el-descriptions>
          
          <div v-if="taskStatus.error" class="error-section">
            <el-alert
              :title="'错误: ' + taskStatus.error"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </div>
        
        <div class="action-buttons">
          <el-button 
            v-if="!taskStatus || taskStatus.status === 'pending' || taskStatus.status === 'chapters_ready'"
            type="primary" 
            size="large"
            @click="startTranslation"
            :loading="starting"
          >
            开始翻译
          </el-button>
          
          <el-button 
            v-if="taskStatus && taskStatus.status === 'completed'"
            type="success" 
            size="large"
            @click="downloadNovel"
          >
            <el-icon><Download /></el-icon>
            下载译文
          </el-button>
          
          <el-button 
            @click="refreshProgress"
            :loading="refreshing"
          >
            刷新进度
          </el-button>
          
          <el-button 
            type="warning"
            @click="$router.push('/glossary')"
          >
            管理人名词典
          </el-button>
        </div>
        
        <div v-if="chapters.length > 0" class="chapters-list">
          <h3>章节列表</h3>
          <el-table :data="chapters" stripe style="width: 100%" max-height="400">
            <el-table-column prop="chapter_number" label="序号" width="80" />
            <el-table-column prop="title" label="章节标题" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag 
                  :type="row.translated_content ? 'success' : 'info'"
                  size="small"
                >
                  {{ row.translated_content ? '已翻译' : '待翻译' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Right, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { translateApi, novelApi } from '../api/request'

const route = useRoute()
const currentTaskId = ref('')
const taskStatus = ref(null)
const chapters = ref([])
const starting = ref(false)
const refreshing = ref(false)
const sourceLang = ref('Chinese')
const targetLang = ref('English')

let progressInterval = null

onMounted(() => {
  currentTaskId.value = route.query.task_id || localStorage.getItem('currentTaskId') || ''
  sourceLang.value = localStorage.getItem('sourceLanguage') || 'Chinese'
  targetLang.value = localStorage.getItem('targetLanguage') || 'English'
  
  if (currentTaskId.value) {
    refreshProgress()
    loadChapters()
    startAutoRefresh()
  }
})

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})

const startAutoRefresh = () => {
  progressInterval = setInterval(async () => {
    await refreshProgress()
    
    // 翻译过程中实时更新章节状态
    if (taskStatus.value && taskStatus.value.status === 'translating') {
      await loadChapters()
    }
    
    if (taskStatus.value && taskStatus.value.status === 'completed') {
      clearInterval(progressInterval)
      // 完成后最终加载一次完整的章节状态
      await loadChapters()
    }
  }, 3000)  // 改为3秒刷新一次，更及时
}

const startTranslation = async () => {
  starting.value = true
  
  try {
    await translateApi.start(currentTaskId.value, sourceLang.value, targetLang.value)
    ElMessage.success('翻译任务已启动')
    startAutoRefresh()
  } catch (error) {
    ElMessage.error('启动翻译失败: ' + (error.message || '未知错误'))
  } finally {
    starting.value = false
  }
}

const refreshProgress = async () => {
  refreshing.value = true
  
  try {
    taskStatus.value = await translateApi.getProgress(currentTaskId.value)
  } catch (error) {
    console.error('获取进度失败:', error)
  } finally {
    refreshing.value = false
  }
}

const loadChapters = async () => {
  try {
    const result = await novelApi.getChapters(currentTaskId.value)
    chapters.value = result.chapters || []
  } catch (error) {
    console.error('加载章节失败:', error)
  }
}

const downloadNovel = async () => {
  try {
    const response = await novelApi.download(currentTaskId.value)
    
    const blob = new Blob([response], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'translated_novel.txt'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  }
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    splitting: 'warning',
    chapters_ready: 'success',
    translating: '',
    completed: 'success',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    splitting: '正在识别章节...',
    chapters_ready: '就绪',
    translating: '翻译中...',
    completed: '已完成',
    error: '出错'
  }
  return texts[status] || status
}

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'error') return 'exception'
  return ''
}
</script>

<style scoped>
.translate-container {
  max-width: 1200px;
  margin: 30px auto;
}

.no-task {
  text-align: center;
  padding: 50px 0;
}

.language-display {
  text-align: center;
  margin: 20px 0;
}

.progress-section {
  margin: 30px 0;
}

.progress-section h3 {
  margin-bottom: 15px;
  color: #303133;
}

.error-section {
  margin-top: 20px;
}

.action-buttons {
  margin: 30px 0;
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.chapters-list {
  margin-top: 30px;
}

.chapters-list h3 {
  margin-bottom: 15px;
  color: #303133;
}
</style>
