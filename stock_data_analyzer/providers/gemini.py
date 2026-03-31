# providers/gemini.py
from . import BaseProvider, ProviderAPIKeyAuth, AuthResult
import google.generativeai as genai


class GeminiProvider(BaseProvider[ProviderAPIKeyAuth]):

    AUTH_TYPE = ProviderAPIKeyAuth

    def __init__(self):
        super().__init__("Gemini")
        # Gemini has no client object — genai is configured globally.
        # We store a reference to the module itself as the "client"
        # so _require_auth() and logout() work consistently.
        self._client: type[genai] | None = None

    def authenticate(self, provider_auth: ProviderAPIKeyAuth) -> AuthResult:
        try:
            genai.configure(api_key=provider_auth.api_key)
            # Validation call — also filters to only chat-capable models
            models = [
                m
                for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
            if not models:
                return AuthResult(
                    success=False, error="No generateContent models found."
                )
            self._client = genai
            self.provider_auth = provider_auth
            self.is_authenticated = True
            return AuthResult(success=True)
        except Exception as e:
            return AuthResult(success=False, error=str(e))

    def list_models(self) -> list[str]:
        self._require_auth()
        return [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]

    def chat(self, model: str, messages: list[dict]) -> str:
        self._require_auth()

        # Gemini separates system prompt from chat history
        system_prompt = next(
            (m["content"] for m in messages if m["role"] == "system"), None
        )

        # Build history excluding system and the last user message
        history = [
            {
                "role": "user" if m["role"] == "user" else "model",
                "parts": [m["content"]],
            }
            for m in messages[:-1]
            if m["role"] != "system"
        ]

        last_message = messages[-1]["content"]

        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt,
        )
        chat_session = gemini_model.start_chat(history=history)
        response = chat_session.send_message(last_message)
        return response.text
