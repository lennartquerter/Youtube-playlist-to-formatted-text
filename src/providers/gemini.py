"""Google Gemini AI provider implementation."""
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import AIProvider
from src.config import GEMINI_MODELS


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation"""

    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def configure(self):
        genai.configure(api_key=self.api_key)

    def generate_content(self, prompt: str) -> str:
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt, safety_settings=self.safety_settings)
        return response.text

    def get_available_models(self) -> list:
        return GEMINI_MODELS

    def handle_error(self, error: Exception) -> str:
        if isinstance(error, ValueError):
            return "Content blocked by Gemini safety filters"
        return f"Gemini API error: {str(error)}"
