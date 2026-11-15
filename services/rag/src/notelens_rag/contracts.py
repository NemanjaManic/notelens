"""Apply B's frozen runtime validators with fixed, safe service diagnostics."""

import hashlib
from importlib.resources import files
from pathlib import Path

from notelens_contracts.v1 import ContractValidationError, validate_json, validate_record


SCHEMA_SHA256 = '707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78'


class ContractError(ValueError):
    """A frozen record fails validation; never forward payloads or issue paths."""


class ContractJsonError(ContractError):
    """The wire input is malformed, duplicated or contains non-finite numbers."""


class Contracts:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else files('notelens_contracts')
        try:
            digest = hashlib.sha256((self.directory / 'schema.json').read_bytes()).hexdigest()
        except OSError:
            raise ContractError('The frozen schema is unavailable.') from None
        if digest != SCHEMA_SHA256:
            raise ContractError('The installed schema does not match the frozen contract.')

    def validate(self, definition, payload):
        try:
            return validate_record(definition, payload)
        except ContractValidationError:
            raise ContractError('The payload does not match the frozen contract.') from None

    def parse(self, definition, wire):
        try:
            return validate_json(definition, wire)
        except ContractValidationError as failure:
            if any(issue.rule == 'JSON_INPUT' for issue in failure.issues):
                raise ContractJsonError('A valid finite JSON body without duplicate keys is required.') from None
            raise ContractError('The request does not match the frozen contract.') from None
