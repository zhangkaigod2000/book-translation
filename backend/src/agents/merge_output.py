from typing import List, Dict

class MergeOutputAgent:
    def __init__(self):
        pass
    
    def merge_chapters(
        self,
        translated_chapters: List[Dict],
        keep_original_format: bool = True
    ) -> str:
        merged_content = []
        
        for i, chapter in enumerate(translated_chapters, 1):
            chapter_num = chapter.get("chapter_number", i)
            title = chapter.get("title", f"第{i}章")
            translated_content = chapter.get("translated_content", "")
            
            if keep_original_format:
                merged_content.append(f"{title}\n")
                merged_content.append(translated_content)
            else:
                merged_content.append(f"Chapter {chapter_num}: {title}\n")
                merged_content.append(translated_content)
            
            if i < len(translated_chapters):
                merged_content.append("\n")
        
        return "\n".join(merged_content)
    
    def generate_table_of_contents(
        self,
        chapters: List[Dict]
    ) -> str:
        toc_lines = ["目录\n", "=" * 40 + "\n"]
        
        for i, chapter in enumerate(chapters, 1):
            chapter_num = chapter.get("chapter_number", i)
            title = chapter.get("title", f"第{i}章")
            toc_lines.append(f"  第{chapter_num:03d}章  {title}\n")
        
        return "".join(toc_lines)

merge_output_agent = MergeOutputAgent()
