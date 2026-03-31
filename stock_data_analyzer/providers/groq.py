from . import BaseProvider, ProviderAPIKeyAuth, AuthResult
from groq import Groq


class GroqProvider(BaseProvider[ProviderAPIKeyAuth]):

    AUTH_TYPE = ProviderAPIKeyAuth

    def __init__(self):
        super().__init__("Groq")
        self._client: Groq | None = None

    def authenticate(self, provider_auth: ProviderAPIKeyAuth) -> AuthResult:
        try:
            client = Groq(api_key=provider_auth.api_key)
            client.models.list()  # validation call
            self._client = client
            self.provider_auth = provider_auth
            self.is_authenticated = True
            return AuthResult(success=True)
        except Exception as e:
            return AuthResult(success=False, error=str(e))

    def list_models(self) -> list[str]:
        self._require_auth()
        assert self._client is not None
        return sorted([m.id for m in self._client.models.list().data])

    def chat(self, model: str, messages: list[dict]) -> str:
        self._require_auth()
        assert self._client is not None
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
        )
        return response.choices[0].message.content or ""
