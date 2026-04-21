<template>
  <div class="home-container">
    <el-card class="upload-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>📄 上传小说</span>
          <el-tag type="info">支持 .txt 格式</el-tag>
        </div>
      </template>
      
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        accept=".txt"
        class="upload-area"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将小说文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">只能上传 txt 格式的小说文件</div>
        </template>
      </el-upload>
      
      <div v-if="selectedFile" class="file-info">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="文件名">{{ selectedFile.name }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatFileSize(selectedFile.size) }}</el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div class="language-selector">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="源语言">
              <el-select v-model="sourceLanguage" placeholder="选择源语言" style="width: 100%;">
                <el-option label="中文" value="Chinese" />
                <el-option label="英文" value="English" />
                <el-option label="日文" value="Japanese" />
                <el-option label="韩文" value="Korean" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标语言">
              <el-select v-model="targetLanguage" placeholder="选择目标语言" style="width: 100%;">
                <el-option label="英文" value="English" />
                <el-option label="中文" value="Chinese" />
                <el-option label="日文" value="Japanese" />
                <el-option label="韩文" value="Korean" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
      
      <div class="action-buttons">
        <el-button 
          type="primary" 
          size="large"
          @click="handleUpload"
          :loading="uploading"
          :disabled="!selectedFile"
        >
          上传并识别章节
        </el-button>
        
        <el-button 
          v-if="taskId"
          type="success" 
          size="large"
          @click="goToTranslate"
        >
          进入翻译控制台 →
        </el-button>
      </div>
      
      <el-alert
        v-if="uploadMessage"
        :title="uploadMessage"
        :type="uploadSuccess ? 'success' : 'error'"
        show-icon
        :closable="false"
        style="margin-top: 20px;"
      />
    </el-card>
    
    <el-card class="feature-card">
      <template #header>
        <span>✨ 系统特性</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="feature-item">
            <el-icon :size="40" color="#409EFF"><Document /></el-icon>
            <h4>自动章节识别</h4>
            <p>智能识别章节标题，自动拆分小说</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="feature-item">
            <el-icon :size="40" color="#67C23A"><User /></el-icon>
            <h4>人名一致性保障</h4>
            <p>全局人名词典，跨章节统一翻译</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="feature-item">
            <el-icon :size="40" color="#E6A23C"><Monitor /></el-icon>
            <h4>多Agent协作</h4>
            <p>6个专业Agent分工处理翻译任务</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled, Document, User, Monitor } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { novelApi } from '../api/request'

const router = useRouter()
const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const taskId = ref('')
const uploadMessage = ref('')
const uploadSuccess = ref(false)
const sourceLanguage = ref('Chinese')
const targetLanguage = ref('English')

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  uploadMessage.value = ''
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleUpload = async () => {
  if (!selectedFile.value) return
  
  uploading.value = true
  uploadMessage.value = ''
  
  try {
    const result = await novelApi.upload(selectedFile.value)
    taskId.value = result.task_id
    
    localStorage.setItem('currentTaskId', result.task_id)
    localStorage.setItem('sourceLanguage', sourceLanguage.value)
    localStorage.setItem('targetLanguage', targetLanguage.value)
    
    await novelApi.autoChapter(result.task_id)
    
    uploadSuccess.value = true
    uploadMessage.value = `上传成功！共识别 ${result.text_length} 字符`
    ElMessage.success('上传并识别章节成功')
    
  } catch (error) {
    uploadSuccess.value = false
    uploadMessage.value = `上传失败: ${error.message || '未知错误'}`
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const goToTranslate = () => {
  router.push({ name: 'Translate' })
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 30px auto;
}

.upload-card {
  margin-bottom: 30px;
}

.upload-area {
  width: 100%;
}

.file-info {
  margin-top: 20px;
}

.language-selector {
  margin-top: 25px;
}

.action-buttons {
  margin-top: 25px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.feature-card {
  margin-bottom: 30px;
}

.feature-item {
  text-align: center;
  padding: 20px;
}

.feature-item h4 {
  margin: 15px 0 10px;
  color: #303133;
}

.feature-item p {
  color: #909399;
  font-size: 14px;
  line-height: 1.6;
}
</style>
