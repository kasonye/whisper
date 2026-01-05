"""Ollama LLM service wrapper for text formatting and translation."""

import httpx
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable


def clean_llm_output(text: str) -> str:
    """Clean LLM output by removing thinking tags and other artifacts."""
    if not text:
        return ""
    # Remove <think>...</think> blocks (qwen3 thinking mode)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Remove horizontal rules
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # Remove bullet points
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    # Remove hashtags
    text = re.sub(r'#\S+', '', text)
    # Remove emojis (common unicode ranges)
    text = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    # Remove "处理后：" or "翻译：" prefix if present
    text = re.sub(r'^(处理后|翻译)[：:]\s*', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# Default configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "base_url": "http://localhost:11434",
    "default_model": "qwen3:8b",
    "timeout": 300,
    "chunk_size": 4000,
    "chunk_overlap": 200
}

CONFIG_PATH = Path("storage/config/ollama.json")


class OllamaService:
    """Service for interacting with Ollama LLM."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading Ollama config: {e}")
        return DEFAULT_CONFIG.copy()

    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving Ollama config: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration."""
        self.config.update(new_config)
        self._save_config(self.config)
        return self.config.copy()

    async def check_status(self) -> Dict[str, Any]:
        """Check Ollama service status."""
        result = {
            "available": False,
            "url": self.config.get("base_url", "http://localhost:11434"),
            "enabled": self.config.get("enabled", True),
            "models_count": 0,
            "error": None
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config['base_url']}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    result["available"] = True
                    result["models_count"] = len(models)
                else:
                    result["error"] = f"HTTP {response.status_code}"
        except httpx.ConnectError:
            result["error"] = "Cannot connect to Ollama service"
        except httpx.TimeoutException:
            result["error"] = "Connection timeout"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def list_models(self) -> List[str]:
        """List available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config['base_url']}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    return [model["name"] for model in models]
        except Exception as e:
            print(f"Error listing models: {e}")
        return []

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Generate text using Ollama LLM."""
        model = model or self.config.get("default_model", "qwen3:8b")
        timeout = self.config.get("timeout", 300)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.config['base_url']}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    print(f"Ollama generate error: HTTP {response.status_code}")
                    return None
        except Exception as e:
            print(f"Error generating text: {e}")
            return None

    async def format_transcript(
        self,
        text: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Optional[str]:
        """Format transcript text using LLM."""
        if progress_callback:
            await progress_callback(0, "Preparing to format transcript...")

        prompt = f"""/no_think
任务：给语音转录添加标点符号（逗号、句号、问号）和分段。
规则：
- 保留原文每一个字，不得删减或改写
- 不加标题、emoji、总结、解释
- 直接输出处理后的文本

原文：
{text}

处理后："""

        if progress_callback:
            await progress_callback(30, "Sending to LLM for formatting...")

        result = await self.generate(prompt, model)
        result = clean_llm_output(result) if result else None

        if progress_callback:
            await progress_callback(100, "Formatting complete")

        return result

    async def translate_and_format(
        self,
        text: str,
        target_language: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Optional[str]:
        """Translate and format transcript text using LLM."""
        if progress_callback:
            await progress_callback(0, f"Preparing to translate to {target_language}...")

        # Language name mapping
        language_names = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español",
            "ru": "Русский",
            "pt": "Português",
            "it": "Italiano",
            "ar": "العربية",
            "th": "ไทย",
            "vi": "Tiếng Việt"
        }

        target_lang_name = language_names.get(target_language, target_language)

        prompt = f"""/no_think
任务：将语音转录翻译成{target_lang_name}，添加标点符号和分段。
规则：
- 翻译原文全部内容，不得遗漏
- 不加标题、emoji、总结、解释
- 直接输出翻译后的文本

原文：
{text}

翻译："""

        if progress_callback:
            await progress_callback(30, f"Translating to {target_lang_name}...")

        result = await self.generate(prompt, model)
        result = clean_llm_output(result) if result else None

        if progress_callback:
            await progress_callback(100, "Translation complete")

        return result

    async def detect_language(self, text: str, model: Optional[str] = None) -> Optional[str]:
        """Detect the language of the given text."""
        sample = text[:500] if len(text) > 500 else text

        prompt = f"""/no_think
识别语言，只回复语言代码(zh/en/ja/ko/fr/de/es/ru/pt/it/ar/th/vi)：

{sample}"""

        result = await self.generate(prompt, model)
        if result:
            result = clean_llm_output(result).strip().lower()
            for code in ["zh", "en", "ja", "ko", "fr", "de", "es", "ru", "pt", "it", "ar", "th", "vi"]:
                if code in result:
                    return code
        return None


# Global service instance
ollama_service = OllamaService()
