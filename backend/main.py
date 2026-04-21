from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
import asyncio

from src.core.config import config
from src.agents.supervisor import supervisor_agent
from src.agents.glossary_manager import glossary_manager_agent
from src.global_memory.novel_glossary import global_glossary
from src.core.vllm_client import llm_client

app = FastAPI(title="小说翻译系统 - Novel Translation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranslateRequest(BaseModel):
    task_id: str
    source_language: Optional[str] = None
    target_language: Optional[str] = None

class GlossaryEditRequest(BaseModel):
    task_id: str
    original: str
    new_translation: str

@app.post("/api/novel/upload")
async def upload_novel(file: UploadFile = File(...)):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="只支持txt格式文件")
    
    content = await file.read()
    text = content.decode('utf-8')
    
    task_id = str(uuid.uuid4())
    
    await supervisor_agent.create_task(
        task_id=task_id,
        novel_text=text,
        source_language=config.SOURCE_LANGUAGE,
        target_language=config.TARGET_LANGUAGE,
        filename=file.filename
    )
    
    return {
        "task_id": task_id,
        "filename": file.filename,
        "text_length": len(text),
        "message": "上传成功"
    }

@app.post("/api/novel/auto-chapter")
async def auto_detect_chapters(task_id: str = Query(...)):
    success = await supervisor_agent.split_chapters(task_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="章节识别失败")
    
    chapters = await supervisor_agent.get_chapters(task_id)
    
    return {
        "task_id": task_id,
        "total_chapters": len(chapters) if chapters else 0,
        "chapters": [
            {
                "chapter_number": ch["chapter_number"],
                "title": ch["title"]
            }
            for ch in (chapters or [])
        ]
    }

@app.post("/api/translate/start")
async def start_translation(request: TranslateRequest):
    task = supervisor_agent.tasks.get(request.task_id)
    if not task:
        # 尝试从数据库加载任务
        from src.db.database import db
        task_data = db.get_task(request.task_id)
        if task_data:
            task = TranslationTask(
                task_id=request.task_id,
                novel_text="",  # 需要重新加载
                source_language=request.source_language or config.SOURCE_LANGUAGE,
                target_language=request.target_language or config.TARGET_LANGUAGE
            )
            supervisor_agent.tasks[request.task_id] = task
        else:
            raise HTTPException(status_code=404, detail="任务不存在")
    
    if request.source_language:
        task.source_language = request.source_language
    if request.target_language:
        task.target_language = request.target_language
    
    asyncio.create_task(supervisor_agent.translate_all_chapters(request.task_id))
    
    return {
        "task_id": request.task_id,
        "message": "翻译已开始",
        "source_language": task.source_language,
        "target_language": task.target_language
    }

@app.get("/api/translate/progress")
async def get_translation_progress(task_id: str = Query(...)):
    status = await supervisor_agent.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status

@app.get("/api/glossary/global")
async def get_global_glossary(task_id: Optional[str] = Query(None)):
    """获取全局词典，支持按任务ID筛选"""
    if task_id:
        # 从数据库获取指定任务的词典
        from src.db.database import db
        glossary = db.get_glossary_by_task(task_id)
    else:
        # 获取内存中的词典
        glossary = await glossary_manager_agent.get_full_glossary()
    
    return {
        "glossary": glossary,
        "total_count": len(glossary)
    }

@app.post("/api/glossary/edit")
async def edit_glossary_entry(request: GlossaryEditRequest):
    success = await glossary_manager_agent.update_entry(
        request.original,
        request.new_translation
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="更新失败，词条可能被锁定或不存在")
    
    return {
        "message": "更新成功",
        "original": request.original,
        "new_translation": request.new_translation
    }

@app.post("/api/glossary/lock")
async def lock_glossary_entry(original: str = Query(...)):
    success = await glossary_manager_agent.lock_entry(original)
    
    if not success:
        raise HTTPException(status_code=404, detail="词条不存在")
    
    return {"message": "锁定成功", "original": original}

@app.post("/api/glossary/unlock")
async def unlock_glossary_entry(original: str = Query(...)):
    success = await glossary_manager_agent.unlock_entry(original)
    
    if not success:
        raise HTTPException(status_code=404, detail="词条不存在")
    
    return {"message": "解锁成功", "original": original}

@app.delete("/api/glossary/delete")
async def delete_glossary_entry(original: str = Query(...)):
    success = await glossary_manager_agent.delete_entry(original)
    
    if not success:
        raise HTTPException(status_code=404, detail="词条不存在")
    
    return {"message": "删除成功", "original": original}

@app.get("/api/novel/download")
async def download_novel(task_id: str = Query(...)):
    content = await supervisor_agent.get_translated_content(task_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="翻译未完成或任务不存在")
    
    from io import StringIO
    
    def generate():
        yield content
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=translated_novel.txt"}
    )

@app.get("/api/novel/chapters")
async def get_novel_chapters(task_id: str = Query(...)):
    chapters = await supervisor_agent.get_chapters(task_id)
    
    if not chapters:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    return {
        "task_id": task_id,
        "chapters": chapters
    }

@app.get("/api/llm/backend-info")
async def get_llm_backend_info():
    """获取当前 LLM 后端信息"""
    return llm_client.get_backend_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)
