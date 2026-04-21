import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Chapter:
    chapter_number: int
    title: str
    content: str
    start_pos: int
    end_pos: int

class ChapterSplitAgent:
    def __init__(self):
        self.chapter_patterns = [
            r'^第[一二三四五六七八九十百千零〇0-9]{1,5}章[\s\S]*?$',
            r'^Chapter\s*[一二三四五六七八九十百千零〇0-9]+.*?$',
            r'^第[一二三四五六七八九十百千零〇0-9]{1,5}卷\s*第[一二三四五六七八九十百千零〇0-9]{1,5}章[\s\S]*?$',
            r'^【第?[一二三四五六七八九十百千零〇0-9]{1,5}章?】.*?$',
            r'^『第?[一二三四五六七八九十百千零〇0-9]{1,5}章?』.*?$',
        ]
    
    async def split_chapters(self, text: str) -> List[Chapter]:
        chapters = []
        
        combined_pattern = '|'.join(f'({p})' for p in self.chapter_patterns)
        
        matches = list(re.finditer(combined_pattern, text, re.MULTILINE))
        
        if not matches:
            chapters.append(Chapter(
                chapter_number=1,
                title="全文",
                content=text,
                start_pos=0,
                end_pos=len(text)
            ))
            return chapters
        
        for i, match in enumerate(matches):
            title = match.group(0).strip()
            start_pos = match.start()
            
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
                content = text[start_pos:end_pos].strip()
            else:
                end_pos = len(text)
                content = text[start_pos:].strip()
            
            chapters.append(Chapter(
                chapter_number=i + 1,
                title=title,
                content=content,
                start_pos=start_pos,
                end_pos=end_pos
            ))
        
        return chapters
    
    def detect_chapter_title(self, line: str) -> bool:
        for pattern in self.chapter_patterns:
            if re.match(pattern, line.strip(), re.MULTILINE):
                return True
        return False

chapter_split_agent = ChapterSplitAgent()
