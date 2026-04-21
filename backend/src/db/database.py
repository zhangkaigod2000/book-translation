import json
import sqlite3
import threading
from typing import Optional, Dict, List
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "novel_translate.db")

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()
    
    def _get_connection(self):
        """获取线程本地连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                timeout=30,
                check_same_thread=False
            )
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=30000")
            self._local.conn.execute("PRAGMA read_uncommitted=ON")
        return self._local.conn
    
    def _close_connection(self):
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            try:
                self._local.conn.close()
            except:
                pass
            self._local.conn = None
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=60)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                filename TEXT,
                source_language TEXT,
                target_language TEXT,
                status TEXT,
                current_chapter INTEGER,
                total_chapters INTEGER,
                chapters TEXT,
                translated_chapters TEXT,
                merged_content TEXT,
                error TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                original TEXT NOT NULL,
                translation TEXT NOT NULL,
                entity_type TEXT DEFAULT 'person',
                aliases TEXT DEFAULT '[]',
                locked BOOLEAN DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(task_id, original)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ========== 任务相关操作 ==========
    
    def save_task(self, task: Dict):
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    INSERT OR REPLACE INTO tasks 
                    (task_id, filename, source_language, target_language, status, 
                     current_chapter, total_chapters, chapters, translated_chapters,
                     merged_content, error, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.get("task_id"),
                    task.get("filename"),
                    task.get("source_language"),
                    task.get("target_language"),
                    task.get("status"),
                    task.get("current_chapter", 0),
                    task.get("total_chapters", 0),
                    json.dumps(task.get("chapters", []), ensure_ascii=False),
                    json.dumps(task.get("translated_chapters", []), ensure_ascii=False),
                    task.get("merged_content"),
                    task.get("error"),
                    task.get("created_at", datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                conn.commit()
            except Exception as e:
                print(f"[Database] 保存任务失败: {e}")
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                task = dict(row)
                task["chapters"] = json.loads(task["chapters"]) if task["chapters"] else []
                task["translated_chapters"] = json.loads(task["translated_chapters"]) if task["translated_chapters"] else []
                return task
            return None
        except Exception as e:
            print(f"[Database] 获取任务失败: {e}")
            return None
    
    def get_all_tasks(self) -> List[Dict]:
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM tasks ORDER BY updated_at DESC")
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                task["chapters"] = json.loads(task["chapters"]) if task["chapters"] else []
                task["translated_chapters"] = json.loads(task["translated_chapters"]) if task["translated_chapters"] else []
                tasks.append(task)
            return tasks
        except Exception as e:
            print(f"[Database] 获取所有任务失败: {e}")
            return []
    
    def delete_task(self, task_id: str):
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                conn.commit()
            except Exception as e:
                print(f"[Database] 删除任务失败: {e}")
    
    # ========== 词典相关操作 ==========
    
    def save_glossary_entry(self, task_id: str, entry: Dict):
        """保存或更新词典条目"""
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    INSERT OR REPLACE INTO glossary 
                    (task_id, original, translation, entity_type, aliases, locked, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    entry.get("original"),
                    entry.get("translation"),
                    entry.get("entity_type", "person"),
                    json.dumps(entry.get("aliases", []), ensure_ascii=False),
                    int(entry.get("locked", False)),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
            except Exception as e:
                print(f"[Database] 保存词典条目失败: {e}")
    
    def save_glossary_batch(self, task_id: str, entries: List[Dict]):
        """批量保存词典条目"""
        with self._lock:
            try:
                conn = self._get_connection()
                for entry in entries:
                    conn.execute("""
                        INSERT OR REPLACE INTO glossary 
                        (task_id, original, translation, entity_type, aliases, locked, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task_id,
                        entry.get("original"),
                        entry.get("translation"),
                        entry.get("entity_type", "person"),
                        json.dumps(entry.get("aliases", []), ensure_ascii=False),
                        int(entry.get("locked", False)),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                conn.commit()
            except Exception as e:
                print(f"[Database] 批量保存词典失败: {e}")
    
    def get_glossary_by_task(self, task_id: str) -> List[Dict]:
        """获取指定任务的词典"""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM glossary WHERE task_id = ? ORDER BY created_at ASC",
                (task_id,)
            )
            entries = []
            for row in cursor.fetchall():
                entry = dict(row)
                entry["aliases"] = json.loads(entry["aliases"]) if entry["aliases"] else []
                entries.append(entry)
            return entries
        except Exception as e:
            print(f"[Database] 获取词典失败: {e}")
            return []
    
    def get_glossary_entry(self, task_id: str, original: str) -> Optional[Dict]:
        """获取单个词典条目"""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM glossary WHERE task_id = ? AND original = ?",
                (task_id, original)
            )
            row = cursor.fetchone()
            if row:
                entry = dict(row)
                entry["aliases"] = json.loads(entry["aliases"]) if entry["aliases"] else []
                return entry
            return None
        except Exception as e:
            print(f"[Database] 获取词典条目失败: {e}")
            return None
    
    def update_glossary_entry(self, task_id: str, original: str, new_translation: str) -> bool:
        """更新词典条目的翻译"""
        with self._lock:
            try:
                conn = self._get_connection()
                result = conn.execute(
                    "UPDATE glossary SET translation = ?, updated_at = ? WHERE task_id = ? AND original = ? AND locked = 0",
                    (new_translation, datetime.now().isoformat(), task_id, original)
                )
                conn.commit()
                return result.rowcount > 0
            except Exception as e:
                print(f"[Database] 更新词典条目失败: {e}")
                return False
    
    def lock_glossary_entry(self, task_id: str, original: str) -> bool:
        """锁定词典条目"""
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute(
                    "UPDATE glossary SET locked = 1, updated_at = ? WHERE task_id = ? AND original = ?",
                    (datetime.now().isoformat(), task_id, original)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[Database] 锁定词典条目失败: {e}")
                return False
    
    def unlock_glossary_entry(self, task_id: str, original: str) -> bool:
        """解锁词典条目"""
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute(
                    "UPDATE glossary SET locked = 0, updated_at = ? WHERE task_id = ? AND original = ?",
                    (datetime.now().isoformat(), task_id, original)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[Database] 解锁词典条目失败: {e}")
                return False
    
    def delete_glossary_entry(self, task_id: str, original: str) -> bool:
        """删除词典条目"""
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute(
                    "DELETE FROM glossary WHERE task_id = ? AND original = ?",
                    (task_id, original)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[Database] 删除词典条目失败: {e}")
                return False
    
    def delete_glossary_by_task(self, task_id: str):
        """删除任务的所有词典"""
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("DELETE FROM glossary WHERE task_id = ?", (task_id,))
                conn.commit()
            except Exception as e:
                print(f"[Database] 删除任务词典失败: {e}")

db = Database()
