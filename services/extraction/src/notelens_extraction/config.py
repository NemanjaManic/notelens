"""Local configuration. No approved live provider/model is present in this checkout."""

import os
from dataclasses import dataclass

from .providers import FakeProvider, UnconfiguredLiveProvider


@dataclass(frozen=True)
class Settings:
    mode: str
    service_token: str | None
    mock_not_ready: bool = False

    @classmethod
    def from_env(cls):
        return cls(
            mode=os.getenv("NOTELENS_MODE", "mock"),
            service_token=os.getenv("NOTELENS_SERVICE_TOKEN"),
            mock_not_ready=os.getenv("NOTELENS_EXTRACTION_MOCK_NOT_READY") == "1",
        )

    def provider(self):
        # Any non-mock setting fails closed. No guessed model/budget or SDK call.
        return FakeProvider() if self.mode == "mock" else UnconfiguredLiveProvider()
