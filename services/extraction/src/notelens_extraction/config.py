"""Mock defaults and explicit operator-configured provider execution."""

import os
from dataclasses import dataclass
from decimal import InvalidOperation
from pathlib import Path

from .providers import FakeProvider, UnconfiguredLiveProvider


@dataclass(frozen=True)
class Settings:
    mode: str
    service_token: str | None
    mock_not_ready: bool = False
    provider_policy: str | None = None

    @classmethod
    def from_env(cls):
        return cls(
            mode=os.getenv("NOTELENS_MODE", "mock"),
            service_token=os.getenv("NOTELENS_SERVICE_TOKEN"),
            mock_not_ready=os.getenv("NOTELENS_EXTRACTION_MOCK_NOT_READY") == "1",
            provider_policy=os.getenv("NOTELENS_EXTRACTION_PROVIDER_POLICY"),
        )

    def provider(self):
        if self.mode == "mock":
            return FakeProvider()
        if self.mode == "live" and self.provider_policy:
            from .approved_provider import configured_provider

            try:
                return configured_provider(
                    Path(self.provider_policy), api_key=os.getenv("OPENAI_API_KEY", ""),
                    service_token=self.service_token or "",
                )
            except (OSError, ValueError, TypeError, KeyError, InvalidOperation):
                pass
        return UnconfiguredLiveProvider()
