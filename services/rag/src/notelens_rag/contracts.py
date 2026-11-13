"""Validate the immutable review snapshot; do not maintain a competing schema."""

import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry
from referencing.exceptions import NoSuchResource


CANDIDATE_COMMIT = "01e96ab6c6a676efb43073a2eca711e89e419030"
MANIFEST_SHA256 = "2c5043aa375a5aef1b0fa3806e8204284218d7b671c48bd8474ac74330c8affa"


class ContractError(ValueError):
    """A pinned artifact or instance violates this provisional contract."""


def require_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError("Non-finite numbers are not permitted.")
    if isinstance(value, dict):
        for nested in value.values(): require_finite(nested)
    elif isinstance(value, list):
        for nested in value: require_finite(nested)


def no_remote_resource(uri):
    raise NoSuchResource(ref=uri)


class Contracts:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else Path(__file__).with_name("contract_data")
        manifest_bytes = (self.directory / "candidate.json").read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
            raise ContractError("Pinned candidate manifest integrity check failed.")
        self.manifest = json.loads(manifest_bytes)
        if self.manifest["candidate_id"] != "p2-rc1" or self.manifest["revision"] != 2:
            raise ContractError("Unexpected contract candidate revision.")
        for name in ("schema.json", "openapi.json"):
            payload = (self.directory / name).read_bytes()
            if hashlib.sha256(payload).hexdigest() != self.manifest["generated_files"][name]:
                raise ContractError("Pinned candidate asset integrity check failed.")
        self.schema = json.loads((self.directory / "schema.json").read_bytes())
        Draft202012Validator.check_schema(self.schema)
        self._validators = {}

    def validate(self, definition, payload):
        require_finite(payload)
        if definition not in self.schema["$defs"]:
            raise ContractError("Unknown contract definition.")
        if definition not in self._validators:
            root = {"$schema": self.schema["$schema"], "$defs": self.schema["$defs"],
                    "$ref": f"#/$defs/{definition}"}
            self._validators[definition] = Draft202012Validator(
                root, format_checker=FormatChecker(), registry=Registry(retrieve=no_remote_resource))
        try:
            self._validators[definition].validate(payload)
        except ValidationError:
            # Validator exception strings contain payload values; never forward or log them.
            raise ContractError("The payload does not match the contract.") from None
