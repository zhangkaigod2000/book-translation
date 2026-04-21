import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 5020))
    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5021")
    
    # LLM 后端选择: vllm, ollama, openai
    LLM_BACKEND = os.getenv("LLM_BACKEND", "vllm").lower()
    
    # vLLM 配置
    VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8080/v1")
    VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "Qwen-7B-Chat")
    VLLM_API_KEY = os.getenv("VLLM_API_KEY", "sk-local")
    
    # Ollama 配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:7b")
    
    # OpenAI 标准 API 配置 (支持硅基流动、DeepSeek、OpenAI等)
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    # 通用 LLM 配置
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.05))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 60000))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 1200))
    
    SOURCE_LANGUAGE = os.getenv("SOURCE_LANGUAGE", "Chinese")
    TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "English")
    AUTO_DETECT_CHAPTER = os.getenv("AUTO_DETECT_CHAPTER", "true").lower() == "true"
    GLOBAL_GLOSSARY_MEMORY = os.getenv("GLOBAL_GLOSSARY_MEMORY", "true").lower() == "true"
    FORCE_NAME_CONSISTENCY = os.getenv("FORCE_NAME_CONSISTENCY", "true").lower() == "true"
    MERGE_ALIAS = os.getenv("MERGE_ALIAS", "true").lower() == "true"
    MAX_CHUNK_PER_CHAPTER = int(os.getenv("MAX_CHUNK_PER_CHAPTER", 8000))
    CONSISTENCY_CHECK_ENABLE = os.getenv("CONSISTENCY_CHECK_ENABLE", "true").lower() == "true"
    
    CHAPTER_REGEX = os.getenv("CHAPTER_REGEX", r"^第.{1,5}章.*$")
    TITLE_KEEP_FORMAT = os.getenv("TITLE_KEEP_FORMAT", "true").lower() == "true"
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./novel_translate.db")
    SAVE_GLOSSARY_TO_DB = os.getenv("SAVE_GLOSSARY_TO_DB", "true").lower() == "true"

config = Config()
