from .base import (
    BaseProvider,
    ProviderAuth,
    ProviderBasicAuth,
    ProviderAPIKeyAuth,
    AuthResult,
)
from .ollama import OllamaProvider
from .gemini import GeminiProvider
from .groq import GroqProvider

__all__ = [
    "BaseProvider",
    "ProviderAuth",
    "ProviderBasicAuth",
    "ProviderAPIKeyAuth",
    "AuthResult",
    "OllamaProvider",
    "GeminiProvider",
    "GroqProvider",
]

# Registry — lets the UI iterate providers without hardcoding names
PROVIDER_REGISTRY: dict[str, BaseProvider] = {
    "Ollama": OllamaProvider(),
    "Gemini": GeminiProvider(),
    "Groq":   GroqProvider(),
}