import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

from src.agents.chapter_split import chapter_split_agent
from src.agents.entity_extract import entity_extract_agent
from src.agents.glossary_manager import glossary_manager_agent
from src.agents.translate import translate_agent
from src.agents.consistency_check import consistency_check_agent
from src.agents.merge_output import merge_output_agent
from src.global_memory.novel_glossary import global_glossary
from src.db.database import db

@dataclass
class TranslationTask:
    task_id: str
    novel_text: str
    source_language: str
    target_language: str
    status: str = "pending"
    current_chapter: int = 0
    total_chapters: int = 0
    chapters: List[Dict] = field(default_factory=list)
    translated_chapters: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    filename: str = ""

class SupervisorAgent:
    def __init__(self):
        self.tasks: Dict[str, TranslationTask] = {}
        self._progress_callbacks = []
        self._load_tasks_from_db()
    
    def _load_tasks_from_db(self):
        """从数据库加载未完成的任务"""
        try:
            tasks_data = db.get_all_tasks()
            for task_data in tasks_data:
                task_id = task_data.get("task_id")
                if task_id and task_data.get("status") not in ["completed", "error"]:
                    # 恢复任务到内存
                    task = TranslationTask(
                        task_id=task_id,
                        novel_text=task_data.get("novel_text", ""),
                        source_language=task_data.get("source_language", "Chinese"),
                        target_language=task_data.get("target_language", "English"),
                        status=task_data.get("status", "pending"),
                        current_chapter=task_data.get("current_chapter", 0),
                        total_chapters=task_data.get("total_chapters", 0),
                        chapters=task_data.get("chapters", []),
                        translated_chapters=task_data.get("translated_chapters", []),
                        error=task_data.get("error"),
                        filename=task_data.get("filename", "")
                    )
                    # 恢复合并内容
                    if task_data.get("merged_content"):
                        task.merged_content = task_data.get("merged_content")
                    self.tasks[task_id] = task
                    print(f"[Supervisor] 从数据库恢复任务: {task_id}, 状态: {task.status}")
        except Exception as e:
            print(f"[Supervisor] 从数据库加载任务失败: {e}")
    
    def _save_task_to_db(self, task: TranslationTask):
        """保存任务到数据库"""
        try:
            task_dict = {
                "task_id": task.task_id,
                "filename": getattr(task, 'filename', ''),
                "source_language": task.source_language,
                "target_language": task.target_language,
                "status": task.status,
                "current_chapter": task.current_chapter,
                "total_chapters": task.total_chapters,
                "chapters": task.chapters,
                "translated_chapters": task.translated_chapters,
                "merged_content": getattr(task, 'merged_content', None),
                "error": task.error
            }
            db.save_task(task_dict)
        except Exception as e:
            print(f"[Supervisor] 保存任务到数据库失败: {e}")
    
    def register_progress_callback(self, callback):
        self._progress_callbacks.append(callback)
    
    async def _notify_progress(self, task_id: str):
        task = self.tasks.get(task_id)
        if task:
            # 保存到数据库
            self._save_task_to_db(task)
            for callback in self._progress_callbacks:
                await callback(task)
    
    async def create_task(
        self,
        task_id: str,
        novel_text: str,
        source_language: str,
        target_language: str,
        filename: str = ""
    ) -> TranslationTask:
        
        task = TranslationTask(
            task_id=task_id,
            novel_text=novel_text,
            source_language=source_language,
            target_language=target_language,
            filename=filename
        )
        
        self.tasks[task_id] = task
        
        # 保存到数据库
        self._save_task_to_db(task)
        
        if config.GLOBAL_GLOSSARY_MEMORY:
            await global_glossary.clear()
        
        return task
    
    async def split_chapters(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            # 尝试从数据库加载
            task_data = db.get_task(task_id)
            if task_data:
                task = TranslationTask(
                    task_id=task_id,
                    novel_text=task_data.get("novel_text", ""),
                    source_language=task_data.get("source_language", "Chinese"),
                    target_language=task_data.get("target_language", "English"),
                    status=task_data.get("status", "pending"),
                    filename=task_data.get("filename", "")
                )
                self.tasks[task_id] = task
            else:
                return False
        
        try:
            task.status = "splitting"
            await self._notify_progress(task_id)
            
            chapters = await chapter_split_agent.split_chapters(task.novel_text)
            
            task.chapters = [
                {
                    "chapter_number": ch.chapter_number,
                    "title": ch.title,
                    "original_content": ch.content,
                    "translated_content": None
                }
                for ch in chapters
            ]
            
            task.total_chapters = len(chapters)
            task.status = "chapters_ready"
            
            await self._notify_progress(task_id)
            return True
            
        except Exception as e:
            task.status = "error"
            task.error = f"章节拆分失败: {str(e)}"
            await self._notify_progress(task_id)
            return False
    
    async def translate_all_chapters(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        try:
            task.status = "translating"
            
            # 加载该任务的词典（从数据库恢复）
            await global_glossary.set_task(task_id)
            
            await self._notify_progress(task_id)
            
            for i, chapter in enumerate(task.chapters):
                task.current_chapter = i + 1
                await self._notify_progress(task_id)
                
                original_content = chapter["original_content"]
                
                entities = await entity_extract_agent.extract_entities_from_chapter(
                    original_content,
                    task.source_language,
                    task.target_language
                )
                
                new_entries = await glossary_manager_agent.process_new_entities(
                    entities,
                    task.source_language,
                    task.target_language
                )
                
                async def do_translate():
                    return await translate_agent.translate_chapter(
                        original_content,
                        task.source_language,
                        task.target_language
                    )
                
                translated_content = await do_translate()
                
                translated_content = await consistency_check_agent.validate_and_fix(
                    original_content,
                    translated_content,
                    do_translate
                )
                
                chapter["translated_content"] = translated_content
                task.translated_chapters.append(chapter)
                
                # 保存进度到数据库
                self._save_task_to_db(task)
                
                # 章节间延迟，避免vLLM服务器过载
                if i < len(task.chapters) - 1:
                    print(f"[Supervisor] 第{i+1}章翻译完成，等待5秒后翻译下一章...")
                    await asyncio.sleep(5)
            
            merged = merge_output_agent.merge_chapters(task.translated_chapters)
            task.merged_content = merged
            
            task.status = "completed"
            await self._notify_progress(task_id)
            
            return True
            
        except Exception as e:
            task.status = "error"
            task.error = f"翻译失败: {str(e)}"
            await self._notify_progress(task_id)
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        # 先检查内存
        task = self.tasks.get(task_id)
        
        # 如果内存中没有，从数据库加载
        if not task:
            task_data = db.get_task(task_id)
            if task_data:
                return {
                    "task_id": task_data["task_id"],
                    "status": task_data["status"],
                    "current_chapter": task_data.get("current_chapter", 0),
                    "total_chapters": task_data.get("total_chapters", 0),
                    "progress": round((task_data.get("current_chapter", 0) / max(task_data.get("total_chapters", 1), 1)) * 100, 2),
                    "error": task_data.get("error"),
                    "source_language": task_data.get("source_language", "Chinese"),
                    "target_language": task_data.get("target_language", "English")
                }
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "current_chapter": task.current_chapter,
            "total_chapters": task.total_chapters,
            "progress": round((task.current_chapter / max(task.total_chapters, 1)) * 100, 2),
            "error": task.error,
            "source_language": task.source_language,
            "target_language": task.target_language
        }
    
    async def get_translated_content(self, task_id: str) -> Optional[str]:
        # 先检查内存
        task = self.tasks.get(task_id)
        if task and hasattr(task, 'merged_content'):
            return task.merged_content
        
        # 从数据库加载
        task_data = db.get_task(task_id)
        if task_data:
            return task_data.get("merged_content")
        
        return None
    
    async def get_chapters(self, task_id: str) -> Optional[List[Dict]]:
        # 先检查内存
        task = self.tasks.get(task_id)
        if task:
            return task.chapters
        
        # 从数据库加载
        task_data = db.get_task(task_id)
        if task_data:
            return task_data.get("chapters", [])
        
        return None

from src.core.config import config
supervisor_agent = SupervisorAgent()
