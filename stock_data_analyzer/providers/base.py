from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic


@dataclass
class ProviderBasicAuth:
    username: str
    password: str
    host: str
    host_field: bool = True  # always True for basic auth, keep for UI rendering hint


@dataclass
class ProviderAPIKeyAuth:
    api_key: str
    host: str | None = (
        None  # some API-key providers also need a custom host (e.g. self-hosted)
    )


ProviderAuth = ProviderBasicAuth | ProviderAPIKeyAuth
TAuth = TypeVar("TAuth", bound=ProviderAuth)


@dataclass
class AuthResult:
    success: bool
    error: str | None = None  # human-readable error message on failure


class BaseProvider(ABC, Generic[TAuth]):

    # Subclasses declare what auth type they expect — used by UI to render correct form
    AUTH_TYPE: type[ProviderAuth] = ProviderAPIKeyAuth

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.provider_auth: ProviderAuth | None = None
        self.is_authenticated = False
        self._client: Any = None  # holds the actual SDK client after auth

    # ---- Auth ----
    @abstractmethod
    def authenticate(self, provider_auth: TAuth) -> AuthResult:
        """
        Validate credentials by making a real API call.
        On success: store credentials, set is_authenticated = True, store client.
        On failure: do NOT modify existing state (safe swap guarantee).
        """
        ...

    def logout(self) -> None:
        self.provider_auth = None
        self.is_authenticated = False
        self._client = None

    # ---- Models ----
    @abstractmethod
    def list_models(self) -> list[str]:
        """Return all model IDs available for this provider."""
        ...

    # ---- Inference ----
    @abstractmethod
    def chat(self, model: str, messages: list[dict]) -> str:
        """
        Send a chat request. messages follow OpenAI format:
        [{"role": "system"|"user"|"assistant", "content": "..."}]
        Returns the assistant reply as a plain string.
        """
        ...

    # ---- Serialisation (for localStorage persistence) ----
    def dump_credentials(self) -> dict:
        """Return credentials as a plain dict for storage. Override if needed."""
        if self.provider_auth is None:
            return {}
        return self.provider_auth.__dict__

    def load_credentials(self, data: dict) -> AuthResult:
        """
        Reconstruct auth from a stored dict and re-authenticate.
        Called on page restore.
        """
        try:
            auth = self.AUTH_TYPE(**data)
            return self.authenticate(auth)
        except Exception as e:
            return AuthResult(success=False, error=str(e))

    # ---- Helpers ----
    def _require_auth(self) -> None:
        """Call at the top of list_models() and chat() to guard unauthenticated calls."""
        if not self.is_authenticated or self._client is None:
            raise RuntimeError(f"{self.provider_name} is not authenticated.")

    def __repr__(self) -> str:
        status = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"<{self.__class__.__name__} [{status}]>"
