"""Anthropic Claude AI provider implementation."""
import anthropic

from .base import AIProvider
from src.config import CLAUDE_MODELS


class ClaudeProvider(AIProvider):
    """Anthropic Claude AI provider implementation"""

    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
        self.client = None

    def configure(self):
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_content(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def get_available_models(self) -> list:
        return CLAUDE_MODELS

    def handle_error(self, error: Exception) -> str:
        if hasattr(error, 'status_code'):
            if error.status_code == 429:
                return "Claude API rate limit exceeded"
            elif error.status_code == 401:
                return "Invalid Claude API key"
        return f"Claude API error: {str(error)}"
