import json
from typing import Dict, List
from src.core.vllm_client import vllm_client
from src.global_memory.novel_glossary import global_glossary

class EntityExtractAgent:
    def __init__(self):
        self.client = vllm_client
    
    async def extract_entities_from_chapter(
        self,
        chapter_content: str,
        source_lang: str,
        target_lang: str
    ) -> List[Dict]:
        try:
            raw_result = await self.client.extract_entities(
                chapter_content,
                source_lang,
                target_lang
            )
            
            result = json.loads(raw_result)
            entities = result.get("entities", [])
            
            processed_entities = []
            for entity in entities:
                original = entity.get("original", "").strip()
                if not original:
                    continue
                
                entity_type = entity.get("type", "person")
                aliases = entity.get("aliases", [])
                
                existing_translation = await global_glossary.get_translation(original)
                
                processed_entity = {
                    "original": original,
                    "type": entity_type,
                    "aliases": aliases,
                    "existing_translation": existing_translation,
                    "is_new": existing_translation is None
                }
                processed_entities.append(processed_entity)
            
            return processed_entities
            
        except Exception as e:
            print(f"实体提取失败: {e}")
            return []

entity_extract_agent = EntityExtractAgent()
