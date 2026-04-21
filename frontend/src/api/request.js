import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const novelApi = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/novel/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  autoChapter: (taskId) => api.post('/novel/auto-chapter', null, { params: { task_id: taskId } }),
  
  getChapters: (taskId) => api.get('/novel/chapters', { params: { task_id: taskId } }),
  
  download: (taskId) => {
    return api.get('/novel/download', {
      params: { task_id: taskId },
      responseType: 'blob'
    })
  }
}

export const translateApi = {
  start: (taskId, sourceLanguage, targetLanguage) => 
    api.post('/translate/start', {
      task_id: taskId,
      source_language: sourceLanguage,
      target_language: targetLanguage
    }),
  
  getProgress: (taskId) => 
    api.get('/translate/progress', { params: { task_id: taskId } })
}

export const glossaryApi = {
  getAll: (taskId) => api.get('/glossary/global', { params: { task_id: taskId } }),
  
  edit: (taskId, original, newTranslation) => 
    api.post('/glossary/edit', { task_id: taskId, original, new_translation: newTranslation }),
  
  lock: (original) => api.post('/glossary/lock', null, { params: { original } }),
  
  unlock: (original) => api.post('/glossary/unlock', null, { params: { original } }),
  
  delete: (original) => api.delete('/glossary/delete', { params: { original } })
}

export const llmApi = {
  getBackendInfo: () => api.get('/llm/backend-info')
}

export default api
