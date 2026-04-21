from typing import Dict
from src.core.vllm_client import vllm_client
from src.global_memory.novel_glossary import global_glossary
from src.core.config import config
import traceback
import asyncio

class TranslateAgent:
    def __init__(self):
        self.client = vllm_client
        self.max_chunk_size = config.MAX_CHUNK_PER_CHAPTER
        self.force_consistency = config.FORCE_NAME_CONSISTENCY
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 10  # 重试间隔（秒）
    
    async def translate_chapter(
        self,
        chapter_content: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        glossary = global_glossary.get_glossary_for_prompt()
        
        print(f"[TranslateAgent] 开始翻译章节，长度: {len(chapter_content)}, 源语言: {source_lang}, 目标语言: {target_lang}")
        print(f"[TranslateAgent] 当前词典条目数: {len(glossary)}")
        
        if len(chapter_content) <= self.max_chunk_size:
            translated = await self._translate_with_retry(
                chapter_content,
                glossary,
                source_lang,
                target_lang
            )
            return translated
        
        chunks = self._split_into_chunks(chapter_content)
        print(f"[TranslateAgent] 章节分块数: {len(chunks)}")
        translated_chunks = []
        
        for i, chunk in enumerate(chunks):
            print(f"[TranslateAgent] 翻译块 {i+1}/{len(chunks)}")
            translated_chunk = await self._translate_with_retry(
                chunk,
                glossary,
                source_lang,
                target_lang
            )
            translated_chunks.append(translated_chunk)
            
            # 块之间也添加延迟
            if i < len(chunks) - 1:
                await asyncio.sleep(2)
        
        return "\n\n".join(translated_chunks)
    
    async def _translate_with_retry(
        self,
        text: str,
        glossary: Dict[str, str],
        source_lang: str,
        target_lang: str
    ) -> str:
        """带重试机制的翻译"""
        for attempt in range(self.max_retries):
            try:
                print(f"[TranslateAgent] 翻译尝试 {attempt + 1}/{self.max_retries}")
                result = await self._translate_single_chunk(
                    text,
                    glossary,
                    source_lang,
                    target_lang
                )
                
                # 检查是否成功翻译（不是错误消息且不是原文）
                if not result.startswith("[Translation Error:"):
                    if result.strip() != text.strip():
                        print(f"[TranslateAgent] 翻译成功")
                        return result
                    else:
                        print(f"[TranslateAgent] 警告: 返回了原文，可能是vLLM未正确响应")
                        if attempt < self.max_retries - 1:
                            print(f"[TranslateAgent] 等待{self.retry_delay}秒后重试...")
                            await asyncio.sleep(self.retry_delay)
                        else:
                            return result  # 最后一次尝试，直接返回
                else:
                    # 翻译出错
                    if attempt < self.max_retries - 1:
                        print(f"[TranslateAgent] 翻译出错，等待{self.retry_delay}秒后重试...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        return result  # 最后一次尝试，返回错误
                        
            except Exception as e:
                print(f"[TranslateAgent] 翻译异常: {e}")
                if attempt < self.max_retries - 1:
                    print(f"[TranslateAgent] 等待{self.retry_delay}秒后重试...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    return f"[Translation Error: {str(e)}]\n\n{text}"
        
        return f"[Translation Error: Max retries exceeded]\n\n{text}"
    
    async def _translate_single_chunk(
        self,
        text: str,
        glossary: Dict[str, str],
        source_lang: str,
        target_lang: str
    ) -> str:
        try:
            print(f"[TranslateAgent] 调用vLLM翻译，文本长度: {len(text)}")
            result = await self.client.translate_text(
                text=text,
                glossary=glossary,
                source_lang=source_lang,
                target_lang=target_lang
            )
            print(f"[TranslateAgent] vLLM返回结果长度: {len(result)}")
            
            # 检查结果是否有效
            if not result or result.strip() == "":
                print(f"[TranslateAgent] 警告: vLLM返回空结果")
                return f"[Translation Error: Empty response from LLM]\n\n{text}"
            
            # 检查是否返回了原文（没有翻译）
            if result.strip() == text.strip():
                print(f"[TranslateAgent] 警告: vLLM返回了原文，可能没有正确翻译")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"[TranslateAgent] 翻译失败: {error_msg}")
            print(f"[TranslateAgent] 错误堆栈:\n{error_trace}")
            return f"[Translation Error: {error_msg}]\n\n{text}"
    
    def _split_into_chunks(self, text: str) -> list:
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n"
            else:
                current_chunk += para + "\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

translate_agent = TranslateAgent()
