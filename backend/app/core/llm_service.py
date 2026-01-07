"""Unified LLM service supporting multiple providers (Ollama, OpenRouter)."""

import httpx
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod


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


# Language name mapping
LANGUAGE_NAMES = {
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


# Default configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "provider": "ollama",
    "ollama": {
        "enabled": True,
        "base_url": "http://localhost:11434",
        "default_model": "qwen3:8b",
        "timeout": 300,
        "chunk_size": 4000,
        "chunk_overlap": 200
    },
    "openrouter": {
        "api_key": "",
        "default_model": "openai/gpt-4o-mini",
        "timeout": 300
    }
}

CONFIG_PATH = Path("storage/config/llm.json")


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def check_status(self) -> Dict[str, Any]:
        """Check provider status."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Generate text using LLM."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

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
            print(f"Error listing Ollama models: {e}")
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
            print(f"Error generating text with Ollama: {e}")
            return None


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter LLM provider."""

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1"

    # Popular models available on OpenRouter
    POPULAR_MODELS = [
        "openai/gpt-4o-mini",
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "google/gemini-pro-1.5",
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.1-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
        "deepseek/deepseek-chat",
        "qwen/qwen-2.5-72b-instruct",
        "qwen/qwen-2.5-7b-instruct",
        "mistralai/mistral-large",
    ]

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def check_status(self) -> Dict[str, Any]:
        """Check OpenRouter service status."""
        result = {
            "available": False,
            "enabled": bool(self.config.get("api_key")),
            "error": None
        }

        api_key = self.config.get("api_key", "")
        if not api_key:
            result["error"] = "API key not configured"
            return result

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.OPENROUTER_API_URL}/models",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Video Transcription App"
                    }
                )
                if response.status_code == 200:
                    result["available"] = True
                elif response.status_code == 401:
                    result["error"] = "Invalid API key"
                else:
                    result["error"] = f"HTTP {response.status_code}"
        except httpx.ConnectError:
            result["error"] = "Cannot connect to OpenRouter"
        except httpx.TimeoutException:
            result["error"] = "Connection timeout"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def list_models(self) -> List[str]:
        """List available models from OpenRouter."""
        api_key = self.config.get("api_key", "")
        if not api_key:
            return self.POPULAR_MODELS

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.OPENROUTER_API_URL}/models",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Video Transcription App"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    return [model["id"] for model in models]
        except Exception as e:
            print(f"Error listing OpenRouter models: {e}")
        return self.POPULAR_MODELS

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Generate text using OpenRouter API."""
        model = model or self.config.get("default_model", "openai/gpt-4o-mini")
        timeout = self.config.get("timeout", 300)
        api_key = self.config.get("api_key", "")

        if not api_key:
            print("OpenRouter API key not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.OPENROUTER_API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Video Transcription App",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    return ""
                else:
                    print(f"OpenRouter generate error: HTTP {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"Error details: {error_data}")
                    except:
                        pass
                    return None
        except Exception as e:
            print(f"Error generating text with OpenRouter: {e}")
            return None


class LLMService:
    """Unified LLM service supporting multiple providers."""

    def __init__(self):
        self.config = self._load_config()
        self._init_providers()

    def _init_providers(self):
        """Initialize LLM providers."""
        self.ollama = OllamaProvider(self.config.get("ollama", {}))
        self.openrouter = OpenRouterProvider(self.config.get("openrouter", {}))

    def _get_current_provider(self) -> BaseLLMProvider:
        """Get the currently selected provider."""
        provider_name = self.config.get("provider", "ollama")
        if provider_name == "openrouter":
            return self.openrouter
        return self.ollama

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        # Also check for legacy ollama.json config
        legacy_path = Path("storage/config/ollama.json")

        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading LLM config: {e}")
        elif legacy_path.exists():
            # Migrate from legacy config
            try:
                with open(legacy_path, 'r', encoding='utf-8') as f:
                    legacy_config = json.load(f)
                    new_config = DEFAULT_CONFIG.copy()
                    new_config["ollama"] = legacy_config
                    new_config["enabled"] = legacy_config.get("enabled", True)
                    self._save_config(new_config)
                    return new_config
            except Exception as e:
                print(f"Error migrating legacy config: {e}")

        return DEFAULT_CONFIG.copy()

    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving LLM config: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration."""
        self.config.update(new_config)
        self._save_config(self.config)
        self._init_providers()  # Re-initialize providers with new config
        return self.config.copy()

    async def check_status(self) -> Dict[str, Any]:
        """Check current provider status."""
        provider_name = self.config.get("provider", "ollama")

        result = {
            "enabled": self.config.get("enabled", True),
            "provider": provider_name,
            "ollama": None,
            "openrouter": None
        }

        # Check the active provider
        if provider_name == "ollama":
            result["ollama"] = await self.ollama.check_status()
        else:
            result["openrouter"] = await self.openrouter.check_status()

        return result

    async def check_ollama_status(self) -> Dict[str, Any]:
        """Check Ollama service status specifically."""
        return await self.ollama.check_status()

    async def check_openrouter_status(self) -> Dict[str, Any]:
        """Check OpenRouter service status specifically."""
        return await self.openrouter.check_status()

    async def list_models(self, provider: Optional[str] = None) -> List[str]:
        """List available models for the specified or current provider."""
        if provider == "ollama":
            return await self.ollama.list_models()
        elif provider == "openrouter":
            return await self.openrouter.list_models()
        else:
            return await self._get_current_provider().list_models()

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Generate text using the current LLM provider."""
        if not self.config.get("enabled", True):
            return None
        return await self._get_current_provider().generate(prompt, model, progress_callback)

    async def format_transcript(
        self,
        text: str,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Optional[str]:
        """Format transcript text using LLM."""
        if not self.config.get("enabled", True):
            return None

        if progress_callback:
            await progress_callback(0, "Preparing to format transcript...")

        prompt = f"""你是一个专业的文字整理助手。请对以下语音转录文本进行格式化处理。

