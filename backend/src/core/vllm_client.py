import httpx
from typing import Dict, List, Optional
from src.core.config import config
import json
import traceback

class LLMClient:
    """统一的 LLM 客户端，支持 vLLM、Ollama 和 OpenAI 标准 API"""
    
    def __init__(self):
        self.backend = config.LLM_BACKEND
        self.temperature = config.LLM_TEMPERATURE
        self.max_tokens = config.LLM_MAX_TOKENS
        self.timeout = config.LLM_TIMEOUT
        
        # 根据后端类型初始化配置
        if self.backend == "ollama":
            self._init_ollama()
        elif self.backend == "openai":
            self._init_openai()
        else:  # vllm (默认)
            self._init_vllm()
        
        print(f"[LLMClient] 初始化完成")
        print(f"[LLMClient] 后端类型: {self.backend.upper()}")
        print(f"[LLMClient] Base URL: {self.base_url}")
        print(f"[LLMClient] 模型: {self.model_name}")
    
    def _init_ollama(self):
        """初始化 Ollama 配置"""
        self.base_url = config.OLLAMA_BASE_URL
        self.model_name = config.OLLAMA_MODEL_NAME
        self.api_key = "ollama"
        self.chat_endpoint = "/api/chat"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.response_format = "ollama"
    
    def _init_vllm(self):
        """初始化 vLLM 配置"""
        self.base_url = config.VLLM_BASE_URL
        self.model_name = config.VLLM_MODEL_NAME
        self.api_key = config.VLLM_API_KEY
        self.chat_endpoint = "/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.response_format = "openai"
    
    def _init_openai(self):
        """初始化 OpenAI 标准 API 配置"""
        self.base_url = config.OPENAI_BASE_URL
        self.model_name = config.OPENAI_MODEL_NAME
        self.api_key = config.OPENAI_API_KEY
        self.chat_endpoint = "/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.response_format = "openai"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 构建请求 payload
            payload = self._build_payload(messages, temperature, max_tokens)
            
            print(f"[LLMClient] 发送请求到 {self.base_url}{self.chat_endpoint}")
            print(f"[LLMClient] 模型: {self.model_name}, 后端: {self.backend.upper()}")
            
            try:
                response = await client.post(
                    f"{self.base_url}{self.chat_endpoint}",
                    headers=self.headers,
                    json=payload
                )
                
                print(f"[LLMClient] 响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"[LLMClient] 错误响应内容: {error_text[:500]}")
                    raise Exception(f"LLM API error ({self.backend}): {response.status_code} - {error_text[:200]}")
                
                result = response.json()
                
                # 解析响应
                content = self._parse_response(result)
                
                print(f"[LLMClient] 成功获取响应，内容长度: {len(content)}")
                print(f"[LLMClient] 内容前100字符: {content[:100]}")
                
                return content
                
            except httpx.ConnectError as e:
                print(f"[LLMClient] 连接错误: 无法连接到 {self.base_url}")
                raise Exception(f"Cannot connect to {self.backend.upper()} server at {self.base_url}. Please check if the service is running.")
            except httpx.TimeoutException as e:
                print(f"[LLMClient] 请求超时 ({self.timeout}秒)")
                raise Exception(f"Request timeout after {self.timeout} seconds")
            except Exception as e:
                print(f"[LLMClient] 请求异常: {type(e).__name__}: {e}")
                print(f"[LLMClient] 错误堆栈:\n{traceback.format_exc()}")
                raise
    
    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> Dict:
        """构建请求 payload"""
        if self.backend == "ollama":
            return {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature or self.temperature,
                    "num_predict": max_tokens or self.max_tokens
                }
            }
        else:
            # vLLM 和 OpenAI 使用相同的 payload 格式
            return {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
    
    def _parse_response(self, result: Dict) -> str:
        """解析响应格式"""
        if self.response_format == "ollama":
            # Ollama 响应格式
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            elif "response" in result:
                return result["response"]
            else:
                print(f"[LLMClient] Ollama响应结构异常: {json.dumps(result, ensure_ascii=False)[:500]}")
                raise Exception("Invalid Ollama response structure")
        else:
            # OpenAI / vLLM 响应格式
            if "choices" not in result:
                print(f"[LLMClient] 响应缺少 choices 字段: {json.dumps(result, ensure_ascii=False)[:500]}")
                raise Exception("Invalid response structure: missing 'choices'")
            
            if len(result["choices"]) == 0:
                print(f"[LLMClient] choices 为空数组")
                raise Exception("Empty choices in response")
            
            choice = result["choices"][0]
            if "message" not in choice:
                print(f"[LLMClient] choice 缺少 message: {choice}")
                raise Exception("Missing 'message' in choice")
            
            message = choice["message"]
            content = message.get("content", "")
            return content
    
    async def extract_entities(self, text: str, source_lang: str, target_lang: str) -> Dict:
        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的小说{source_lang}->{target_lang}翻译实体提取专家。
请从以下小说文本中提取所有人名、地名、势力名、功法名、道具名等专有名词。

要求：
1. 只提取专有名词（人名、地名、组织/势力名、特殊称号、功法/技能名、重要道具）
2. 区分每个实体的类型（person/location/organization/title/skill/item）
3. 如果有别名或昵称，需要标注主名称和别名关系
4. 输出JSON格式：{{"entities": [{{"original": "原名", "type": "类型", "aliases": ["别名1"]}}]}}
只输出JSON，不要其他内容。"""
            },
            {
                "role": "user",
                "content": text[:3000]
            }
        ]
        
        result = await self.chat_completion(messages)
        return result
    
    async def translate_text(
        self,
        text: str,
        glossary: Dict[str, str],
        source_lang: str,
        target_lang: str
    ) -> str:
        glossary_str = "\n".join([f"{k} -> {v}" for k, v in glossary.items()])
        
        print(f"[LLMClient] 翻译文本，源语言: {source_lang}, 目标语言: {target_lang}")
        print(f"[LLMClient] 词典条目数: {len(glossary)}")
        print(f"[LLMClient] 待翻译文本长度: {len(text)}")
        
        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的小说翻译家，将{source_lang}小说翻译成{target_lang}。

【强制规则】
1. 必须严格使用以下人名词典中的翻译，禁止自行修改人名：
{glossary_str}

2. 保留原文的对话格式、换行、标点符号、段落结构
3. 翻译风格要符合小说文风，口语化自然流畅
4. 人名一致性优先于译文优美度
5. 只翻译正文内容，不翻译章节标题"""
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        result = await self.chat_completion(messages, max_tokens=4096)
        return result
    
    async def check_consistency(
        self,
        original_text: str,
        translated_text: str,
        glossary: Dict[str, str]
    ) -> Dict:
        glossary_str = "\n".join([f"{k} -> {v}" for k, v in glossary.items()])
        
        messages = [
            {
                "role": "system",
                "content": f"""你是小说翻译一致性检查专家。对比原文和译文，检查人名是否一致。

全局词典：
{glossary_str}

检查项：
1. 译文中的人名是否与词典完全一致
2. 是否出现词典外的新人名（未在词典中）
3. 是否漏译了人物名称
4. 是否错译了称号或别名

输出JSON格式：
{{"consistent": true/false, "issues": ["问题描述"], "suggestions": ["修改建议"]}}"""
            },
            {
                "role": "user",
                "content": f"原文：\n{original_text}\n\n译文：\n{translated_text}"
            }
        ]
        
        result = await self.chat_completion(messages)
        return result
    
    def get_backend_info(self) -> Dict:
        """获取当前后端信息"""
        return {
            "backend": self.backend,
            "base_url": self.base_url,
            "model_name": self.model_name
        }

# 保持向后兼容的别名
vllm_client = LLMClient()
llm_client = LLMClient()
