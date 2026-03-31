from . import BaseProvider, ProviderBasicAuth, AuthResult
from ollama import Client


class OllamaProvider(BaseProvider):

    AUTH_TYPE = ProviderBasicAuth

    def __init__(self):
        super().__init__("Ollama")
        self._client: Client | None = None

    def authenticate(self, provider_auth: ProviderBasicAuth) -> AuthResult:
        try:
            client = Client(
                host=provider_auth.host,
                auth=(provider_auth.username, provider_auth.password),
            )
            client.list()  # validation call
            # Only write state after success
            self._client = client
            self.provider_auth = provider_auth
            self.is_authenticated = True
            return AuthResult(success=True)
        except Exception as e:
            return AuthResult(success=False, error=str(e))

    def list_models(self) -> list[str]:
        self._require_auth()
        assert self._client is not None
        return [m.model for m in self._client.list().models if m.model is not None]

    def chat(self, model: str, messages: list[dict]) -> str:
        self._require_auth()
        assert self._client is not None
        response = self._client.chat(model=model, messages=messages)
        return response["message"]["content"]
