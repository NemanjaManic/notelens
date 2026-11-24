"""Canonical preparation for one already-decoded MTSamples transcription."""

from dataclasses import dataclass
from hashlib import sha256
import unicodedata


CANONICALIZATION_VERSION = "nfc-lf-v1"
MAX_DOCUMENT_CODE_POINTS = 100_000
# ECMAScript String.prototype.trim whitespace, used only to test for blank input.
_TRIM_WHITESPACE = (
    "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
    "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
)


class PreparationError(ValueError):
    """A safe canonical preparation failure with B's rejection code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class PreparedTranscription:
    text: str
    text_sha256: str
    canonicalization_version: str = CANONICALIZATION_VERSION


def prepare_transcription(decoded_transcription: str) -> PreparedTranscription:
    """Apply nfc-lf-v1 once and hash the exact canonical UTF-8 bytes."""
    if not isinstance(decoded_transcription, str):
        raise PreparationError("invalid-text")
    for count, character in enumerate(decoded_transcription, start=1):
        if 0xD800 <= ord(character) <= 0xDFFF:
            raise PreparationError("invalid-unicode")
        if count > MAX_DOCUMENT_CODE_POINTS:
            raise PreparationError("text-too-large")

    canonical = unicodedata.normalize("NFC", decoded_transcription.replace("\r\n", "\n").replace("\r", "\n"))
    if len(canonical) > MAX_DOCUMENT_CODE_POINTS:
        raise PreparationError("text-too-large")
    if not canonical.strip(_TRIM_WHITESPACE):
        raise PreparationError("empty-text")
    return PreparedTranscription(canonical, sha256(canonical.encode("utf-8")).hexdigest())
