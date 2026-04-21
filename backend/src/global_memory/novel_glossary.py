from typing import Dict, List, Optional
import json
import asyncio
from src.db.database import db

class NovelGlobalGlossary:
    def __init__(self):
        self.glossary: Dict[str, GlossaryEntry] = {}
        self._lock = asyncio.Lock()
        self.current_task_id: Optional[str] = None
    
    async def set_task(self, task_id: str):
        """设置当前任务的词典"""
        self.current_task_id = task_id
        
        # 先清空内存中的词典
        self.glossary.clear()
        
        # 从数据库加载该任务的词典
        entries = db.get_glossary_by_task(task_id)
        
        for entry in entries:
            self.glossary[entry["original"]] = GlossaryEntry(
                original=entry["original"],
                translation=entry["translation"],
                entity_type=entry["entity_type"],
                aliases=entry.get("aliases", []),
                locked=bool(entry.get("locked", 0))
            )
        
        print(f"[Glossary] 从数据库加载了 {len(entries)} 个词典条目 (task_id={task_id})")
    
    async def add_entry(
        self,
        original: str,
        translation: str,
        entity_type: str = "person",
        aliases: Optional[List[str]] = None,
        locked: bool = False
    ):
        async with self._lock:
            if original not in self.glossary:
                entry = GlossaryEntry(
                    original=original,
                    translation=translation,
                    entity_type=entity_type,
                    aliases=aliases or [],
                    locked=locked
                )
                self.glossary[original] = entry
                
                # 持久化到数据库
                if self.current_task_id:
                    db.save_glossary_entry(self.current_task_id, {
                        "original": original,
                        "translation": translation,
                        "entity_type": entity_type,
                        "aliases": aliases or [],
                        "locked": locked
                    })
                    
            elif not self.glossary[original].locked:
                old_translation = self.glossary[original].translation
                self.glossary[original].translation = translation
                if aliases:
                    for alias in aliases:
                        if alias not in self.glossary[original].aliases:
                            self.glossary[original].aliases.append(alias)
                
                # 更新数据库
                if self.current_task_id:
                    db.save_glossary_entry(self.current_task_id, {
                        "original": original,
                        "translation": translation,
                        "entity_type": entity_type,
                        "aliases": self.glossary[original].aliases,
                        "locked": self.glossary[original].locked
                    })
    
    async def get_translation(self, original: str) -> Optional[str]:
        async with self._lock:
            if original in self.glossary:
                return self.glossary[original].translation
            return None
    
    async def get_all_entries(self) -> List[dict]:
        async with self._lock:
            return [v.to_dict() for v in self.glossary.values()]
    
    async def update_translation(self, original: str, new_translation: str) -> bool:
        async with self._lock:
            if original in self.glossary and not self.glossary[original].locked:
                self.glossary[original].translation = new_translation
                
                # 更新数据库
                if self.current_task_id:
                    success = db.update_glossary_entry(
                        self.current_task_id, 
                        original, 
                        new_translation
                    )
                    return success
                return True
            return False
    
    async def lock_entry(self, original: str) -> bool:
        async with self._lock:
            if original in self.glossary:
                self.glossary[original].locked = True
                
                # 更新数据库
                if self.current_task_id:
                    db.lock_glossary_entry(self.current_task_id, original)
                
                return True
            return False
    
    async def unlock_entry(self, original: str) -> bool:
        async with self._lock:
            if original in self.glossary:
                self.glossary[original].locked = False
                
                # 更新数据库
                if self.current_task_id:
                    db.unlock_glossary_entry(self.current_task_id, original)
                
                return True
            return False
    
    async def delete_entry(self, original: str) -> bool:
        async with self._lock:
            if original in self.glossary:
                del self.glossary[original]
                
                # 删除数据库记录
                if self.current_task_id:
                    db.delete_glossary_entry(self.current_task_id, original)
                
                return True
            return False
    
    async def merge_aliases(self, main_name: str, alias_names: List[str]):
        async with self._lock:
            if main_name in self.glossary:
                for alias in alias_names:
                    if alias not in self.glossary[main_name].aliases:
                        self.glossary[main_name].aliases.append(alias)
                    if alias in self.glossary and alias != main_name:
                        del self.glossary[alias]
                        
                # 更新数据库
                if self.current_task_id:
                    db.save_glossary_entry(self.current_task_id, {
                        "original": main_name,
                        "translation": self.glossary[main_name].translation,
                        "entity_type": self.glossary[main_name].entity_type,
                        "aliases": self.glossary[main_name].aliases,
                        "locked": self.glossary[main_name].locked
                    })
    
    async def to_dict_list(self) -> List[dict]:
        async with self._lock:
            return [v.to_dict() for v in self.glossary.values()]
    
    def get_glossary_for_prompt(self) -> Dict[str, str]:
        return {k: v.translation for k, v in self.glossary.items()}
    
    async def clear(self):
        async with self._lock:
            self.glossary.clear()
    
    async def save_all_to_db(self):
        """将所有条目保存到数据库（用于批量保存）"""
        if self.current_task_id and self.glossary:
            entries = [v.to_dict() for v in self.glossary.values()]
            db.save_glossary_batch(self.current_task_id, entries)
            print(f"[Glossary] 批量保存 {len(entries)} 个词条到数据库")

class GlossaryEntry:
    def __init__(
        self,
        original: str,
        translation: str,
        entity_type: str = "person",
        aliases: Optional[List[str]] = None,
        locked: bool = False
    ):
        self.original = original
        self.translation = translation
        self.entity_type = entity_type
        self.aliases = aliases or []
        self.locked = locked
    
    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "translation": self.translation,
            "entity_type": self.entity_type,
            "aliases": self.aliases,
            "locked": self.locked
        }

global_glossary = NovelGlobalGlossary()
