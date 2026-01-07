"""Abstract base class for AI providers."""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    def configure(self):
        """Configure the provider with API key"""
        pass

    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """Generate content from prompt, return text response"""
        pass

    @abstractmethod
    def get_available_models(self) -> list:
        """Return list of available models for this provider"""
        pass

    @abstractmethod
    def handle_error(self, error: Exception) -> str:
        """Provider-specific error handling, return formatted error message"""
        pass
