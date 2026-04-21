import json
from typing import Dict, Tuple, List
from src.core.vllm_client import vllm_client
from src.global_memory.novel_glossary import global_glossary
from src.core.config import config

class ConsistencyCheckAgent:
    def __init__(self):
        self.client = vllm_client
        self.enabled = config.CONSISTENCY_CHECK_ENABLE
        self.max_retries = 2
    
    async def check_translation(
        self,
        original_text: str,
        translated_text: str
    ) -> Tuple[bool, List[str]]:
        if not self.enabled:
            return True, []
        
        glossary = global_glossary.get_glossary_for_prompt()
        
        try:
            raw_result = await self.client.check_consistency(
                original_text=original_text,
                translated_text=translated_text,
                glossary=glossary
            )
            
            result = json.loads(raw_result)
            is_consistent = result.get("consistent", True)
            issues = result.get("issues", [])
            
            return is_consistent, issues
            
        except Exception as e:
            print(f"一致性检查失败: {e}")
            return True, []  # 检查失败不阻塞翻译流程
    
    async def validate_and_fix(
        self,
        original_text: str,
        translated_text: str,
        translate_func
    ) -> str:
        if not self.enabled:
            return translated_text
        
        for attempt in range(self.max_retries + 1):
            is_consistent, issues = await self.check_translation(
                original_text,
                translated_text
            )
            
            if is_consistent:
                return translated_text
            
            print(f"一致性检查未通过 (尝试 {attempt + 1}/{self.max_retries + 1}): {issues}")
            
            if attempt < self.max_retries:
                translated_text = await translate_func()
        
        print(f"达到最大重试次数，返回最后一次翻译结果")
        return translated_text

consistency_check_agent = ConsistencyCheckAgent()