## 任务要求

对语音转录内容添加适当的标点符号和段落分隔，使其更易阅读。

## 处理规则

1. **保持原文完整**：保留每一个字词，不删减、不改写、不添加内容
2. **添加标点符号**：根据语义和停顿添加逗号、句号、问号、感叹号等
3. **合理分段**：根据话题或语义变化进行段落划分
4. **输出要求**：直接输出处理后的文本，不要添加标题、说明、总结或任何额外内容

## 原文内容

{text}

## 处理结果

"""

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
        if not self.config.get("enabled", True):
            return None

        if progress_callback:
            await progress_callback(0, f"Preparing to translate to {target_language}...")

        target_lang_name = LANGUAGE_NAMES.get(target_language, target_language)

        prompt = f"""你是一个专业的翻译和文字整理助手。请将以下语音转录文本翻译成{target_lang_name}，并进行格式化处理。

## 任务要求

将原文翻译成{target_lang_name}，同时添加适当的标点符号和段落分隔。

## 处理规则

1. **完整翻译**：翻译全部内容，不得遗漏任何部分
2. **准确传达**：保持原文的语义和语气
3. **添加标点**：根据目标语言习惯添加适当的标点符号
4. **合理分段**：根据内容逻辑进行段落划分
5. **输出要求**：直接输出翻译后的文本，不要添加标题、说明、总结或任何额外内容

## 原文内容

{text}

## 翻译结果

"""

        if progress_callback:
            await progress_callback(30, f"Translating to {target_lang_name}...")

        result = await self.generate(prompt, model)
        result = clean_llm_output(result) if result else None

        if progress_callback:
            await progress_callback(100, "Translation complete")

        return result

    async def detect_language(self, text: str, model: Optional[str] = None) -> Optional[str]:
        """Detect the language of the given text."""
        if not self.config.get("enabled", True):
            return None

        sample = text[:500] if len(text) > 500 else text

        prompt = f"""请识别以下文本的语言，只需回复对应的语言代码。

可选的语言代码：zh（中文）、en（英文）、ja（日语）、ko（韩语）、fr（法语）、de（德语）、es（西班牙语）、ru（俄语）、pt（葡萄牙语）、it（意大利语）、ar（阿拉伯语）、th（泰语）、vi（越南语）

文本内容：
{sample}

语言代码："""

        result = await self.generate(prompt, model)
        if result:
            result = clean_llm_output(result).strip().lower()
            for code in ["zh", "en", "ja", "ko", "fr", "de", "es", "ru", "pt", "it", "ar", "th", "vi"]:
                if code in result:
                    return code
        return None


# Global service instance
llm_service = LLMService()

# Keep backward compatibility with ollama_service
ollama_service = llm_service
