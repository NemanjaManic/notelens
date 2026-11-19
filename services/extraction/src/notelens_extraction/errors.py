from dataclasses import dataclass


@dataclass
class ServiceError(Exception):
    status: int
    code: str
    message: str
    retryable: bool = False

    def envelope(self, request_id: str) -> dict:
        return {"schema_version": "1.0.0", "request_id": request_id,
                "error": {"code": self.code, "message": self.message,
                          "retryable": self.retryable}}
