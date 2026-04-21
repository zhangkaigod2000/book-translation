<template>
  <div class="glossary-container">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>📖 全局人名词典管理</span>
          <el-button type="primary" size="small" @click="loadGlossary">
            刷新列表
          </el-button>
        </div>
      </template>
      
      <el-alert
        title="提示：修改人名后，后续未翻译的章节将使用新翻译。锁定的人名将无法被自动修改。"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      />
      
      <div class="stats-bar">
        <el-statistic title="总词条数" :value="glossary.length" />
        <el-statistic title="已锁定" :value="lockedCount" />
        <el-statistic title="人物名" :value="personCount" />
        <el-statistic title="地名/其他" :value="otherCount" />
      </div>
      
      <el-input
        v-model="searchText"
        placeholder="搜索原名或译文..."
        prefix-icon="Search"
        clearable
        style="margin-bottom: 20px;"
      />
      
      <el-table 
        :data="filteredGlossary" 
        stripe 
        style="width: 100%"
        max-height="600"
        v-loading="loading"
      >
        <el-table-column prop="original" label="原文" min-width="150" />
        <el-table-column prop="translation" label="译文" min-width="150">
          <template #default="{ row }">
            <span v-if="editingRow !== row.original">{{ row.translation }}</span>
            <el-input
              v-else
              v-model="editTranslation"
              size="small"
              @keyup.enter="saveEdit(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="entity_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.entity_type)" size="small">
              {{ getTypeLabel(row.entity_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="aliases" label="别名" min-width="150">
          <template #default="{ row }">
            <span>{{ Array.isArray(row.aliases) ? row.aliases.join(', ') : row.aliases }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="locked" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.locked ? 'danger' : 'success'" size="small">
              {{ row.locked ? '已锁' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="editingRow !== row.original"
                size="small" 
                @click="startEdit(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-else
                size="small" 
                type="success"
                @click="saveEdit(row)"
              >
                保存
              </el-button>
              
              <el-button 
                size="small"
                :type="row.locked ? 'warning' : 'info'"
                @click="toggleLock(row)"
              >
                {{ row.locked ? '解锁' : '锁定' }}
              </el-button>
              
              <el-button 
                size="small" 
                type="danger"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="filteredGlossary.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无词典数据，请先开始翻译任务" />
      </div>
    </el-card>
    
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="400px"
    >
      <p>确定要删除 "{{ deleteTarget?.original }}" 这个词条吗？</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { glossaryApi } from '../api/request'

const glossary = ref([])
const loading = ref(false)
const searchText = ref('')
const editingRow = ref('')
const editTranslation = ref('')
const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)

// 获取当前任务ID
const currentTaskId = localStorage.getItem('currentTaskId') || ''

const filteredGlossary = computed(() => {
  if (!searchText.value) return glossary.value
  
  const search = searchText.value.toLowerCase()
  return glossary.value.filter(item =>
    item.original.toLowerCase().includes(search) ||
    item.translation.toLowerCase().includes(search)
  )
})

const lockedCount = computed(() => glossary.value.filter(item => item.locked).length)
const personCount = computed(() => glossary.value.filter(item => item.entity_type === 'person').length)
const otherCount = computed(() => glossary.value.filter(item => item.entity_type !== 'person').length)

const getTypeTagType = (type) => {
  const types = {
    person: '',
    location: 'success',
    organization: 'warning',
    title: 'danger',
    skill: 'info',
    item: 'info'
  }
  return types[type] || ''
}

const getTypeLabel = (type) => {
  const labels = {
    person: '人物',
    location: '地名',
    organization: '组织',
    title: '称号',
    skill: '功法',
    item: '道具'
  }
  return labels[type] || type
}

const loadGlossary = async () => {
  loading.value = true
  
  try {
    // 使用task_id获取词典
    const result = await glossaryApi.getAll(currentTaskId)
    glossary.value = result.glossary || []
  } catch (error) {
    ElMessage.error('加载词典失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const startEdit = (row) => {
  editingRow.value = row.original
  editTranslation.value = row.translation
}

const saveEdit = async (row) => {
  try {
    await glossaryApi.edit(currentTaskId, row.original, editTranslation.value)
    
    const index = glossary.value.findIndex(item => item.original === row.original)
    if (index !== -1) {
      glossary.value[index].translation = editTranslation.value
    }
    
    editingRow.value = ''
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败: ' + (error.message || '未知错误'))
  }
}

const toggleLock = async (row) => {
  try {
    if (row.locked) {
      await glossaryApi.unlock(row.original)
      ElMessage.success('已解锁')
    } else {
      await glossaryApi.lock(row.original)
      ElMessage.success('已锁定')
    }
    
    const index = glossary.value.findIndex(item => item.original === row.original)
    if (index !== -1) {
      glossary.value[index].locked = !row.locked
    }
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

const handleDelete = (row) => {
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  
  try {
    await glossaryApi.delete(deleteTarget.value.original)
    
    glossary.value = glossary.value.filter(item => item.original !== deleteTarget.value.original)
    
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    deleteTarget.value = null
  } catch (error) {
    ElMessage.error('删除失败: ' + (error.message || '未知错误'))
  }
}

onMounted(() => {
  loadGlossary()
})
</script>

<style scoped>
.glossary-container {
  max-width: 1400px;
  margin: 30px auto;
}

.stats-bar {
  display: flex;
  gap: 30px;
  margin-bottom: 25px;
  justify-content: center;
  background-color: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding: 50px 0;
}
</style>
