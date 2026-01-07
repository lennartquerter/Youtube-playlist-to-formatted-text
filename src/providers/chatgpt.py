"""OpenAI ChatGPT provider implementation."""
import openai

from .base import AIProvider
from src.config import CHATGPT_MODELS


class ChatGPTProvider(AIProvider):
    """OpenAI ChatGPT provider implementation"""

    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
        self.client = None

    def configure(self):
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_content(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        return response.choices[0].message.content

    def get_available_models(self) -> list:
        return CHATGPT_MODELS

    def handle_error(self, error: Exception) -> str:
        if hasattr(error, 'status_code'):
            if error.status_code == 429:
                return "OpenAI API rate limit exceeded"
            elif error.status_code == 401:
                return "Invalid OpenAI API key"
        return f"ChatGPT API error: {str(error)}"
