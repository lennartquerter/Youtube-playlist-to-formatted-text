"""Factory for creating AI provider instances."""
from .base import AIProvider
from .gemini import GeminiProvider
from .claude import ClaudeProvider
from .chatgpt import ChatGPTProvider


class AIProviderFactory:
    """Factory to create provider instances"""

    @staticmethod
    def create_provider(provider_name: str, api_key: str, model_name: str) -> AIProvider:
        providers = {
            "Gemini": GeminiProvider,
            "Claude": ClaudeProvider,
            "ChatGPT": ChatGPTProvider
        }

        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        return providers[provider_name](api_key, model_name)
