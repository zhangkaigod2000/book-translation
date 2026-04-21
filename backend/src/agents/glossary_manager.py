from typing import Dict, List
from src.core.vllm_client import vllm_client
from src.global_memory.novel_glossary import global_glossary
from src.core.config import config

class GlossaryManagerAgent:
    def __init__(self):
        self.client = vllm_client
        self.merge_alias_enabled = config.MERGE_ALIAS
    
    async def process_new_entities(
        self,
        entities: List[Dict],
        source_lang: str,
        target_lang: str
    ) -> Dict[str, str]:
        new_entries = {}
        
        for entity in entities:
            original = entity["original"]
            entity_type = entity["type"]
            aliases = entity.get("aliases", [])
            
            existing = await global_glossary.get_translation(original)
            
            if existing is None:
                translation = await self._translate_single_entity(
                    original,
                    entity_type,
                    source_lang,
                    target_lang
                )
                
                await global_glossary.add_entry(
                    original=original,
                    translation=translation,
                    entity_type=entity_type,
                    aliases=aliases
                )
                
                new_entries[original] = translation
                
                if self.merge_alias_enabled and aliases:
                    await global_glossary.merge_aliases(original, aliases)
                    
                    for alias in aliases:
                        await global_glossary.add_entry(
                            original=alias,
                            translation=translation,
                            entity_type=entity_type,
                            locked=True
                        )
                        new_entries[alias] = translation
        
        return new_entries
    
    async def _translate_single_entity(
        self,
        entity: str,
        entity_type: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        type_hint = {
            "person": "人名",
            "location": "地名",
            "organization": "组织/势力名",
            "title": "称号",
            "skill": "功法/技能名",
            "item": "道具名"
        }.get(entity_type, "专有名词")
        
        messages = [
            {
                "role": "system",
                "content": f"你是翻译专家。将以下{source_lang}{type_hint}翻译成{target_lang}。只输出翻译结果，不要其他内容。"
            },
            {
                "role": "user",
                "content": entity
            }
        ]
        
        try:
            result = await self.client.chat_completion(messages, temperature=0.01)
            return result.strip()
        except Exception as e:
            print(f"翻译实体失败: {entity}, 错误: {e}")
            return entity
    
    async def get_full_glossary(self) -> Dict[str, dict]:
        return await global_glossary.to_dict_list()
    
    async def update_entry(self, original: str, new_translation: str) -> bool:
        success = await global_glossary.update_translation(original, new_translation)
        return success
    
    async def lock_entry(self, original: str) -> bool:
        return await global_glossary.lock_entry(original)
    
    async def unlock_entry(self, original: str) -> bool:
        return await global_glossary.unlock_entry(original)
    
    async def delete_entry(self, original: str) -> bool:
        return await global_glossary.delete_entry(original)

glossary_manager_agent = GlossaryManagerAgent()
